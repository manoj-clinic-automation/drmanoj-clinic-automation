#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""darpan_app.py — Darpan's day card, exceptions-first, as a blueprint.

THE OPERATING MODEL (owner, 29-Aug-2026, final)
    The two truths arrive by themselves each morning -- the bank MPR and
    Marg's sale export -- and bank_match.py ties them together by 09:45.
    Darpan is a CHECKER, not a source: everything the server can verify it
    verifies silently, and he sees only what the two truths could not settle
    between themselves. On a clean day his whole morning is one tap.

    Evening: he counts the drawer and types ONE number. Mandatory.
    Morning: the card, in HIS convention -- the order his Marg report reads:
        1 day sale (net of returns), CN bills expandable
        2 UPI (his word for non-cash), matched bills under it
        3 net cash = day sale - UPI - home medicines - procedure medicines
          (home and procedure are billed but their money never enters the
           drawer -- owner-ruled, and v_cash_ledger has said so since S179)
        4 categories: home | procedure | orthotics, expandable to detail
        5 bank (MPR), collapsed by default
        6 exceptions, only when they exist -- two taps each
        7 drawer: his count vs the ledger's expected closing, tolerance Rs 50

WHAT THIS FILE DELIBERATELY DOES NOT DO
    It never edits Marg, never touches sale_item/day_entry money paths, and
    never deletes anything except a data_flag the owner explicitly dismisses.
    A no-identity bill is NEVER Darpan's to fix and never fixed in Marg
    (owner-ruled): it queues for the owner or Amir, in our records only.

INSTALL: two lines in finance_app.py, by patch_finance_app_darpan.py.
Flask and the standard library only, to match the app it joins.
"""
import datetime as dt
import io
import json
import os
import sqlite3
import sys

from flask import Blueprint, jsonify, request, send_file

HERE = os.path.dirname(os.path.abspath(__file__))

bp = Blueprint("darpan", __name__)

_db = None
_require = None
_unit = "medical"

TOLERANCE_P = 5000              # Rs 50, owner-ruled 29-Aug
FILE_BLOCK_STATUSES = ("submitted", "approved", "locked")

ANSWERS = ("was_upi", "not_upi", "attach_bill", "advance", "dont_know")


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ensure_schema(con):
    """Idempotent; safe on every boot, safe twice."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_day ("
        " unit TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " counted_p INTEGER,"
        " counted_by TEXT, counted_at TEXT,"
        " status TEXT NOT NULL DEFAULT 'open'"
        "   CHECK (status IN ('open','verified','escalated')),"
        " submitted_by TEXT, submitted_at TEXT,"
        " PRIMARY KEY (unit, business_date))")
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_advance ("
        " id INTEGER PRIMARY KEY,"
        " unit TEXT NOT NULL,"
        " received_date TEXT NOT NULL,"
        " amount_p INTEGER NOT NULL,"
        " rrn TEXT,"
        " note TEXT,"
        " status TEXT NOT NULL DEFAULT 'open'"
        "   CHECK (status IN ('open','reconciled')),"
        " bill_no TEXT, bill_date TEXT,"
        " created_by TEXT, created_at TEXT,"
        " reconciled_by TEXT, reconciled_at TEXT)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_correction ("
        " id INTEGER PRIMARY KEY,"
        " match_id INTEGER NOT NULL UNIQUE,"
        " ticked_by TEXT NOT NULL,"
        " ticked_at TEXT NOT NULL,"
        " note TEXT)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_grant ("
        " id INTEGER PRIMARY KEY,"
        " unit TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " granted_by TEXT NOT NULL,"
        " granted_at TEXT NOT NULL,"
        " used_at TEXT)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_return_approval ("
        " id INTEGER PRIMARY KEY,"
        " unit TEXT NOT NULL,"
        " cn_bill TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'pending'"
        "   CHECK (status IN ('pending','approved','rejected')),"
        " decided_by TEXT, decided_at TEXT, note TEXT,"
        " UNIQUE (unit, cn_bill))")
    con.execute(
        "CREATE TABLE IF NOT EXISTS darpan_audit ("
        " id INTEGER PRIMARY KEY,"
        " at TEXT NOT NULL, who TEXT NOT NULL,"
        " action TEXT NOT NULL, detail TEXT)")
    con.commit()


def _audit(con, who, action, detail):
    con.execute("INSERT INTO darpan_audit (at, who, action, detail) "
                "VALUES (?,?,?,?)", (now_iso(), who, action,
                                     json.dumps(detail)[:500]))


def _owners(con):
    """Usernames allowed the owner-only tools. A SETTING, never hard-coded."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='darpan.owners'"
                        ).fetchone()
        v = (r[0] if r else "") or ""
    except sqlite3.OperationalError:
        v = ""
    return set(w.strip().lower() for w in (v or "manoj").split(",") if w.strip())


def _is_owner(con, u):
    return str(u.get("user", "")).lower() in _owners(con)


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r else default) or default
    except sqlite3.OperationalError:
        return default


def init(app, db_getter, require_fn, unit="medical"):
    """Mount. Also installs the duplicate-filing guard on the EXISTING filing
    endpoint: a second form for an already-filed date is refused with 'ask
    the owner', unless an unused owner grant exists for that date. The guard
    lives here, before_request, so the 11,000-line core is not edited."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)

    @app.before_request
    def _darpan_refile_guard():
        if request.path.rstrip("/") != "/finance/api/day" or request.method != "POST":
            return None
        # THE SWITCH, and why it exists: the app's own filing flow saves a day
        # through REPEATED posts -- an advance, a non-cash bill, a correction
        # each re-save the same date. A guard that reads every re-save as "a
        # second form" breaks the app (the smoke suite proved it: 722 -> 706).
        # So the guard ships OFF and the owner turns it on -- once Darpan is
        # on the day card and no longer files this form at all, a re-save IS
        # a second form, and blocking it is finally true.
        con0 = _db()
        ensure_schema(con0)
        if _setting(con0, "darpan.refile_guard", "0") != "1":
            return None
        p = request.get_json(silent=True) or {}
        d = str(p.get("business_date") or "").strip()
        if not d:
            return None                      # the endpoint's own validation answers
        con = _db()
        ensure_schema(con)
        row = con.execute(
            "SELECT status FROM day_entry WHERE unit=? AND business_date=?",
            (_unit, d)).fetchone()
        status = row[0] if row else None
        if status not in FILE_BLOCK_STATUSES:
            return None                      # new day, or a draft being edited
        g = con.execute(
            "SELECT id FROM darpan_grant WHERE unit=? AND business_date=? "
            "AND used_at IS NULL ORDER BY id LIMIT 1", (_unit, d)).fetchone()
        if g:
            con.execute("UPDATE darpan_grant SET used_at=? WHERE id=?",
                        (now_iso(), g[0]))
            _audit(con, "system", "refile_grant_used", {"date": d, "grant": g[0]})
            con.commit()
            return None
        return jsonify(ok=False, error="already_filed",
                       message="%s is already filed (%s). Yeh din pehle se "
                               "bhara hai -- dobara bharne ke liye doctor "
                               "sahab se kahiye; unke portal par 'allow "
                               "re-file' hai." % (d, status)), 403

    return bp


# ------------------------------------------------------------------ pages
@bp.route("/finance/darpan")
def page_card():
    u, err = _require("maker", "checker")
    if err:
        return err
    return send_file(os.path.join(HERE, "darpan_card.html"))


