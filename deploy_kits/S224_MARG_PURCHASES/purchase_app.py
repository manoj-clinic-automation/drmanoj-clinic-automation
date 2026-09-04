#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
purchase_app.py -- S224: Marg's purchases, on the box.  (rev 2, 04-Sep-2026)

REV 2 -- gross vs net (the owner's find on the first screen).
    Rev 1 summed purchase_line.amount_p, which is Marg's GROSS line value before the
    discount; the bill-wise report is NET. Every item-wise rupee here is now
    net_amount_p (after discount); gross appears only where it is labelled "gross".
    Reconciliation is per bill (AGREES / DIFFERS / NO ITEM LINES / ITEM LINES WITH
    NO BILL) and finalise reads those buckets. Where two live exports both carry the
    same bill's lines, the export with the LATER export_stamp is the bill's line set
    and the other's lines for that bill are ignored (kept, never deleted).

WHAT THIS IS
    The pharmacy's purchase exports -- BILLWISE, SUPPLIERWISE, ITEMWISE, BILLITEMWISE --
    are pushed from manojz (push_purchases.py) through ONE machine door and kept here
    in finance.db. On top of them: a month page where each bill is marked Correct or
    Wrong and the month is FINALISED; a scan-link page that pairs Marg's bills with
    the pharmacy scans in the asset app; and an order book whose reorder plan is the
    S207 engine run server-side on the newest stock snapshot and the last 28 days of
    sale lines. The contract both legs implement is S224_PURCHASE_PUSH_CONTRACT.md.

WHO
    machine door   header X-Finance-Marg == FINANCE_MARG_TOKEN (F-237: never X-Finance-Cron)
    pages          a signed-in maker | checker | viewer of the medical unit; viewers read only
    verdicts       maker | checker
    finalise, reopen, orders   the DOCTOR -- the medical unit's checker, who by the
                   owner's own rule (S179) is Dr Manoj alone. Same test stock_app uses.
    vendor phones  maker | checker only. A viewer never sees a phone.

RULES (D325)
    Nothing here writes to Marg, sends to a bank or a vendor, or leaves the server.
    Tables are created on FIRST REQUEST, never at import (F-303: an import-time db()
    call took the whole finance app down once).
"""
import datetime as dt
import io
import json
import math
import os
import re
import sqlite3

from flask import Blueprint, jsonify, redirect, request

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "purchase_schema.sql")

bp = Blueprint("purchase", __name__)

_db = None
_require = None
_unit = "medical"
_marg_token = ""
_assets_db = "/root/assetapp/assets.db"
_assets_url = "https://assets.dr-manoj.in"
_schema_done = False

TYPES = ("ITEMWISE", "BILLWISE", "SUPPLIERWISE", "BILLITEMWISE")
ORDER_STATUS = ("draft", "sent", "received", "cancelled")
MD5_RE = re.compile(r"^[0-9a-f]{32}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STAMP_RE = re.compile(r"^\d{8}-\d{6}$")
PACE_DAYS = 28
FEED_DAYS_FOR_TRUST = 28


def init(app, db_getter, require_fn, unit="medical", url_prefix="/finance/purchase",
         marg_token="", assets_db=None, assets_url=None):
    """Mount only. Opens no connection: at import there is no app context to open one in."""
    global _db, _require, _unit, _marg_token, _assets_db, _assets_url
    _db, _require, _unit = db_getter, require_fn, unit
    _marg_token = marg_token or ""
    _assets_db = assets_db or os.environ.get("ASSETS_DB", _assets_db)
    _assets_url = (assets_url or os.environ.get("ASSETS_URL", _assets_url)).rstrip("/")
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ====================================================================== keys
# Copies of packmap.norm (S206) and push_expected._billno (S208), and the S224
# supplier_key -- identical to marg_purchase_rows.py on the manojz leg, by design.
_CITY_TAILS = ("BAREILLY", "BAREILL", "BAREIL", "BAREI", "BARE", "BAR", "BA")


def norm(s):
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)


def supplier_key(s):
    """norm() minus a trailing city token, whole or truncated: SUPPLIERWISE prints
    the bare name, BILLWISE/ITEMWISE print name + 'BAREILLY', so the plain norm
    cannot join the reports (push_expected's finding, confirmed on August 2026)."""
    parts = norm(s).split(" ")
    while len(parts) > 1 and parts[-1] in _CITY_TAILS:
        parts.pop()
    return " ".join(parts)


def billno(s):
    s = str(s if s is not None else "").strip().strip("'")
    try:
        return str(int(float(s)))
    except (TypeError, ValueError):
        return s


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    with io.open(SCHEMA, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()
    _schema_done = True


def _audit(con, who, action, ref="", detail=None):
    con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                (now_iso(), who or "", action, str(ref or ""),
                 json.dumps(detail, ensure_ascii=False) if detail is not None else None))


# ====================================================================== auth
def _machine_auth():
    """The machine door. The token grants exactly these paths and no identity."""
    if _marg_token and request.headers.get("X-Finance-Marg") == _marg_token:
        return {"user": "push_purchases", "roles": []}, None
    return None, (jsonify(ok=False, error="bad_token",
                          message="X-Finance-Marg is missing or wrong."), 401)


def _person(*roles):
    """A signed-in person with one of these roles on the medical unit. Pages are
    fail-closed: the app's own gate has already refused anyone with no role here."""
    u, err = _require(*roles)
    if err:
        return None, err
    return u, None


def _is_doctor(u):
    """The medical unit's checker -- Dr Manoj alone, by the owner's S179 rule."""
    roles = set(u.get("roles") or [])
    return "checker" in roles or u.get("role") == "checker"


def _is_viewer_only(u):
    roles = set(u.get("roles") or [])
    if u.get("role") in ("maker", "checker"):
        return False
    return not roles.intersection({"maker", "checker"})


def _refuse(msg, code=403):
    return jsonify(ok=False, error="not_permitted", message=msg), code


# ====================================================================== pushes
def _iso(s):
    s = str(s or "").strip()
    return s if ISO_RE.match(s) else None


def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _float_or_none(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _effective_md5s(con):
    return {r[0] for r in con.execute(
        "SELECT md5 FROM purchase_export WHERE superseded_by IS NULL")}


@bp.route("/api/healthz")
def api_healthz():
    con = _db()
    _ensure(con)
    r = con.execute("SELECT COUNT(*) n, MAX(received_at) last FROM purchase_export").fetchone()
    return jsonify(ok=True, exports=r[0], last_received=r[1])


@bp.route("/api/push", methods=["POST"])
def api_push():
    u, err = _machine_auth()
    if err:
        return err
    b = request.get_json(silent=True)
    if not isinstance(b, dict):
        return jsonify(ok=False, error="malformed", reason="body is not a JSON object"), 400
    typ = str(b.get("type") or "").upper()
    md5 = str(b.get("md5") or "").lower()
    pf, pt = _iso(b.get("period_from")), _iso(b.get("period_to"))
    stamp = str(b.get("export_stamp") or "")
    rows = b.get("rows")
    for cond, why in ((typ in TYPES, "type must be one of %s" % ", ".join(TYPES)),
                      (bool(MD5_RE.match(md5)), "md5 must be 32 hex"),
                      (bool(pf and pt and pf <= pt), "period_from/period_to must be ISO dates"),
                      (bool(STAMP_RE.match(stamp)), "export_stamp must be YYYYMMDD-HHMMSS"),
                      (isinstance(rows, list), "rows must be a list")):
        if not cond:
            return jsonify(ok=False, error="malformed", reason=why), 400
    con = _db()
    _ensure(con)
    if con.execute("SELECT 1 FROM purchase_export WHERE md5=?", (md5,)).fetchone():
        return jsonify(ok=True, stored=False, reason="duplicate")
    rivals = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type=? AND period_from=? "
        "AND period_to=? AND superseded_by IS NULL", (typ, pf, pt)).fetchall()
    newer = [r for r in rivals if r[1] > stamp]
    if newer:
        con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,"
                    "export_stamp,received_at,n_rows,grand_amount_p,superseded_by) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (md5, typ, str(b.get("file") or "")[:200], pf, pt, stamp, now_iso(),
                     len(rows), _int_or_none(b.get("grand_amount_p")), newer[0][0]))
        con.commit()
        return jsonify(ok=True, stored=False, reason="superseded_older")
    con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,"
                "export_stamp,received_at,n_rows,grand_amount_p,superseded_by) "
                "VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                (md5, typ, str(b.get("file") or "")[:200], pf, pt, stamp, now_iso(),
                 len(rows), _int_or_none(b.get("grand_amount_p"))))
    for r in rivals:
        con.execute("UPDATE purchase_export SET superseded_by=? WHERE md5=?", (md5, r[0]))
    try:
        if typ in ("BILLWISE", "SUPPLIERWISE"):
            n = _store_bills(con, typ, md5, rows)
        else:
            n = _store_lines(con, typ, md5, pf, pt, rows)
    except _Malformed as e:
        con.rollback()
        return jsonify(ok=False, error="malformed", reason=str(e)), 400
    _redate_lines(con)
    _audit(con, "push_purchases", "push", md5, dict(type=typ, period=[pf, pt], rows=n,
                                                     superseded=[r[0] for r in rivals]))
    con.commit()
    return jsonify(ok=True, stored=True, reason="new", rows=n)


class _Malformed(Exception):
    pass


