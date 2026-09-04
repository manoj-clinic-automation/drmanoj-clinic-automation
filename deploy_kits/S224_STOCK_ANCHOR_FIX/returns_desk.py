#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns_desk.py -- S214 v2: the counter return flow ("Vaapsi Desk"), ITEM-FIRST.

V2 (the owner's live walk, 01-Sep): staff never navigate bills. One picker
lists everything the patient ever bought; quantities are typed in the
product's OWN units (goli, tube) with the strip conversion shown; the
BACKEND allocates returned units to the actual bills (newest purchase
first -- the allocation that favours the patient), judges, files, and hands
back the finished slip. Bills appear only on the slip, as evidence. The
slip prints decisions and refusal reasons ONLY (ruling "a"); internal flags
stay internal; a standing policy footer states the 2-month window, measured
per medicine from its own sale date.

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

DESK_ROLES = ("viewer", "maker", "checker")
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

/* S221 star-1-1 -- what Darpan said, and nothing else. Append-only: a second
   answer is a second row, never an overwrite. Nothing reads this table to
   decide anything; it is evidence for the owner, by his ruling of 03-Sep. */
CREATE TABLE IF NOT EXISTS jaankari_answer (
  id INTEGER PRIMARY KEY,
  unit TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('dispute','identity','spot')),
  ref TEXT NOT NULL,
  business_date TEXT,
  answer TEXT NOT NULL,
  value TEXT,
  note TEXT,
  answered_by TEXT NOT NULL,
  answered_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ja_kind ON jaankari_answer(kind, ref);
"""


def init(app, db_getter, require_fn, unit="medical",
         url_prefix="/finance/returns/desk"):
    """Mount. finance_app calls this once, after its own setup (S208 pattern)."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ------------------------------------------------------------------ helpers
V8_COLS = (("settle_state", "TEXT NOT NULL DEFAULT 'pending'"),
           ("settle_by", "TEXT"), ("settle_at", "TEXT"),
           ("settle_bill_no", "TEXT"), ("status", "TEXT NOT NULL DEFAULT 'ok'"),
           ("void_reason", "TEXT"), ("void_by", "TEXT"), ("void_at", "TEXT"))


def _con():
    con = _db()
    con.executescript(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(return_visit)")}
    for col, ddl in V8_COLS:
        if col not in have:
            con.execute("ALTER TABLE return_visit ADD COLUMN %s %s" % (col, ddl))
    # S224 anchor -- a spot count is pinned to the last sale bill, like every
    # count on the counting page has been since S207. Its own column, so the
    # rows stay the truth (D367) and nobody has to parse `note` later.
    have = {r[1] for r in con.execute("PRAGMA table_info(jaankari_answer)")}
    if "anchor_bill" not in have:
        con.execute("ALTER TABLE jaankari_answer ADD COLUMN anchor_bill TEXT")
    return con


def _auth():
    """Who may work the desk: the NAMED staff, through the unit-role system.

    The owner's list -- reception (alisha, shivani), fallbacks darpan and
    shavez, plus himself -- lives where every other permission lives:
    `unit_role` rows. Reception carries role `viewer` on the medical unit:
    the schema's CHECK allows only maker/checker/viewer (the first install
    attempt invented a fourth word and the constraint refused it -- rightly),
    S222 (F-296): that WAS true at S214 and is FALSE since S221 -- the
    corrections desk and the stock count both accept a viewer now, so viewer no
    longer means reception. `returns.desk_users` is what names them. Makers and
    checkers can always work the desk. Seeded by seed_desk_roles.py (the roles)
    and seed_desk_users_s222.py (the names) -- visible rows, not code."""
    u, err = _require(*DESK_ROLES)
    if err:
        return None, err
    if not _desk_allowed(u):
        return None, (jsonify(
            ok=False, error="not_desk_user",
            message="Vaapsi desk aapke naam par nahin hai. "
                    "Apne incharge se kahein."), 403)
    return u, None


# ---- S222 star-1-1: F-296, the viewer over-grant --------------------------
# `viewer` opens this desk. Since S221 it also opens the corrections desk and
# the stock count, so `viewer` no longer means "reception". This is the list
# that makes the S214 ruling -- NAMED staff -- true in code.
#
# Empty or missing list = NOT CONFIGURED = nothing changes. A read error also
# allows. See the patcher header: keeping the counter working outranks this
# gate, which exists to keep a purchase man out of cash refunds.

DESK_USERS_KEY = "returns.desk_users"


def _desk_users(con):
    """The allow-list as a set of lower-case logins. Empty set = not set.

    Accepts commas, semicolons or spaces so the owner can type the row by hand
    in any shape he likes."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?",
                        (DESK_USERS_KEY,)).fetchone()
    except Exception:
        return set()
    raw = ""
    if r is not None:
        try:
            raw = r["value"] or ""
        except Exception:
            raw = r[0] or ""
    return set(p.strip().lower() for p in re.split(r"[,;\s]+", str(raw)) if p.strip())


def _desk_allowed(u):
    """May this login work the Vaapsi desk?"""
    roles = set((u or {}).get("roles") or [])
    one = (u or {}).get("role")
    if one:
        roles.add(str(one))          # every caller shape, not just finance_app's
    if roles.intersection(("maker", "checker")):
        return True                      # Darpan, and the owner. Never listed.
    try:
        allow = _desk_users(_con())
    except Exception:
        return True                      # deliberate: see the header
    if not allow:
        return True                      # not configured -> nothing changes
    who = str((u or {}).get("user") or (u or {}).get("username") or "").strip().lower()
    return bool(who) and who in allow
# ---- end S222 star-1-1 -----------------------------------------------------


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


PACK_RE = re.compile(r"(\d+)\s*\*\s*(\d+)")


def _pack_n(pack):
    """'1*10' -> 10 units per strip; None when unreadable."""
    m = PACK_RE.search(str(pack or ""))
    if m:
        n = int(m.group(2))
        return n if 0 < n <= 1000 else None
    return None


def _units_sold(qty_raw, pack):
    """Marg 'strips:loose' -> single units (the S211 anomaly-module rule)."""
    sr = str(qty_raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*[:.]\s*(\d+)", sr)
    if m:
        strips, loose = int(m.group(1)), int(m.group(2))
        ps = _pack_n(pack)
        if ps:
            return strips * ps + loose
        return loose if strips == 0 else (strips if loose == 0 else None)
    if re.fullmatch(r"\d+", sr):
        return int(sr)
    return None


def _per_unit_p(rate_p, qty_raw, pack):
    """Best-guess price of ONE unit. A strip-form line's printed rate is the
    strip's; a whole-unit line's is the unit's. Editable on screen -- this is
    a default, never an assertion."""
    if not rate_p:
        return 0
    sr = str(qty_raw or "").strip()
    ps = _pack_n(pack)
    if ps and re.fullmatch(r"\d+\s*[:.]\s*\d+", sr):
        return int(round(rate_p / ps))
    return int(rate_p)


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
        if not b["sale_date"] and (b["amount_p"] or 0) <= 0:
            continue        # a credit-note ref is not a purchase bill
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


@bp.route("/api/items")
def api_items():
    """Everything this patient ever bought, ONE row per medicine -- the v2
    picker. Bills stay in the backend; they resurface only on the slip."""
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
    rows = con.execute(
        "SELECT l.item_key, l.item_name, l.qty_raw, l.pack, l.amount_p, "
        "       l.expiry_ym, l.business_date, l.bill_no "
        "FROM sale_line_item l JOIN sale_item s ON s.source_ref = l.bill_no "
        "WHERE s.patient_ref_id=? AND l.is_return=0 "
        "ORDER BY l.business_date DESC, l.seq", (pid,)).fetchall()
    disc = {r["source_ref"]: (r["amount_p"], r["gross_p"], r["disc_p"])
            for r in con.execute(
                "SELECT source_ref, amount_p, gross_p, disc_p FROM sale_item "
                "WHERE patient_ref_id=? AND source_ref IS NOT NULL", (pid,))}
    agg = {}
    for r in rows:
        k = r["item_key"] or r["item_name"]
        a = agg.setdefault(k, dict(
            item_key=r["item_key"], item_name=r["item_name"], bought_units=0,
            unreadable_qty=False, last_date=r["business_date"],
            last_expiry=r["expiry_ym"], pack_n=_pack_n(r["pack"]),
            unit_p=_per_unit_p(r["amount_p"], r["qty_raw"], r["pack"]),
            bills=[], n_bills=set()))
        u = _units_sold(r["qty_raw"], r["pack"])
        if u is None:
            a["unreadable_qty"] = True
        else:
            a["bought_units"] += u
        if r["bill_no"] not in a["n_bills"] and len(a["bills"]) < 3:
            dg = disc.get(r["bill_no"])
            pct = int(round(100.0 * dg[2] / dg[1])) if dg and dg[1] and dg[2] else 0
            a["bills"].append(dict(bill_no=r["bill_no"], date=r["business_date"],
                                   units=u, disc_pct=pct))
        a["n_bills"].add(r["bill_no"])
    # PREVIOUS RETURNS reduce what is returnable (v9, the owner's question
    # "does it find any previous sales returns also" -- it does now):
    #   * desk slips: accepted lines of non-void visits for this patient;
    #   * Marg credit notes: is_return=1 lines on this patient's own refs.
    desk_ret = {}
    for r in con.execute(
            "SELECT rl.item_key, SUM(COALESCE(rl.qty_units,0)) u, "
            "       MAX(rv.business_date) d "
            "FROM return_line rl JOIN return_visit rv ON rv.id=rl.visit_id "
            "WHERE rv.patient_ref_id=? AND rl.accepted=1 "
            "AND COALESCE(rv.status,'ok')!='void' AND rl.item_key IS NOT NULL "
            "GROUP BY rl.item_key", (pid,)):
        desk_ret[r["item_key"]] = (int(r["u"] or 0), r["d"])
    marg_ret = {}
    for r in con.execute(
            "SELECT l.item_key, l.qty_raw, l.pack, l.business_date "
            "FROM sale_line_item l JOIN sale_item s ON s.source_ref=l.bill_no "
            "WHERE s.patient_ref_id=? AND l.is_return=1", (pid,)):
        u = _units_sold(r["qty_raw"], r["pack"]) or 0
        k = r["item_key"]
        pu, pd = marg_ret.get(k, (0, None))
        marg_ret[k] = (pu + u, max(pd or "", r["business_date"] or ""))
    out = []
    for a in agg.values():
        k = a["item_key"]
        du, dd = desk_ret.get(k, (0, None))
        mu, md = marg_ret.get(k, (0, None))
        a["returned_units"] = du + mu
        a["returns"] = ([dict(src="CN", date=md, units=mu)] if mu else []) +                        ([dict(src="slip", date=dd, units=du)] if du else [])
        a["cap_units"] = max(0, (a["bought_units"] or 0) - a["returned_units"])
        # NET price: the newest bill's own recorded discount ratio applied to
        # the per-unit rate -- the owner's rule: refund what was PAID, not MRP.
        ratio = 1.0
        if a["bills"]:
            net_g = disc.get(a["bills"][0]["bill_no"])
            if net_g and net_g[1]:
                ratio = max(0.0, min(1.0, (net_g[0] or net_g[1]) / net_g[1]))
        a["unit_net_p"] = int(round(a["unit_p"] * ratio))
        a["discounted"] = a["unit_net_p"] < a["unit_p"]
        a["n_bills"] = len(a["n_bills"])
        a["last_expired"] = _expired(a["last_expiry"], today)
        out.append(a)
    out.sort(key=lambda x: x["last_date"] or "", reverse=True)
    return jsonify(ok=True, items=out, today=today)


@bp.route("/api/catalog")
def api_catalog():
    """Type-ahead over the WHOLE shop's sold-item records -- the v3 "not in
    list" path. Price fetched from the newest sale line; no typing prompts."""
    _u, err = _auth()
    if err:
        return err
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    con = _con()
    rows = con.execute(
        "SELECT item_key, item_name, MAX(business_date) last_date "
        "FROM sale_line_item WHERE is_return=0 AND lower(item_name) LIKE ? "
        "GROUP BY item_key ORDER BY last_date DESC LIMIT 20",
        ("%" + q + "%",)).fetchall()
    out = []
    for r in rows:
        nl = con.execute(
            "SELECT qty_raw, pack, amount_p, expiry_ym FROM sale_line_item "
            "WHERE item_key=? AND is_return=0 ORDER BY business_date DESC "
            "LIMIT 1", (r["item_key"],)).fetchone()
        up = _per_unit_p(nl["amount_p"], nl["qty_raw"], nl["pack"]) if nl else 0
        out.append(dict(item_key=r["item_key"], item_name=r["item_name"],
                        last_date=r["last_date"], unit_p=up, unit_net_p=up,
                        pack_n=_pack_n(nl["pack"]) if nl else None))
    return jsonify(ok=True, items=out)


def _allocate(con, pid, item_key, units_wanted):
    """Give the returned units their bills, NEWEST purchase first -- the
    allocation that favours the patient (newest = least late). Returns
    (chunks, sold_total); each chunk carries the sale line it drew from."""
    rows = con.execute(
        "SELECT l.bill_no, l.business_date, l.qty_raw, l.pack, l.amount_p, "
        "       l.expiry_ym "
        "FROM sale_line_item l JOIN sale_item s ON s.source_ref = l.bill_no "
        "WHERE s.patient_ref_id=? AND l.item_key=? AND l.is_return=0 "
        "ORDER BY l.business_date DESC, l.seq", (pid, item_key)).fetchall()
    chunks, left, sold_total = [], units_wanted, 0
    for r in rows:
        u = _units_sold(r["qty_raw"], r["pack"]) or 0
        sold_total += u
        if left > 0 and u > 0:
            take = min(left, u)
            chunks.append(dict(bill_no=r["bill_no"], sale_date=r["business_date"],
                               units=take, expiry_ym=r["expiry_ym"],
                               rate_p=r["amount_p"], pack=r["pack"]))
            left -= take
    return chunks, sold_total, left


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
    # v8 (owner's ruling, 01-Sep night): ALL money stays at the medical sales
    # counter. The desk issues the slip; settlement is recorded there via
    # /api/slip/settle. closure is accepted for backward compatibility but
    # every new slip starts pending.
    closure = (b.get("closure") or "nothing").lower()
    if closure not in ("cash", "adjust", "nothing"):
        closure = "nothing"
    con = _con()
    today = _today()
    pid = b.get("patient_ref_id")
    pid = int(pid) if pid else None
    who = str((u or {}).get("user") or (u or {}).get("username") or "counter")

    judged, refund_p = [], 0
    for ln in lines_in:
        units = ln.get("units") or ln.get("qty_units") or 1
        try:
            units = max(1, int(units))
        except (TypeError, ValueError):
            units = 1
        item_key = ln.get("item_key")
        chunks, sold_total, unmatched = ([], 0, units)
        if pid and item_key:
            chunks, sold_total, unmatched = _allocate(con, pid, item_key, units)
        newest = chunks[0] if chunks else {}
        pack_n = _pack_n(newest.get("pack")) if newest else None
        unit_p = int(ln.get("unit_p") or
                     (_per_unit_p(newest.get("rate_p"), "1:0", newest.get("pack"))
                      if pack_n else (newest.get("rate_p") or 0)))
        amt = ln.get("amount_p")
        amt = int(amt) if amt not in (None, "") else unit_p * units
        jl = dict(ln)
        jl.update(sale_bill_no=newest.get("bill_no"),
                  sale_date=newest.get("sale_date"),
                  expiry_ym=newest.get("expiry_ym") or ln.get("expiry_ym"),
                  qty_units=units, sold_units=sold_total or None)
        v, reasons = judge_line(con, jl, today, pid)
        if unmatched > 0 and chunks:
            reasons = sorted(set(reasons + ["qty_over_bought"]))
            if v == "GREEN":
                v = "YELLOW"
        want = (ln.get("verdict") or v).upper()
        if want not in ("GREEN", "YELLOW", "RED"):
            want = v
        overridden = 1 if want != v else 0
        accepted = 1 if want in ("GREEN", "YELLOW") else 0
        if accepted:
            refund_p += amt
        bills_txt = ", ".join("%s (%s)" % (c["bill_no"], c["sale_date"])
                              for c in chunks[:3])
        conv = ""
        if pack_n:
            strips, loose = divmod(units, pack_n)
            conv = ("%d पत्ता + %d" % (strips, loose)) if strips else str(units)
        judged.append(dict(
            item_name=str(ln.get("item_name") or "").strip() or "item",
            item_key=item_key, qty_units=units,
            qty_text=str(ln.get("qty_text") or conv or units),
            sale_bill_no=jl["sale_bill_no"], sale_date=jl["sale_date"],
            expiry_ym=jl.get("expiry_ym"), rate_p=unit_p,
            amount_p=amt, condition=(ln.get("condition") or "sealed").lower(),
            verdict=want, accepted=accepted, reasons=reasons,
            computed_verdict=v, overridden=overridden, bills=bills_txt))

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


@bp.route("/api/slip/settle", methods=["POST"])
def api_settle():
    """The medical sales counter settles a slip: cash (payer named) or
    adjust (new bill no). One tap; logged with who and when."""
    u, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    slip_no = (b.get("slip_no") or "").strip()
    how = (b.get("how") or "").lower()
    con = _con()
    v = con.execute("SELECT * FROM return_visit WHERE slip_no=?",
                    (slip_no,)).fetchone()
    if not v:
        return jsonify(ok=False, error="no_such_slip"), 404
    if v["status"] == "void":
        return jsonify(ok=False, error="slip_void",
                       message="yeh parchi Cancel ho chuki hai"), 400
    if v["settle_state"] != "pending":
        return jsonify(ok=False, error="already_settled"), 400
    if how == "cash":
        payer = (b.get("cash_paid_by") or "").strip()
        if not payer:
            return jsonify(ok=False, error="payer_required",
                           message="cash kisne diya -- naam zaroori hai"), 400
        con.execute("UPDATE return_visit SET settle_state='cash', "
                    "cash_paid_by=?, settle_by=?, settle_at=? WHERE id=?",
                    (payer, str((u or {}).get("user") or ""),
                     datetime.datetime.now().isoformat(timespec="seconds"),
                     v["id"]))
    elif how == "adjust":
        bill = (b.get("adjust_bill_no") or "").strip()
        if not bill:
            return jsonify(ok=False, error="bill_required",
                           message="naye bill ka number zaroori hai"), 400
        con.execute("UPDATE return_visit SET settle_state='adjust', "
                    "adjust_bill_no=?, settle_by=?, settle_at=? WHERE id=?",
                    (bill, str((u or {}).get("user") or ""),
                     datetime.datetime.now().isoformat(timespec="seconds"),
                     v["id"]))
    else:
        return jsonify(ok=False, error="how_required",
                       message="cash ya adjust chahiye"), 400
    con.commit()
    return jsonify(ok=True, slip_no=slip_no, settle_state=how)


VOID_REASONS = ("matra_galat", "dawa_galat", "raqam_galat",
                "irada_badla", "anya")


@bp.route("/api/slip/void", methods=["POST"])
def api_void():
    """Cancel a slip -- crossed out in ink, never deleted (the house rule).

    Staff: SAME DAY and only while UN-SETTLED (owner's rulings, 01-Sep).
    Once money moved at the counter, or the day has passed, cancelling
    needs a checker (the owner). A voided slip stops expecting a Marg
    credit note; the kit-2 matcher skips it."""
    u, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    slip_no = (b.get("slip_no") or "").strip()
    reason = (b.get("reason") or "").strip()
    note = (b.get("note") or "").strip()
    if reason not in VOID_REASONS:
        return jsonify(ok=False, error="reason_required",
                       message="Cancel ki wajah chuniye"), 400
    con = _con()
    v = con.execute("SELECT * FROM return_visit WHERE slip_no=?",
                    (slip_no,)).fetchone()
    if not v:
        return jsonify(ok=False, error="no_such_slip"), 404
    if v["status"] == "void":
        return jsonify(ok=False, error="already_void"), 400
    roles = set((u or {}).get("roles") or [])
    is_checker = "checker" in roles
    if not is_checker:
        if v["business_date"] != _today():
            return jsonify(ok=False, error="not_today",
                           message="purani parchi -- doctor sahab hi Cancel "
                                   "kar sakte hain"), 403
        if v["settle_state"] != "pending":
            return jsonify(ok=False, error="settled",
                           message="raqam ka nipTaan ho chuka -- doctor sahab "
                                   "hi Cancel kar sakte hain"), 403
    con.execute("UPDATE return_visit SET status='void', void_reason=?, "
                "void_by=?, void_at=?, match_state='cancelled' WHERE id=?",
                (reason + ((" | " + note) if note else ""),
                 str((u or {}).get("user") or ""),
                 datetime.datetime.now().isoformat(timespec="seconds"),
                 v["id"]))
    con.commit()
    return jsonify(ok=True, slip_no=slip_no, status="void")


# ---- S221 star-1-1: DARPAN'S JAANKARI LIST ---------------------------------
# Read-only, except one INSERT into jaankari_answer. See this kit's README and
# the patcher header for why nothing here is allowed to act on what he says.

JAANKARI_ANSWERS = ("ok", "find_bill", "dont_know", "counted")


def _rd_setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] not in (None, "")) else default
    except Exception:
        return default