@bp.route("/finance/darpan/corrections")
def page_corrections():
    # S221 AMIR VIEWER -- this desk is Amir's by the S218 contract; viewer is
    # how named staff hold one desk without unit-wide authority (S214).
    u, err = _require("checker", "viewer")
    if err:
        return err
    return send_file(os.path.join(HERE, "darpan_corrections.html"))


# ------------------------------------------------------------------ card
def _ortho_words(con):
    v = _setting(con, "orthotics.vocab")
    return [w.strip().lower() for w in v.split(",") if w.strip()]


def _sms_p(con, iso):
    """S295: the bank's settlement SMS total for this day (bank_sms.py, S290), or None. Early signal only."""
    try:
        import bank_sms                                              # noqa: PLC0415
        return bank_sms.sms_total_p(con, _unit, iso)
    except Exception:                                                # noqa: BLE001
        return None


@bp.route("/finance/darpan/api/card")
def api_card():
    u, err = _require("maker", "checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    iso = str(request.args.get("date") or "").strip() or \
        (dt.date.today() - dt.timedelta(days=1)).isoformat()

    # ---- 1 · day sale, net of returns, CN bills expandable ----
    sale = con.execute(
        "SELECT COALESCE(SUM(CASE WHEN si.service NOT LIKE '%return%' "
        "  THEN si.amount_p END),0) sold, "
        " COALESCE(SUM(CASE WHEN si.service LIKE '%return%' "
        "  THEN si.amount_p END),0) returned "
        "FROM sale_item si JOIN day_entry e ON e.id=si.day_entry_id "
        "WHERE e.unit=? AND e.business_date=?", (_unit, iso)).fetchone()
    sold_p = int(sale["sold"] or 0)
    ret_p = int(sale["returned"] or 0)
    cn_bills = [dict(bill=r["source_ref"], amount_p=int(r["amount_p"] or 0))
                for r in con.execute(
                    "SELECT si.source_ref, si.amount_p FROM sale_item si "
                    "JOIN day_entry e ON e.id=si.day_entry_id "
                    "WHERE e.unit=? AND e.business_date=? "
                    "AND si.service LIKE '%return%'", (_unit, iso))]
    # S220 F-282: the bills parked for review are Marg's sales too -- only the
    # patient is unknown. Their SIGNED money (v_day_attribution, S180) joins the
    # day sale, and the card shows them as identity still owed.
    _va = con.execute("SELECT in_review_p, in_review_count FROM v_day_attribution "
                      "WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    review_p = int(_va["in_review_p"] or 0) if _va is not None else 0
    review_n = int(_va["in_review_count"] or 0) if _va is not None else 0
    day_sale_p = sold_p - ret_p + review_p
    # S220 F-282b: the parked bills themselves, so Darpan sees WHICH need a name.
    # Bill, rupees (signed -- a parked return shows negative), the name as typed,
    # the phone's last four. Never the whole number.
    review_bills = []
    try:
        import json as _json                                        # noqa: PLC0415
        for r in con.execute(
                "SELECT r.raw_text, r.guess_name, r.guess_clinic_id, r.amount_p FROM sale_item_review r "
                "JOIN day_entry e ON e.id=r.day_entry_id "
                "WHERE e.unit=? AND e.business_date=? AND r.status='open' ORDER BY r.id",
                (_unit, iso)):
            try:
                raw = _json.loads(r["raw_text"] or "{}")
            except Exception:                                       # noqa: BLE001
                raw = {}
            review_bills.append(dict(
                bill=(raw.get("bill_no") or "?"), amount_p=int(r["amount_p"] or 0),
                name=(r["guess_name"] or raw.get("patient_name") or ""),
                clinic_id=(r["guess_clinic_id"] or raw.get("clinic_id") or ""),
                mobile=(raw.get("mobile") or ""),   # S220 FULL MOBILE (owner's ruling)
                last4=(raw.get("phone_last4") or "")))
    except Exception:                                               # noqa: BLE001
        review_bills = []

    # ---- 2 · UPI, with the matched bills under it ----
    upi_bills = [dict(bill=r["bill_no"], amount_p=int(r["txn_amount_p"] or 0),
                      rrn=r["rrn"])
                 for r in con.execute(
                     "SELECT bill_no, txn_amount_p, rrn FROM upi_match "
                     "WHERE unit=? AND business_date=? AND status='agreed' "
                     "ORDER BY txn_amount_p DESC", (_unit, iso))]
    upi_p = sum(b["amount_p"] for b in upi_bills)

    # ---- 4 · categories ----
    heads = {}
    for r in con.execute(
            "SELECT b.head, b.bill_no, b.amount_p FROM day_noncash_bill b "
            "JOIN day_entry e ON e.id=b.day_entry_id "
            "WHERE e.unit=? AND e.business_date=?", (_unit, iso)):
        heads.setdefault(r["head"], []).append(
            dict(bill=r["bill_no"], amount_p=int(r["amount_p"] or 0)))
    home = heads.get("home_medicine", [])
    proc = heads.get("procedure_medicine", [])
    home_p = sum(x["amount_p"] for x in home)
    proc_p = sum(x["amount_p"] for x in proc)

    ortho, ortho_p = [], 0
    words = _ortho_words(con)
    if words:
        like = " OR ".join(["lower(item_name) LIKE ?"] * len(words))
        args = ["%" + w + "%" for w in words]
        for r in con.execute(
                "SELECT item_name, qty_raw, COALESCE(amount_p,0) amount_p "
                "FROM sale_line_item WHERE unit=? AND business_date=? "
                "AND is_return=0 AND (" + like + ") ORDER BY amount_p DESC",
                [_unit, iso] + args):
            ortho.append(dict(item=r["item_name"], qty=r["qty_raw"],
                              amount_p=int(r["amount_p"] or 0)))
            ortho_p += int(r["amount_p"] or 0)

    # ---- 3 · net cash, the owner's formula ----
    net_cash_p = day_sale_p - upi_p - home_p - proc_p

    # ---- 5 · bank, collapsed ----
    md = con.execute("SELECT * FROM upi_match_day WHERE unit=? AND "
                     "business_date=?", (_unit, iso)).fetchone()
    txns = [dict(amount_p=r["amount_p"], rrn=r["rrn"], mode=r["mode"],
                 time=r["txn_time"])
            for r in con.execute(
                "SELECT amount_p, rrn, mode, txn_time FROM upi_txn "
                "WHERE unit=? AND txn_date=? ORDER BY amount_p DESC",
                (_unit, iso))]

    # ---- 6 · exceptions, unanswered only ----
    exceptions = [dict(id=r["id"], kind=r["status"], bill=r["bill_no"],
                       bill_amount_p=r["bill_amount_p"],
                       txn_amount_p=r["txn_amount_p"], rrn=r["rrn"],
                       time=r["txn_time"])
                  for r in con.execute(
                      "SELECT * FROM upi_match WHERE unit=? AND business_date=? "
                      "AND status IN ('cash','bank_orphan','bill_orphan') "
                      "AND resolved IS NULL ORDER BY status, txn_amount_p DESC",
                      (_unit, iso))]

    # ---- 7 · drawer ----
    led = con.execute("SELECT opening_p, closing_p, expense_p, cash_out_p, "
                      "cash_back_p, noncash_p, cash_in_p FROM v_cash_ledger "
                      "WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    dd = con.execute("SELECT * FROM darpan_day WHERE unit=? AND business_date=?",
                     (_unit, iso)).fetchone()
    drawer = dict(counted_p=(dd["counted_p"] if dd else None),
                  counted_at=(dd["counted_at"] if dd else None),
                  expected_p=(int(led["closing_p"]) if led else None),
                  tolerance_p=TOLERANCE_P, show=False, parts=None)
    if drawer["counted_p"] is not None and drawer["expected_p"] is not None:
        gap = drawer["counted_p"] - drawer["expected_p"]
        drawer["gap_p"] = gap
        drawer["show"] = abs(gap) > TOLERANCE_P
        if drawer["show"] and led:
            drawer["parts"] = dict(opening_p=int(led["opening_p"] or 0),
                                   cash_in_p=int(led["cash_in_p"] or 0),
                                   noncash_p=int(led["noncash_p"] or 0),
                                   expense_p=int(led["expense_p"] or 0),
                                   cash_out_p=int(led["cash_out_p"] or 0),
                                   cash_back_p=int(led["cash_back_p"] or 0))

    e = con.execute("SELECT status FROM day_entry WHERE unit=? AND "
                    "business_date=?", (_unit, iso)).fetchone()
    return jsonify(ok=True, date=iso, unit=_unit,
                   filed_status=(e["status"] if e else None),
                   day_status=(dd["status"] if dd else "open"),
                   sale=dict(day_sale_p=day_sale_p, sold_p=sold_p,
                             review_p=review_p, review_n=review_n,   # S220 F-282
                             review_bills=review_bills,             # S220 F-282b
                             returned_p=ret_p, cn_bills=cn_bills),
                   upi=dict(total_p=upi_p, bills=upi_bills),
                   net_cash_p=net_cash_p,
                   categories=dict(
                       home=dict(total_p=home_p, bills=home),
                       procedure=dict(total_p=proc_p, bills=proc),
                       orthotics=dict(total_p=ortho_p, items=ortho)),
                   bank=dict(day=(dict(md) if md else None), txns=txns, sms_p=_sms_p(con, iso)),
                   exceptions=exceptions, drawer=drawer)


# ------------------------------------------------------------------ drawer
@bp.route("/finance/darpan/api/drawer", methods=["POST"])
def api_drawer():
    u, err = _require("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    try:
        counted = int(b.get("counted_p"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount",
                       message="Ginti ka amount samajh nahin aaya."), 400
    if not iso or counted < 0:
        return jsonify(ok=False, error="bad_request"), 400
    con = _db()
    ensure_schema(con)
    con.execute(
        "INSERT INTO darpan_day (unit, business_date, counted_p, counted_by, "
        " counted_at) VALUES (?,?,?,?,?) "
        "ON CONFLICT(unit, business_date) DO UPDATE SET counted_p=excluded.counted_p, "
        " counted_by=excluded.counted_by, counted_at=excluded.counted_at",
        (_unit, iso, counted, u["user"], now_iso()))
    _audit(con, u["user"], "drawer_count", {"date": iso, "counted_p": counted})
    con.commit()
    return jsonify(ok=True, date=iso, counted_p=counted)


# --------------------------------------------------------------- exceptions
@bp.route("/finance/darpan/api/exception/<int:mid>/answer", methods=["POST"])
def api_answer(mid):
    u, err = _require("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ans = str(b.get("answer") or "").strip()
    if ans not in ANSWERS:
        return jsonify(ok=False, error="bad_answer",
                       message="answer must be one of %s" % (ANSWERS,)), 400
    con = _db()
    ensure_schema(con)
    row = con.execute("SELECT * FROM upi_match WHERE id=? AND unit=?",
                      (mid, _unit)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    if row["resolved"]:
        return jsonify(ok=False, error="already_answered",
                       message="answered by %s at %s"
                               % (row["resolved"], row["resolved_at"])), 409

    note = str(b.get("note") or "")[:200]
    resolution = ans
    if ans == "attach_bill":
        bill = str(b.get("bill_no") or "").strip().upper()
        if not bill:
            return jsonify(ok=False, error="bill_required",
                           message="Kaunsa bill? Bill number chahiye."), 400
        resolution = "attach:%s" % bill
    if ans == "advance":
        con.execute(
            "INSERT INTO darpan_advance (unit, received_date, amount_p, rrn, "
            " note, created_by, created_at) VALUES (?,?,?,?,?,?,?)",
            (_unit, row["business_date"], row["txn_amount_p"], row["rrn"],
             note or "advance -- bill later", u["user"], now_iso()))
    if ans in ("not_upi", "dont_know"):
        con.execute(
            "INSERT INTO data_flag (unit, business_date, code, severity, detail) "
            "VALUES (?,?, 'DARPAN_ESCALATION', 'high', ?)",
            (_unit, row["business_date"],
             ("%s: bill %s / bank %s (RRN %s) -- %s by %s"
              % (row["status"], row["bill_no"] or "-",
                 row["txn_amount_p"], row["rrn"] or "-", ans, u["user"]))[:400]))
    con.execute("UPDATE upi_match SET resolved=?, resolved_at=?, resolution=? "
                "WHERE id=?", (u["user"], now_iso(), resolution + (
                    (" | " + note) if note and ans != "advance" else ""), mid))
    _audit(con, u["user"], "exception_answer",
           {"id": mid, "answer": ans, "note": note})
    con.commit()
    return jsonify(ok=True, id=mid, answer=ans)


# ------------------------------------------------------------------ submit
@bp.route("/finance/darpan/api/handover", methods=["POST"])
def api_handover():
    """S210 (handover) -- Darpan records a drawer transfer: bank deposit, to a doctor, or
    a doctor's RETURN to the drawer. One cash_movement row (S194 convention),
    anchored to the latest filed day. Refuses a handover already recorded as
    a custody event for the same date+party+amount -- one handover, ONE
    record (S210 boundary finding: the app SUMS the two tables)."""
    u, err = _require("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    KINDS = {"bank":        ("out", "bank"),
             "to_bhawna":   ("out", "dr_bhawna"),
             "to_manoj":    ("out", "dr_manoj"),
             "back_bhawna": ("in",  "dr_bhawna"),
             "back_manoj":  ("in",  "dr_manoj")}
    kind = str(b.get("kind") or "").strip()
    if kind not in KINDS:
        return jsonify(ok=False, error="bad_kind", kinds=sorted(KINDS)), 400
    try:
        amt_p = int(round(float(b.get("amount") or 0) * 100))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount"), 400
    if amt_p <= 0:
        return jsonify(ok=False, error="amount_must_be_positive"), 400
    note = str(b.get("note") or "").strip()[:120]
    direction, party = KINDS[kind]
    con = _db()
    ensure_schema(con)
    today = dt.date.today().isoformat()
    anchor = con.execute(
        "SELECT id, business_date FROM day_entry WHERE unit=? AND "
        "business_date<=? ORDER BY business_date DESC LIMIT 1",
        (_unit, today)).fetchone()
    if not anchor:
        return jsonify(ok=False, error="no_filed_day",
                       message="koi din file nahin hua -- pehle din ki "
                               "report load honi chahiye"), 409
    dup = con.execute(
        "SELECT id FROM cash_custody_event WHERE unit=? AND amount_p=? "
        "AND (from_party=? OR to_party=?) AND event_date>=?",
        (_unit, amt_p, party, party, anchor["business_date"])).fetchone()
    if dup:
        return jsonify(ok=False, error="already_recorded",
                       message="yeh handover pehle se owner transfer mein "
                               "likha hai -- dubara likhne se hisaab double "
                               "ho jayega"), 409
    ref = ("[darpan handover] %s%s" % (kind, (" -- " + note) if note else ""))[:120]
    con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, "
                "amount_p, reference) VALUES (?,?,?,?,?)",
                (anchor["id"], direction, party, amt_p, ref))
    _audit(con, u["user"], "darpan_handover",
           {"kind": kind, "amount_p": amt_p, "party": party,
            "direction": direction, "anchor_date": anchor["business_date"],
            "note": note})
    con.commit()
    return jsonify(ok=True, kind=kind, amount_p=amt_p,
                   anchor_date=anchor["business_date"])


@bp.route("/finance/darpan/api/submit", methods=["POST"])
def api_submit():
    u, err = _require("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    if not iso:
        return jsonify(ok=False, error="bad_request"), 400
    con = _db()
    ensure_schema(con)
    open_ex = con.execute(
        "SELECT COUNT(*) FROM upi_match WHERE unit=? AND business_date=? "
        "AND status IN ('cash','bank_orphan','bill_orphan') AND resolved IS NULL",
        (_unit, iso)).fetchone()[0]
    if open_ex:
        return jsonify(ok=False, error="exceptions_open",
                       message="%d sawaal baaki hain -- pehle unka jawab "
                               "dijiye." % open_ex), 400
    dd = con.execute("SELECT counted_p FROM darpan_day WHERE unit=? AND "
                     "business_date=?", (_unit, iso)).fetchone()
    if _setting(con, "darpan.drawer_mandatory", "1") == "1" and \
            (not dd or dd["counted_p"] is None):
        return jsonify(ok=False, error="drawer_missing",
                       message="Shaam ki ginti nahin hui -- pehle drawer "
                               "giniye."), 400
    escalated = con.execute(
        "SELECT COUNT(*) FROM upi_match WHERE unit=? AND business_date=? "
        "AND (resolution LIKE 'not_upi%' OR resolution LIKE 'dont_know%')",
        (_unit, iso)).fetchone()[0]
    status = "escalated" if escalated else "verified"
    con.execute(
        "INSERT INTO darpan_day (unit, business_date, status, submitted_by, "
        " submitted_at) VALUES (?,?,?,?,?) "
        "ON CONFLICT(unit, business_date) DO UPDATE SET status=excluded.status, "
        " submitted_by=excluded.submitted_by, submitted_at=excluded.submitted_at",
        (_unit, iso, status, u["user"], now_iso()))
    _audit(con, u["user"], "day_submit", {"date": iso, "status": status})
    con.commit()
    return jsonify(ok=True, date=iso, status=status)


# -------------------------------------------------------------- corrections
@bp.route("/finance/darpan/api/corrections")
def api_corrections():
    u, err = _require("checker", "viewer")          # S221 AMIR VIEWER
    if err:
        return err
    con = _db()
    ensure_schema(con)
    month = str(request.args.get("month") or "").strip() or \
        dt.date.today().isoformat()[:7]
    rows = []
    for r in con.execute(
            "SELECT m.*, c.ticked_by, c.ticked_at, c.note tick_note "
            "FROM upi_match m LEFT JOIN darpan_correction c ON c.match_id=m.id "
            "WHERE m.unit=? AND m.status='cash' "
            "AND substr(m.business_date,1,7)=? "
            "ORDER BY m.business_date DESC, m.txn_amount_p DESC", (_unit, month)):
        rows.append(dict(
            id=r["id"], date=r["business_date"], bill=r["bill_no"],
            amount_p=r["txn_amount_p"], rrn=r["rrn"],
            answer=r["resolution"], answered_by=r["resolved"],
            ticked_by=r["ticked_by"], ticked_at=r["ticked_at"],
            # S220 OWNER ENGLISH: the owner reads this and relays it to Darpan,
            # who acts in Marg -- so English first, the Hindi kept for the relay.
            instruction="Marg: change bill %s payment mode CASH \u2192 UPI "
                        "(bill %s ka payment mode CASH se UPI kijiye)"
                        % (r["bill_no"] or "?", r["bill_no"] or "?")))
    done = sum(1 for x in rows if x["ticked_by"])
    months = [r[0] for r in con.execute(
        "SELECT DISTINCT substr(business_date,1,7) FROM upi_match "
        "WHERE unit=? AND status='cash' ORDER BY 1 DESC", (_unit,))]
    return jsonify(ok=True, month=month, months=months, rows=rows,
                   corrected=done, pending=len(rows) - done)


@bp.route("/finance/darpan/api/correction/<int:mid>/tick", methods=["POST"])
def api_tick(mid):
    # S221 AMIR VIEWER -- ticking a correction he has fixed in Marg IS the job.
    # A desk he can read but not close would be worse than no desk.
    u, err = _require("checker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    row = con.execute("SELECT id FROM upi_match WHERE id=? AND unit=? AND "
                      "status='cash'", (mid, _unit)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    note = str((request.get_json(silent=True) or {}).get("note") or "")[:200]
    try:
        con.execute("INSERT INTO darpan_correction (match_id, ticked_by, "
                    "ticked_at, note) VALUES (?,?,?,?)",
                    (mid, u["user"], now_iso(), note))
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error="already_ticked"), 409
    _audit(con, u["user"], "correction_tick", {"id": mid, "note": note})
    con.commit()
    return jsonify(ok=True, id=mid)


# -------------------------------------------------------------- owner tools
# =====================================================================
#  S208_LEDGER3 — the ledgers, diagnosed and repairable (Sprint 3)
#
#  THE COMPLAINT (owner, 29-Aug): "ledgers for Darpan, Bhawna and me are
#  not updating; a Darpan->Bhawna transfer on 27-Aug did not go through,
#  while his page reduced the drawer per the transfer-out he filed."
#
#  THE MACHINERY, as the app actually computes it: reserve (Bhawna) and
#  Dr Manoj's cash = the counted baseline in cash_custody_event PLUS the
#  live cash_movement hand-overs, read through v_cash_custody_balance --
#  a VIEW created by the S186 migration, not by the schema file. If that
#  view is absent or a movement row never landed, the page shows nothing
#  and every ledger looks frozen. So: first a check that returns the RAW
#  rows (diagnosis before repair, D-discipline), then two repairs -- the
#  view (its own migration's exact SQL, additive) and an owner-recorded
#  transfer event (the same thing /finance/api/custody records; it never
#  moves money, it records custody).
# =====================================================================
LEDGER_PARTIES = ("counter", "drawer", "dr_bhawna", "dr_manoj", "bank")

BALANCE_VIEW_SQL = (
    "CREATE VIEW IF NOT EXISTS v_cash_custody_balance AS "
    "SELECT unit, party, SUM(amount_p) AS held_p FROM ( "
    "  SELECT unit, to_party   AS party,  amount_p FROM cash_custody_event "
    "  UNION ALL "
    "  SELECT unit, from_party AS party, -amount_p FROM cash_custody_event "
    ") GROUP BY unit, party")     # verbatim from finance_migration_S186_reserve_yesbank.sql


@bp.route("/finance/darpan/api/ledger-check")
def api_ledger_check():
    """Owner-only. The raw truth behind the frozen ledgers, for one date."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    iso = str(request.args.get("date") or "").strip()

    out = {"ok": True, "date": iso or None, "problems": []}
    # 1 -- does the balance view exist at all?
    try:
        bal = [dict(r) for r in con.execute(
            "SELECT party, held_p FROM v_cash_custody_balance WHERE unit=?",
            (_unit,))]
        out["balance_view"] = {"exists": True, "rows": bal}
    except sqlite3.OperationalError as e:
        out["balance_view"] = {"exists": False, "error": str(e)}
        out["problems"].append(
            "v_cash_custody_balance is MISSING -- the S186 migration view was "
            "never created on this database. Every ledger reads through it, so "
            "all three freeze at once. POST /finance/darpan/api/ledger-repair-view "
            "creates it (additive, the migration's own SQL).")

    # 2 -- the movements for the date (or the latest 20)
    q = ("SELECT de.business_date d, cm.direction, cm.party, cm.amount_p, "
         "cm.reference FROM cash_movement cm JOIN day_entry de "
         "ON de.id=cm.day_entry_id WHERE de.unit=?")
    args = [_unit]
    if iso:
        q += " AND de.business_date=?"
        args.append(iso)
    q += " ORDER BY de.business_date DESC, cm.id DESC LIMIT 20"
    out["movements"] = [dict(r) for r in con.execute(q, args)]
    if iso and not out["movements"]:
        out["problems"].append(
            "NO cash_movement row for %s -- the transfer-out was never saved "
            "into the day. Record it as an owner transfer below, with the "
            "date, so the record exists with an audit trail." % iso)

    # 3 -- custody events for the date (or latest 20)
    q = ("SELECT event_date, from_party, to_party, amount_p, note, entered_by "
         "FROM cash_custody_event WHERE unit=?")
    args = [_unit]
    if iso:
        q += " AND event_date=?"
        args.append(iso)
    q += " ORDER BY event_date DESC, id DESC LIMIT 20"
    try:
        out["custody_events"] = [dict(r) for r in con.execute(q, args)]
    except sqlite3.OperationalError as e:
        out["custody_events"] = []
        out["problems"].append("cash_custody_event table missing: %s" % e)

    # S209 (F-246) -- the day ledger and the custody record answer
    # different questions. This sentence used to prescribe a remedy that could
    # not satisfy it, and then kept accusing the owner after he had done it.
    if out.get("custody_events"):
        _fixed = []
        for _p in out["problems"]:
            if "the transfer-out was never saved" in _p:
                _p = ("No cash_movement row for %s, so the day ledger still "
                      "counts this cash in the drawer. Your override below "
                      "records where it actually went -- dated, signed, in the "
                      "custody record." % (iso or "this date"))
            _fixed.append(_p)
        out["problems"] = _fixed

    if not out["problems"]:
        out["problems"].append(
            "nothing structurally wrong found%s -- compare the rows above "
            "with what the page shows" % (" for this date" if iso else ""))
    return jsonify(**out)


@bp.route("/finance/darpan/api/ledger-repair-view", methods=["POST"])
def api_ledger_repair_view():
    """Owner-only. Creates v_cash_custody_balance if absent. Additive: the
    exact CREATE VIEW IF NOT EXISTS from the S186 migration, nothing else."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    try:
        con.execute("SELECT 1 FROM v_cash_custody_balance LIMIT 1")
        return jsonify(ok=True, created=False,
                       message="the view already exists -- nothing to repair")
    except sqlite3.OperationalError:
        pass
    con.execute(BALANCE_VIEW_SQL)
    _audit(con, u["user"], "ledger_view_created", {"view": "v_cash_custody_balance"})
    con.commit()
    return jsonify(ok=True, created=True,
                   message="v_cash_custody_balance created (additive). Reload "
                           "the cash position page.")


@bp.route("/finance/darpan/api/transfer", methods=["POST"])
def api_transfer():
    """Owner-only: perform or repair a transfer as a CUSTODY EVENT -- the same
    record /finance/api/custody writes. It never moves money; it records who
    handed cash to whom, dated, with the owner's name on it. The 27-Aug
    Darpan->Bhawna case is exactly this: drawer -> dr_bhawna, dated 2026-08-27,
    note saying it repairs the missing landing."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    frm = str(b.get("from") or "").strip()
    to = str(b.get("to") or "").strip()
    iso = str(b.get("date") or "").strip()
    note = str(b.get("note") or "").strip()
    try:
        amt_p = int(round(float(b.get("amount") or 0) * 100))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount"), 400
    if amt_p <= 0:
        return jsonify(ok=False, error="amount_must_be_positive"), 400
    if frm not in LEDGER_PARTIES or to not in LEDGER_PARTIES or frm == to:
        return jsonify(ok=False, error="bad_parties",
                       parties=list(LEDGER_PARTIES)), 400
    if not iso or len(iso) != 10:
        return jsonify(ok=False, error="bad_date",
                       message="date must be YYYY-MM-DD"), 400
    if not note:
        return jsonify(ok=False, error="note_required",
                       message="an owner transfer always says why"), 400
    con.execute(
        "INSERT INTO cash_custody_event (unit, event_date, from_party, "
        " to_party, amount_p, note, entered_by, entered_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (_unit, iso, frm, to, amt_p,
         ("[owner transfer] " + note)[:400], u["user"], now_iso()))
    _audit(con, u["user"], "owner_transfer",
           {"date": iso, "from": frm, "to": to, "amount_p": amt_p, "note": note})
    con.commit()
    return jsonify(ok=True, date=iso, frm=frm, to=to, amount_p=amt_p)


# =====================================================================
#  S208 Sprint 4 — the pipeline, one page, whole path
#  medical PC -> manojz -> VPS -> matcher, each leg with its own evidence.
#  Everything read-only; a missing table is REPORTED, never fatal.
# =====================================================================
@bp.route("/finance/pipeline")
def page_pipeline():
    u, err = _require("maker", "checker")
    if err:
        return err
    return send_file(os.path.join(HERE, "pipeline_status.html"))


@bp.route("/finance/darpan/api/pipeline")
def api_pipeline():
    u, err = _require("maker", "checker")
    if err:
        return err
    con = _db()
    out = {"ok": True, "at": now_iso(), "legs": {}}

    def leg(name, fn):
        try:
            out["legs"][name] = fn()
        except sqlite3.OperationalError as e:
            out["legs"][name] = {"error": str(e)}

    def _manojz():
        r = con.execute("SELECT received_at, payload_json FROM pipeline_status "
                        "WHERE source='manojz' ORDER BY id DESC LIMIT 1").fetchone()
        if not r:
            return {"posted": None,
                    "note": "manojz has never posted a heartbeat here"}
        try:
            d = json.loads(r["payload_json"])
        except ValueError:
            d = {"broken": True}
        d["posted"] = r["received_at"]
        return d

    def _pushes():
        rows = [dict(r) for r in con.execute(
            "SELECT id, received_at, filename_hint, status FROM marg_push_staging "
            "WHERE unit=? ORDER BY id DESC LIMIT 8", (_unit,))]
        pend = con.execute("SELECT COUNT(*) FROM marg_push_staging WHERE unit=? "
                           "AND status='pending'", (_unit,)).fetchone()[0]
        return {"recent": rows, "pending": pend}

    def _days():
        return [dict(r) for r in con.execute(
            "SELECT business_date, status FROM day_entry WHERE unit=? "
            "ORDER BY business_date DESC LIMIT 8", (_unit,))]

    def _bank():
        r = con.execute("SELECT MAX(statement_date) d, COUNT(*) n FROM "
                        "upi_statement WHERE unit=?", (_unit,)).fetchone()
        t = con.execute("SELECT COUNT(*) n, COUNT(DISTINCT txn_date) d FROM "
                        "upi_txn WHERE unit=?", (_unit,)).fetchone()
        return {"latest_statement": r["d"], "statements": r["n"],
                "transactions": t["n"], "days_with_detail": t["d"]}

    def _match():
        return [dict(r) for r in con.execute(
            "SELECT business_date, status, bank_p, n_agreed, n_cash, "
            "n_bank_orphan, n_bill_orphan, run_at FROM upi_match_day "
            "WHERE unit=? ORDER BY business_date DESC LIMIT 7", (_unit,))]

    def _stock():
        r = con.execute("SELECT MAX(as_on) d, COUNT(DISTINCT as_on) n FROM "
                        "stock_snapshot").fetchone()
        o = con.execute("SELECT COUNT(*) FROM stock_diff WHERE status='open'"
                        ).fetchone()[0]
        return {"latest_snapshot": r["d"], "snapshots": r["n"], "open_diffs": o}

    leg("manojz_heartbeat", _manojz)
    leg("marg_pushes", _pushes)
    leg("filed_days", _days)
    leg("bank", _bank)
    leg("matcher", _match)
    leg("stock", _stock)
    return jsonify(**out)


# =====================================================================
#  S208_CONSOLE — the page is the owner's console (owner spec, 30-Aug):
#  status is COMPUTED FRESH, never a stale record shown as if it were
#  current; every number expands to the granular level, here.
# =====================================================================
@bp.route("/finance/darpan/api/coverage")
def api_coverage():
    """Marg coverage, one row per interesting day, verdict computed NOW.

    THE CONFUSION THIS ENDS: data_flag rows are RECORDS ('a refusal must
    leave a record that outlives the run' -- F-113) and persist by design.
    Showing them as if they were live status made a filed-and-covered day
    look broken. Here the flag is shown WITH today's truth beside it, and a
    flag whose day is now fine is labelled STALE with its dismiss right
    there.
    """
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    days_n = min(int(request.args.get("days", "45") or 45), 120)
    since = (dt.date.today() - dt.timedelta(days=days_n)).isoformat()

    filed = {r["business_date"]: dict(id=r["id"], status=r["status"])
             for r in con.execute(
                 "SELECT id, business_date, status FROM day_entry "
                 "WHERE unit=? AND business_date>=?", (_unit, since))}
    applied = set()
    try:
        for r in con.execute(
                "SELECT e.business_date d FROM ingest_batch b "
                "JOIN day_entry e ON e.id=b.day_entry_id "
                "WHERE e.unit=? AND e.business_date>=? "
                "AND b.adapter='marg_export' AND b.status IN ('ok','partial')",
                (_unit, since)):
            applied.add(r["d"])
    except sqlite3.OperationalError:
        pass
    staged_docs = []
    try:
        staged_docs = [(r["id"], r["status"], r["survey_json"] or "")
                       for r in con.execute(
                           "SELECT id, status, survey_json FROM marg_push_staging "
                           "WHERE unit=? AND status IN ('pending','applied')",
                           (_unit,))]
    except sqlite3.OperationalError:
        pass
    flags = {}
    for r in con.execute(
            "SELECT id, business_date, code, detail FROM data_flag "
            "WHERE unit=? AND business_date>=? "
            "AND code IN ('MARG_DAY_NOT_FILED','BANKMATCH_FEED_MISSING')",
            (_unit, since)):
        flags.setdefault(r["business_date"], []).append(
            dict(id=r["id"], code=r["code"], detail=(r["detail"] or "")[:120]))

    dates = sorted(set(list(filed) + list(flags)) |
                   {d for d in applied}, reverse=True)
    rows = []
    for d in dates:
        f = filed.get(d)
        if d in applied:
            export = "applied"
        elif any(('"%s"' % d) in sv for _i, _st, sv in staged_docs):
            export = "staged"
        else:
            export = "none"
        fl = flags.get(d, [])
        # S220 OWNER ENGLISH: these lines are rendered on the owner's hub (the
        # Marg coverage table). The field keeps its old name so the page needs
        # no change; the words are the owner's language now.
        if f and export == "applied":
            verdict, hindi = "OK", "filed, report in, applied"
        elif f and export == "staged":
            verdict, hindi = "REPORT WAITING", "the report is in; apply it from the workbench"
        elif f:
            verdict, hindi = "EXPORT MISSING", "the day is filed, but there is no Marg report"
        elif export in ("applied", "staged"):
            verdict, hindi = "DAY NOT FILED", "the report is in, but the day is not filed"
        else:
            verdict, hindi = "DAY NOT FILED", "neither filed nor reported"
        stale = [x for x in fl] if (fl and verdict == "OK") else []
        rows.append(dict(date=d, filed=(f or {}).get("status"),
                         export=export, verdict=verdict, hindi=hindi,
                         flags=fl, stale=bool(stale)))
    return jsonify(ok=True, since=since, rows=rows,
                   note="verdict is computed NOW; a flag on an OK day is a "
                        "record, not a problem — dismiss it there")


# ---- S220 LARGE-RETURN GATE: the spot-count list ------------------------------
SPOT_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS stock_spot_check ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
    " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
    " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
    " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
    " UNIQUE(unit, bill_no, item_key))")


def _spot_checks(con, unit, month):
    """The spot-count list: items the system flagged (a large return, or a money
    verdict) that a person should physically count. Rows are written by
    finance_returns_escalate (after Apply, and hourly) -- never here."""
    try:
        con.execute(SPOT_SCHEMA)
        rows = con.execute(
            "SELECT id, business_date, bill_no, item_key, item_name, batch, reason, "
            "status, counted_qty, counted_by, counted_at, note FROM stock_spot_check "
            "WHERE unit=? AND business_date LIKE ? ORDER BY status='due' DESC, "
            "business_date DESC, id", (unit, month + "%")).fetchall()
        return [dict(r) for r in rows]
    except Exception:                                        # noqa: BLE001
        return []


@bp.route("/finance/darpan/api/spot-check", methods=["POST"])
def api_spot_check():
    """Mark one spot-count item counted (or skipped). Owner only. What was
    counted is recorded as typed, with the name and the time; the tool never
    judges the count -- the difference against Marg's stock is a later read."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    try:
        sid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        sid = 0
    status = str(b.get("status") or "done").strip()
    if status not in ("done", "skipped"):
        return jsonify(ok=False, error="bad_status"), 400
    qty = str(b.get("counted_qty") or "").strip()
    note = str(b.get("note") or "").strip()
    if status == "done" and not qty:
        return jsonify(ok=False, error="qty_required",
                       message="a count records the quantity counted"), 400
    con.execute(SPOT_SCHEMA)
    r = con.execute("SELECT id, status FROM stock_spot_check WHERE id=? AND unit=?",
                    (sid, _unit)).fetchone()
    if r is None:
        return jsonify(ok=False, error="not_found"), 404
    con.execute("UPDATE stock_spot_check SET status=?, counted_qty=?, counted_by=?, "
                "counted_at=?, note=? WHERE id=?",
                (status, qty or None, u["user"], now_iso(), note or None, sid))
    _audit(con, u["user"], "spot_check_" + status, {"id": sid, "counted_qty": qty, "note": note})
    con.commit()
    return jsonify(ok=True, id=sid, status=status)
# ---- end S220 LARGE-RETURN GATE ---------------------------------------------------


@bp.route("/finance/darpan/api/cn-detail")
def api_cn_detail():
    """S213 (returns sump r1) -- every return of the month, from BOTH spines.

    The engine is finance_returns_audit (the S212 sump): the UNION of
    sale_line_item WHERE is_return=1 (the item spine -- sees the orphans) and
    sale_item WHERE service LIKE '%_return' (the money spine -- sees the bills
    with no lines). Three populations, named, never averaged. Every rupee
    through finance_money; gross and net both carried, so a discount on a
    refund is a verdict.

    READ-ONLY. The owner ruling of 30-Aug stands -- an untraceable return is
    not entertained without approval -- but the pending row is now COMPUTED
    here and CREATED only when the owner decides, in the POST below. A page
    load writes nothing (the S212 finding: the old card wrote on a GET).
    """
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    try:
        from finance_returns_audit import returns_for_day                  # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="module_absent",
                       message="finance_returns_audit.py is not in "
                               "/root/finance/ -- install S212_SUMP first"), 503
    month = str(request.args.get("month") or "").strip() or \
        dt.date.today().isoformat()[:7]
    lo, hi = month + "-01", month + "-31"
    # day discovery: the same union returns_for_range uses, kept identical on
    # purpose -- run per-day here so every return can carry its date.
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item "
        "WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION "
        "SELECT DISTINCT e.business_date FROM sale_item s "
        "JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
        "AND e.business_date BETWEEN ? AND ? ORDER BY 1 DESC",
        (_unit, lo, hi, _unit, lo, hi))]
    out = []
    total_p = 0
    tally = {"audited": 0, "orphan": 0, "no item detail": 0}
    flagged = 0
    pending = 0
    # S220 METRICS: rupees the audit could judge, and rupees it flagged.
    _examinable_p = 0
    _flagged_p = 0
    _CANT = ("not examinable", "identity needed", "identity disputed",
             "no patient attributed")
    try:
        from finance_returns_escalate import MONEY_FLAGS as _MONEY   # noqa: PLC0415
    except Exception:                                                # noqa: BLE001
        _MONEY = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID",
                  "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")
    # S219 M7 -- THE OWNER'S RULING OF 02-Sep-2026: THE PAST IS ACCEPTED.
    # A date, in one setting, because a cutover written into code is one that
    # cannot be moved when he decides to move it.
    _act_from = _setting(con, "returns.act_from", "") or "2026-09-02"
    # S220 LARGE-RETURN GATE: the line above which a return needs the owner's
    # OK regardless of verdict. A setting since S208; enforced from here.
    try:
        _large_p = int(_setting(con, "returns.large_p", "100000") or 100000)
    except (TypeError, ValueError):
        _large_p = 100000
    for d in days:
        rows, _summary = returns_for_day(con, d, _unit)
        for r in rows:
            total_p += r["amount_p"]
            if r["verdict"] not in _CANT:                 # S220 METRICS
                _examinable_p += r["amount_p"]
            if r["verdict"] in _MONEY:
                _flagged_p += r["amount_p"]
            tally[r["population"]] = tally.get(r["population"], 0) + 1
            # THE PAST IS ACCEPTED (02-Sep-2026). A return from before the
            # cutover keeps its verdict, its money and its place in the list --
            # the data stays whole, and it is the baseline the detector is
            # calibrated against -- but IT GENERATES NO WORK. Nobody is asked to
            # reconstruct an identity from April: before July the counter
            # captured no clinic ID at all (43 of 43 in April, 36 of 36 in May),
            # so 109 of those rows are a missing system, not a missing answer.
            _hist = (d < _act_from)
            # S220 LARGE-RETURN GATE: Rs 1,000+ (returns.large_p) needs the
            # owner's decision even when the audit says ok -- size is where
            # the money moved (0 -> 6 such returns, May -> Aug). It joins
            # `needs` (PENDING until decided), never `flagged`.
            _large = (int(r["amount_p"] or 0) >= _large_p) and not _hist
            needs = ((r["verdict"] != "ok") or _large) and not _hist
            # "identity needed" joins the two verdicts already excluded here,
            # for the same reason: all three say the audit COULD NOT RUN, which
            # is not a finding. Counting them inflates the number the owner is
            # meant to act on, and a count that cries wolf is one he stops
            # reading. It stays in `needs`, so the row still reaches Darpan's
            # desk -- as a question, not as a charge.
            # S220 F-277: "identity disputed" -- two names on one clinic ID --
            # is a question for a person, not a finding about money. It
            # joins the three above: on the desk, not in the count.
            if not _hist and r["verdict"] not in (
                    "ok", "no patient attributed", "not examinable",
                    "identity needed", "identity disputed"):
                flagged += 1
            appr = con.execute(
                "SELECT status, decided_by, decided_at, note FROM "
                "darpan_return_approval WHERE unit=? AND cn_bill=?",
                (_unit, r["bill"])).fetchone()
            if needs and (appr is None or appr["status"] == "pending"):
                pending += 1
            # the bill as Marg exported it -- shown even when the audit could
            # not run (an orphan has lines but no patient; they are still real)
            marg = [dict(seq=m["seq"], item=m["item_name"], qty=m["qty_raw"],
                         pack=m["pack"], rate_p=m["amount_p"],
                         batch=m["batch"], expiry=m["expiry_ym"])
                    for m in con.execute(
                        "SELECT seq, item_name, qty_raw, pack, amount_p, "
                        "batch, expiry_ym FROM sale_line_item "
                        "WHERE unit=? AND bill_no=? AND is_return=1 "
                        "ORDER BY seq", (_unit, r["bill"]))]
            out.append(dict(
                date=d, bill=r["bill"], population=r["population"],
                amount_p=r["amount_p"], gross_p=r["gross_p"],
                net_p=r["net_p"], refund_shortfall_p=r["refund_shortfall_p"],
                money_from=r["money_from"], verdict=r["verdict"],
                note=r["note"], flags=r["flags"],
                name=r["name"], clinic_id=r["clinic_id"],
                mobile_last4=r["mobile_last4"],
                mobile=r.get("mobile", ""),          # S219 M7 (D356)
                historical=_hist,                    # S219 M7 (the cutover)
                large=_large,                        # S220 LARGE-RETURN GATE
                audit_lines=r["lines"], marg_lines=marg,
                needs_approval=needs,
                approval=(dict(appr) if appr else None)))
    return jsonify(ok=True, month=month, count=len(out), total_p=total_p,
                   audited=tally.get("audited", 0),
                   orphans=tally.get("orphan", 0),
                   no_item_detail=tally.get("no item detail", 0),
                   flagged=flagged, pending_approval=pending, notes=out,
                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month),
                   metrics=_month_metrics(con, _unit, month, total_p, _examinable_p, _flagged_p))


def _month_metrics(con, unit, month, total_p, examinable_p, flagged_p):
    """S220 METRICS: the gist line's numbers. The return RATE is returns / sales
    on the bill spine for this month and the previous one -- the same source and
    the same rule for both, so the arrow never compares two definitions (D349).
    The examinable and flagged shares come from the audit's verdicts above.
    Fail-soft: anything it cannot compute is None, and the card says so."""
    def _spine(m):
        try:
            r = con.execute(
                "SELECT COALESCE(SUM(CASE WHEN s.service LIKE '%!_return' ESCAPE '!' THEN s.amount_p END),0),"
                " COALESCE(SUM(CASE WHEN s.service NOT LIKE '%!_return' ESCAPE '!' THEN s.amount_p END),0)"
                " FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id"
                " WHERE e.unit=? AND substr(e.business_date,1,7)=?", (unit, m)).fetchone()
            return int(r[0] or 0), int(r[1] or 0)
        except Exception:                                            # noqa: BLE001
            return 0, 0
    try:
        y, mo = int(month[:4]), int(month[5:7])
        prev = "%04d-%02d" % ((y - 1, 12) if mo == 1 else (y, mo - 1))
    except Exception:                                                # noqa: BLE001
        prev = None
    ret_p, sales_p = _spine(month)
    pret_p, psales_p = _spine(prev) if prev else (0, 0)
    pct = lambda a, b: (round(100.0 * a / b, 1) if b else None)
    return dict(examinable_p=examinable_p, flagged_p=flagged_p,
                examinable_pct=pct(examinable_p, total_p), flagged_pct=pct(flagged_p, total_p),
                sales_p=sales_p, rate_pct=pct(ret_p, sales_p),
                prev_month=prev, prev_rate_pct=pct(pret_p, psales_p))


@bp.route("/finance/darpan/api/intent")
def api_intent():
    """S220 INTENT: the newest run of the intent scorer (finance_intent.py), for the
    owner's card. Signals are patterns against their own baselines -- rows to look
    at, never findings. Owner-only until proven (his rule). READ-ONLY."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    if not _is_owner(con, u):
        return jsonify(ok=True, as_of=None, signals=[], note="owner only")
    try:
        import finance_intent                                   # noqa: PLC0415
        as_of, rows = finance_intent.latest(con, _unit)
    except Exception as ex:                                     # noqa: BLE001
        return jsonify(ok=True, as_of=None, signals=[],
                       note="the intent scorer is not installed or has not run yet (%s)" % ex)
    look = sum(1 for r in rows if r.get("level") == "look" and not r.get("historical"))
    return jsonify(ok=True, as_of=as_of, signals=rows, look=look,
                   note=None if rows else "no run recorded yet -- finance_intent.py runs nightly")


@bp.route("/finance/darpan/api/cn-approve", methods=["POST"])
def api_cn_approve():
    """The owner's decision on an unverified sales return. approve = 'I know
    this case, the return stands'; reject = 'not entertained -- recover'. A
    rejection always says why. Recorded, dated, named."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    bill = str(b.get("bill") or "").strip().upper()
    decision = str(b.get("decision") or "").strip()
    note = str(b.get("note") or "").strip()
    if decision not in ("approved", "rejected"):
        return jsonify(ok=False, error="bad_decision",
                       message="decision is approved or rejected"), 400
    if decision == "rejected" and not note:
        return jsonify(ok=False, error="note_required",
                       message="a rejection always says why"), 400
    # S213 (returns sump r1): the GET no longer writes, so the row may not
    # exist yet -- the owner's decision is what creates it. business_date
    # comes from the return itself (either spine), refusing a bill this
    # server has never seen.
    r = con.execute("SELECT id, status FROM darpan_return_approval "
                    "WHERE unit=? AND cn_bill=?", (_unit, bill)).fetchone()
    if not r:
        d0 = con.execute(
            "SELECT business_date d FROM sale_line_item "
            "WHERE unit=? AND bill_no=? AND is_return=1 "
            "UNION "
            "SELECT e.business_date d FROM sale_item s "
            "JOIN day_entry e ON e.id=s.day_entry_id "
            "WHERE e.unit=? AND s.source_ref=? "
            "AND s.service LIKE '%!_return' ESCAPE '!' LIMIT 1",
            (_unit, bill, _unit, bill)).fetchone()
        if not d0:
            return jsonify(ok=False, error="not_found",
                           message="no return bill %s on this server" % bill), 404
        con.execute("INSERT OR IGNORE INTO darpan_return_approval "
                    "(unit, cn_bill, business_date) VALUES (?,?,?)",
                    (_unit, bill, d0["d"]))
        r = con.execute("SELECT id, status FROM darpan_return_approval "
                        "WHERE unit=? AND cn_bill=?", (_unit, bill)).fetchone()
    con.execute("UPDATE darpan_return_approval SET status=?, decided_by=?, "
                "decided_at=?, note=? WHERE id=?",
                (decision, u["user"], now_iso(), note, r["id"]))
    _audit(con, u["user"], "cn_" + decision, {"bill": bill, "note": note})
    con.commit()
    return jsonify(ok=True, bill=bill, status=decision)


@bp.route("/finance/darpan/api/idlookup")
def api_idlookup():
    """A short clinic ID is often a REAL old ID (842 is Nanhi Devi), not an
    error. Until the patient master lives on this server (Sprint 5: a GAS
    push from the Followup Tracker), this answers from patient_ref -- every
    patient this server has ever matched."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ids = [x.strip() for x in str(request.args.get("ids") or "").split(",")
           if x.strip()][:20]
    out = []
    for cid in ids:
        try:
            r = con.execute("SELECT clinic_id, name FROM patient_ref "
                            "WHERE clinic_id=?", (cid,)).fetchone()
        except sqlite3.OperationalError:
            r = None
        out.append(dict(clinic_id=cid,
                        name=(r["name"] if r else None),
                        known=bool(r)))
    return jsonify(ok=True, results=out)


@bp.route("/finance/darpan/api/guard", methods=["POST"])
def api_guard():
    """Owner switch for the duplicate-filing guard. OFF by default because the
    old form's own flow re-saves a day many times; turn it ON when Darpan is
    on the day card and the form is retired."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    on = bool((request.get_json(silent=True) or {}).get("on"))
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES "
                "('darpan.refile_guard', ?)", ("1" if on else "0",))
    _audit(con, u["user"], "refile_guard", {"on": on})
    con.commit()
    return jsonify(ok=True, on=on)


@bp.route("/finance/darpan/api/refile-grant", methods=["POST"])
def api_refile_grant():
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only",
                       message="only the owner grants a re-file"), 403
    iso = str((request.get_json(silent=True) or {}).get("date") or "").strip()
    if not iso:
        return jsonify(ok=False, error="bad_request"), 400
    con.execute("INSERT INTO darpan_grant (unit, business_date, granted_by, "
                "granted_at) VALUES (?,?,?,?)", (_unit, iso, u["user"], now_iso()))
    _audit(con, u["user"], "refile_grant", {"date": iso})
    con.commit()
    return jsonify(ok=True, date=iso,
                   message="one re-file allowed for %s -- used on the next "
                           "save, then gone" % iso)