def _store_bills(con, typ, md5, rows):
    """BILLWISE / SUPPLIERWISE rows -> purchase_bill. Identity (supplier_key, bill_no);
    the date from BILLWISE first, SUPPLIERWISE second; verdicts survive re-pushes."""
    col = "bw_md5" if typ == "BILLWISE" else "sw_md5"
    n = 0
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise _Malformed("row %d is not an object" % i)
        sup = str(r.get("supplier") or "").strip()
        bno = billno(r.get("bill_no"))
        d = _iso(r.get("bill_date"))
        cash, credit = _int_or_none(r.get("cash_p")), _int_or_none(r.get("credit_p"))
        if not (sup and bno and d) or cash is None or credit is None:
            raise _Malformed("row %d: supplier, bill_no, bill_date, cash_p, credit_p required" % i)
        key = supplier_key(sup)
        have = con.execute("SELECT id, bill_date, date_src, supplier FROM purchase_bill "
                           "WHERE supplier_norm=? AND bill_no=?", (key, bno)).fetchall()
        target = None
        for h in have:
            if h[1] == d:
                target = h
                break
        if target is None and have:
            # a different date for the same bill: BILLWISE wins over SUPPLIERWISE, and a
            # later export of the same type replaces its own earlier date
            for h in have:
                if typ == "BILLWISE" or h[2] != "BILLWISE":
                    target = h
                    break
        if target is None:
            con.execute("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,"
                        "month,cash_p,credit_p,amount_p,source_md5,%s,date_src) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)" % col,
                        (key, sup, bno, d, d[:7], cash, credit, cash + credit, md5, md5, typ))
        else:
            # keep the longer printed name (the one carrying the city), and the BILLWISE date
            name = target[3] if len(target[3] or "") >= len(sup) else sup
            newdate = d if (typ == "BILLWISE" or target[2] != "BILLWISE") else target[1]
            src = "BILLWISE" if (typ == "BILLWISE" or target[2] == "BILLWISE") else typ
            con.execute("UPDATE purchase_bill SET supplier=?, bill_date=?, month=?, cash_p=?, "
                        "credit_p=?, amount_p=?, source_md5=?, %s=?, date_src=? WHERE id=?" % col,
                        (name, newdate, newdate[:7], cash, credit, cash + credit, md5, md5,
                         src, target[0]))
        n += 1
    return n


def _store_lines(con, typ, md5, pf, pt, rows):
    """ITEMWISE / BILLITEMWISE rows -> purchase_line, dated by the bills when possible."""
    n = 0
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise _Malformed("row %d is not an object" % i)
        item = str(r.get("item") or "").strip()
        if not item:
            raise _Malformed("row %d: item required" % i)
        sup = str(r.get("supplier") or "").strip()
        key = supplier_key(sup) if sup else None
        bno = billno(r.get("bill_no")) or None
        own = _iso(r.get("bill_date"))
        d = _date_for_line(con, key, bno, own, pf, pt)
        if key is None and bno and d:
            k2 = con.execute("SELECT DISTINCT supplier_norm FROM purchase_bill WHERE bill_no=? "
                             "AND bill_date=?", (bno, d)).fetchall()
            if len(k2) == 1:
                key = k2[0][0]
        con.execute(
            "INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,packing,batch,"
            "expiry,tax,qty,free,rate_p,discount_pct,amount_p,net_rate_p,net_amount_p,loose_qty,"
            "purchase_rate_p,direction,source_md5,line_type) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (key, bno, d, d[:7] if d else None, item, r.get("packing"), r.get("batch"),
             r.get("expiry"), _float_or_none(r.get("tax")), _float_or_none(r.get("qty")),
             _float_or_none(r.get("free")), _int_or_none(r.get("rate_p")),
             _float_or_none(r.get("discount_pct")), _int_or_none(r.get("amount_p")),
             _int_or_none(r.get("net_rate_p")), _int_or_none(r.get("net_amount_p")),
             _float_or_none(r.get("loose_qty")), _int_or_none(r.get("purchase_rate_p")),
             str(r.get("direction") or "PURCHASE"), md5, typ))
        n += 1
    return n


def _date_for_line(con, key, bno, own, pf, pt):
    """(supplier_key, bill_no) -> the bill's date, preferring one inside the export's
    period; else the row's own date; else None (shown as UNDATED, blocks finalise)."""
    if bno:
        if key:
            q = con.execute("SELECT bill_date FROM purchase_bill WHERE supplier_norm=? AND "
                            "bill_no=? AND bill_date IS NOT NULL ORDER BY bill_date DESC",
                            (key, bno)).fetchall()
        else:
            q = con.execute("SELECT DISTINCT bill_date FROM purchase_bill WHERE bill_no=? AND "
                            "bill_date IS NOT NULL ORDER BY bill_date DESC", (bno,)).fetchall()
            if len(q) > 1 and not own:
                q = [x for x in q if pf <= x[0] <= pt] if pf and pt else []
                q = q if len(q) == 1 else []
        inside = [x[0] for x in q if pf and pt and pf <= x[0] <= pt]
        if inside:
            return inside[0]
        if q and not own:
            return q[0][0]
    return own


def _redate_lines(con):
    """A bill's date can arrive AFTER its lines (ITEMWISE is pushed before BILLWISE on
    some nights). Re-date every line from the bills, keeping a date the bills confirm.
    Rev 2: a line with NO supplier (BILLITEMWISE prints none) that arrived before its
    bill is linked to the bill the moment (bill_no, date) names exactly one."""
    dates, by_no = {}, {}
    for r in con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill "
                         "WHERE bill_date IS NOT NULL ORDER BY bill_date"):
        dates.setdefault((r[0], r[1]), []).append(r[2])
        by_no.setdefault(r[1], []).append((r[0], r[2]))
    for r in con.execute("SELECT id, supplier_norm, bill_no, bill_date FROM purchase_line "
                         "WHERE supplier_norm IS NOT NULL AND bill_no IS NOT NULL").fetchall():
        have = dates.get((r[1], r[2]))
        if not have or r[3] in have:
            continue
        con.execute("UPDATE purchase_line SET bill_date=? WHERE id=?", (have[-1], r[0]))
    for r in con.execute("SELECT id, bill_no, bill_date FROM purchase_line "
                         "WHERE supplier_norm IS NULL AND bill_no IS NOT NULL").fetchall():
        cands = by_no.get(r[1]) or []
        if r[2]:
            cands = [c for c in cands if c[1] == r[2]]
        keys = {c[0] for c in cands}
        if len(keys) == 1:
            k = keys.pop()
            d = r[2] if r[2] else sorted(c[1] for c in cands)[-1]
            con.execute("UPDATE purchase_line SET supplier_norm=?, bill_date=? WHERE id=?", (k, d, r[0]))
    con.execute("UPDATE purchase_line SET month=substr(bill_date,1,7) WHERE bill_date IS NOT NULL")


@bp.route("/api/vendors", methods=["POST"])
def api_vendors():
    """Vendor phones from manojz's own config. Stored here, shown to maker/checker only,
    never logged, never echoed back in a response."""
    u, err = _machine_auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    pairs = b.get("pairs")
    if not isinstance(pairs, dict):
        return jsonify(ok=False, error="malformed", reason="pairs must be an object"), 400
    con = _db()
    _ensure(con)
    n = 0
    for name, phone in pairs.items():
        name = str(name or "").strip()
        if not name:
            continue
        con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at) "
                    "VALUES (?,?,?,?) ON CONFLICT(vendor_norm) DO UPDATE SET vendor=excluded.vendor, "
                    "phone=excluded.phone, updated_at=excluded.updated_at",
                    (supplier_key(name), name, str(phone or "").strip(), now_iso()))
        n += 1
    _audit(con, "push_purchases", "vendors", "", dict(n=n))
    con.commit()
    return jsonify(ok=True, stored=n)


@bp.route("/api/feed", methods=["POST"])
def api_feed():
    u, err = _machine_auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    con = _db()
    _ensure(con)
    con.execute("INSERT INTO purchase_feed (at, host, pull_last, pull_age_min, state) "
                "VALUES (?,?,?,?,?)",
                (now_iso(), str(b.get("host") or "")[:40], str(b.get("pull_last") or "")[:40],
                 _int_or_none(b.get("pull_age_min")), str(b.get("state") or "")[:20]))
    con.commit()
    return jsonify(ok=True)


# ====================================================================== the effective set
# An export that has been superseded is kept and IGNORED. A bill is effective while
# either export that last carried it (BILLWISE or SUPPLIERWISE) is un-superseded; a
# line is effective while its own export is.
EFF_BILL = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND "
            "(e.md5=b.bw_md5 OR e.md5=b.sw_md5))")
EFF_LINE = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND "
            "e.md5=l.source_md5)")


def _bills_for_month(con, month):
    return con.execute(
        "SELECT b.* FROM purchase_bill b WHERE b.month=? AND " + EFF_BILL +
        " ORDER BY b.supplier, b.bill_date, b.bill_no", (month,)).fetchall()


AGREE_P = 100          # a bill AGREES with its lines when |bill-wise - item-wise net| <= Rs 1


def _line_sets(con, month):
    """The month's effective item lines, ONE set per bill.

    Key (supplier_norm, bill_no). Money is NET (net_amount_p, after discount; gross is
    carried beside it, labelled). Where more than one live export carries the same
    bill's lines (ITEMWISE 28-29 Aug and BILLITEMWISE 28-31 Aug both carry bill 370),
    the export with the LATER export_stamp is the bill's set and the other export's
    lines for that bill are ignored -- kept in the table, never deleted."""
    sets = {}
    for r in con.execute(
            "SELECT l.supplier_norm, l.bill_no, l.bill_date, l.line_type, l.source_md5, "
            "e.export_stamp, COALESCE(SUM(COALESCE(l.net_amount_p, l.amount_p)),0), "
            "COALESCE(SUM(l.amount_p),0), COUNT(*) FROM purchase_line l JOIN purchase_export e "
            "ON e.md5=l.source_md5 WHERE l.month=? AND e.superseded_by IS NULL "
            "GROUP BY l.supplier_norm, l.bill_no, l.bill_date, l.line_type, l.source_md5, e.export_stamp",
            (month,)):
        cand = dict(supplier_norm=r[0], bill_no=r[1], bill_date=r[2], line_type=r[3], md5=r[4],
                    stamp=r[5], net_p=r[6], gross_p=r[7], n=r[8])
        k = (r[0], r[1])
        have = sets.get(k)
        if have is None or (cand["stamp"], cand["md5"]) > (have["stamp"], have["md5"]):
            sets[k] = cand
    return sets


def _bill_lines(bill, sets):
    """The bill's line set, or None. A set with no supplier (a BILLITEMWISE bill whose
    bill-wise row has not yet named it) still counts when bill_no and date agree."""
    t = sets.get((bill["supplier_norm"], bill["bill_no"]))
    if t is None:
        t = sets.get((None, bill["bill_no"]))
        if t is not None and t["bill_date"] != bill["bill_date"]:
            t = None
    return t