def _rd_has(con, name):
    try:
        return bool(con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,)).fetchone())
    except Exception:
        return False


def _rd_answers(con, kind):
    """The LATEST answer per ref -- the table is append-only, so the last row
    for a ref wins for display, and every earlier one stays on the record."""
    out = {}
    try:
        for r in con.execute(
                "SELECT ref, answer, value, answered_by, answered_at, anchor_bill "
                "FROM jaankari_answer WHERE kind=? ORDER BY id", (kind,)):
            out[str(r["ref"])] = dict(answer=r["answer"], value=r["value"],
                                      by=r["answered_by"], at=r["answered_at"],
                                      anchor=r["anchor_bill"])   # S224 anchor
    except Exception:
        pass
    return out


def _rd_mobile(con, clinic_id):
    """D363 -- the counter's own screen shows the whole number. Read at request
    time from the master; never stored in this file (F-185). Falls back to the
    last four, and to nothing at all rather than guessing."""
    if not clinic_id:
        return ""
    try:
        r = con.execute("SELECT * FROM patient_ref WHERE clinic_id=?",
                        (clinic_id,)).fetchone()
    except Exception:
        return ""
    if not r:
        return ""
    k = r.keys()
    m = (r["mobile"] or "").strip() if "mobile" in k else ""
    if m:
        return m
    l4 = (r["phone_last4"] or "").strip() if "phone_last4" in k else ""
    return ("xxxxxx" + l4) if l4 else ""