@bp.route("/finance/darpan/api/dismiss-flag", methods=["POST"])
def api_dismiss_flag():
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    code = str(b.get("code") or "MARG_DAY_NOT_FILED").strip()
    reason = str(b.get("reason") or "").strip()
    if not iso or not reason:
        return jsonify(ok=False, error="reason_required",
                       message="a dismissal always carries a reason"), 400
    n = con.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND "
                    "business_date=? AND code=?", (_unit, iso, code)).fetchone()[0]
    con.execute("DELETE FROM data_flag WHERE unit=? AND business_date=? AND "
                "code=?", (_unit, iso, code))
    _audit(con, u["user"], "flag_dismissed",
           {"date": iso, "code": code, "n": n, "reason": reason})
    con.commit()
    return jsonify(ok=True, removed=n, date=iso, code=code)


@bp.route("/finance/darpan/api/reject-staged", methods=["POST"])
def api_reject_staged():
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    sid = b.get("id")
    reason = str(b.get("reason") or "").strip()
    if not sid or not reason:
        return jsonify(ok=False, error="reason_required"), 400
    row = con.execute("SELECT id, status FROM marg_push_staging WHERE id=?",
                      (sid,)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    if row["status"] != "pending":
        return jsonify(ok=False, error="not_pending",
                       message="only a pending push can be rejected "
                               "(this one is %s)" % row["status"]), 409
    con.execute("UPDATE marg_push_staging SET status='rejected' WHERE id=?",
                (sid,))
    _audit(con, u["user"], "staged_rejected", {"id": sid, "reason": reason})
    con.commit()
    return jsonify(ok=True, id=sid)