def _undated_lines(con, month=None):
    """Effective lines with no date. With a month: only those whose export's period
    touches that month (that is what stops the month from finalising)."""
    sql = ("SELECT l.*, e.file, e.period_from, e.period_to FROM purchase_line l JOIN "
           "purchase_export e ON e.md5=l.source_md5 WHERE l.bill_date IS NULL AND "
           "e.superseded_by IS NULL")
    args = ()
    if month:
        sql += " AND substr(e.period_from,1,7)<=? AND substr(e.period_to,1,7)>=?"
        args = (month, month)
    return con.execute(sql + " ORDER BY e.period_from, l.bill_no, l.item", args).fetchall()


def _month_status(con, month):
    r = con.execute("SELECT * FROM purchase_month WHERE month=?", (month,)).fetchone()
    return dict(r) if r else {"month": month, "status": "provisional", "finalised_by": None,
                              "finalised_at": None, "billwise_total_p": None,
                              "itemwise_total_p": None, "note": None}


def _plural(n, one, many=None):
    return "%d %s" % (n, one if n == 1 else (many or one + "s"))


def _dates_text(dates):
    """['2026-08-22','2026-08-24',...] -> '22, 24, 25-Aug' (one month) -- readable, short."""
    ds = sorted(set(d for d in dates if d))
    if not ds:
        return ""
    if len(ds) <= 6:
        days = ", ".join(_human(d)[:2].lstrip("0") for d in ds)
        return "%s-%s" % (days, _human(ds[0])[3:6])
    return "%s ... %s (%d days)" % (_human(ds[0])[:6], _human(ds[-1])[:6], len(ds))


def _bill_short(b):
    return "%s (%s, %s)" % (b["bill_no"], _human(b["bill_date"])[:6], b["supplier_norm"] or "?")


def _name_some(items, fmt, limit=6):
    out = [fmt(x) for x in items[:limit]]
    if len(items) > limit:
        out.append("and %d more" % (len(items) - limit))
    return ", ".join(out)


def _month_summary(con, month):
    """Per-bill reconciliation. Buckets: AGREES (|diff| <= Rs 1), DIFFERS, NO ITEM LINES,
    and ITEM LINES WITH NO BILL. Money: bill-wise from Marg's bill report; item-wise is
    the NET sum of each bill's one line set (see _line_sets)."""
    bills = _bills_for_month(con, month)
    sets = _line_sets(con, month)
    bw = sum(b["amount_p"] for b in bills)
    agree, differ, no_lines, used = [], [], [], set()
    iw = 0
    for b in bills:
        t = _bill_lines(b, sets)
        if t is None:
            no_lines.append(b)
            continue
        used.add((t["supplier_norm"], t["bill_no"]))
        iw += t["net_p"]
        d = t["net_p"] - b["amount_p"]
        if abs(d) <= AGREE_P:
            agree.append(b)
        else:
            hint = "purchase return?" if t["net_p"] > b["amount_p"] else "discount or rounding at bill level?"
            differ.append(dict(bill=b, net_p=t["net_p"], gross_p=t["gross_p"], n=t["n"], diff_p=d, hint=hint))
    orphans = [t for k, t in sets.items() if k not in used]
    orphan_p = sum(t["net_p"] for t in orphans)
    wrong = [b for b in bills if b["verdict"] == "WRONG"]
    unverdicted = [b for b in bills if not b["verdict"]]
    differ_open = [x for x in differ if x["bill"]["verdict"] != "CORRECT"]
    gap_dates = sorted(set(b["bill_date"] for b in no_lines))
    undated = _undated_lines(con, month)
    st = _month_status(con, month)
    reasons = []
    if wrong:
        reasons.append("%s marked WRONG and not yet resolved: %s"
                       % (_plural(len(wrong), "bill"), _name_some(wrong, _bill_short)))
    if undated:
        reasons.append("%s could not be dated" % _plural(len(undated), "item line"))
    if no_lines:
        reasons.append("%s no item-wise lines (item-wise export missing for %s): %s"
                       % (_plural(len(no_lines), "bill has", "bills have"), _dates_text(gap_dates),
                          _name_some(no_lines, _bill_short)))
    if differ_open:
        reasons.append("%s from %s item lines and %s not yet marked Correct: %s"
                       % (_plural(len(differ_open), "bill differs", "bills differ"),
                          "its" if len(differ_open) == 1 else "their",
                          "is" if len(differ_open) == 1 else "are",
                          _name_some(differ_open, lambda x: "%s (bill-wise %s, item-wise net %s, %s)"
                                     % (_bill_short(x["bill"]), _r(x["bill"]["amount_p"]), _r(x["net_p"]), x["hint"]))))
    if orphans:
        reasons.append("%s belong to no bill of this month (%s): %s"
                       % (_plural(len(orphans), "item line set"), _r(orphan_p),
                          _name_some(orphans, lambda t: "%s (%s)" % (t["bill_no"], _human(t["bill_date"])[:6]))))
    if not bills:
        reasons.append("no bills have been pushed for this month")
    # the one-line plain-English verdict for the hub
    mn = _month_name(month)
    if st["status"] == "final":
        story = "%s: FINAL -- finalised by %s on %s." % (mn, st["finalised_by"], (st["finalised_at"] or "")[:10])
    elif not bills:
        story = "%s: no bills yet." % mn
    else:
        bits = []
        if no_lines:
            last = "%02d" % _days_in_month(month)
            bits.append("%s on %s have no item-wise lines (%s) -- export item-wise 01-%s %s once and this closes"
                        % (_plural(len(no_lines), "bill"), _plural(len(gap_dates), "day"), _dates_text(gap_dates),
                           last, _human(month + "-01")[3:6]))
        if differ_open:
            bits.append("%s from %s item lines (%s) -- mark each Correct (a return or rounding) or Wrong"
                        % (_plural(len(differ_open), "bill differs", "bills differ"),
                           "its" if len(differ_open) == 1 else "their",
                           _name_some(differ_open, lambda x: "%s %s" % (x["bill"]["bill_no"], x["hint"].rstrip("?")), 3)))
        if wrong:
            bits.append("%s marked WRONG" % _plural(len(wrong), "bill"))
        if undated:
            bits.append("%s undated" % _plural(len(undated), "item line"))
        if orphans:
            bits.append("%s with no bill here" % _plural(len(orphans), "item line set"))
        if not bits:
            bits.append("all %d bills agree with their item lines to the rupee -- the doctor can finalise" % len(bills))
        elif len(agree) == len(bills):
            bits.insert(0, "all %d bills agree" % len(bills))
        else:
            bits.insert(0, "%d of %d bills agree" % (len(agree), len(bills)))
        story = "%s: %s." % (mn, "; ".join(bits))
    return dict(month=month, bills=bills, sets=sets, billwise_p=bw, itemwise_p=iw + orphan_p,
                itemwise_bills_p=iw, orphan_p=orphan_p, diff_p=bw - (iw + orphan_p),
                agree=agree, differ=differ, differ_open=differ_open, no_lines=no_lines,
                orphans=orphans, gap_dates=gap_dates, wrong=len(wrong), unverdicted=len(unverdicted),
                undated=undated, status=st, can_finalise=not reasons, reasons=reasons, story=story)


def _days_in_month(ym):
    try:
        y, m = int(ym[:4]), int(ym[5:7])
        nxt = dt.date(y + (m == 12), (m % 12) + 1, 1)
        return (nxt - dt.timedelta(days=1)).day
    except (TypeError, ValueError):
        return 31


def _months(con, n=6):
    got = [r[0] for r in con.execute(
        "SELECT DISTINCT b.month FROM purchase_bill b WHERE b.month IS NOT NULL AND " + EFF_BILL +
        " ORDER BY b.month DESC LIMIT ?", (n,))]
    return got


# ====================================================================== verdict / finalise
def _who(u):
    return u.get("user") or ""


