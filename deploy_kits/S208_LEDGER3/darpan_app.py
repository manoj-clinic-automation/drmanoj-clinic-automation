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
    u, err = _require("checker")
    if err:
        return err
    return send_file(os.path.join(HERE, "darpan_corrections.html"))


# ------------------------------------------------------------------ card
def _ortho_words(con):
    v = _setting(con, "orthotics.vocab")
    return [w.strip().lower() for w in v.split(",") if w.strip()]


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
    day_sale_p = sold_p - ret_p

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
                             returned_p=ret_p, cn_bills=cn_bills),
                   upi=dict(total_p=upi_p, bills=upi_bills),
                   net_cash_p=net_cash_p,
                   categories=dict(
                       home=dict(total_p=home_p, bills=home),
                       procedure=dict(total_p=proc_p, bills=proc),
                       orthotics=dict(total_p=ortho_p, items=ortho)),
                   bank=dict(day=(dict(md) if md else None), txns=txns),
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
    u, err = _require("checker")
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
            instruction="Marg: bill %s ka payment mode CASH se UPI kijiye"
                        % (r["bill_no"] or "?")))
    done = sum(1 for x in rows if x["ticked_by"])
    months = [r[0] for r in con.execute(
        "SELECT DISTINCT substr(business_date,1,7) FROM upi_match "
        "WHERE unit=? AND status='cash' ORDER BY 1 DESC", (_unit,))]
    return jsonify(ok=True, month=month, months=months, rows=rows,
                   corrected=done, pending=len(rows) - done)


@bp.route("/finance/darpan/api/correction/<int:mid>/tick", methods=["POST"])
def api_tick(mid):
    u, err = _require("checker")
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