@bp.route("/api/jaankari")
def api_jaankari():
    """The three lists. READ-ONLY -- it writes nothing at all."""
    _u, err = _auth()
    if err:
        return err
    con = _con()
    out = dict(disputes=[], identity=[], spot=[])
    ans = dict((k, _rd_answers(con, k)) for k in ("dispute", "identity", "spot"))

    # 1 -- the disputes the ingest recorded (S220 F-277)
    if _rd_has(con, "identity_dispute"):
        try:
            for r in con.execute(
                    "SELECT id, business_date, bill_no, clinic_id, bill_name, master_name "
                    "FROM identity_dispute WHERE status='open' AND unit=? "
                    "ORDER BY business_date DESC, id DESC LIMIT 60", (_unit,)):
                ref = str(r["id"])
                out["disputes"].append(dict(
                    ref=ref, date=r["business_date"], bill=r["bill_no"],
                    clinic_id=r["clinic_id"], bill_name=r["bill_name"],
                    master_name=r["master_name"],
                    mobile=_rd_mobile(con, r["clinic_id"]),
                    answered=ans["dispute"].get(ref)))
        except Exception:
            pass

    # 2 -- returns still sitting on WALK-IN since the owner's line
    # D361 -- THE PAST IS ACCEPTED AND RAISES NO WORK, so the default does not
    # reach into it: it is the day the identity machinery went live (the S220
    # close). Left at the owner's line of 18-Jun this list opened with 22
    # historical rows on a phone -- seen in the render test, not guessed. The
    # backlog is one setting row away (returns.act_from = 2026-06-18) if he
    # ever wants it worked.
    act_from = _rd_setting(con, "returns.act_from", "2026-09-02")
    try:
        walk = con.execute(
            "SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'").fetchone()
    except Exception:
        walk = None
    if walk:
        try:
            for r in con.execute(
                    "SELECT s.source_ref ref, d.business_date bd, s.amount_p amt, "
                    "s.description ds FROM sale_item s "
                    "JOIN day_entry d ON d.id=s.day_entry_id "
                    "WHERE s.service='pharmacy_return' AND s.patient_ref_id=? "
                    "AND d.business_date>=? AND d.unit=? "
                    "ORDER BY d.business_date DESC LIMIT 60",
                    (walk[0], act_from, _unit)):
                ref = str(r["ref"] or "")
                if not ref:
                    continue
                nm = ""
                try:
                    nm = (json.loads(r["ds"] or "{}") or {}).get("patient_name") or ""
                except Exception:
                    nm = ""
                out["identity"].append(dict(
                    ref=ref, date=r["bd"], amount_p=abs(r["amt"] or 0), name=nm,
                    answered=ans["identity"].get(ref)))
        except Exception:
            pass

    # 3 -- the shelves to count (D365, the deterrent)
    if _rd_has(con, "stock_spot_check"):
        try:
            for r in con.execute(
                    "SELECT id, business_date, item_name, batch, bill_no, reason "
                    "FROM stock_spot_check WHERE status='due' AND unit=? "
                    "ORDER BY requested_at DESC LIMIT 60", (_unit,)):
                ref = str(r["id"])
                out["spot"].append(dict(
                    ref=ref, date=r["business_date"], item=r["item_name"],
                    batch=r["batch"], bill=r["bill_no"],
                    answered=ans["spot"].get(ref)))
        except Exception:
            pass

    pending = sum(1 for k in out for x in out[k] if not x.get("answered"))
    return jsonify(ok=True, lists=out, pending=pending,
                   counts=dict((k, len(v)) for k, v in out.items()))