@bp.route("/api/verdict", methods=["POST"])
def api_verdict():
    u, err = _person("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    bid = _int_or_none(b.get("bill_id"))
    verdict = str(b.get("verdict") or "").upper()
    if not bid or verdict not in ("CORRECT", "WRONG"):
        return jsonify(ok=False, error="malformed", message="bill_id and verdict CORRECT|WRONG"), 400
    con = _db()
    _ensure(con)
    row = con.execute("SELECT * FROM purchase_bill WHERE id=?", (bid,)).fetchone()
    if row is None:
        return jsonify(ok=False, error="no_such_bill"), 404
    st = _month_status(con, row["month"] or "")
    if st["status"] == "final":
        return _refuse("This month is FINAL. The doctor must reopen it first.")
    wrong_p, reason = None, str(b.get("reason") or "").strip()[:300]
    if verdict == "WRONG":
        wrong_p = _int_or_none(b.get("wrong_amount_p"))
        if wrong_p is None:
            rup = str(b.get("wrong_amount") or "").replace(",", "").replace("₹", "").strip()
            try:
                wrong_p = int(round(float(rup) * 100)) if rup else None
            except ValueError:
                wrong_p = None
        if wrong_p is None or not reason:
            return jsonify(ok=False, error="malformed",
                           message="WRONG needs the amount you believe is right, and a reason"), 400
    con.execute("UPDATE purchase_bill SET verdict=?, verdict_by=?, verdict_at=?, wrong_amount_p=?, "
                "reason=? WHERE id=?", (verdict, _who(u), now_iso(), wrong_p, reason or None, bid))
    _audit(con, _who(u), "verdict", bid, dict(verdict=verdict, wrong_amount_p=wrong_p,
                                              reason=reason, before=row["verdict"]))
    con.commit()
    return jsonify(ok=True, bill_id=bid, verdict=verdict)


@bp.route("/api/finalise", methods=["POST"])
def api_finalise():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("Only the doctor can finalise a month.")
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    if not re.match(r"^\d{4}-\d{2}$", month):
        return jsonify(ok=False, error="malformed", message="month yyyy-mm"), 400
    con = _db()
    _ensure(con)
    s = _month_summary(con, month)
    if s["status"]["status"] == "final":
        return jsonify(ok=True, month=month, status="final", already=True)
    if not s["can_finalise"]:
        return jsonify(ok=False, error="cannot_finalise", month=month, reasons=s["reasons"]), 409
    con.execute("INSERT INTO purchase_month (month,status,finalised_by,finalised_at,"
                "billwise_total_p,itemwise_total_p,note) VALUES (?,?,?,?,?,?,?) ON CONFLICT(month) "
                "DO UPDATE SET status=excluded.status, finalised_by=excluded.finalised_by, "
                "finalised_at=excluded.finalised_at, billwise_total_p=excluded.billwise_total_p, "
                "itemwise_total_p=excluded.itemwise_total_p, note=excluded.note",
                (month, "final", _who(u), now_iso(), s["billwise_p"], s["itemwise_p"],
                 str(b.get("note") or "")[:300] or None))
    _audit(con, _who(u), "finalise", month, dict(billwise_p=s["billwise_p"],
                                                 itemwise_p=s["itemwise_p"], bills=len(s["bills"])))
    con.commit()
    return jsonify(ok=True, month=month, status="final")


@bp.route("/api/reopen", methods=["POST"])
def api_reopen():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("Only the doctor can reopen a month.")
    b = request.get_json(silent=True) or {}
    month, reason = str(b.get("month") or ""), str(b.get("reason") or "").strip()[:300]
    if not re.match(r"^\d{4}-\d{2}$", month) or not reason:
        return jsonify(ok=False, error="malformed", message="month yyyy-mm and a reason"), 400
    con = _db()
    _ensure(con)
    con.execute("INSERT INTO purchase_month (month,status,note) VALUES (?,?,?) ON CONFLICT(month) "
                "DO UPDATE SET status='provisional', note=excluded.note", (month, "provisional",
                                                                             "reopened: " + reason))
    _audit(con, _who(u), "reopen", month, dict(reason=reason))
    con.commit()
    return jsonify(ok=True, month=month, status="provisional")


# ====================================================================== scans (asset app)
def _assets_con():
    """READ-ONLY. None when the asset app's database is not reachable -- and then the
    scan-link section says so and nothing else breaks."""
    try:
        if not _assets_db or not os.path.exists(_assets_db):
            return None
        con = sqlite3.connect("file:%s?mode=ro" % _assets_db, uri=True, timeout=2)
        con.row_factory = sqlite3.Row
        con.execute("SELECT 1 FROM bills LIMIT 1")
        return con
    except Exception:                                   # noqa: BLE001
        return None


def _scans(acon):
    """Pharmacy scans: kind='Pharmacy'. Columns that a given asset.db may lack are read
    as NULL rather than assumed."""
    cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
    want = ["id", "vendor", "bill_no", "bill_date", "total_amount", "status", "ocr_status",
            "created_at"]
    sel = ", ".join(c if c in cols else "NULL AS %s" % c for c in want)
    rows = acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' ORDER BY id DESC LIMIT 2000"
                        % sel).fetchall()
    out = []
    for r in rows:
        amt = _float_or_none(r["total_amount"])
        out.append(dict(id=r["id"], vendor=r["vendor"] or "", bill_no=billno(r["bill_no"]),
                        bill_date=_iso(r["bill_date"]) or _iso_any(r["bill_date"]),
                        amount_p=int(round(amt * 100)) if amt is not None else None,
                        status=r["status"] or "", ocr_status=r["ocr_status"] or "",
                        created_at=r["created_at"] or ""))
    return out


