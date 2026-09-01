#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns_desk.py -- S214: the counter return flow ("Vaapsi Desk").

WHY (the owner, 01-Sep-2026, his rulings verbatim in the design record)
    Return rejections are a pain point and escalate to arguments. So the desk
    is COURTESY-FIRST: permit maximum returns, flag what we catch -- silently,
    internally -- and file EVERYTHING, including refusals, which today leave
    no trace at all.

THE SHAPE
    * Search the patient, see the WHOLE purchase history -- every bill, not
      the last one. A return with no traceable bill still proceeds (flagged).
    * Verdicts are ITEM-WISE. One slip, mixed outcomes.
    * Three colours per line:
        GREEN  accept quietly
        YELLOW accept as courtesy + silent flag (late >60 days . near-expiry .
               bill not traced . qty over bought . frequent returner .
               large refund) -- the patient NEVER sees the yellow
        RED    refuse AT THE COUNTER, logged with reason (expired .
               damaged/opened . not ours). No parking step -- owner's ruling.
    * Close by CASH (payer named and logged) or ADJUST into the new sale
      (new bill number recorded on the slip).
    * Operated by NAMED staff: setting `returns_desk.users`, seeded
      alisha,shivani,darpan,shavez,manoj (reception + fallbacks, owner's list).

THE LOOP (kit 2, recorded here so nobody wonders)
    Marg credit-note entry happens LATER, by hand, same day preferred. The
    matcher pairs slips with CNs at the next export; slips without a CN and
    CNs without a slip both flag to the owner. This module only STORES what
    that matcher will need (match_state on the visit, default 'open').

SERVER-AUTHORITATIVE VERDICTS (the S213 stock lesson): the page proposes,
this module RE-COMPUTES every verdict from the database before saving; a
staff override of a computed colour is allowed but recorded as its own flag.

Money: this kit writes NO ledger rows. The refund is LOGGED on the slip
(named payer); the money reaches the books through the credit note and the
existing daily flow, exactly as today -- one system of record, no double
entry. (Owner preference: nothing that destabilizes the live money paths.)

Mounted by patch_finance_app_returns_desk.py:
    import returns_desk
    returns_desk.init(app, db, require, unit=UNIT)
Tables are created lazily inside the same finance.db (additive; nothing
existing is altered). READ patient_ref / sale_item / sale_line_item /
setting; WRITE only return_visit / return_line.
"""
import datetime
import io
import json
import os
import re
import sqlite3

from flask import Blueprint, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "returns_desk.html")

bp = Blueprint("returns_desk", __name__)

_db = None          # callable -> sqlite3 connection (finance_app's db())
_require = None     # finance_app's require(role)
_unit = "medical"

DESK_ROLES = ("returns", "maker", "checker")
LATE_DAYS = 60                  # the 2-month courtesy line (owner: stays)
NEAR_EXPIRY_MONTHS = 1
BIG_REFUND_P = 200000           # Rs 2,000 -- flag, never block (default D1)
FREQUENT_N, FREQUENT_DAYS = 3, 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS return_visit (
  id INTEGER PRIMARY KEY,
  slip_no TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  business_date TEXT NOT NULL,
  staff TEXT NOT NULL,
  unit TEXT NOT NULL,
  patient_ref_id INTEGER,
  patient_label TEXT,
  closure TEXT NOT NULL CHECK (closure IN ('cash','adjust','nothing')),
  adjust_bill_no TEXT,
  cash_paid_by TEXT,
  refund_p INTEGER NOT NULL DEFAULT 0,
  flags TEXT NOT NULL DEFAULT '[]',
  match_state TEXT NOT NULL DEFAULT 'open',
  match_cn TEXT,
  note TEXT
);
CREATE TABLE IF NOT EXISTS return_line (
  id INTEGER PRIMARY KEY,
  visit_id INTEGER NOT NULL REFERENCES return_visit(id),
  item_name TEXT NOT NULL,
  item_key TEXT,
  qty_units REAL,
  qty_text TEXT,
  sale_bill_no TEXT,
  sale_date TEXT,
  expiry_ym TEXT,
  rate_p INTEGER,
  amount_p INTEGER NOT NULL DEFAULT 0,
  condition TEXT NOT NULL DEFAULT 'sealed',
  verdict TEXT NOT NULL CHECK (verdict IN ('GREEN','YELLOW','RED')),
  accepted INTEGER NOT NULL,
  reasons TEXT NOT NULL DEFAULT '[]',
  computed_verdict TEXT,
  overridden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_rv_date ON return_visit(business_date);
CREATE INDEX IF NOT EXISTS idx_rv_patient ON return_visit(patient_ref_id);
CREATE INDEX IF NOT EXISTS idx_rl_visit ON return_line(visit_id);
"""


def init(app, db_getter, require_fn, unit="medical",
         url_prefix="/finance/returns/desk"):
    """Mount. finance_app calls this once, after its own setup (S208 pattern)."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ------------------------------------------------------------------ helpers
def _con():
    con = _db()
    con.executescript(SCHEMA)
    return con


def _auth():
    """Who may work the desk: the NAMED staff, through the unit-role system.

    The owner's list -- reception (alisha, shivani), fallbacks darpan and
    shavez, plus himself -- lives where every other permission lives:
    `unit_role` rows. Reception carries the dedicated role `returns`, which
    grants THIS desk and nothing else (require("maker") elsewhere still
    refuses them); makers and checkers can always work the desk. Seeded by
    seed_desk_roles.py at install -- visible rows, not code."""
    u, err = _require(*DESK_ROLES)
    if err:
        return None, err
    return u, None


def _today():
    return datetime.date.today().isoformat()


def _ym_plus_months(ym, months):
    y, m = int(ym[:4]), int(ym[5:7])
    m += months
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return "%04d-%02d" % (y, m)


def _expired(expiry_ym, on_date):
    """Marg prints expiry as YYYY-MM; the medicine is good THROUGH that month."""
    if not expiry_ym or not re.fullmatch(r"\d{4}-\d{2}", str(expiry_ym)):
        return False
    return str(on_date)[:7] > str(expiry_ym)


def _near_expiry(expiry_ym, on_date):
    if not expiry_ym or not re.fullmatch(r"\d{4}-\d{2}", str(expiry_ym)):
        return False
    return (not _expired(expiry_ym, on_date)) and \
        str(on_date)[:7] >= _ym_plus_months(str(expiry_ym), -NEAR_EXPIRY_MONTHS)


def _next_slip_no(con, business_date):
    ym = business_date[:7].replace("-", "")
    n = con.execute("SELECT COUNT(*) FROM return_visit WHERE "
                    "substr(business_date,1,7)=?",
                    (business_date[:7],)).fetchone()[0]
    return "R-%s-%04d" % (ym, n + 1)


# ------------------------------------------------------------------ verdicts
def judge_line(con, line, business_date, patient_ref_id):
    """The one place a line becomes a colour. Returns (verdict, reasons).

    reasons carry machine keys; the page translates to Hindi. RED only for
    what physically cannot go back (owner's ruling): expired, damaged/opened,
    not ours. Everything suspicious-but-sellable is YELLOW: accepted, flagged.
    """
    reasons = []
    cond = (line.get("condition") or "sealed").lower()
    if cond in ("damaged", "opened"):
        return "RED", ["damaged_or_opened"]
    if line.get("not_ours"):
        return "RED", ["not_ours"]
    if _expired(line.get("expiry_ym"), business_date):
        return "RED", ["expired"]

    sale_date = line.get("sale_date")
    if not line.get("sale_bill_no"):
        reasons.append("bill_not_traced")
    elif sale_date:
        try:
            days = (datetime.date.fromisoformat(business_date)
                    - datetime.date.fromisoformat(sale_date)).days
            if days > LATE_DAYS:
                reasons.append("late_over_2_months")
        except ValueError:
            reasons.append("sale_date_unreadable")
    if _near_expiry(line.get("expiry_ym"), business_date):
        reasons.append("near_expiry")
    try:
        if line.get("qty_units") and line.get("sold_units") and \
                float(line["qty_units"]) > float(line["sold_units"]):
            reasons.append("qty_over_bought")
    except (TypeError, ValueError):
        pass
    return ("YELLOW" if reasons else "GREEN"), reasons


def _visit_flags(con, patient_ref_id, refund_p, lines, business_date):
    flags = sorted({r for ln in lines for r in ln["reasons"]
                    if r != "sale_date_unreadable"})
    if refund_p >= BIG_REFUND_P:
        flags.append("big_refund")
    if patient_ref_id:
        since = (datetime.date.fromisoformat(business_date)
                 - datetime.timedelta(days=FREQUENT_DAYS)).isoformat()
        n = con.execute("SELECT COUNT(*) FROM return_visit WHERE "
                        "patient_ref_id=? AND business_date>=?",
                        (patient_ref_id, since)).fetchone()[0]
        if n + 1 >= FREQUENT_N:
            flags.append("frequent_returner")
    if any(ln.get("overridden") for ln in lines):
        flags.append("staff_override")
    return sorted(set(flags))


# ------------------------------------------------------------------ routes
@bp.route("")
@bp.route("/")
def page():
    u, err = _auth()
    if err:
        return err
    try:
        with io.open(PAGE, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="page_missing",
                       message="returns_desk.html is not beside returns_desk.py"), 503
    who = str((u or {}).get("user") or (u or {}).get("username") or "")
    html = t.replace("__DESK_USER__", json.dumps(who))
    return html, 200, {"Content-Type": "text/html; charset=utf-8",
                       "Cache-Control": "no-store"}


@bp.route("/api/search")
def api_search():
    _u, err = _auth()
    if err:
        return err
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, patients=[])
    con = _con()
    digits = re.sub(r"\D", "", q)
    rows = []
    if digits and 2 <= len(digits) <= 4:
        rows = con.execute(
            "SELECT id, clinic_id, name, phone_last4 FROM patient_ref "
            "WHERE merged_into IS NULL AND phone_last4 LIKE ? LIMIT 25",
            ("%" + digits,)).fetchall()
    if not rows:
        rows = con.execute(
            "SELECT id, clinic_id, name, phone_last4 FROM patient_ref "
            "WHERE merged_into IS NULL AND (name LIKE ? OR clinic_id LIKE ?) "
            "ORDER BY name LIMIT 25", ("%" + q + "%", "%" + q + "%")).fetchall()
    return jsonify(ok=True, patients=[
        dict(id=r["id"], clinic_id=r["clinic_id"], name=r["name"],
             last4=r["phone_last4"]) for r in rows])


@bp.route("/api/history")
def api_history():
    """EVERY bill of this patient, item lines included -- the owner's rule:
    never locked to the last bill."""
    _u, err = _auth()
    if err:
        return err
    try:
        pid = int(request.args.get("pid") or 0)
    except ValueError:
        pid = 0
    if not pid:
        return jsonify(ok=False, error="pid_required"), 400
    con = _con()
    today = _today()
    bills = con.execute(
        "SELECT s.source_ref bill_no, s.amount_p, s.mode, s.gross_p, s.disc_p, "
        "       COALESCE(MIN(l.business_date),'') sale_date "
        "FROM sale_item s LEFT JOIN sale_line_item l "
        "     ON l.bill_no = s.source_ref AND l.is_return=0 "
        "WHERE s.patient_ref_id=? AND s.source_ref IS NOT NULL "
        "GROUP BY s.source_ref ORDER BY sale_date DESC", (pid,)).fetchall()
    out = []
    for b in bills:
        lines = con.execute(
            "SELECT seq, item_name, item_key, qty_raw, pack, amount_p, "
            "       expiry_ym, business_date FROM sale_line_item "
            "WHERE bill_no=? AND is_return=0 ORDER BY seq",
            (b["bill_no"],)).fetchall()
        ret = {r[0]: r[1] for r in con.execute(
            "SELECT rl.item_key, SUM(COALESCE(rl.qty_units,0)) "
            "FROM return_line rl JOIN return_visit rv ON rv.id=rl.visit_id "
            "WHERE rl.sale_bill_no=? AND rl.accepted=1 GROUP BY rl.item_key",
            (b["bill_no"],))}
        out.append(dict(
            bill_no=b["bill_no"], sale_date=b["sale_date"],
            amount_p=b["amount_p"], mode=b["mode"],
            days_ago=((datetime.date.fromisoformat(today)
                       - datetime.date.fromisoformat(b["sale_date"])).days
                      if b["sale_date"] else None),
            lines=[dict(seq=l["seq"], item_name=l["item_name"],
                        item_key=l["item_key"], qty_raw=l["qty_raw"],
                        pack=l["pack"], rate_p=l["amount_p"],
                        expiry_ym=l["expiry_ym"],
                        already_returned=ret.get(l["item_key"], 0),
                        expired=_expired(l["expiry_ym"], today),
                        near_expiry=_near_expiry(l["expiry_ym"], today))
                   for l in lines]))
    return jsonify(ok=True, patient_ref_id=pid, bills=out, today=today)


@bp.route("/api/slip", methods=["POST"])
def api_slip():
    """Create one slip. The page proposes; THIS recomputes and records."""
    u, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    lines_in = b.get("lines") or []
    if not lines_in:
        return jsonify(ok=False, error="no_lines"), 400
    closure = (b.get("closure") or "").lower()
    if closure not in ("cash", "adjust", "nothing"):
        return jsonify(ok=False, error="closure_required",
                       message="cash, adjust ya nothing (sab RED) chahiye"), 400
    con = _con()
    today = _today()
    pid = b.get("patient_ref_id")
    pid = int(pid) if pid else None
    who = str((u or {}).get("user") or (u or {}).get("username") or "counter")

    judged, refund_p = [], 0
    for ln in lines_in:
        v, reasons = judge_line(con, ln, today, pid)
        want = (ln.get("verdict") or v).upper()
        overridden = 0
        if want != v:
            # staff may accept a computed RED (their eyes beat our data on
            # physical condition ONLY when the reason is data-side) or refuse
            # a GREEN; either way it is recorded, never silent.
            overridden = 1
        accepted = 1 if want in ("GREEN", "YELLOW") else 0
        amt = int(ln.get("amount_p") or 0)
        if accepted:
            refund_p += amt
        judged.append(dict(
            item_name=str(ln.get("item_name") or "").strip() or "item",
            item_key=ln.get("item_key"), qty_units=ln.get("qty_units"),
            qty_text=str(ln.get("qty_text") or ln.get("qty_units") or ""),
            sale_bill_no=ln.get("sale_bill_no"), sale_date=ln.get("sale_date"),
            expiry_ym=ln.get("expiry_ym"), rate_p=ln.get("rate_p"),
            amount_p=amt, condition=(ln.get("condition") or "sealed").lower(),
            verdict=want if want in ("GREEN", "YELLOW", "RED") else v,
            accepted=accepted, reasons=reasons, computed_verdict=v,
            overridden=overridden))

    if closure == "cash" and refund_p > 0 and not (b.get("cash_paid_by") or "").strip():
        return jsonify(ok=False, error="payer_required",
                       message="cash kisne diya -- naam zaroori hai"), 400
    if closure == "adjust" and refund_p > 0 and not (b.get("adjust_bill_no") or "").strip():
        return jsonify(ok=False, error="bill_required",
                       message="naye bill ka number zaroori hai"), 400

    flags = _visit_flags(con, pid, refund_p, judged, today)
    slip_no = _next_slip_no(con, today)
    cur = con.execute(
        "INSERT INTO return_visit (slip_no, created_at, business_date, staff, "
        "unit, patient_ref_id, patient_label, closure, adjust_bill_no, "
        "cash_paid_by, refund_p, flags, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (slip_no, datetime.datetime.now().isoformat(timespec="seconds"), today,
         who, _unit, pid, b.get("patient_label"), closure,
         (b.get("adjust_bill_no") or "").strip() or None,
         (b.get("cash_paid_by") or "").strip() or None,
         refund_p, json.dumps(flags), (b.get("note") or "").strip() or None))
    vid = cur.lastrowid
    for j in judged:
        con.execute(
            "INSERT INTO return_line (visit_id, item_name, item_key, qty_units, "
            "qty_text, sale_bill_no, sale_date, expiry_ym, rate_p, amount_p, "
            "condition, verdict, accepted, reasons, computed_verdict, overridden) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (vid, j["item_name"], j["item_key"], j["qty_units"], j["qty_text"],
             j["sale_bill_no"], j["sale_date"], j["expiry_ym"], j["rate_p"],
             j["amount_p"], j["condition"], j["verdict"], j["accepted"],
             json.dumps(j["reasons"]), j["computed_verdict"], j["overridden"]))
    con.commit()
    return jsonify(ok=True, slip_no=slip_no, refund_p=refund_p, flags=flags,
                   lines=judged, business_date=today, staff=who)


@bp.route("/api/slips")
def api_slips():
    """The day's slips (reprint + owner view). ?d=YYYY-MM-DD, default today;
    ?open=1 -> every slip still awaiting its Marg credit note, any date."""
    _u, err = _auth()
    if err:
        return err
    con = _con()
    if request.args.get("open"):
        vs = con.execute("SELECT * FROM return_visit WHERE match_state='open' "
                         "ORDER BY business_date DESC, id DESC LIMIT 200").fetchall()
    else:
        d = request.args.get("d") or _today()
        vs = con.execute("SELECT * FROM return_visit WHERE business_date=? "
                         "ORDER BY id DESC", (d,)).fetchall()
    out = []
    for v in vs:
        ls = con.execute("SELECT * FROM return_line WHERE visit_id=? ORDER BY id",
                         (v["id"],)).fetchall()
        out.append(dict(
            slip_no=v["slip_no"], created_at=v["created_at"],
            business_date=v["business_date"], staff=v["staff"],
            patient_label=v["patient_label"], closure=v["closure"],
            adjust_bill_no=v["adjust_bill_no"], cash_paid_by=v["cash_paid_by"],
            refund_p=v["refund_p"], flags=json.loads(v["flags"] or "[]"),
            match_state=v["match_state"],
            lines=[dict(item_name=l["item_name"], qty_text=l["qty_text"],
                        amount_p=l["amount_p"], verdict=l["verdict"],
                        accepted=bool(l["accepted"]),
                        reasons=json.loads(l["reasons"] or "[]"))
                   for l in ls]))
    return jsonify(ok=True, slips=out)