@bp.route("/api/jaankari/answer", methods=["POST"])
def api_jaankari_answer():
    """Record what he said. EVIDENCE ONLY: this endpoint writes exactly one row
    in one table and touches nothing else in the database -- no money, no
    patient, no dispute status, no spot-check status. The owner's ruling."""
    u, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    kind = str(b.get("kind") or "").strip()
    ref = str(b.get("ref") or "").strip()
    answer = str(b.get("answer") or "").strip()
    if kind not in ("dispute", "identity", "spot") or not ref \
            or answer not in JAANKARI_ANSWERS:
        return jsonify(ok=False, error="bad_request",
                       message="kind/ref/answer theek nahin"), 400
    val = b.get("value")
    val = str(val).strip() if val not in (None, "") else None
    note = b.get("note")
    note = str(note).strip() if note not in (None, "") else None
    # S224 anchor -- THE OWNER'S RULE, the same one stock_app.py enforces at
    # /api/count: a count that is not pinned to the last sale bill cannot be
    # reconciled later, so it is not accepted at all. Refused before anything
    # is written; the page shows this message word for word.
    anchor = str(b.get("anchor_bill") or "").strip().upper() or None
    if kind == "spot" and answer == "counted" and not anchor:
        return jsonify(ok=False, error="anchor_required",
                       message="\u0906\u0916\u093c\u093f\u0930\u0940 \u0938\u0947\u0932 "
                               "\u092c\u093f\u0932 \u0928\u0902\u092c\u0930 \u091c\u093c\u0930\u0942\u0930\u0940 "
                               "\u0939\u0948 \u2014 \u092c\u093f\u0928\u093e \u092c\u093f\u0932 \u0915\u0940 "
                               "\u0917\u093f\u0928\u0924\u0940 \u092c\u093e\u0926 \u092e\u0947\u0902 "
                               "\u092e\u093f\u0932\u093e\u0908 \u0928\u0939\u0940\u0902 \u091c\u093e "
                               "\u0938\u0915\u0924\u0940 \u0964"), 400
    con = _con()
    who = str((u or {}).get("user") or (u or {}).get("username") or "")
    con.execute(
        "INSERT INTO jaankari_answer (unit, kind, ref, business_date, answer,"
        " value, note, answered_by, answered_at, anchor_bill)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (_unit, kind, ref, (str(b.get("date")).strip() or None) if b.get("date") else None,
         answer, val, note, who,
         datetime.datetime.now().replace(microsecond=0).isoformat(), anchor))
    con.commit()
    return jsonify(ok=True)
# ---- end S221 star-1-1 ------------------------------------------------------


@bp.route("/api/slips")
def api_slips():
    """The day's slips (reprint + owner view). ?d=YYYY-MM-DD, default today;
    ?open=1 -> every slip still awaiting its Marg credit note, any date."""
    _u, err = _auth()
    if err:
        return err
    con = _con()
    if request.args.get("open"):
        vs = con.execute("SELECT * FROM return_visit WHERE match_state='open' AND status!='void' "
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
            match_state=v["match_state"], settle_state=v["settle_state"],
            status=v["status"],
            lines=[dict(item_name=l["item_name"], qty_text=l["qty_text"],
                        amount_p=l["amount_p"], verdict=l["verdict"],
                        accepted=bool(l["accepted"]),
                        reasons=json.loads(l["reasons"] or "[]"))
                   for l in ls]))
    return jsonify(ok=True, slips=out)