def _iso_any(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y"):
        try:
            return dt.datetime.strptime(s[:10] if fmt != "%d-%b-%Y" else s[:11], fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _vendor_match(a, b):
    a, b = supplier_key(a), supplier_key(b)
    return bool(a and b) and (a == b or a in b or b in a)


def _grade(scan, bill):
    """EXACT: vendor match AND bill no equal AND amount within Rs 1.
    PROBABLE: bill no equal AND amount within 2 %, OR vendor match AND date equal AND
    amount within Rs 1. Else NONE."""
    sa, ba = scan["amount_p"], bill["amount_p"]
    if sa is None:
        return "NONE", ""
    vend = _vendor_match(scan["vendor"], bill["supplier"])
    bno = bool(scan["bill_no"]) and scan["bill_no"] == bill["bill_no"]
    near1 = abs(sa - ba) <= 100
    near2 = abs(sa - ba) <= max(100, int(round(0.02 * ba)))
    date = bool(scan["bill_date"]) and scan["bill_date"] == bill["bill_date"]
    if vend and bno and near1:
        return "EXACT", "vendor+bill+amount"
    if bno and near2:
        return "PROBABLE", "bill+amount~2%"
    if vend and date and near1:
        return "PROBABLE", "vendor+date+amount"
    return "NONE", ""


def _rematch(con, who="system"):
    """Recompute every scan link from scratch. Stores EXACT and PROBABLE; a bill with no
    match has no row, and is what the page lists as 'unscanned'."""
    acon = _assets_con()
    if acon is None:
        return None
    scans = _scans(acon)
    acon.close()
    bills = con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()
    con.execute("DELETE FROM purchase_scan_link")
    used, n = set(), 0
    for want in ("EXACT", "PROBABLE"):
        for b in bills:
            if con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=?", (b["id"],)).fetchone():
                continue
            for s in scans:
                if s["id"] in used:
                    continue
                g, on = _grade(s, b)
                if g == want:
                    con.execute("INSERT INTO purchase_scan_link (bill_id,asset_bill_id,grade,"
                                "matched_on,linked_at) VALUES (?,?,?,?,?)",
                                (b["id"], s["id"], g, on, now_iso()))
                    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (s["id"], b["id"]))
                    used.add(s["id"])
                    n += 1
                    break
    _audit(con, who, "rematch", "", dict(links=n, scans=len(scans), bills=len(bills)))
    con.commit()
    return dict(links=n, scans=len(scans), bills=len(bills),
                unmatched_scans=[s for s in scans if s["id"] not in used],
                unscanned_bills=[b for b in bills if b["id"] not in {
                    r[0] for r in con.execute("SELECT bill_id FROM purchase_scan_link")}])


def _scan_state(con):
    """What the hub shows without re-matching: counts from the stored links."""
    acon = _assets_con()
    if acon is None:
        return None
    scans = _scans(acon)
    acon.close()
    linked = {r[0] for r in con.execute("SELECT asset_bill_id FROM purchase_scan_link")}
    linked_bills = {r[0] for r in con.execute("SELECT bill_id FROM purchase_scan_link")}
    bills = con.execute("SELECT b.id FROM purchase_bill b WHERE " + EFF_BILL).fetchall()
    return dict(scans=len(scans), unmatched_scans=sum(1 for s in scans if s["id"] not in linked),
                unscanned_bills=sum(1 for b in bills if b[0] not in linked_bills))


@bp.route("/api/rematch", methods=["POST"])
def api_rematch():
    u, err = _person("maker", "checker")
    if err:
        return err
    con = _db()
    _ensure(con)
    r = _rematch(con, _who(u))
    if r is None:
        return jsonify(ok=False, error="assets_unreachable",
                       message="asset app not reachable"), 503
    return jsonify(ok=True, links=r["links"], scans=r["scans"], bills=r["bills"])


# ====================================================================== the reorder engine
# A COPY of po_engine.py (S207_PO: cadence_for, confidence, plan_line) with the S206
# cadence and every quantity rail intact. Copied, not imported: kits do not import
# across each other on the box. NOTHING HERE SENDS ANYTHING. It writes a plan.
TIER_WEEKLY_P = 2000000
TIER_FORTNIGHT_P = 400000
CADENCE_DAYS = {"weekly": 7, "fortnightly": 14, "monthly": 30}
LEAD_DAYS = 2
SAFETY_DAYS = 3
SINGLE_SOURCE_EXTRA_DAYS = 3
MAX_COVER_DAYS = 45
PEAK_SHARE_SPIKE = 0.40
THIN_SELL_DAYS = 5
LOW_CONF_DAYS = 20
DEAD_AFTER_DAYS = 60
MIN_LINE_P = 5000
DEFAULT_BOX = 10
BOX_STRETCH_ASK = 2.0
CONFIRM_LINE_P = 500000


def ceil_div(a, b):
    return -(-a // b) if b else 0


def cadence_for(monthly_p, observed_per_month):
    if monthly_p >= TIER_WEEKLY_P:
        want = "weekly"
    elif monthly_p >= TIER_FORTNIGHT_P:
        want = "fortnightly"
    else:
        want = "monthly"
    if observed_per_month and observed_per_month > 0:
        observed_days = 30.0 / observed_per_month
        for name in ("weekly", "fortnightly", "monthly"):
            if CADENCE_DAYS[name] >= observed_days - 0.01:
                break
        if CADENCE_DAYS[name] > CADENCE_DAYS[want]:
            return name, want
    return want, want


def confidence(sell_days):
    if sell_days >= LOW_CONF_DAYS:
        return "high"
    if sell_days >= THIN_SELL_DAYS:
        return "medium"
    return "thin"


def plan_line(it, cad_days):
    cover = cad_days + LEAD_DAYS + SAFETY_DAYS
    if it["single_source"]:
        cover += SINGLE_SOURCE_EXTRA_DAYS
    capped = min(cover, MAX_COVER_DAYS)
    rate = it["rate_per_day"]
    target = rate * capped
    need = target - it["on_hand"]
    size = max(1, int(it["pack_size"] or 1))
    strips = 0 if need <= 0 else ceil_div(int(math.ceil(need)), size)
    reasons, confirm = [], False
    box = int(it.get("box") or 0)
    if size == 1:
        box = box if box > 1 else 1
    elif box <= 1:
        box = DEFAULT_BOX
    if strips and box > 1:
        rounded = ceil_div(strips, box) * box
        if rounded != strips:
            reasons.append("rounded up from %d to a box of %d" % (strips, box))
            if rounded >= BOX_STRETCH_ASK * strips:
                confirm = True
                reasons.append("the box is %.0fx what is actually needed" % (float(rounded) / strips))
        strips = rounded
    value_p = int(strips * size * (it["cost_p"] or 0))
    conf = confidence(it["sell_days"])
    peak = it.get("peak_share") or 0.0
    if strips and peak >= PEAK_SHARE_SPIKE:
        confirm = True
        reasons.append("one day was %d%% of the window's sales -- a spike, not a rate" % round(peak * 100))
    if strips and conf == "thin":
        confirm = True
        reasons.append("sold on only %d day%s in %d -- the daily rate is a guess"
                       % (it["sell_days"], "" if it["sell_days"] == 1 else "s", PACE_DAYS))
    if strips and value_p >= CONFIRM_LINE_P:
        confirm = True
        reasons.append("one line over Rs %d" % (CONFIRM_LINE_P // 100))
    if strips and it["days_since_sale"] > DEAD_AFTER_DAYS:
        strips, value_p = 0, 0
        reasons.append("nothing sold for %d days -- not reordered" % it["days_since_sale"])
    if strips and value_p < MIN_LINE_P and it["on_hand"] > 0:
        strips, value_p = 0, 0
        reasons.append("under Rs %d and not out of stock -- waits for the next run" % (MIN_LINE_P // 100))
    if cover > MAX_COVER_DAYS:
        reasons.append("cover capped at %d days" % MAX_COVER_DAYS)
    return {"item": it["item"], "vendor": it["vendor"], "on_hand": it["on_hand"],
            "rate_per_day": round(rate, 2), "sell_days": it["sell_days"], "confidence": conf,
            "cover_days": capped, "pack_size": size, "box": box, "order_strips": strips,
            "order_units": strips * size, "value_p": value_p, "confirm": confirm,
            "single_source": it["single_source"], "days_since_sale": it["days_since_sale"],
            "peak_share": round(peak, 3), "why": reasons}


# ---------------------------------------------------------------- the engine's inputs
def _as_on_key(s):
    t = (s or "").strip().replace("/", "-").split("-")
    if len(t) == 3:
        try:
            a, b, c = (int(x) for x in t)
            if a > 1900:
                return (a, b, c)
            if c > 1900:
                return (c, b, a)
        except ValueError:
            pass
    return (0, 0, 0)


def _table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


def _latest_snapshot(con):
    """{norm(item): dict(item, qty, packing, pack_size)} from the newest stock_snapshot."""
    if not _table_exists(con, "stock_snapshot"):
        return None, {}
    dates = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not dates:
        return None, {}
    as_on = max(dates, key=_as_on_key)
    out = {}
    for r in con.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on=?",
                         (as_on,)):
        out[norm(r[0])] = dict(item=r[0], qty=int(r[1] or 0), packing=r[2] or "",
                               pack_size=max(1, int(r[3] or 1)))
    return as_on, out


def _units(qty_raw, size):
    """sale_line_item.qty_raw is 'strips:loose' as Marg prints it, or a plain number."""
    s = str(qty_raw or "").strip()
    if not s or s == "-":
        return 0.0
    if ":" in s:
        a, b = (s.split(":", 1) + ["0"])[:2]
        try:
            return float(a or 0) * size + float(b or 0)
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _pace(con, snap, today):
    """Per item: units per day over the last PACE_DAYS of sale_line_item, the count of
    selling days, the peak day's share, and days since the last sale."""
    out = {}
    if not _table_exists(con, "sale_line_item"):
        return out
    since = (today - dt.timedelta(days=PACE_DAYS)).isoformat()
    rows = con.execute(
        "SELECT item_name, business_date, qty_raw, is_return FROM sale_line_item WHERE unit=? AND "
        "business_date>=? AND business_date<=?", (_unit, since, today.isoformat())).fetchall()
    last = {r[0]: r[1] for r in con.execute(
        "SELECT item_name, MAX(business_date) FROM sale_line_item WHERE unit=? GROUP BY item_name",
        (_unit,))}
    per = {}
    for r in rows:
        k = norm(r[0])
        size = (snap.get(k) or {}).get("pack_size", 1)
        u = _units(r[2], size) * (-1 if r[3] else 1)
        e = per.setdefault(k, {"days": {}, "total": 0.0})
        e["days"][r[1]] = e["days"].get(r[1], 0.0) + u
        e["total"] += u
    lastn = {}
    for name, d in last.items():
        k = norm(name)
        if k not in lastn or d > lastn[k]:
            lastn[k] = d
    for k, e in per.items():
        total = max(0.0, e["total"])
        peak = max(e["days"].values()) if e["days"] else 0.0
        out[k] = dict(rate_per_day=total / PACE_DAYS,
                      sell_days=sum(1 for v in e["days"].values() if v > 0),
                      peak_share=(peak / total) if total > 0 else 0.0)
    for k, d in lastn.items():
        try:
            dsl = (today - dt.date.fromisoformat(d)).days
        except ValueError:
            dsl = 999
        out.setdefault(k, dict(rate_per_day=0.0, sell_days=0, peak_share=0.0))["days_since_sale"] = dsl
    return out


def _last_purchase(con):
    """Per item: the last supplier and rate (paise per pack), how many suppliers ever, and
    the box (GCD of the quantities it was bought in)."""
    out = {}
    rows = con.execute(
        "SELECT l.item, l.supplier_norm, l.bill_date, l.rate_p, l.purchase_rate_p, l.qty, "
        "l.packing FROM purchase_line l WHERE " + EFF_LINE + " AND l.line_type='ITEMWISE' "
        "ORDER BY l.bill_date").fetchall()
    for r in rows:
        k = norm(r[0])
        e = out.setdefault(k, dict(vendor=None, vendor_disp=None, rate_p=None, suppliers=set(),
                                   qtys=[], packing=r[6]))
        if r[1]:
            e["suppliers"].add(r[1])
            e["vendor"] = r[1]
        rp = r[4] or r[3]
        if rp:
            e["rate_p"] = rp
        if r[5]:
            e["qtys"].append(int(r[5]))
    names = {r[0]: r[1] for r in con.execute(
        "SELECT supplier_norm, MAX(supplier) FROM purchase_bill GROUP BY supplier_norm")}
    for e in out.values():
        g = 0
        for q in e["qtys"]:
            g = math.gcd(g, q)
        e["box"] = g if g > 1 else 0
        e["vendor_disp"] = names.get(e["vendor"]) or e["vendor"]
    return out


def _vendor_cadence(con, today):
    """{supplier_norm: cadence_days} from the last 90 days of effective bills."""
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    for r in con.execute(
            "SELECT b.supplier_norm, SUM(b.amount_p), COUNT(*) FROM purchase_bill b WHERE "
            "b.bill_date>=? AND " + EFF_BILL + " GROUP BY b.supplier_norm", (since,)):
        monthly_p = (r[1] or 0) / 3.0
        cad, _want = cadence_for(monthly_p, (r[2] or 0) / 3.0)
        out[r[0]] = CADENCE_DAYS[cad]
    return out


def _feed_days(con):
    if not _table_exists(con, "stock_feed"):
        return 0
    return con.execute("SELECT COUNT(DISTINCT as_on) FROM stock_feed").fetchone()[0]


def reorder_plan(con, today=None):
    """The plan: per vendor, the lines the engine would order, and why."""
    today = today or dt.date.today()
    as_on, snap = _latest_snapshot(con)
    pace = _pace(con, snap, today)
    purch = _last_purchase(con)
    cad = _vendor_cadence(con, today)
    vendors = {}
    considered = 0
    for k, s in snap.items():
        p = pace.get(k)
        if not p:
            continue
        lp = purch.get(k) or {}
        vendor = lp.get("vendor")
        cost_pack = lp.get("rate_p")
        cost_unit = (cost_pack / float(s["pack_size"])) if cost_pack else 0
        if not cost_unit and _table_exists(con, "stock_rate"):
            r = con.execute("SELECT rate_p FROM stock_rate WHERE item=?", (s["item"],)).fetchone()
            cost_unit = r[0] if r else 0
        it = dict(item=s["item"], vendor=lp.get("vendor_disp") or "(no supplier on record)",
                  on_hand=s["qty"], rate_per_day=p["rate_per_day"], sell_days=p["sell_days"],
                  peak_share=p["peak_share"], days_since_sale=p.get("days_since_sale", 0),
                  pack_size=s["pack_size"], cost_p=cost_unit,
                  single_source=len(lp.get("suppliers") or ()) <= 1, box=lp.get("box") or 0)
        considered += 1
        line = plan_line(it, cad.get(vendor, CADENCE_DAYS["fortnightly"]))
        if line["order_strips"] <= 0 and not line["confirm"]:
            continue
        line["rate_p"] = int(round(cost_unit * s["pack_size"]))
        line["cover_after"] = (round((s["qty"] + line["order_units"]) / p["rate_per_day"], 1)
                               if p["rate_per_day"] > 0 else None)
        line["vendor_norm"] = vendor or ""
        v = vendors.setdefault(line["vendor"], dict(vendor=line["vendor"], vendor_norm=vendor or "",
                                                     lines=[], total_p=0,
                                                     cadence_days=cad.get(vendor)))
        v["lines"].append(line)
        v["total_p"] += line["value_p"]
    for v in vendors.values():
        v["lines"].sort(key=lambda x: -x["value_p"])
    feed_days = _feed_days(con)
    return dict(as_on=as_on, considered=considered, items_paced=len(pace),
                vendors=sorted(vendors.values(), key=lambda v: -v["total_p"]),
                feed_days=feed_days, provisional=feed_days < FEED_DAYS_FOR_TRUST,
                pace_days=PACE_DAYS, today=today.isoformat())


# ====================================================================== orders
@bp.route("/api/order", methods=["POST"])
def api_order():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("Only the doctor can create or move an order.")
    b = request.get_json(silent=True) or {}
    action = str(b.get("action") or "")
    con = _db()
    _ensure(con)
    if action == "create":
        vendor = str(b.get("vendor") or "").strip()[:120]
        lines = b.get("lines")
        if not vendor or not isinstance(lines, list) or not lines:
            return jsonify(ok=False, error="malformed", message="vendor and lines required"), 400
        cur = con.execute("INSERT INTO purchase_order (created_at,created_by,vendor,status,note,"
                          "total_p) VALUES (?,?,?,?,?,0)",
                          (now_iso(), _who(u), vendor, "draft", str(b.get("note") or "")[:300] or None))
        oid = cur.lastrowid
        total = 0
        for ln in lines:
            if not isinstance(ln, dict) or not str(ln.get("item") or "").strip():
                continue
            packs = _int_or_none(ln.get("packs")) or 0
            size = max(1, _int_or_none(ln.get("pack_size")) or 1)
            rate = _int_or_none(ln.get("rate_p")) or 0
            units = packs * size
            value = packs * rate
            total += value
            con.execute("INSERT INTO purchase_order_line (order_id,item,packs,pack_size,units,rate_p,"
                        "value_p,on_hand,per_day,cover_after) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid, str(ln.get("item")).strip()[:120], packs, size, units, rate, value,
                         _int_or_none(ln.get("on_hand")), _float_or_none(ln.get("per_day")),
                         _float_or_none(ln.get("cover_after"))))
        con.execute("UPDATE purchase_order SET total_p=? WHERE id=?", (total, oid))
        _audit(con, _who(u), "order_create", oid, dict(vendor=vendor, total_p=total, lines=len(lines)))
        con.commit()
        return jsonify(ok=True, order_id=oid, total_p=total)
    if action == "status":
        oid, status = _int_or_none(b.get("id")), str(b.get("status") or "")
        if not oid or status not in ORDER_STATUS:
            return jsonify(ok=False, error="malformed", message="id and status draft|sent|received|cancelled"), 400
        row = con.execute("SELECT status FROM purchase_order WHERE id=?", (oid,)).fetchone()
        if row is None:
            return jsonify(ok=False, error="no_such_order"), 404
        con.execute("UPDATE purchase_order SET status=? WHERE id=?", (status, oid))
        _audit(con, _who(u), "order_status", oid, dict(before=row[0], after=status))
        con.commit()
        return jsonify(ok=True, order_id=oid, status=status)
    return jsonify(ok=False, error="malformed", message="action create|status"), 400


def _orders(con):
    out = []
    for o in con.execute("SELECT * FROM purchase_order ORDER BY id DESC LIMIT 100"):
        lines = con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY id",
                            (o["id"],)).fetchall()
        out.append(dict(o, lines=[dict(l) for l in lines]))
    return out


def _phone_for(con, vendor):
    r = con.execute("SELECT phone FROM purchase_vendor_contact WHERE vendor_norm=?",
                    (supplier_key(vendor),)).fetchone()
    return (r[0] or "") if r else ""


# ====================================================================== pages
def _r(p):
    """paise -> 'Rs 12,345' (whole rupees; the reports print whole rupees)."""
    if p is None:
        return "—"
    neg = p < 0
    v = int(round(abs(p) / 100.0))
    s = "{:,}".format(v)
    return ("−" if neg else "") + "₹" + s


def _esc(s):
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _human(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return iso or "—"


def _month_name(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except (TypeError, ValueError):
        return ym


def _hhmm_ist(iso):
    try:
        return dt.datetime.fromisoformat(iso).strftime("%H:%M")
    except (TypeError, ValueError):
        return "?"


CSS = """
:root{--ink:#1a1a1a;--muted:#5b5b5b;--line:#d9d9d9;--bg:#fafafa;--warn:#8a5300;
      --bad:#8c1d18;--ok:#14532d;--chip:#f0f0f0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:14px}
h1{font-size:19px;margin:0 0 2px}
h2{font-size:16px;margin:18px 0 8px}
h3{font-size:15px;margin:14px 0 6px}
.muted{color:var(--muted);font-size:13.5px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.spread{justify-content:space-between}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:7px 6px;text-align:left;vertical-align:top}
th{font-size:12.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
td.n,th.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
button{font:inherit;padding:7px 11px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer}
button.p{background:var(--ink);color:#fff;border-color:var(--ink)}
button.sm{padding:4px 8px;font-size:13px}
input,select,textarea{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.kv{border:1px solid var(--line);border-radius:8px;padding:9px 11px;background:#fff}
.kv b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.kv span{color:var(--muted);font-size:12.5px}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:1px 9px;font-size:12.5px}
.bad{color:var(--bad)}.ok{color:var(--ok)}.warn{color:var(--warn)}
.note{border-left:3px solid var(--warn);padding:8px 11px;background:#fffaf1;border-radius:0 8px 8px 0;margin:10px 0}
.copy{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;white-space:pre-wrap;
      background:#f6f6f6;border:1px solid var(--line);border-radius:8px;padding:9px}
a{color:#0b4f9c}
nav a{margin-right:12px}
.scroll{overflow-x:auto}
@media print{body{background:#fff}.noprint{display:none!important}
  .card{border:none;padding:0;margin:0 0 16px}.wrap{max-width:none;padding:0}table{font-size:11.5px}}
"""

JS = """
async function post(url, body){
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'},
                              credentials:'same-origin', body: JSON.stringify(body||{})});
  let j = {}; try { j = await r.json(); } catch(e) {}
  if (!r.ok || j.ok === false){
    alert((j.message || j.error || ('HTTP ' + r.status)) + (j.reasons ? '\\n\\n- ' + j.reasons.join('\\n- ') : ''));
    return null;
  }
  return j;
}
async function verdict(id, v){
  let body = {bill_id:id, verdict:v};
  if (v === 'WRONG'){
    const amt = prompt('What should this bill amount be? (rupees)'); if (amt === null) return;
    const why = prompt('Why is it wrong?'); if (why === null) return;
    body.wrong_amount = amt; body.reason = why;
  }
  if (await post(P + '/api/verdict', body)) location.reload();
}
async function finalise(m){
  if (!confirm('Finalise ' + m + '? Verdicts are then locked until the doctor reopens it.')) return;
  if (await post(P + '/api/finalise', {month:m})) location.reload();
}
async function reopen(m){
  const why = prompt('Reason for reopening ' + m + ':'); if (!why) return;
  if (await post(P + '/api/reopen', {month:m, reason:why})) location.reload();
}
async function rematch(){ if (await post(P + '/api/rematch', {})) location.reload(); }
async function orderStatus(id, s){ if (await post(P + '/api/order', {action:'status', id:id, status:s})) location.reload(); }
async function saveOrder(idx){
  const v = PLAN[idx]; if (!v) return;
  const lines = v.lines.filter(l => l.order_strips > 0).map(l => ({item:l.item, packs:l.order_strips,
      pack_size:l.pack_size, rate_p:l.rate_p, on_hand:l.on_hand, per_day:l.rate_per_day, cover_after:l.cover_after}));
  if (!lines.length){ alert('Nothing to order for this vendor.'); return; }
  if (!confirm('Save a draft order for ' + v.vendor + ' with ' + lines.length + ' line(s)?')) return;
  const j = await post(P + '/api/order', {action:'create', vendor:v.vendor, lines:lines});
  if (j) location.reload();
}
function copyText(id){
  const el = document.getElementById(id); if (!el) return;
  navigator.clipboard.writeText(el.innerText).then(()=>alert('Copied.'), ()=>alert('Select and copy by hand.'));
}
"""


def _page(title, body, extra_js=""):
    prefix = request.script_root + (bp.url_prefix or "")
    nav = ('<nav class="noprint muted"><a href="%s/page/hub">Hub</a>'
           '<a href="%s/page/scans">Scan links</a><a href="%s/page/orders">Orders</a>'
           '<a href="/finance/stock/page/drift">Stock check</a></nav>' % (prefix, prefix, prefix))
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><style>%s</style></head><body><div class="wrap">%s%s</div>'
            '<script>const P=%s;%s%s</script></body></html>'
            % (_esc(title), CSS, nav, body, json.dumps(prefix), JS, extra_js))
    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


def _feed_card(con):
    f = con.execute("SELECT * FROM purchase_feed ORDER BY id DESC LIMIT 1").fetchone()
    last = con.execute("SELECT MAX(received_at) FROM purchase_export").fetchone()[0]
    per = con.execute("SELECT type, COUNT(*), SUM(superseded_by IS NULL) FROM purchase_export "
                      "GROUP BY type").fetchall()
    held = ", ".join("%s %d live / %d held" % (r[0], r[2], r[1]) for r in per) or "nothing yet"
    if f is None:
        pull = '<span class="warn">no ping from manojz yet</span>'
    elif (f["state"] or "") == "ok":
        pull = '<span class="ok">manojz pull ok</span> (last pull %s, %s min ago at ping)' % (
            _esc(f["pull_last"]), f["pull_age_min"] if f["pull_age_min"] is not None else "?")
    else:
        pull = '<span class="bad">manojz pull asleep since %s IST</span> (state %s, pinged %s)' % (
            _hhmm_ist(f["pull_last"] or ""), _esc(f["state"]), _esc(f["at"]))
    return ('<div class="card"><h2>Feed health</h2><div>Last push received: <b>%s</b></div>'
            '<div>Exports held: %s</div><div>%s</div></div>'
            % (_esc(last or "never"), _esc(held), pull))


def _stock_card(con):
    line = ""
    if _table_exists(con, "stock_feed"):
        rows = con.execute("SELECT as_on, source, item, qty, MAX(received_at) FROM stock_feed "
                           "GROUP BY as_on, source, item").fetchall()
        by = {}
        for r in rows:
            src = (r[1] or "").lower()
            kind = "expected" if src.startswith("push_expected") else (
                "marg" if src.startswith("push_snapshot") else None)
            if kind:
                by.setdefault(r[0], {}).setdefault(r[2], {})[kind] = int(r[3] or 0)
        days = [d for d, items in by.items() if any("expected" in v and "marg" in v for v in items.values())]
        if days:
            d = max(days, key=_as_on_key)
            items = [v for v in by[d].values() if "expected" in v and "marg" in v]
            agree = sum(1 for v in items if v["expected"] == v["marg"])
            line = ("<div>Latest comparable day <b>%s</b>: %d items compared, <b>%d agree</b>, "
                    "%d differ. %d day%s of feed so far.</div>"
                    % (_esc(d), len(items), agree, len(items) - agree, len(days),
                       "" if len(days) == 1 else "s"))
    if not line:
        line = '<div class="muted">No computed-vs-Marg comparison is readable here yet.</div>'
    return ('<div class="card"><h2>Stock verification</h2>%s'
            '<div><a href="/finance/stock/page/drift">Open the stock drift page</a></div></div>' % line)


@bp.route("/page/hub")
def page_hub():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    prefix = request.script_root + (bp.url_prefix or "")
    rows = []
    for m in _months(con):
        s = _month_summary(con, m)
        st = s["status"]["status"].upper()
        rows.append('<tr><td><a href="%s/page/month/%s">%s</a></td><td class="n">%s</td>'
                    '<td class="n">%s</td><td class="n">%d</td><td class="n ok">%d</td>'
                    '<td class="n %s">%d</td><td class="n %s">%d</td><td class="n %s">%d</td>'
                    '<td><span class="chip %s">%s</span></td></tr>'
                    '<tr><td colspan="9" class="muted" style="padding-top:2px;padding-bottom:12px">%s</td></tr>'
                    % (prefix, m, _esc(_month_name(m)), _r(s["billwise_p"]), _r(s["itemwise_p"]),
                       len(s["bills"]), len(s["agree"]),
                       "bad" if s["differ_open"] else "", len(s["differ"]),
                       "warn" if s["no_lines"] else "", len(s["no_lines"]),
                       "bad" if s["wrong"] else "", s["wrong"],
                       "ok" if st == "FINAL" else "warn", st, _esc(s["story"])))
    months = ('<div class="card"><h2>Months</h2><div class="muted">Item-wise is NET (after discount), each '
              'bill\'s lines counted once. Agree = bill-wise and item-wise within &#8377;1.</div>'
              '<div class="scroll"><table><tr><th>Month</th>'
              '<th class="n">Bill-wise</th><th class="n">Item-wise (net)</th><th class="n">Bills</th>'
              '<th class="n">Agree</th><th class="n">Differ</th><th class="n">No lines</th>'
              '<th class="n">Wrong</th><th>Status</th></tr>%s</table></div>%s</div>'
              % ("".join(rows), '' if rows else '<div class="muted">No purchase bills have arrived yet.</div>'))
    sc = _scan_state(con)
    if sc is None:
        scan = ('<div class="card"><h2>Scan links</h2><div class="warn">asset app not reachable</div></div>')
    else:
        scan = ('<div class="card"><h2>Scan links</h2><div class="grid"><div class="kv"><b>%d</b>'
                '<span>pharmacy scans with no Marg bill</span></div><div class="kv"><b>%d</b>'
                '<span>Marg bills with no scan</span></div></div>'
                '<div><a href="%s/page/scans">Open the scan-link page</a></div></div>'
                % (sc["unmatched_scans"], sc["unscanned_bills"], prefix))
    n_open = con.execute("SELECT COUNT(*) FROM purchase_order WHERE status IN ('draft','sent')").fetchone()[0]
    orders = ('<div class="card"><h2>Orders</h2><div class="kv" style="max-width:240px"><b>%d</b>'
              '<span>open orders (draft or sent)</span></div>'
              '<div><a href="%s/page/orders">Make this week\'s order</a></div></div>' % (n_open, prefix))
    body = ('<h1>Marg Purchases</h1><div class="muted">Sanjeevni Medicos &middot; what Marg says was '
            'bought, checked bill by bill. Signed in as %s%s.</div>%s%s%s%s%s'
            % (_esc(_who(u)), " (doctor)" if _is_doctor(u) else (" (view only)" if _is_viewer_only(u) else ""),
               months, _feed_card(con), _stock_card(con), scan, orders))
    return _page("Marg Purchases", body)


@bp.route("/page/month/<month>")
def page_month(month):
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    s = _month_summary(con, month)
    final = s["status"]["status"] == "final"
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
    links = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link")}
    groups, cur, out = [], None, []
    for b in s["bills"]:
        if b["supplier_norm"] != cur:
            cur = b["supplier_norm"]
            groups.append((b["supplier"], []))
        groups[-1][1].append(b)
    for name, bills in groups:
        out.append('<tr><th colspan="7" style="text-transform:none;font-size:14px;color:var(--ink);'
                   'padding-top:14px">%s</th></tr>' % _esc(name))
        for b in bills:
            t = _bill_lines(b, s["sets"])
            tot, n = (t["net_p"], t["n"]) if t else (0, 0)
            lk = links.get(b["id"])
            scan = ('<a href="%s/bills/%d" target="_blank">scan %s</a>' % (_assets_url, lk[0], lk[1].lower())
                    if lk else '<span class="muted">no scan</span>')
            v = b["verdict"] or ""
            if v == "WRONG":
                vh = ('<span class="chip bad">WRONG</span> <span class="muted">should be %s: %s</span>'
                      % (_r(b["wrong_amount_p"]), _esc(b["reason"])))
            elif v == "CORRECT":
                vh = '<span class="chip ok">Correct</span>'
            else:
                vh = '<span class="muted">unverified</span>'
            btn = ""
            if not final and not viewer:
                btn = ('<span class="noprint"> <button class="sm" onclick="verdict(%d,\'CORRECT\')">Correct</button>'
                       ' <button class="sm" onclick="verdict(%d,\'WRONG\')">Wrong</button></span>' % (b["id"], b["id"]))
            gap = "" if n and abs(tot - b["amount_p"]) <= AGREE_P else (
                '<span class="warn"> no lines</span>' if not n else
                '<span class="bad"> &ne; %s</span>' % _r(tot - b["amount_p"]))
            out.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s%s</td>'
                       '<td class="n">%d</td><td>%s</td><td>%s%s</td></tr>'
                       % (_human(b["bill_date"]), _esc(b["bill_no"]), _r(b["amount_p"]), _r(tot) if n else "—",
                          gap, n, scan, vh, btn))
    buckets = []
    if s["differ"]:
        buckets.append(
            '<h2>Bills that differ from their item lines (%d)</h2><div class="muted">Bill-wise is Marg\'s '
            'bill report; item-wise is the net sum of the bill\'s lines. A purchase return shows as a negative '
            'bill with positive lines. Mark each Correct (an acknowledged return or rounding) or Wrong.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Bill-wise</th>'
            '<th class="n">Item-wise (net)</th><th class="n">Item-wise (gross)</th><th class="n">Difference</th>'
            '<th>Hint</th><th>Verdict</th></tr>%s</table></div>' % (len(s["differ"]), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n muted">%s</td>'
                '<td class="n bad">%s</td><td class="muted">%s</td><td>%s</td></tr>'
                % (_human(x["bill"]["bill_date"]), _esc(x["bill"]["bill_no"]), _esc(x["bill"]["supplier"]),
                   _r(x["bill"]["amount_p"]), _r(x["net_p"]), _r(x["gross_p"]), _r(x["diff_p"]), _esc(x["hint"]),
                   _esc(x["bill"]["verdict"] or "unverified")) for x in s["differ"])))
    if s["no_lines"]:
        buckets.append(
            '<h2>Bills with no item lines (%d)</h2><div class="note">Item-wise export missing for %s. '
            'Export item-wise for those days (or the whole month) once and these close.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Bill-wise</th>'
            '<th>Missing</th></tr>%s</table></div>' % (len(s["no_lines"]), _esc(_dates_text(s["gap_dates"])), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="muted">item-wise export missing for %s</td></tr>'
                % (_human(b["bill_date"]), _esc(b["bill_no"]), _esc(b["supplier"]), _r(b["amount_p"]),
                   _human(b["bill_date"])) for b in s["no_lines"])))
    if s["orphans"]:
        buckets.append(
            '<h2>Item lines with no bill (%d)</h2><div class="note">These lines are dated in this month but no '
            'bill-wise or supplier-wise row names their bill. Usually the bill report was exported before the '
            'bill was entered; a fresh bill-wise export closes it.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Lines</th>'
            '<th class="n">Item-wise (net)</th><th>From</th></tr>%s</table></div>' % (len(s["orphans"]), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%d</td><td class="n">%s</td><td class="muted">%s</td></tr>'
                % (_human(t["bill_date"]), _esc(t["bill_no"] or "?"), _esc(t["supplier_norm"] or "(none printed)"),
                   t["n"], _r(t["net_p"]), _esc(t["line_type"])) for t in s["orphans"])))
    und = "".join(buckets)
    if s["undated"]:
        und += ('<h2>Undated item lines</h2><div class="note">These lines came from an ITEMWISE export '
               'whose bill has not arrived in a BILLWISE or SUPPLIERWISE push, so they cannot be placed '
               'in a month. They stop the month from finalising.</div><div class="scroll"><table><tr>'
               '<th>Bill</th><th>Item</th><th class="n">Qty</th><th class="n">Net amount</th><th>From export</th></tr>%s'
               '</table></div>' % "".join(
                   '<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="muted">%s</td></tr>'
                   % (_esc(l["bill_no"] or "?"), _esc(l["item"]), l["qty"] if l["qty"] is not None else "",
                      _r(l["net_amount_p"] if l["net_amount_p"] is not None else l["amount_p"]),
                      _esc(l["file"])) for l in s["undated"]))
    diff = s["diff_p"]
    recon = ('<div class="grid"><div class="kv"><b>%s</b><span>bill-wise total (Marg)</span></div>'
             '<div class="kv"><b>%s</b><span>item-wise total (net, after discount)</span></div>'
             '<div class="kv"><b class="%s">%s</b><span>difference</span></div>'
             '<div class="kv"><b>%d</b><span>bills &middot; <span class="ok">%d agree</span> &middot; '
             '<span class="%s">%d differ</span> &middot; <span class="%s">%d without lines</span> &middot; '
             '%d line sets with no bill</span></div>'
             '<div class="kv"><b>%d</b><span>wrong &middot; %d unverified</span></div></div>'
             '<div class="muted" style="margin-top:8px">%s</div>'
             % (_r(s["billwise_p"]), _r(s["itemwise_p"]), "ok" if abs(diff) <= AGREE_P else "bad", _r(diff),
                len(s["bills"]), len(s["agree"]), "bad" if s["differ_open"] else "", len(s["differ"]),
                "warn" if s["no_lines"] else "", len(s["no_lines"]), len(s["orphans"]),
                s["wrong"], s["unverdicted"], _esc(s["story"])))
    if final:
        st = ('<div class="note"><b>FINAL</b> &mdash; finalised by %s at %s.%s</div>'
              % (_esc(s["status"]["finalised_by"]), _esc(s["status"]["finalised_at"]),
                 ' <button class="sm noprint" onclick="reopen(\'%s\')">reopen</button>' % month if doctor else ""))
    else:
        if s["can_finalise"]:
            st = ('<div class="note"><b>PROVISIONAL</b> &mdash; everything reconciles. %s</div>'
                  % ('<button class="p noprint" onclick="finalise(\'%s\')">FINALISE %s</button>' % (month, _esc(_month_name(month)))
                     if doctor else '<span class="muted">Only the doctor can finalise.</span>'))
        else:
            st = ('<div class="note"><b>PROVISIONAL</b> &mdash; cannot finalise yet:<ul>%s</ul>%s</div>'
                  % ("".join("<li>%s</li>" % _esc(r) for r in s["reasons"]),
                     '<span class="muted">The FINALISE button appears for the doctor once these are cleared.</span>'))
    body = ('<h1>%s &mdash; purchases</h1><div class="muted">One row per Marg bill. Item-wise is the NET '
            '(after discount) sum of that bill\'s lines, from the latest export that carries the bill.</div><div class="card">%s%s</div><div class="card"><div class="scroll">'
            '<table><tr><th>Date</th><th>Bill</th><th class="n">Amount</th><th class="n">Item-wise (net)</th>'
            '<th class="n">Lines</th><th>Scan</th><th>Verdict</th></tr>%s</table></div>%s</div>'
            % (_esc(_month_name(month)), recon, st, "".join(out) or
               '<tr><td colspan="7" class="muted">No bills for this month.</td></tr>', und))
    return _page("%s purchases" % _month_name(month), body)


@bp.route("/page/scans")
def page_scans():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    prefix = request.script_root + (bp.url_prefix or "")
    acon = _assets_con()
    if acon is None:
        return _page("Scan links", '<h1>Scan links</h1><div class="card"><div class="warn">asset app not '
                     'reachable</div><div class="muted">The pharmacy scans live in the asset app\'s '
                     'database. It is not readable from here right now; nothing else on these pages '
                     'depends on it.</div></div>')
    scans = _scans(acon)
    acon.close()
    linked = {r[0]: r[1] for r in con.execute("SELECT asset_bill_id, bill_id FROM purchase_scan_link")}
    linked_bills = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link")}
    bills = con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL +
                        " ORDER BY b.bill_date DESC, b.supplier").fetchall()
    un_s = [s for s in scans if s["id"] not in linked]
    un_b = [b for b in bills if b["id"] not in linked_bills]
    btn = ('<button class="p noprint" onclick="rematch()">Re-match now</button>'
           if not _is_viewer_only(u) else "")
    t1 = "".join('<tr><td><a href="%s/bills/%d" target="_blank">#%d</a></td><td>%s</td><td>%s</td>'
                 '<td>%s</td><td class="n">%s</td><td class="muted">%s / %s</td></tr>'
                 % (_assets_url, s["id"], s["id"], _esc(s["vendor"]), _esc(s["bill_no"]),
                    _human(s["bill_date"]) if s["bill_date"] else "—", _r(s["amount_p"]),
                    _esc(s["status"]), _esc(s["ocr_status"])) for s in un_s)
    t2 = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td><a href="%s/page/month/%s">%s</a></td></tr>'
                 % (_human(b["bill_date"]), _esc(b["supplier"]), _esc(b["bill_no"]), _r(b["amount_p"]),
                    prefix, b["month"], _esc(_month_name(b["month"] or ""))) for b in un_b)
    body = ('<h1>Scan links</h1><div class="muted">Pharmacy scans in the asset app, paired with Marg\'s '
            'bills. EXACT = vendor, bill number and amount all agree; PROBABLE = bill number and amount, '
            'or vendor, date and amount.</div><div class="card"><div class="row spread"><div>'
            '<b>%d</b> links stored &middot; <b>%d</b> scans with no Marg bill &middot; <b>%d</b> Marg '
            'bills with no scan</div>%s</div></div>'
            '<div class="card"><h2>Scans with no Marg bill (%d)</h2><div class="scroll"><table><tr><th>Scan</th>'
            '<th>Vendor</th><th>Bill no</th><th>Date</th><th class="n">Amount</th><th>Status / OCR</th></tr>%s</table></div></div>'
            '<div class="card"><h2>Marg bills with no scan (%d)</h2><div class="scroll"><table><tr><th>Date</th>'
            '<th>Supplier</th><th>Bill no</th><th class="n">Amount</th><th>Month</th></tr>%s</table></div></div>'
            % (len(linked_bills), len(un_s), len(un_b), btn, len(un_s),
               t1 or '<tr><td colspan="6" class="muted">none</td></tr>', len(un_b),
               t2 or '<tr><td colspan="5" class="muted">none</td></tr>'))
    return _page("Scan links", body)


@bp.route("/page/orders")
def page_orders():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
    plan = reorder_plan(con)
    label = ('<div class="note"><b>PROVISIONAL until the stock verification has run a month</b> '
             '&mdash; %d day%s of stock feed so far (needs %d). Treat every quantity as a proposal.</div>'
             % (plan["feed_days"], "" if plan["feed_days"] == 1 else "s", FEED_DAYS_FOR_TRUST)
             if plan["provisional"] else "")
    vend_html, plan_json = [], []
    for i, v in enumerate(plan["vendors"]):
        phone = "" if viewer else _phone_for(con, v["vendor"])
        tel = (' &middot; <a href="tel:%s">call %s</a>' % (_esc(phone), _esc(phone))) if phone else ""
        lines = "".join(
            '<tr><td>%s%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%.1f</td><td class="n">%s</td><td class="muted">%s%s</td></tr>'
            % (_esc(l["item"]), ' <span class="chip warn">confirm</span>' if l["confirm"] else "",
               l["on_hand"], l["order_strips"], _esc(l["pack_size"]), _r(l["rate_p"]),
               l["rate_per_day"], l["cover_after"] if l["cover_after"] is not None else "—",
               l["confidence"], ("; " + "; ".join(l["why"])) if l["why"] else "")
            for l in v["lines"])
        copy = "ORDER — %s\n%s\n%s\nTotal approx %s" % (
            v["vendor"], plan["today"],
            "\n".join("%s × %d (%s)" % (l["item"], l["order_strips"], l["pack_size"])
                      for l in v["lines"] if l["order_strips"] > 0), _r(v["total_p"]))
        vend_html.append(
            '<div class="card"><div class="row spread"><h3 style="margin:0">%s%s</h3><div class="noprint">%s%s</div></div>'
            '<div class="muted">cadence %s days &middot; approx %s</div><div class="scroll"><table><tr><th>Item</th>'
            '<th class="n">On hand</th><th class="n">Packs</th><th class="n">Pack</th><th class="n">Rate</th>'
            '<th class="n">Per day</th><th class="n">Cover after</th><th>Why</th></tr>%s</table></div>%s</div>'
            % (_esc(v["vendor"]), tel,
               ('<button class="sm" onclick="copyText(\'copy%d\')">Copy this order</button> ' % i) if not viewer else "",
               ('<button class="sm p" onclick="saveOrder(%d)">Save as order</button>' % i) if doctor else "",
               v["cadence_days"] or "—", _r(v["total_p"]), lines,
               ('<div class="copy" id="copy%d">%s</div>' % (i, _esc(copy))) if not viewer else ""))
        plan_json.append(dict(vendor=v["vendor"], lines=[
            dict(item=l["item"], order_strips=l["order_strips"], pack_size=l["pack_size"], rate_p=l["rate_p"],
                 on_hand=l["on_hand"], rate_per_day=l["rate_per_day"], cover_after=l["cover_after"])
            for l in v["lines"]]))
    book = []
    for o in _orders(con):
        phone = "" if viewer else _phone_for(con, o["vendor"])
        tel = (' &middot; <a href="tel:%s">call</a>' % _esc(phone)) if phone else ""
        moves = ""
        if doctor and o["status"] in ("draft", "sent"):
            nxt = [("sent", "mark sent"), ("received", "mark received"), ("cancelled", "cancel")]
            moves = " ".join('<button class="sm noprint" onclick="orderStatus(%d,\'%s\')">%s</button>' % (o["id"], s, lab)
                             for s, lab in nxt if s != o["status"])
        book.append('<tr><td>#%d</td><td>%s</td><td>%s%s</td><td class="n">%d</td><td class="n">%s</td>'
                    '<td><span class="chip">%s</span> %s</td></tr>'
                    % (o["id"], _esc(o["created_at"][:10]), _esc(o["vendor"]), tel, len(o["lines"]),
                       _r(o["total_p"]), _esc(o["status"]), moves))
    body = ('<h1>Orders</h1><div class="muted">The reorder plan is the S207 engine on the newest stock '
            'snapshot (%s), the last %d days of sale lines (%d items paced) and the last purchase rate. '
            'Nothing here sends anything: a person calls the vendor.</div>%s'
            '<div class="card"><h2>Order book</h2><div class="scroll"><table><tr><th>#</th><th>Made</th><th>Vendor</th>'
            '<th class="n">Lines</th><th class="n">Approx</th><th>Status</th></tr>%s</table></div></div>'
            '<h2>Reorder plan &mdash; %s</h2>%s'
            % (_esc(plan["as_on"] or "no snapshot yet"), plan["pace_days"], plan["items_paced"], label,
               "".join(book) or '<tr><td colspan="6" class="muted">no orders yet</td></tr>', _esc(plan["today"]),
               "".join(vend_html) or '<div class="card muted">Nothing to order on the current numbers.</div>'))
    return _page("Orders", body, "const PLAN=%s;" % json.dumps(plan_json))
