#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
purchase_app.py -- S224: Marg's purchases, on the box.  (rev 12, S225, 05-Sep-2026)

REV 12 (S225, 05-Sep, the owner: "full bank details that display correctly in page, and a bank detail
    addition/modification opens an inline form and not a popup") -- the phone book shows the FULL account
    number and IFSC to its three editors (it is the NEFT file's source; last-4 stays for audit rows and every
    other screen), names the bank from the IFSC, labels rows that came from the NEFT records, and every
    add / edit numbers / edit bank / verify is an INLINE form in the row -- no prompt(), confirm() or
    alert() anywhere on the book page. The API and its rules (D370) are untouched.

REV 11 (S225) -- AMIR'S SALT WORK LIST, SERVER-SIDE (spec §6: "Amir's salt correction list should be
    available as Excel download with him and me, and A4 print also"). The owner's answers of 28-Aug
    (S207) already made the list: rename 2 · create 38 · change 77 · 7 waiting on him · 1 cleanup.
    push_salts.py (manojz) sends D:\Downloads\Sanjeevni_Salt_Fix_for_Amir.xlsx once; /page/salts is
    where Amir ticks each row DONE (his name, the time) and the doctor answers the 7 waiting rows;
    a later push never un-ticks or overwrites. Excel and A4 come from the record (/salts.xlsx, .pdf).
    11b (19:30): a fresh Marg SALT WISE ITEM LIST is pushed too (purchase_salt_marg) and every task shows
    what MARG SAYS -- done / not yet / the item's current salt -- beside Amir's tick; a note line that
    the rename sheet carried is not a task and is dropped.

REV 10 (S225) -- NEW ITEMS, RECORDED AND HIGHLIGHTED (spec §6: "new medicines added should be recorded
    and highlighted to me"). An item first seen this month in a purchase line, or in the newest stock
    snapshot without ever having been in an earlier one, is logged once (purchase_new_item: first seen,
    where, stockist, packing) and the hub shows the month's count with the list. Items in the earliest
    snapshot on the server are the baseline and never 'new'.

REV 9 (S225) -- THE CROSS-CHECK IS LIVE (spec §6; the owner: "Sarvam -- live, not nightly").
    The scan-vs-bill match runs when a push stores bills or lines, and whenever the scans have
    changed since the last match (checked on every opening of the hub and the scan-links page).
    Quantities RECEIVED on an order but not yet in Marg count as stock in transit for the engine.

REV 8 (S225) -- WHEN THE GOODS ARRIVE (spec §4). On a SENT order the staff page offers Arrived
    (one tap: every line supplied as ordered) or Different (supplied quantity per line, Short where
    the stockist could not supply); the order becomes RECEIVED by that person at that minute,
    audited. A short-supplied line rides into the next reorder plan automatically until it is
    re-ordered from that stockist (45 days). A RECEIVED order shows the Scan-the-bill button with
    the note to type. Columns added on first request (supplied, short, received_at/by, sent_by).

REV 7 (S225) -- THE STOCKIST PHONE BOOK (spec S224_PURCHASE_ORDER_STAFF_FLOW_SPEC §3, the owner's
    rulings of 04-Sep). /page/book for the doctor and the logins named in setting
    purchase.phonebook_users (fail-closed); two phones per stockist; five bank fields server-side
    only; bank fields saved by anyone but the doctor are UNVERIFIED until he taps Verify, his own
    are VERIFIED by the act; the nightly manojz push never overwrites a number edited here
    (source='server' wins); every change audited by field name and last-4. The staff page
    rings either number. Existing bank details are accepted as they stand (owner, S225).

REV 6 (S225) -- THE STAFF ORDER PAGE, as the owner dictated it on 04-Sep 11:45 IST.
    /page/staff shows, per stockist, three columns only: Item / Stock now / Order qty in
    the item's own unit, strips rounded UP to 10 then multiples of 10. ONE tap writes the
    order as SENT (who, when, audited) and opens WhatsApp with exactly the header line
    "Sanjeevni Medicos, G 15 Rampur Garden, Bareilly", a blank line, then "Item - qty unit"
    per line -- nothing else. A Call button (tel:). An A4 PDF per order (/order/<id>/pdf,
    clinic_day_pdf's writer) with no rates, for the reception printer. Any signed-in person
    of the medical unit may send; the phone number is never printed on the page. The
    doctor's Orders page is unchanged and keeps every rate, value and reason.

REV 4 -- the owner's ruling on returns (04-Sep 10:40 IST): "the supplier-wise report is
    FINAL for month-end work; Marg reports purchase returns like this only -- we learn
    and adjust; avoid confusing lines on the page."
    * The month's figure is the SUPPLIER-WISE total. Bill-wise is identical by
      construction; it stands in only while supplier-wise has not been exported, and
      the page says so quietly. Each bill remembers both amounts (bw_amount_p,
      sw_amount_p -- two columns added to purchase_bill on first request, back-filled
      from amount_p; the schema file is untouched).
    * A bill whose item-wise net EXCEEDS its amount is a PURCHASE RETURN as Marg
      reports it: labelled "purchase return Rs d (Marg)", counted in Returns, never
      asked Correct/Wrong, never blocks FINALISE.
    * Correct / Wrong remain only where item-wise net is BELOW the bill by more than
      Rs 1 (item lines missing -- check the bill) or where bill-wise and supplier-wise
      disagree on a bill.
    * FINALISE is refused only for (a) an unresolved WRONG, (b) a bill with no item
      lines, (c) bill-wise vs supplier-wise disagreeing by more than Rs 1 for the
      month. The one-line story never asks the reader to mark anything.

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
_url_prefix = "/finance/purchase"   # rev 3: bp.url_prefix is None when the prefix is given at register time (F-292 family)
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
    global _db, _require, _unit, _marg_token, _assets_db, _assets_url, _url_prefix
    _url_prefix = url_prefix or ""
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
    # rev 4: each bill keeps BOTH reports' amounts. Added here, never in the schema file,
    # so the one-file install stays one file; back-filled from amount_p once.
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_bill)")}
    for col, src in (("bw_amount_p", "bw_md5"), ("sw_amount_p", "sw_md5")):
        if col not in have:
            con.execute("ALTER TABLE purchase_bill ADD COLUMN %s INTEGER" % col)
        con.execute("UPDATE purchase_bill SET %s=amount_p WHERE %s IS NULL AND %s IS NOT NULL"
                    % (col, col, src))
    con.commit()
    # rev 7: the phone-book columns (phone2, the bank fields, source) are read by the staff page
    # and the vendor push as well as the book -- so they are added HERE, on the first request of
    # any kind, not only when the book is opened. (The S225 walk on the box caught exactly that.)
    _ensure_book(con)
    _ensure_arrival(con)
    _ensure_new_items(con)
    _ensure_salts(con)
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
    # rev 4: an export supersedes every live export of its type whose period it CONTAINS and
    # whose stamp is older (01-31 Aug exported on 04-Sep retires 01-29 Aug exported on 30-Aug --
    # otherwise a bill Marg re-keyed in between lives on through the partial export and inflates
    # the month). The same period counts as contained. An incoming export is itself superseded
    # when a live newer export already contains its period.
    rivals = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type=? AND period_from>=? "
        "AND period_to<=? AND superseded_by IS NULL AND export_stamp<?", (typ, pf, pt, stamp)).fetchall()
    newer = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type=? AND period_from<=? "
        "AND period_to>=? AND superseded_by IS NULL AND export_stamp>?", (typ, pf, pt, stamp)).fetchall()
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
    _rematch_after_push(con)                                   # S225 rev 9: live, not nightly
    return jsonify(ok=True, stored=True, reason="new", rows=n)


class _Malformed(Exception):
    pass


def _store_bills(con, typ, md5, rows):
    """BILLWISE / SUPPLIERWISE rows -> purchase_bill. Identity (supplier_key, bill_no);
    the date from BILLWISE first, SUPPLIERWISE second; verdicts survive re-pushes."""
    col = "bw_md5" if typ == "BILLWISE" else "sw_md5"
    amt = "bw_amount_p" if typ == "BILLWISE" else "sw_amount_p"
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
                        "month,cash_p,credit_p,amount_p,source_md5,%s,%s,date_src) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)" % (col, amt),
                        (key, sup, bno, d, d[:7], cash, credit, cash + credit, md5, md5,
                         cash + credit, typ))
        else:
            # keep the longer printed name (the one carrying the city), and the BILLWISE date
            name = target[3] if len(target[3] or "") >= len(sup) else sup
            newdate = d if (typ == "BILLWISE" or target[2] != "BILLWISE") else target[1]
            src = "BILLWISE" if (typ == "BILLWISE" or target[2] == "BILLWISE") else typ
            con.execute("UPDATE purchase_bill SET supplier=?, bill_date=?, month=?, cash_p=?, "
                        "credit_p=?, amount_p=?, source_md5=?, %s=?, %s=?, date_src=? WHERE id=?"
                        % (col, amt),
                        (name, newdate, newdate[:7], cash, credit, cash + credit, md5, md5,
                         cash + credit, src, target[0]))
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
    _ensure_book(con)
    n = 0
    for name, phone in pairs.items():
        name = str(name or "").strip()
        if not name:
            continue
        # rev 7: a number edited in the phone book (source='server') is never overwritten by the push.
        con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at, source) "
                    "VALUES (?,?,?,?,'manojz') ON CONFLICT(vendor_norm) DO UPDATE SET vendor=excluded.vendor, "
                    "phone=CASE WHEN purchase_vendor_contact.source='server' THEN purchase_vendor_contact.phone "
                    "ELSE excluded.phone END, updated_at=excluded.updated_at",
                    (supplier_key(name), name, str(phone or "").strip(), now_iso()))
        n += 1
    _audit(con, "push_purchases", "vendors", "", dict(n=n))
    con.commit()
    extra = {}
    if isinstance(b.get("salt_tasks"), list) and b.get("salt_tasks"):      # S225 rev 11: the salt work list rides this door
        _ensure_salts(con)
        sn, sk = _store_salts(con, dict(tasks=b["salt_tasks"], salts=b.get("salts"), source_md5=b.get("source_md5")))
        extra = dict(salts_stored=sn, salt_kept=sk)
    if isinstance(b.get("marg_items"), list) and b.get("marg_items"):      # 11b: Marg's own salt list rides it too
        _ensure_salts(con)
        extra["marg_items"] = _store_marg_salts(con, b)
    return jsonify(ok=True, stored=n, **extra)


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


AGREE_P = 100          # a bill AGREES with its lines when |Marg amount - item-wise net| <= Rs 1


def _bills_for_month(con, month):
    """The month's effective bills, as dicts, each carrying the rev-4 money view:
    bw_p (bill-wise, while that export is live), sw_p (supplier-wise, while live),
    marg_p (the figure the month closes on: supplier-wise, else bill-wise), basis, and
    disagree_p (supplier-wise minus bill-wise when both are live and differ by more
    than Rs 1, else 0)."""
    out = []
    for r in con.execute(
            "SELECT b.*, EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
            "AND e.md5=b.bw_md5) bw_live, EXISTS (SELECT 1 FROM purchase_export e WHERE "
            "e.superseded_by IS NULL AND e.md5=b.sw_md5) sw_live FROM purchase_bill b WHERE "
            "b.month=? AND " + EFF_BILL + " ORDER BY b.supplier, b.bill_date, b.bill_no", (month,)):
        b = dict(r)
        bw = (b["bw_amount_p"] if b["bw_amount_p"] is not None else b["amount_p"]) if b["bw_live"] else None
        sw = (b["sw_amount_p"] if b["sw_amount_p"] is not None else b["amount_p"]) if b["sw_live"] else None
        b["bw_p"], b["sw_p"] = bw, sw
        b["marg_p"] = sw if sw is not None else (bw if bw is not None else b["amount_p"])
        b["basis"] = "supplier-wise" if sw is not None else "bill-wise"
        b["disagree_p"] = (sw - bw) if (sw is not None and bw is not None and abs(sw - bw) > AGREE_P) else 0
        out.append(b)
    return out


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


def _bill_lines(bill, sets, stray=None):
    """The bill's line set, or None. A set with no supplier (a BILLITEMWISE bill whose
    bill-wise row has not yet named it) still counts when bill_no and date agree; so does
    a STRAY set (rev 4) -- one keyed to a supplier that names no live bill of the month,
    i.e. the old key of a bill Marg moved to its corrected supplier -- when it is the
    only stray with that bill number and date."""
    t = sets.get((bill["supplier_norm"], bill["bill_no"]))
    if t is None:
        t = sets.get((None, bill["bill_no"]))
        if t is not None and t["bill_date"] != bill["bill_date"]:
            t = None
    if t is None and stray:
        t = stray.get((bill["bill_no"], bill["bill_date"]))
    return t


def _stray_sets(bills, sets):
    """(bill_no, bill_date) -> the one line set whose supplier key names no live bill of
    the month; None where two strays share a number and date (ambiguous: left alone)."""
    live = {(b["supplier_norm"], b["bill_no"]) for b in bills}
    out = {}
    for k, t in sets.items():
        if k[0] is None or k in live:
            continue
        key = (t["bill_no"], t["bill_date"])
        out[key] = None if key in out else t
    return {k: t for k, t in out.items() if t is not None}


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
        return "%s %s" % (days, _human(ds[0])[3:6])
    return "%s\u2013%s %s (%d days)" % (_human(ds[0])[:2].lstrip("0"), _human(ds[-1])[:2].lstrip("0"),
                                      _human(ds[-1])[3:6], len(ds))


def _bill_short(b):
    return "%s (%s, %s)" % (b["bill_no"], _human(b["bill_date"])[:6], b["supplier_norm"] or "?")


def _name_some(items, fmt, limit=6):
    out = [fmt(x) for x in items[:limit]]
    if len(items) > limit:
        out.append("and %d more" % (len(items) - limit))
    return ", ".join(out)


def _month_summary(con, month):
    """Per-bill reconciliation on the owner's rev-4 ruling. The month's figure is the
    SUPPLIER-WISE total (bill-wise is identical by construction and stands in only while
    supplier-wise has not been exported). Item lines are the check, not the figure.
    Buckets: AGREES (|item-wise net - Marg| <= Rs 1) · PURCHASE RETURN (item-wise net
    ABOVE the bill by more than Rs 1 -- how Marg reports a return; nothing to mark,
    never blocks) · SHORT (item-wise net BELOW the bill by more than Rs 1 -- item lines
    missing; Correct/Wrong offered) · NO ITEM LINES · ITEM LINES WITH NO BILL. A bill on
    which bill-wise and supplier-wise disagree is offered a verdict too, and a month on
    which the two reports disagree by more than Rs 1 cannot close."""
    bills = _bills_for_month(con, month)
    sets = _line_sets(con, month)
    stray = _stray_sets(bills, sets)
    marg = sum(b["marg_p"] for b in bills)
    sw_p = sum(b["sw_p"] for b in bills if b["sw_p"] is not None)
    bw_p = sum(b["bw_p"] for b in bills if b["bw_p"] is not None)
    n_sw = sum(1 for b in bills if b["sw_p"] is not None)
    if not bills or n_sw == len(bills):
        basis, basis_note = "supplier-wise", ""
    elif n_sw == 0:
        basis, basis_note = "bill-wise", "supplier-wise not exported yet for this month \u2014 bill-wise stands in"
    else:
        basis, basis_note = "supplier-wise", "%s so far only in bill-wise" % _plural(len(bills) - n_sw, "bill")
    month_disagree_p = sum(b["sw_p"] - b["bw_p"] for b in bills
                           if b["sw_p"] is not None and b["bw_p"] is not None)
    agree, returns, short, no_lines, used = [], [], [], [], set()
    iw = 0
    for b in bills:
        t = _bill_lines(b, sets, stray)
        if t is None:
            no_lines.append(b)
            continue
        used.add((t["supplier_norm"], t["bill_no"]))
        iw += t["net_p"]
        d = t["net_p"] - b["marg_p"]
        x = dict(bill=b, net_p=t["net_p"], gross_p=t["gross_p"], n=t["n"], diff_p=d)
        if d > AGREE_P:
            returns.append(x)
        elif d < -AGREE_P:
            short.append(x)
        else:
            agree.append(b)
    # a line set nobody uses is an orphan -- unless a bill with the same number and date
    # already took a set from the same or a later export: then it is the OLD key of a bill
    # Marg re-keyed (moved to its corrected supplier) and is stale, not missing.
    taken = {}
    for k in used:
        t = sets[k]
        taken[(t["bill_no"], t["bill_date"])] = max(taken.get((t["bill_no"], t["bill_date"]), ""), t["stamp"])
    orphans = [t for k, t in sets.items() if k not in used
               and taken.get((t["bill_no"], t["bill_date"]), "") < t["stamp"]]
    orphan_p = sum(t["net_p"] for t in orphans)
    disagree = [b for b in bills if b["disagree_p"]]
    needs_verdict = {x["bill"]["id"] for x in short} | {b["id"] for b in disagree}
    wrong = [b for b in bills if b["verdict"] == "WRONG"]
    short_open = [x for x in short if not x["bill"]["verdict"]]
    disagree_open = [b for b in disagree if not b["verdict"]]
    gap_dates = sorted(set(b["bill_date"] for b in no_lines))
    undated = _undated_lines(con, month)
    st = _month_status(con, month)
    reasons = []
    if wrong:
        reasons.append("%s marked Wrong and not yet resolved: %s"
                       % (_plural(len(wrong), "bill"), _name_some(wrong, _bill_short)))
    if no_lines:
        reasons.append("%s no item lines yet (item-wise export missing for %s): %s"
                       % (_plural(len(no_lines), "bill has", "bills have"), _dates_text(gap_dates),
                          _name_some(no_lines, _bill_short)))
    if abs(month_disagree_p) > AGREE_P:
        reasons.append("bill-wise and supplier-wise disagree by %s for this month: %s"
                       % (_r(abs(month_disagree_p)),
                          _name_some(disagree, lambda b: "%s (bill-wise %s, supplier-wise %s)"
                                     % (_bill_short(b), _r(b["bw_p"]), _r(b["sw_p"])))))
    if not bills:
        reasons.append("no bills have been pushed for this month")
    can = not reasons
    # the one calm line for the hub and the month page
    mn = _month_name(month)
    short_mn = mn.split(" ")[0]
    head = "%s: %s (%s%s)" % (short_mn, _r(marg), basis,
                              ", final for month-end" if basis == "supplier-wise" and bills else "")
    if st["status"] == "final":
        story = "%s. FINAL \u2014 %s, %s IST." % (head, st["finalised_by"], _when_ist(st["finalised_at"]))
    elif not bills:
        story = "%s: no bills yet%s." % (short_mn, ("; %s waiting, undated" % _plural(len(undated), "item line"))
                                         if undated else "")
    else:
        bits = [_plural(len(bills), "bill")]
        if returns:
            bits.append("%d %s a purchase return" % (len(returns), "carries" if len(returns) == 1 else "carry"))
        if no_lines:
            bits.append("%s no item lines yet (%s) \u2014 export item-wise for %s"
                        % (_plural(len(no_lines), "bill has", "bills have"), _dates_text(gap_dates),
                           "that date" if len(gap_dates) == 1 else "those dates"))
        if short_open:
            bits.append("%s item lines short of the bill \u2014 check the bill"
                        % _plural(len(short_open), "bill has", "bills have"))
        if disagree_open:
            bits.append("bill-wise and supplier-wise disagree on %s" % _plural(len(disagree_open), "bill"))
        if abs(month_disagree_p) > AGREE_P:
            bits.append("the two reports disagree by %s for the month" % _r(abs(month_disagree_p)))
        if wrong:
            bits.append("%s marked Wrong" % _plural(len(wrong), "bill"))
        if undated:
            bits.append("%s undated" % _plural(len(undated), "item line"))
        if orphans:
            bits.append("%s a bill not in the reports" % _plural(len(orphans), "item line set names", "item line sets name"))
        if basis_note:
            bits.append(basis_note)
        if can:
            bits.append("ready to finalise")
        story = "%s. %s." % (head, "; ".join(bits))
    return dict(month=month, bills=bills, sets=sets, stray=stray, marg_p=marg, billwise_p=marg, bw_p=bw_p, sw_p=sw_p,
                basis=basis, basis_note=basis_note, month_disagree_p=month_disagree_p,
                itemwise_p=iw + orphan_p, itemwise_bills_p=iw, orphan_p=orphan_p, diff_p=marg - (iw + orphan_p),
                agree=agree, returns=returns, short=short, short_open=short_open, disagree=disagree,
                disagree_open=disagree_open, needs_verdict=needs_verdict, no_lines=no_lines,
                orphans=orphans, gap_dates=gap_dates, wrong=len(wrong),
                to_check=len(short_open) + len(disagree_open), undated=undated, status=st,
                can_finalise=can, reasons=reasons, story=story, head=head)


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _when_ist(iso):
    """A stored timestamp -> '04-Sep-2026 10:52' in IST. now_iso() is naive server-local
    time; astimezone() reads it as such and converts, so the label is right whatever
    zone the box runs in."""
    try:
        return dt.datetime.fromisoformat(iso).astimezone(IST).strftime("%d-%b-%Y %H:%M")
    except (TypeError, ValueError, OverflowError):
        return iso or "?"


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
    transit = _in_transit(con, today)                          # S225 rev 9
    vendors = {}
    considered = 0
    for k, s in snap.items():
        p = pace.get(k)
        if not p:
            continue
        lp = purch.get(k) or {}
        tr = transit.get(k)
        vendor = lp.get("vendor")
        cost_pack = lp.get("rate_p")
        cost_unit = (cost_pack / float(s["pack_size"])) if cost_pack else 0
        if not cost_unit and _table_exists(con, "stock_rate"):
            r = con.execute("SELECT rate_p FROM stock_rate WHERE item=?", (s["item"],)).fetchone()
            cost_unit = r[0] if r else 0
        it = dict(item=s["item"], vendor=lp.get("vendor_disp") or "(no supplier on record)",
                  on_hand=s["qty"] + (tr["units"] if tr else 0), rate_per_day=p["rate_per_day"], sell_days=p["sell_days"],
                  peak_share=p["peak_share"], days_since_sale=p.get("days_since_sale", 0),
                  pack_size=s["pack_size"], cost_p=cost_unit,
                  single_source=len(lp.get("suppliers") or ()) <= 1, box=lp.get("box") or 0)
        considered += 1
        line = plan_line(it, cad.get(vendor, CADENCE_DAYS["fortnightly"]))
        if tr:
            line["why"].append("%d units received on order #%d, not yet in Marg — counted as stock" % (tr["units"], tr["order_id"]))
        if line["order_strips"] <= 0 and not line["confirm"]:
            continue
        # S225 rev 7 -- the owner's rule applied ONCE, here, so the doctor's page, the staff page,
        # the copy text and the WhatsApp all carry the same quantity: strips round UP to 10, then
        # to multiples of 10 (bottles, tubes and units keep the engine's box quantity).
        line["unit"] = _unit_word(s.get("packing"), s["pack_size"])
        if line["order_strips"] > 0:
            rounded = _staff_qty(line["order_strips"], line["unit"])
            if rounded != line["order_strips"]:
                line["why"].append("rounded to %d %ss (the owner's rule: 10, then tens)" % (rounded, line["unit"]))
                line["order_strips"] = rounded
                line["order_units"] = rounded * line["pack_size"]
                line["value_p"] = int(rounded * line["pack_size"] * (it["cost_p"] or 0))
        line["rate_p"] = int(round(cost_unit * s["pack_size"]))
        line["cover_after"] = (round((s["qty"] + line["order_units"]) / p["rate_per_day"], 1)
                               if p["rate_per_day"] > 0 else None)
        line["vendor_norm"] = vendor or ""
        v = vendors.setdefault(line["vendor"], dict(vendor=line["vendor"], vendor_norm=vendor or "",
                                                     lines=[], total_p=0,
                                                     cadence_days=cad.get(vendor)))
        v["lines"].append(line)
        v["total_p"] += line["value_p"]
    # S225 rev 8: short-supplied lines ride into the next plan (the owner: "carries into the next order")
    for k, sh in _carried_shorts(con, today).items():
        v = vendors.setdefault(sh["vendor"], dict(vendor=sh["vendor"], vendor_norm=sh["vendor_norm"], lines=[], total_p=0,
                                                   cadence_days=cad.get(sh["vendor_norm"])))
        hit = next((l for l in v["lines"] if norm(l["item"]) == k), None)
        s = snap.get(k) or {}
        unit = _unit_word(s.get("packing"), s.get("pack_size", 1))
        if hit:
            add = _staff_qty(hit["order_strips"] + sh["shortfall"], unit)
            hit["why"].append("plus %d short-supplied on order #%d (%s) — carried" % (sh["shortfall"], sh["order_id"], sh["since"]))
            v["total_p"] += int((add - hit["order_strips"]) * hit["rate_p"])
            hit["order_strips"], hit["order_units"] = add, add * hit["pack_size"]
            hit["value_p"] = int(add * hit["rate_p"])
        else:
            qty = _staff_qty(sh["shortfall"], unit)
            size = int(s.get("pack_size") or 1)
            lp = purch.get(k) or {}
            rate_p = int(lp.get("rate_p") or 0)
            v["lines"].append(dict(item=sh["item"], vendor=sh["vendor"], vendor_norm=sh["vendor_norm"], on_hand=int(s.get("qty") or 0),
                                   rate_per_day=0.0, sell_days=0, confidence="carried", cover_days=0, pack_size=size, box=0,
                                   order_strips=qty, order_units=qty * size, value_p=int(qty * rate_p), confirm=False,
                                   single_source=True, days_since_sale=0, peak_share=0.0, unit=unit, rate_p=rate_p, cover_after=None,
                                   why=["short-supplied on order #%d (%s) — carried into this order" % (sh["order_id"], sh["since"])]))
            v["total_p"] += int(qty * rate_p)
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
    b = request.get_json(silent=True) or {}
    action = str(b.get("action") or "")
    con = _db()
    _ensure(con)
    if action == "staff_send":                       # S225: any person of the unit may send
        return _staff_send(con, u, b)
    if action in ("arrive", "arrive_diff"):          # S225 rev 8: any person of the unit may receive
        return _arrive(con, u, b)
    if not _is_doctor(u):
        return _refuse("Only the doctor can create or move an order.")
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


def _uw(l):
    """The unit word for a plan line, plural when it should be (rev 7)."""
    u = l.get("unit") or "unit"
    return u if l.get("order_strips") == 1 else u + "s"


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
    """paise -> '₹3,54,879' (whole rupees, Indian grouping -- the way the owner reads a
    figure; the reports print whole rupees)."""
    if p is None:
        return "—"
    neg = p < 0
    v = str(int(round(abs(p) / 100.0)))
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return ("−" if neg else "") + "₹" + v


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


def _book_nav(prefix):
    """The phone-book link, only for those who may open it (rev 7). Never raises."""
    try:
        u, err = _require("checker", "maker", "viewer")
        if err or not u:
            return ""
        con = _db()
        _ensure(con)
        _ensure_book(con)
        out = ('<a href="%s/page/book">Phone book</a>' % prefix) if _book_allowed(u, con) else ""
        if _salt_allowed(u, con):
            out += '<a href="%s/page/salts">Salt list</a>' % prefix
        return out
    except Exception:
        return ""


def _page(title, body, extra_js=""):
    prefix = request.script_root + _url_prefix
    nav = ('<nav class="noprint muted"><a href="%s/page/hub">Hub</a>'
           '<a href="%s/page/scans">Scan links</a><a href="%s/page/orders">Orders</a>'
           '<a href="%s/page/staff">Order medicines</a>%s'
           '<a href="/finance/stock/page/drift">Stock check</a></nav>'
           % (prefix, prefix, prefix, prefix, _book_nav(prefix)))
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><style>%s</style></head><body><div class="wrap">%s%s</div>'
            '<script>const P=%s;%s%s</script></body></html>'
            % (_esc(title), CSS, nav, body, json.dumps(prefix), JS, extra_js))
    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


def _hhmm_ist_full(ts):
    """'2026-09-04T09:21:05' or '...+05:30' -> '04-Sep 09:21' (stored times are IST)."""
    try:
        d = ts[:10]; t = ts[11:16]
        y, m, dd = d.split("-")
        mon = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[int(m) - 1]
        return "%s-%s %s" % (dd, mon, t)
    except (ValueError, TypeError, IndexError):
        return ts or "?"


def _feed_card(con):
    """Rev 5 (the owner: "and such lines also"): plain English, no per-type counts.
    Three lines a person can read in one glance: when Marg's purchase data last
    reached here, which months are on file, and whether manojz is awake."""
    f = con.execute("SELECT * FROM purchase_feed ORDER BY id DESC LIMIT 1").fetchone()
    last = con.execute("SELECT MAX(received_at) FROM purchase_export").fetchone()[0]
    n_live = con.execute("SELECT COUNT(*) FROM purchase_export WHERE superseded_by IS NULL").fetchone()[0]
    span = con.execute("SELECT MIN(period_from), MAX(period_to) FROM purchase_export "
                       "WHERE superseded_by IS NULL").fetchone()
    if n_live and span[0]:
        months = "%s to %s (%d exports on file)" % (_month_name(span[0]), _month_name(span[1]), n_live)
    else:
        months = "nothing yet"
    if last:
        last_txt = "%s IST" % _esc(_hhmm_ist_full(last))
    else:
        last_txt = "never"
    if f is None:
        pull = '<span class="warn">manojz has not reported in yet</span>'
    elif (f["state"] or "") == "ok":
        pull = '<span class="ok">manojz is awake</span> &middot; last Marg pull %s IST' % _esc(_hhmm_ist_full(f["pull_last"] or ""))
    else:
        pull = '<span class="bad">manojz pull asleep since %s IST</span>' % _hhmm_ist(f["pull_last"] or "")
    return ('<div class="card"><h2>Feed health</h2>'
            '<div>Last purchase data received: <b>%s</b></div>'
            '<div>Months on file: %s</div><div>%s</div></div>'
            % (last_txt, _esc(months), pull))


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
    _rematch_if_changed(con, "hub")                            # S225 rev 9
    prefix = request.script_root + _url_prefix
    rows = []
    for m in _months(con):
        s = _month_summary(con, m)
        st = s["status"]["status"].upper()
        rows.append('<tr><td><a href="%s/page/month/%s">%s</a></td><td class="n"><b>%s</b>%s</td>'
                    '<td class="n">%s</td><td class="n">%d</td><td class="n">%d</td>'
                    '<td class="n %s">%d</td><td class="n %s">%d</td>'
                    '<td><span class="chip %s">%s</span></td></tr>'
                    '<tr><td colspan="8" class="muted" style="padding-top:2px;padding-bottom:12px">%s</td></tr>'
                    % (prefix, m, _esc(_month_name(m)), _r(s["marg_p"]),
                       "" if s["basis"] == "supplier-wise" else '<div class="muted">bill-wise</div>',
                       _r(s["itemwise_p"]), len(s["bills"]), len(s["returns"]),
                       "warn" if s["no_lines"] else "", len(s["no_lines"]),
                       "bad" if s["wrong"] else "", s["wrong"],
                       "ok" if st == "FINAL" else "warn", st, _esc(s["story"])))
    months = ('<div class="card"><h2>Months</h2><div class="muted">The Marg total is the supplier-wise '
              'report, final for month-end. Item-wise is NET (after discount), each bill\'s lines counted '
              'once; a bill whose lines add up to more than the bill carries a purchase return, as Marg '
              'reports it.</div>'
              '<div class="scroll"><table><tr><th>Month</th>'
              '<th class="n">Marg total (supplier-wise)</th><th class="n">Item-wise net</th><th class="n">Bills</th>'
              '<th class="n">Returns</th><th class="n">No lines</th>'
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
               months, _feed_card(con), _stock_card(con), scan, orders + _new_items_card(con, prefix)))
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
    ret_by = {x["bill"]["id"]: x for x in s["returns"]}
    short_by = {x["bill"]["id"]: x for x in s["short"]}
    for name, bills in groups:
        out.append('<tr><th colspan="7" style="text-transform:none;font-size:14px;color:var(--ink);'
                   'padding-top:14px">%s</th></tr>' % _esc(name))
        for b in bills:
            t = _bill_lines(b, s["sets"], s["stray"])
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
            elif b["id"] in ret_by:
                vh = '<span class="chip">purchase return %s (Marg)</span>' % _r(ret_by[b["id"]]["diff_p"])
            elif b["id"] in short_by:
                vh = ('<span class="warn">item lines %s short</span> <span class="muted">Item lines missing '
                      '\u2014 check the bill</span>' % _r(-short_by[b["id"]]["diff_p"]))
            elif b["disagree_p"]:
                vh = ('<span class="bad">bill-wise %s, supplier-wise %s</span> <span class="muted">'
                      '\u2014 check the bill</span>' % (_r(b["bw_p"]), _r(b["sw_p"])))
            elif not n:
                vh = '<span class="warn">no item lines yet</span>'
            else:
                vh = '<span class="ok">agrees</span>'
            btn = ""
            if not final and not viewer and b["id"] in s["needs_verdict"]:
                btn = ('<span class="noprint"> <button class="sm" onclick="verdict(%d,\'CORRECT\')">Correct</button>'
                       ' <button class="sm" onclick="verdict(%d,\'WRONG\')">Wrong</button></span>' % (b["id"], b["id"]))
            out.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                       '<td class="n">%d</td><td>%s</td><td>%s%s</td></tr>'
                       % (_human(b["bill_date"]), _esc(b["bill_no"]), _r(b["marg_p"]), _r(tot) if n else "\u2014",
                          n, scan, vh, btn))
    buckets = []
    if s["returns"]:
        buckets.append(
            '<h2>Purchase returns (%d)</h2><div class="muted">Marg reports a purchase return inside the bill: '
            'the bill\'s item lines add up to more than the bill. Nothing to mark \u2014 the supplier-wise '
            'figure already carries it.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Marg amount</th>'
            '<th class="n">Item-wise (net)</th><th class="n">Return (Marg)</th></tr>%s</table></div>' % (len(s["returns"]), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                % (_human(x["bill"]["bill_date"]), _esc(x["bill"]["bill_no"]), _esc(x["bill"]["supplier"]),
                   _r(x["bill"]["marg_p"]), _r(x["net_p"]), _r(x["diff_p"])) for x in s["returns"])))
    if s["short"]:
        buckets.append(
            '<h2>Item lines short of the bill (%d)</h2><div class="muted">The bill\'s item lines add up to less '
            'than the bill \u2014 usually the item-wise export missed a line. Check the bill: Correct if Marg\'s '
            'amount is right, Wrong if it is not.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Marg amount</th>'
            '<th class="n">Item-wise (net)</th><th class="n">Short by</th><th>Check</th></tr>%s</table></div>' % (len(s["short"]), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n warn">%s</td><td>%s</td></tr>'
                % (_human(x["bill"]["bill_date"]), _esc(x["bill"]["bill_no"]), _esc(x["bill"]["supplier"]),
                   _r(x["bill"]["marg_p"]), _r(x["net_p"]), _r(-x["diff_p"]),
                   _esc((x["bill"]["verdict"] or "to check").capitalize())) for x in s["short"])))
    if s["disagree"]:
        buckets.append(
            '<h2>Bill-wise and supplier-wise disagree (%d)</h2><div class="muted">Marg\'s two reports give two '
            'amounts for the same bill. Check the bill in Marg; a fresh export of both reports usually closes it.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Bill-wise</th>'
            '<th class="n">Supplier-wise</th><th>Check</th></tr>%s</table></div>' % (len(s["disagree"]), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                % (_human(b["bill_date"]), _esc(b["bill_no"]), _esc(b["supplier"]), _r(b["bw_p"]), _r(b["sw_p"]),
                   _esc((b["verdict"] or "to check").capitalize())) for b in s["disagree"])))
    if s["no_lines"]:
        buckets.append(
            '<h2>Bills with no item lines yet (%d)</h2><div class="note">Item-wise export missing for %s. '
            'Export item-wise for those dates (or the whole month) once and these close.</div>'
            '<div class="scroll"><table><tr><th>Date</th><th>Bill</th><th>Supplier</th><th class="n">Marg amount</th>'
            '<th>Missing</th></tr>%s</table></div>' % (len(s["no_lines"]), _esc(_dates_text(s["gap_dates"])), "".join(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="muted">item-wise export missing for %s</td></tr>'
                % (_human(b["bill_date"]), _esc(b["bill_no"]), _esc(b["supplier"]), _r(b["marg_p"]),
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
               'in a month. They do not change the month\'s figure.</div><div class="scroll"><table><tr>'
               '<th>Bill</th><th>Item</th><th class="n">Qty</th><th class="n">Net amount</th><th>From export</th></tr>%s'
               '</table></div>' % "".join(
                   '<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="muted">%s</td></tr>'
                   % (_esc(l["bill_no"] or "?"), _esc(l["item"]), l["qty"] if l["qty"] is not None else "",
                      _r(l["net_amount_p"] if l["net_amount_p"] is not None else l["amount_p"]),
                      _esc(l["file"])) for l in s["undated"]))
    basis_line = ('<div class="muted">%s.</div>' % _esc(s["basis_note"])) if s["basis_note"] else ""
    recon = ('<h2 style="margin-top:0;font-size:22px">Marg purchase, %s: %s <span class="muted" style="font-size:14px">(%s%s)</span></h2>%s'
             '<div class="grid"><div class="kv"><b>%s</b><span>item-wise net (after discount)</span></div>'
             '<div class="kv"><b>%d</b><span>bills &middot; %d agree &middot; %d %s a purchase return</span></div>'
             '<div class="kv"><b class="%s">%d</b><span>without item lines yet</span></div>'
             '<div class="kv"><b class="%s">%d</b><span>wrong &middot; %d to check</span></div></div>'
             '<div class="muted" style="margin-top:8px">%s</div>'
             % (_esc(_month_name(month)), _r(s["marg_p"]), s["basis"],
                ", final for month-end" if s["basis"] == "supplier-wise" else "", basis_line,
                _r(s["itemwise_p"]), len(s["bills"]), len(s["agree"]), len(s["returns"]),
                "carries" if len(s["returns"]) == 1 else "carry",
                "warn" if s["no_lines"] else "", len(s["no_lines"]),
                "bad" if s["wrong"] else "", s["wrong"], s["to_check"], _esc(s["story"])))
    if final:
        st = ('<div class="note"><b>FINAL</b> \u2014 %s, %s IST.%s</div>'
              % (_esc(s["status"]["finalised_by"]), _esc(_when_ist(s["status"]["finalised_at"])),
                 ' <button class="sm noprint" onclick="reopen(\'%s\')">reopen</button>' % month if doctor else ""))
    else:
        if s["can_finalise"]:
            st = ('<div class="note"><b>PROVISIONAL</b> \u2014 ready to finalise. %s</div>'
                  % ('<button class="p noprint" onclick="finalise(\'%s\')">FINALISE %s</button>' % (month, _esc(_month_name(month)))
                     if doctor else '<span class="muted">Only the doctor can finalise.</span>'))
        else:
            st = ('<div class="note"><b>PROVISIONAL</b> \u2014 cannot finalise yet:<ul>%s</ul>%s</div>'
                  % ("".join("<li>%s</li>" % _esc(r) for r in s["reasons"]),
                     '<span class="muted">The FINALISE button appears for the doctor once these are cleared.</span>'))
    body = ('<h1>%s \u2014 purchases</h1><div class="muted">One row per Marg bill. The amount is Marg\'s '
            'supplier-wise figure (bill-wise while supplier-wise is not yet exported). Item-wise is the NET '
            '(after discount) sum of that bill\'s lines, from the latest export that carries the bill.</div><div class="card">%s%s</div><div class="card"><div class="scroll">'
            '<table><tr><th>Date</th><th>Bill</th><th class="n">Amount</th><th class="n">Item-wise (net)</th>'
            '<th class="n">Lines</th><th>Scan</th><th>Check</th></tr>%s</table></div>%s</div>'
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
    _rematch_if_changed(con, "scans")                          # S225 rev 9
    prefix = request.script_root + _url_prefix
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
            '<tr><td>%s%s</td><td class="n">%d</td><td class="n"><b>%d</b> %s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%.1f</td><td class="n">%s</td><td class="muted">%s%s</td></tr>'
            % (_esc(l["item"]), ' <span class="chip warn">confirm</span>' if l["confirm"] else "",
               l["on_hand"], l["order_strips"], _esc(_uw(l)), _esc(l["pack_size"]), _r(l["rate_p"]),
               l["rate_per_day"], l["cover_after"] if l["cover_after"] is not None else "—",
               l["confidence"], ("; " + "; ".join(l["why"])) if l["why"] else "")
            for l in v["lines"])
        copy = "ORDER — %s\n%s\n%s\nTotal approx %s" % (
            v["vendor"], plan["today"],
            "\n".join("%s — %d %s" % (l["item"], l["order_strips"], _uw(l))
                      for l in v["lines"] if l["order_strips"] > 0), _r(v["total_p"]))
        vend_html.append(
            '<div class="card"><div class="row spread"><h3 style="margin:0">%s%s</h3><div class="noprint">%s%s</div></div>'
            '<div class="muted">cadence %s days &middot; approx %s</div><div class="scroll"><table><tr><th>Item</th>'
            '<th class="n">On hand</th><th class="n">Order qty</th><th class="n">Pack</th><th class="n">Rate</th>'
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


# ====================================================================== S225: the staff order page
# The owner, 04-Sep-2026 11:45 IST, on seeing the first Orders page: "item, current stock and
# order quantity is all the staff need to know and see" -- "round off to 10 strips, and then in
# multiples of 10" -- "stockist gets it forwarded as WhatsApp = Sanjeevni Medicos, G 15 Rampur
# Garden, Bareilly, then a list of item name with quantity" -- "a system ready for staff to call
# from PWA by clicking the number" -- "staff should be able to print PDF A4 of purchase order".
# Rates, values, cadence, cover, confidence and reasons are ADMIN DETAIL and stay on the doctor's
# Orders page. This page shows three columns and three buttons, and nothing else.

WA_HEADER = "Sanjeevni Medicos, G 15 Rampur Garden, Bareilly"
STAFF_ROUND = 10          # strips: round UP to 10, then multiples of 10 (the owner's rule)


def _unit_word(packing, pack_size, n=1):
    """The unit staff order in. Strips where Marg packs in strips; bottles for liquids; tubes for
    creams; 'unit' otherwise. Plural for n != 1. The owner rules on the words -- he can see them."""
    p = (packing or "").upper()
    if pack_size and int(pack_size) > 1:
        w = "strip"
    elif "ML" in p or "LTR" in p or "LITRE" in p:
        w = "bottle"
    elif "GM" in p or "GRM" in p or "GRAM" in p:
        w = "tube"
    else:
        w = "unit"
    return w if n == 1 else w + "s"


def _staff_qty(order_strips, unit):
    """The owner's rounding: strips go up to 10, then to the next multiple of 10. Other units
    keep the engine's box-rounded quantity (a syrup is not ordered ten at a time by rule)."""
    n = int(order_strips or 0)
    if n <= 0:
        return 0
    if unit.startswith("strip"):
        return max(STAFF_ROUND, ceil_div(n, STAFF_ROUND) * STAFF_ROUND)
    return n


def _wa_digits(phone):
    """'+91 98xxx', '098xxx', '98xxx' -> '9198xxx'. Empty when there is no usable number."""
    d = re.sub(r"\D", "", str(phone or ""))
    if len(d) == 10:
        d = "91" + d
    elif len(d) == 11 and d.startswith("0"):
        d = "91" + d[1:]
    return d if 12 <= len(d) <= 15 else ""


def _wa_text(lines):
    """EXACTLY what the owner dictated: the header line, a blank line, then 'Item - qty unit'
    per line. No date, no rates, no total, no sign-off."""
    body = "\n".join("%s — %d %s" % (l["item"], l["qty"], _unit_word(l.get("packing"), l.get("pack_size"), l["qty"]))
                     for l in lines if int(l.get("qty") or 0) > 0)
    return WA_HEADER + "\n\n" + body


def _wa_url(phone, text):
    from urllib.parse import quote
    d = _wa_digits(phone)
    if not d:
        return ""
    return "https://wa.me/%s?text=%s" % (d, quote(text, safe=""))


def _staff_plan(con):
    """The doctor's reorder plan, reduced to what staff see: per stockist, item / stock now /
    order qty in the item's unit, the owner's rounding applied. Lines the engine flags 'confirm'
    are still shown -- the stockist can only send what is asked, and the doctor's page keeps the
    reasons -- but a line the engine zeroed is not."""
    plan = reorder_plan(con)
    _, snap = _latest_snapshot(con)
    out = []
    for v in plan["vendors"]:
        lines = []
        for l in v["lines"]:
            if l["order_strips"] <= 0:
                continue
            s = snap.get(norm(l["item"])) or {}
            unit = l.get("unit") or _unit_word(s.get("packing"), l["pack_size"])
            qty = l["order_strips"]          # already rounded by the engine (rev 7)
            lines.append(dict(item=l["item"], on_hand=l["on_hand"], qty=qty, unit=unit,
                              packing=s.get("packing") or "", pack_size=l["pack_size"],
                              rate_p=l["rate_p"], per_day=l["rate_per_day"], cover_after=l["cover_after"]))
        if not lines:
            continue
        lines.sort(key=lambda x: x["item"])
        phone = _phone_for(con, v["vendor"])
        out.append(dict(vendor=v["vendor"], lines=lines, has_phone=bool(_wa_digits(phone)),
                        no_vendor=v["vendor"].startswith("(")))
    out.sort(key=lambda v: (v["no_vendor"], v["vendor"]))
    return plan["as_on"], out


def _staff_send(con, u, b):
    """One tap: the order is written as SENT by this person at this minute, audited, and the
    WhatsApp address comes back for the browser to open. The phone number itself is never in
    the page; it travels only inside the wa.me link."""
    vendor = str(b.get("vendor") or "").strip()[:120]
    lines = b.get("lines")
    if not vendor or not isinstance(lines, list) or not lines:
        return jsonify(ok=False, error="malformed", message="vendor and lines required"), 400
    clean = []
    for ln in lines:
        if not isinstance(ln, dict) or not str(ln.get("item") or "").strip():
            continue
        qty = _int_or_none(ln.get("qty")) or 0
        if qty <= 0:
            continue
        clean.append(dict(item=str(ln.get("item")).strip()[:120], qty=qty,
                          pack_size=max(1, _int_or_none(ln.get("pack_size")) or 1),
                          packing=str(ln.get("packing") or "")[:40],
                          rate_p=_int_or_none(ln.get("rate_p")) or 0,
                          on_hand=_int_or_none(ln.get("on_hand")),
                          per_day=_float_or_none(ln.get("per_day")),
                          cover_after=_float_or_none(ln.get("cover_after"))))
    if not clean:
        return jsonify(ok=False, error="malformed", message="no line has a quantity"), 400
    phone = _phone_for(con, vendor)
    text = _wa_text(clean)
    url = _wa_url(phone, text)
    if not url:
        return jsonify(ok=False, error="no_phone",
                       message="No WhatsApp number on record for %s. Ask Dr Manoj to add it." % vendor), 409
    cur = con.execute("INSERT INTO purchase_order (created_at,created_by,vendor,status,note,total_p,sent_by) "
                      "VALUES (?,?,?,?,?,0,?)", (now_iso(), _who(u), vendor, "sent", "whatsapp", _who(u)))
    oid = cur.lastrowid
    total = 0
    for ln in clean:
        value = ln["qty"] * ln["rate_p"]
        total += value
        con.execute("INSERT INTO purchase_order_line (order_id,item,packs,pack_size,units,rate_p,"
                    "value_p,on_hand,per_day,cover_after) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (oid, ln["item"], ln["qty"], ln["pack_size"], ln["qty"] * ln["pack_size"],
                     ln["rate_p"], value, ln["on_hand"], ln["per_day"], ln["cover_after"]))
    con.execute("UPDATE purchase_order SET total_p=? WHERE id=?", (total, oid))
    _audit(con, _who(u), "order_sent_whatsapp", oid,
           dict(vendor=vendor, lines=len(clean), total_p=total, via="wa.me"))
    con.commit()
    return jsonify(ok=True, order_id=oid, wa_url=url)


@bp.route("/order/<int:oid>/pdf")
def order_pdf(oid):
    """A4 purchase order for the reception printer: header, stockist, Item / Qty / Unit, a
    signature line. No rates -- staff print this. The writer is clinic_day_pdf's (S224)."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    o = con.execute("SELECT * FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if o is None:
        return jsonify(ok=False, error="no_such_order"), 404
    lines = [dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY item",
                                          (oid,)).fetchall()]
    _, snap = _latest_snapshot(con)
    try:
        import clinic_day_pdf as cdp
    except ImportError:
        return jsonify(ok=False, error="no_pdf_writer",
                       message="clinic_day_pdf.py (S224) is not beside this app; the PDF needs it."), 501
    L, R, TOP, BOT = 40.0, 555.28, 800.0, 60.0
    pdf = cdp._PDF("Purchase Order %d" % oid)
    pdf.new_page()
    y = TOP
    pdf.text(L, y - 16, WA_HEADER, 15, bold=True)
    y -= 24
    pdf.text(L, y - 12, "Purchase Order #%d  -  %s" % (oid, _human(o["created_at"][:10])), 11.5, bold=True, gray=0.15)
    y -= 20
    pdf.line(L, y, R, y, 0.8)
    y -= 16
    pdf.text(L, y, "To: " + str(o["vendor"]), 11)
    y -= 26
    C_ITEM, C_QTY, C_UNIT = L, 430.0, 470.0
    pdf.text(C_ITEM, y, "ITEM", 9, bold=True, gray=0.35)
    pdf.text(C_QTY, y, "QTY", 9, bold=True, align="r", gray=0.35)
    pdf.text(C_UNIT, y, "UNIT", 9, bold=True, gray=0.35)
    y -= 5
    pdf.line(L, y, R, y, 0.4, 0.6)
    y -= 15
    for l in lines:
        if y < BOT + 40:
            pdf.new_page()
            y = TOP
            pdf.text(L, y - 12, "Purchase Order #%d (contd.)" % oid, 10, bold=True, gray=0.3)
            y -= 30
        s = snap.get(norm(l["item"])) or {}
        unit = _unit_word(s.get("packing"), l["pack_size"], l["packs"])
        pdf.text(C_ITEM, y, cdp._fit(l["item"], 10.5, C_QTY - C_ITEM - 40), 10.5)
        pdf.text(C_QTY, y, str(l["packs"]), 10.5, bold=True, align="r")
        pdf.text(C_UNIT, y, unit, 10.5)
        y -= 15
    y -= 6
    pdf.line(L, y, R, y, 0.4, 0.6)
    y -= 16
    pdf.text(L, y, "%d line%s" % (len(lines), "" if len(lines) == 1 else "s"), 9.5, gray=0.35)
    y = max(BOT + 30, y - 60)
    pdf.line(R - 200, y, R, y, 0.5)
    pdf.text(R, y - 12, "Signature", 9, align="r", gray=0.35)
    pdf.text(L, BOT, "Prepared by %s  -  %s" % (o["created_by"], _hhmm_ist_full(o["created_at"])), 8.5, gray=0.45)
    data = pdf.build()
    return data, 200, {"Content-Type": "application/pdf", "Cache-Control": "no-store",
                       "Content-Disposition": 'inline; filename="purchase_order_%d.pdf"' % oid}


STAFF_JS = """
async function sendWA(idx){
  const v = STAFF[idx]; if (!v) return;
  const lines = v.lines.filter(l => l.qty > 0);
  if (!lines.length){ alert('Nothing to order for ' + v.vendor + '.'); return; }
  if (!confirm('Send this order to ' + v.vendor + ' on WhatsApp?\\n' + lines.length + ' item(s).')) return;
  const j = await post(P + '/api/order', {action:'staff_send', vendor:v.vendor, lines:lines});
  if (j && j.wa_url){ window.location.href = j.wa_url; }
}
"""


@bp.route("/page/staff")
def page_staff():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    as_on, vendors = _staff_plan(con)
    prefix = request.script_root + _url_prefix
    cards, staff_json = [], []
    for i, v in enumerate(vendors):
        rows = "".join('<tr><td>%s</td><td class="n">%d</td><td class="n"><b>%d</b> %s</td></tr>'
                       % (_esc(l["item"]), l["on_hand"], l["qty"], _unit_word(l["packing"], l["pack_size"], l["qty"]))
                       for l in v["lines"])
        if v["no_vendor"]:
            btns = '<span class="muted">No stockist on record for these &mdash; ask Dr Manoj.</span>'
        elif v["has_phone"]:
            phones = _phones_for(con, v["vendor"])
            btns = ('<button class="p" onclick="sendWA(%d)">Send on WhatsApp</button> ' % i
                    + " ".join('<a href="tel:%s"><button>Call%s</button></a>' % (_esc(_wa_digits(p)), (" %d" % (k + 1)) if len(phones) > 1 else "")
                               for k, p in enumerate(phones)))
        else:
            btns = '<span class="muted">No WhatsApp number on record &mdash; ask Dr Manoj.</span>'
        cards.append('<div class="card"><div class="row spread"><h3 style="margin:0">%s</h3>'
                     '<div class="noprint">%s</div></div><div class="scroll"><table><tr><th>Item</th>'
                     '<th class="n">Stock now</th><th class="n">Order qty</th></tr>%s</table></div></div>'
                     % (_esc(v["vendor"]), btns, rows))
        staff_json.append(dict(vendor=v["vendor"], lines=[
            dict(item=l["item"], qty=l["qty"], pack_size=l["pack_size"], packing=l["packing"],
                 rate_p=l["rate_p"], on_hand=l["on_hand"], per_day=l["per_day"], cover_after=l["cover_after"])
            for l in v["lines"]]))
    book = []
    for o in _orders(con)[:30]:
        book.append('<tr><td>#%d</td><td>%s</td><td>%s</td><td class="n">%d</td>'
                    '<td><span class="chip">%s</span>%s</td>'
                    '<td class="noprint"><a href="%s/order/%d/pdf" target="_blank"><button class="sm">Print A4</button></a> %s</td></tr>'
                    % (o["id"], _esc(_hhmm_ist_full(o["created_at"])), _esc(o["vendor"]), len(o["lines"]),
                       _esc(o["status"]), (" <small class=\"muted\">%s</small>" % _esc(_hhmm_ist_full(o["received_at"]))) if o.get("received_at") else "",
                       prefix, o["id"], _arrival_block(prefix, o)))
    body = ('<h1>Order medicines</h1><div class="muted">Stock as on %s. Tap <b>Send on WhatsApp</b> '
            'and the order goes to the stockist as a message; it is recorded here as sent, by you, at that '
            'minute. <b>Call</b> rings the stockist. <b>Print A4</b> is for the reception printer. When the goods come, '
            'tap <b>Arrived</b> — or <b>Different</b> to enter what was actually supplied and mark what the stockist was short of; '
            'a short item is carried into the next order by itself.</div>%s'
            '<div class="card"><h2>Orders sent</h2><div class="scroll"><table><tr><th>#</th><th>When</th>'
            '<th>Stockist</th><th class="n">Items</th><th>Status</th><th class="noprint"></th></tr>%s</table></div></div>'
            % (_esc(_human(as_on) if as_on and ISO_RE.match(as_on or "") else (as_on or "no snapshot yet")),
               "".join(cards) or '<div class="card muted">Nothing to order on today\'s stock.</div>',
               "".join(book) or '<tr><td colspan="6" class="muted">no orders yet</td></tr>'))
    return _page("Order medicines", body, STAFF_JS + ARRIVE_JS + "const STAFF=%s;" % json.dumps(staff_json))


# ====================================================================== S225 rev 7: the stockist phone book
# The owner, 04-Sep-2026: "I and Darpan and Shavez should have access to the stockist phone book" ·
# "up to 2 numbers for each supplier, for modification, and adding a new one" · "new addition should have
# his bank details fields" · "only I can verify the bank details — new and modify, both" · (S225, ~14:00)
# "all existing bank details already accepted as decided; it's for the future part."
# So: an allow-list of editors (setting purchase.phonebook_users; the doctor always; FAIL-CLOSED — no row,
# only the doctor); two phones per supplier; five bank fields, server-side only (F-185/F-31 — never in a
# kit, never in the repo); bank fields saved by anyone but the doctor are UNVERIFIED until he taps Verify;
# a bank field the doctor saves himself is VERIFIED by that act. Server edits are never overwritten by the
# nightly manojz push (source='server' wins; the push fills only what it owns). Every change is audited by
# FIELD NAME and last-4, never by value. The future NEFT leg reads bank_status and refuses UNVERIFIED.
BOOK_USERS_KEY = "purchase.phonebook_users"
BOOK_COLS = (("phone2", "TEXT"), ("acct_name", "TEXT"), ("acct_no", "TEXT"), ("ifsc", "TEXT"),
             ("bank_branch", "TEXT"), ("upi_id", "TEXT"), ("bank_status", "TEXT"),
             ("bank_verified_by", "TEXT"), ("bank_verified_at", "TEXT"), ("source", "TEXT"),
             ("added_by", "TEXT"))
BANK_FIELDS = ("acct_name", "acct_no", "ifsc", "bank_branch", "upi_id")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def _ensure_book(con):
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    for col, typ in BOOK_COLS:
        if col not in have:
            con.execute("ALTER TABLE purchase_vendor_contact ADD COLUMN %s %s" % (col, typ))
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.commit()


def _book_users(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (BOOK_USERS_KEY,)).fetchone()
    except Exception:
        return set()
    raw = (r[0] if r else "") or ""
    return set(p.strip().lower() for p in re.split(r"[,;\s]+", str(raw)) if p.strip())


def _book_allowed(u, con):
    """The doctor always. Otherwise ONLY a login named in the setting. Fail-closed: a missing or
    unreadable setting admits nobody but the doctor -- this page carries bank accounts."""
    if _is_doctor(u):
        return True
    who = str(_who(u) or "").strip().lower()
    return bool(who) and who in _book_users(con)


def _last4(s):
    d = re.sub(r"\D", "", str(s or ""))
    return ("…" + d[-4:]) if d else ""


def _clean_phone(s):
    d = re.sub(r"\D", "", str(s or ""))
    if d.startswith("91") and len(d) == 12:
        d = d[2:]
    if d.startswith("0") and len(d) == 11:
        d = d[1:]
    if not d:
        return ""
    if len(d) != 10:
        raise ValueError("a phone number is 10 digits")
    return d


def _phones_for(con, vendor):
    r = con.execute("SELECT phone, phone2 FROM purchase_vendor_contact WHERE vendor_norm=?",
                    (supplier_key(vendor),)).fetchone()
    if not r:
        return []
    return [p for p in (r[0], r[1]) if p]


def _book_rows(con):
    return [dict(r) for r in con.execute(
        "SELECT * FROM purchase_vendor_contact ORDER BY vendor").fetchall()]


def _bank_clean(b):
    out = {}
    for f in BANK_FIELDS:
        v = str(b.get(f) or "").strip()
        if f == "ifsc":
            v = v.upper()
            if v and not IFSC_RE.match(v):
                raise ValueError("IFSC looks wrong (4 letters, 0, 6 characters)")
        if f == "acct_no":
            v = re.sub(r"\s", "", v)
            if v and not re.match(r"^\d{9,18}$", v):
                raise ValueError("account number: 9 to 18 digits")
        if f == "upi_id" and v and "@" not in v:
            raise ValueError("a UPI id has an @")
        out[f] = v[:80]
    return out


def _book_save(con, u, b):
    """One door, four actions. Audit by field name and last-4 only."""
    action = str(b.get("action") or "")
    who = _who(u)
    vendor = str(b.get("vendor") or "").strip()[:120]
    if not vendor:
        return jsonify(ok=False, error="malformed", message="stockist name required"), 400
    key = supplier_key(vendor)
    row = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,)).fetchone()
    try:
        if action == "add":
            if row is not None:
                return jsonify(ok=False, error="exists", message="%s is already in the book — edit it instead." % vendor), 409
            p1, p2 = _clean_phone(b.get("phone")), _clean_phone(b.get("phone2"))
            if not p1:
                return jsonify(ok=False, error="malformed", message="the first phone number is required"), 400
            bank = _bank_clean(b)
            has_bank = any(bank.values())
            status = ("VERIFIED" if _is_doctor(u) else "UNVERIFIED") if has_bank else ""
            con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, phone2, acct_name, acct_no, "
                        "ifsc, bank_branch, upi_id, bank_status, bank_verified_by, bank_verified_at, source, added_by, "
                        "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (key, vendor, p1, p2, bank["acct_name"], bank["acct_no"], bank["ifsc"], bank["bank_branch"],
                         bank["upi_id"], status, who if status == "VERIFIED" else "", now_iso() if status == "VERIFIED" else "",
                         "server", who, now_iso()))
            _audit(con, who, "book_add", key, dict(vendor=vendor, phone=_last4(p1), phone2=_last4(p2),
                                                   bank_fields=[f for f in BANK_FIELDS if bank[f]], bank_status=status))
            con.commit()
            return jsonify(ok=True, vendor=vendor, bank_status=status)
        if row is None:
            return jsonify(ok=False, error="no_such_vendor", message="%s is not in the book." % vendor), 404
        if action == "phones":
            p1, p2 = _clean_phone(b.get("phone")), _clean_phone(b.get("phone2"))
            if not p1:
                return jsonify(ok=False, error="malformed", message="the first phone number is required"), 400
            con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, source='server', updated_at=? WHERE vendor_norm=?",
                        (p1, p2, now_iso(), key))
            _audit(con, who, "book_phones", key, dict(vendor=row["vendor"], phone=_last4(p1), phone2=_last4(p2),
                                                      was=_last4(row["phone"]), was2=_last4(row["phone2"])))
            con.commit()
            return jsonify(ok=True)
        if action == "bank":
            bank = _bank_clean(b)
            changed = [f for f in BANK_FIELDS if (row[f] or "") != bank[f]]
            if not changed:
                return jsonify(ok=True, unchanged=True, bank_status=row["bank_status"] or "")
            # D370: a modified bank field drops back to UNVERIFIED -- unless the doctor himself saved it.
            status = "VERIFIED" if _is_doctor(u) else "UNVERIFIED"
            if not any(bank.values()):
                status = ""
            con.execute("UPDATE purchase_vendor_contact SET acct_name=?, acct_no=?, ifsc=?, bank_branch=?, upi_id=?, "
                        "bank_status=?, bank_verified_by=?, bank_verified_at=?, source='server', updated_at=? WHERE vendor_norm=?",
                        (bank["acct_name"], bank["acct_no"], bank["ifsc"], bank["bank_branch"], bank["upi_id"], status,
                         who if status == "VERIFIED" else "", now_iso() if status == "VERIFIED" else "", now_iso(), key))
            _audit(con, who, "book_bank", key, dict(vendor=row["vendor"], changed=changed, bank_status=status,
                                                    acct_last4=_last4(bank["acct_no"])))
            con.commit()
            return jsonify(ok=True, bank_status=status)
        if action == "verify":
            if not _is_doctor(u):
                return _refuse("Only the doctor verifies bank details.")
            if not any((row[f] or "") for f in BANK_FIELDS):
                return jsonify(ok=False, error="nothing_to_verify", message="No bank details on record for %s." % row["vendor"]), 400
            con.execute("UPDATE purchase_vendor_contact SET bank_status='VERIFIED', bank_verified_by=?, bank_verified_at=?, "
                        "updated_at=? WHERE vendor_norm=?", (who, now_iso(), now_iso(), key))
            _audit(con, who, "book_verify", key, dict(vendor=row["vendor"], acct_last4=_last4(row["acct_no"])))
            con.commit()
            return jsonify(ok=True, bank_status="VERIFIED")
    except ValueError as e:
        return jsonify(ok=False, error="malformed", message=str(e)), 400
    return jsonify(ok=False, error="malformed", message="action add|phones|bank|verify"), 400


@bp.route("/api/book", methods=["POST"])
def api_book():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _ensure_book(con)
    if not _book_allowed(u, con):
        return _refuse("The phone book is for Dr Manoj, Darpan and Shavez.")
    return _book_save(con, u, request.get_json(silent=True) or {})


IFSC_BANKS = {"SBIN": "State Bank of India", "HDFC": "HDFC Bank", "ICIC": "ICICI Bank", "UTIB": "Axis Bank",
              "KKBK": "Kotak Mahindra Bank", "PUNB": "Punjab National Bank", "BARB": "Bank of Baroda", "CNRB": "Canara Bank",
              "UBIN": "Union Bank of India", "UCBA": "UCO Bank", "CBIN": "Central Bank of India", "KARB": "Karnataka Bank",
              "YESB": "Yes Bank", "IDIB": "Indian Bank", "IOBA": "Indian Overseas Bank", "BKID": "Bank of India",
              "MAHB": "Bank of Maharashtra", "PSIB": "Punjab & Sind Bank", "IDFB": "IDFC First Bank", "INDB": "IndusInd Bank",
              "FDRL": "Federal Bank", "AUBL": "AU Small Finance Bank", "BDBL": "Bandhan Bank", "RATN": "RBL Bank",
              "SIBL": "South Indian Bank", "PYTM": "Paytm Payments Bank", "AIRP": "Airtel Payments Bank"}


def _bank_name(ifsc):
    """The bank, read off the first four letters of the IFSC (public codes). '' when unknown."""
    return IFSC_BANKS.get((ifsc or "")[:4].upper(), "")


BOOK_JS = """
function bookMsg(el, text){ if (!el) return; el.textContent = text || ''; el.hidden = !text; }
async function bookPost(body, msgEl){
  bookMsg(msgEl, 'saving...');
  const r = await fetch(P + '/api/book', {method:'POST', headers:{'Content-Type':'application/json'},
                                          credentials:'same-origin', body: JSON.stringify(body||{})});
  let j = {}; try { j = await r.json(); } catch(e) {}
  if (!r.ok || j.ok === false){ bookMsg(msgEl, j.message || j.error || ('HTTP ' + r.status)); return null; }
  location.reload(); return j;
}
function bookClose(i){ for (const k of ['phones','bank','verify']){ const d = document.getElementById('inl-' + k + '-' + i); if (d){ d.hidden = true; d.innerHTML = ''; } } }
function bookField(label, name, value, hint){
  return '<div><label>' + label + '</label><input name="' + name + '" value="' + (value||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;') + '"' + (hint ? ' inputmode="' + hint + '"' : '') + '></div>';
}
function bookForm(i, kind){
  const v = BOOKV[i]; const b = BOOK[v] || {}; const d = document.getElementById('inl-' + kind + '-' + i);
  if (!d) return;
  if (!d.hidden){ bookClose(i); return; }
  bookClose(i);
  let f = '';
  if (kind === 'phones'){
    f = bookField('First phone (10 digits)', 'phone', b.phone, 'numeric') + bookField('Second phone (blank for none)', 'phone2', b.phone2, 'numeric');
  } else {
    f = bookField('Account name', 'acct_name', b.acct_name) + bookField('Account number', 'acct_no', b.acct_no, 'numeric') +
        bookField('IFSC', 'ifsc', b.ifsc) + bookField('Bank and branch', 'bank_branch', b.bank_branch) + bookField('UPI id (blank for none)', 'upi_id', b.upi_id);
  }
  d.innerHTML = '<div class="grid">' + f + '</div><div class="row" style="margin-top:8px"><button class="p sm" onclick="bookSave(' + i + ',\\'' + kind + '\\')">Save</button>' +
                '<button class="sm" onclick="bookClose(' + i + ')">Cancel</button><span class="bad" id="msg-' + kind + '-' + i + '" hidden></span></div>';
  d.hidden = false;
  const first = d.querySelector('input'); if (first) first.focus();
}
async function bookSave(i, kind){
  const d = document.getElementById('inl-' + kind + '-' + i); const body = {action: kind, vendor: BOOKV[i]};
  for (const el of d.querySelectorAll('input')) body[el.name] = el.value;
  return bookPost(body, document.getElementById('msg-' + kind + '-' + i));
}
function bookVerify(i){
  const d = document.getElementById('inl-verify-' + i); if (!d) return;
  if (!d.hidden){ bookClose(i); return; }
  bookClose(i);
  d.innerHTML = '<span>Mark the bank details of <b></b> as VERIFIED? Only you can do this.</span> ' +
                '<button class="p sm" onclick="bookPost({action:\\'verify\\', vendor:BOOKV[' + i + ']}, document.getElementById(\\'msg-verify-' + i + '\\'))">Yes, verified</button> ' +
                '<button class="sm" onclick="bookClose(' + i + ')">No</button><span class="bad" id="msg-verify-' + i + '" hidden></span>';
  d.querySelector('b').textContent = BOOKV[i];
  d.hidden = false;
}
function bookAdd(){
  const f = document.getElementById('addform'); const d = {action:'add'}; const m = document.getElementById('msg-add');
  for (const el of f.querySelectorAll('input')) d[el.name] = el.value;
  if (!d.vendor || !d.phone){ bookMsg(m, 'Name and first phone are required.'); return; }
  bookPost(d, m);
}
"""


@bp.route("/page/book")
def page_book():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _ensure_book(con)
    if not _book_allowed(u, con):
        return _refuse("The phone book is for Dr Manoj, Darpan and Shavez.")
    doctor = _is_doctor(u)
    rows = _book_rows(con)
    vendors = [r["vendor"] for r in rows]
    book_json = {r["vendor"]: dict(phone=r["phone"] or "", phone2=r["phone2"] or "", acct_name=r["acct_name"] or "",
                                   acct_no=r["acct_no"] or "", ifsc=r["ifsc"] or "", bank_branch=r["bank_branch"] or "",
                                   upi_id=r["upi_id"] or "") for r in rows}
    trs = []
    n_nophone = 0
    for i, r in enumerate(rows):
        st = r["bank_status"] or ""
        if st == "VERIFIED":
            chip = '<span class="chip ok">VERIFIED</span> <small class="muted">%s</small>' % _esc(_hhmm_ist_full(r["bank_verified_at"] or ""))
        elif st == "UNVERIFIED":
            chip = ('<span class="chip warn">UNVERIFIED</span> ' +
                    ('<button class="sm p noprint" onclick="bookVerify(%d)">Verify</button>' % i if doctor else
                     '<small class="muted">waits for Dr Manoj</small>'))
        else:
            chip = '<small class="muted">no bank details</small>'
        has_bank = any((r[f] or "") for f in BANK_FIELDS)
        bank_lines = []
        if has_bank:
            if r["acct_name"]:
                bank_lines.append('<div><small class="muted">Account name</small> %s</div>' % _esc(r["acct_name"]))
            if r["acct_no"]:
                bank_lines.append('<div><small class="muted">A/c no</small> <b style="font-variant-numeric:tabular-nums;letter-spacing:.04em">%s</b></div>' % _esc(r["acct_no"]))
            if r["ifsc"]:
                bname = _bank_name(r["ifsc"])
                bank_lines.append('<div><small class="muted">IFSC</small> <b>%s</b>%s</div>'
                                  % (_esc(r["ifsc"]), (" · " + _esc(bname)) if bname else ""))
            if r["bank_branch"]:
                bank_lines.append('<div><small class="muted">Bank / branch</small> %s</div>' % _esc(r["bank_branch"]))
            if r["upi_id"]:
                bank_lines.append('<div><small class="muted">UPI</small> %s</div>' % _esc(r["upi_id"]))
        src_txt = ("added by " + _esc(r["added_by"]) if (r["added_by"] and r["added_by"] != "neft_import_s225") else
                   "from the NEFT records (04-Sep)" if (r["source"] or "") == "neft_import" else
                   "from Marg / manojz" if (r["source"] or "manojz") != "server" else "edited here")
        if r["phone"]:
            phones = '<a href="tel:%s">%s</a>%s' % (_esc(r["phone"]), _esc(r["phone"]),
                                                   (' · <a href="tel:%s">%s</a>' % (_esc(r["phone2"]), _esc(r["phone2"]))) if r["phone2"] else "")
        else:
            n_nophone += 1
            phones = '<span class="warn">no number yet</span>'
        trs.append('<tr><td><b>%s</b><br><small class="muted">%s</small></td>'
                   '<td>%s<br><button class="sm noprint" onclick="bookForm(%d,\'phones\')">%s numbers</button>'
                   '<div class="inl noprint" id="inl-phones-%d" hidden></div></td>'
                   '<td>%s%s <button class="sm noprint" onclick="bookForm(%d,\'bank\')">%s bank details</button>'
                   '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div></td></tr>'
                   % (_esc(r["vendor"]), src_txt,
                      phones, i, "edit" if r["phone"] else "add", i,
                      "".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))
    add = ('<div class="card" id="addform"><h3>Add a new stockist</h3><div class="grid">'
           '<div><label>Name (as Marg prints it)</label><input name="vendor"></div>'
           '<div><label>Phone</label><input name="phone" inputmode="numeric"></div>'
           '<div><label>Second phone (optional)</label><input name="phone2" inputmode="numeric"></div>'
           '<div><label>Account name</label><input name="acct_name"></div>'
           '<div><label>Account number</label><input name="acct_no" inputmode="numeric"></div>'
           '<div><label>IFSC</label><input name="ifsc"></div>'
           '<div><label>Bank and branch</label><input name="bank_branch"></div>'
           '<div><label>UPI id (optional)</label><input name="upi_id"></div></div>'
           '<div class="row" style="margin-top:8px"><button class="p" onclick="bookAdd()">Save new stockist</button> '
           '<span class="muted">Bank details %s</span><span class="bad" id="msg-add" hidden></span></div></div>'
           % ("you save are VERIFIED by that act." if doctor else "wait UNVERIFIED until Dr Manoj verifies them."))
    nophone = ('<div class="note noprint"><b>%d stockist%s without a phone number yet</b> — their bank details came from the NEFT '
               'records; tap <i>add numbers</i> on the row when you have the number.</div>' % (n_nophone, "s" if n_nophone != 1 else "")
               if n_nophone else "")
    body = ('<h1>Stockist phone book</h1><div class="muted">Two numbers per stockist; bank details stay on this server only and are '
            'shown in full here because this page is the source for the bulk NEFT file — it opens for Dr Manoj, Darpan and Shavez only. '
            'A bank detail added or changed by anyone but Dr Manoj is <b>UNVERIFIED</b> until he taps Verify; payments will refuse an '
            'unverified account. Details on record from the NEFT files stand as accepted (the owner, 04-Sep).</div>%s'
            '<style>.inl{margin-top:8px;padding:10px;border:1px solid var(--line);border-radius:8px;background:#f6f8fb}'
            '.inl label{display:block;font-size:12.5px;color:var(--muted)}.inl input{width:100%%}</style>'
            '<div class="card"><div class="scroll"><table><tr><th>Stockist</th><th>Phones</th><th>Bank</th></tr>%s</table></div></div>%s'
            % (nophone, "".join(trs) or '<tr><td colspan="3" class="muted">nobody in the book yet</td></tr>', add))
    return _page("Stockist phone book", body, BOOK_JS + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(vendors)))


# ====================================================================== S225 rev 8: when the goods arrive
# The owner (spec §4): "on arrival they simply tap to acknowledge" · "if qty is different, they enter the
# supplied one" · "option to mark if stockist is short of a medicine" (carries into the next order
# automatically) · "bill scan button should be at contextual place(s)".
ARRIVAL_COLS = (("purchase_order_line", "supplied", "INTEGER"), ("purchase_order_line", "short", "INTEGER NOT NULL DEFAULT 0"),
                ("purchase_order", "received_at", "TEXT"), ("purchase_order", "received_by", "TEXT"),
                ("purchase_order", "sent_by", "TEXT"))
CARRY_DAYS = 45          # a short-supplied line is carried into the plan for this long, or until re-ordered


def _ensure_arrival(con):
    for table, col, typ in ARRIVAL_COLS:
        have = {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
        if col not in have:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
    con.commit()


def _arrive(con, u, b):
    """One tap (action 'arrive'): every line supplied as ordered. Or 'arrive_diff' with lines
    [{id, supplied, short}]: the supplied quantity per line, and Short where the stockist could not
    supply. Either way the order becomes RECEIVED, by this person, at this minute, audited."""
    oid = _int_or_none(b.get("id"))
    if not oid:
        return jsonify(ok=False, error="malformed", message="order id required"), 400
    o = con.execute("SELECT * FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if o is None:
        return jsonify(ok=False, error="no_such_order"), 404
    if o["status"] != "sent":
        return jsonify(ok=False, error="not_sent", message="Only a SENT order can be received (this one is %s)." % o["status"]), 409
    lines = {l["id"]: dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=?", (oid,))}
    diff = str(b.get("action")) == "arrive_diff"
    given = {}
    if diff:
        for ln in (b.get("lines") or []):
            if not isinstance(ln, dict):
                continue
            lid = _int_or_none(ln.get("id"))
            if lid in lines:
                given[lid] = (max(0, _int_or_none(ln.get("supplied")) if ln.get("supplied") not in (None, "") else lines[lid]["packs"]),
                              1 if ln.get("short") in (True, 1, "1", "true", "on") else 0)
    shorts, changed = [], []
    for lid, l in lines.items():
        supplied, short = given.get(lid, (l["packs"], 0))
        if short and supplied >= l["packs"]:
            supplied = min(supplied, l["packs"])          # 'short' means less came than asked
        if supplied < l["packs"] and not short:
            short = 1                                      # less came: that IS a short, recorded so
        con.execute("UPDATE purchase_order_line SET supplied=?, short=? WHERE id=?", (supplied, short, lid))
        if short:
            shorts.append(dict(item=l["item"], asked=l["packs"], got=supplied))
        if supplied != l["packs"]:
            changed.append(dict(item=l["item"], asked=l["packs"], got=supplied))
    con.execute("UPDATE purchase_order SET status='received', received_at=?, received_by=? WHERE id=?",
                (now_iso(), _who(u), oid))
    _audit(con, _who(u), "order_received", oid, dict(vendor=o["vendor"], lines=len(lines), short=len(shorts),
                                                     changed=changed[:20], how="tap" if not diff else "by line"))
    con.commit()
    return jsonify(ok=True, order_id=oid, status="received", short=shorts, changed=changed)


def _carried_shorts(con, today=None):
    """{norm(item): dict(item, vendor, vendor_norm, shortfall, order_id, since)} -- lines short-supplied on a
    RECEIVED order within CARRY_DAYS that have NOT since been re-ordered from the same stockist. These
    ride into the next plan automatically (the owner's rule)."""
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=CARRY_DAYS)).isoformat()
    out = {}
    try:
        rows = con.execute(
            "SELECT l.item, l.packs, l.supplied, o.vendor, o.id AS oid, o.received_at FROM purchase_order_line l "
            "JOIN purchase_order o ON o.id=l.order_id WHERE o.status='received' AND l.short=1 AND "
            "COALESCE(l.supplied,0) < l.packs AND o.received_at >= ? ORDER BY o.received_at", (since,)).fetchall()
    except Exception:                                      # noqa: BLE001  (columns not there yet)
        return out
    for r in rows:
        later = con.execute(
            "SELECT 1 FROM purchase_order_line l2 JOIN purchase_order o2 ON o2.id=l2.order_id WHERE o2.vendor=? "
            "AND l2.item=? AND o2.status IN ('sent','received') AND o2.id > ? LIMIT 1",
            (r["vendor"], r["item"], r["oid"])).fetchone()          # a LATER order = a higher id (ids are monotonic; times can tie)
        if later:
            continue
        out[norm(r["item"])] = dict(item=r["item"], vendor=r["vendor"], vendor_norm=supplier_key(r["vendor"]),
                                    shortfall=int(r["packs"]) - int(r["supplied"] or 0), order_id=r["oid"],
                                    since=(r["received_at"] or "")[:10])
    return out


ARRIVE_JS = """
async function arrive(id, vendor){
  if (!confirm('Everything on order #' + id + ' from ' + vendor + ' has arrived as ordered?')) return;
  const j = await post(P + '/api/order', {action:'arrive', id:id}); if (j) location.reload();
}
function arriveDiff(id){
  const f = document.getElementById('diff' + id); if (!f) return;
  f.style.display = f.style.display === 'none' ? '' : 'none';
}
async function arriveSave(id){
  const f = document.getElementById('diff' + id); const lines = [];
  for (const tr of f.querySelectorAll('tr[data-line]')){
    lines.push({id: parseInt(tr.dataset.line), supplied: tr.querySelector('input[type=number]').value,
                short: tr.querySelector('input[type=checkbox]').checked});
  }
  const j = await post(P + '/api/order', {action:'arrive_diff', id:id, lines:lines}); if (j) location.reload();
}
"""


def _arrival_block(prefix, o):
    """The RECEIVE controls for a SENT order, and the contextual scan button for a RECEIVED one."""
    if o["status"] == "sent":
        rows = "".join('<tr data-line="%d"><td>%s</td><td class="n">%d</td>'
                       '<td class="n"><input type="number" min="0" value="%d" style="width:5em"></td>'
                       '<td><label><input type="checkbox"> short</label></td></tr>'
                       % (l["id"], _esc(l["item"]), l["packs"], l["packs"]) for l in o["lines"])
        return ('<button class="sm p" onclick="arrive(%d,%s)">Arrived</button> '
                '<button class="sm" onclick="arriveDiff(%d)">Different</button>'
                '<div id="diff%d" style="display:none;margin-top:6px"><table><tr><th>Item</th><th class="n">Asked</th>'
                '<th class="n">Supplied</th><th>Stockist short?</th></tr>%s</table>'
                '<button class="sm p" onclick="arriveSave(%d)">Save arrival</button></div>'
                % (o["id"], _esc(json.dumps(o["vendor"])), o["id"], o["id"], rows, o["id"]))
    if o["status"] == "received":
        shorts = [l for l in o["lines"] if l.get("short")]
        note = (' <small class="warn">%d short — carried to the next order</small>' % len(shorts)) if shorts else ""
        return ('<a href="/scanapp/intake" target="_blank"><button class="sm">Scan the bill</button></a>'
                '<br><small class="muted">note on the scan: %s · ₹%s</small>%s'
                % (_esc(o["vendor"]), _esc(_r(o["total_p"])[1:]), note))
    return ""


# ====================================================================== S225 rev 9: the cross-check is LIVE
# The owner (spec §6, and his S225 ruling "Sarvam — live, not nightly"): the Sarvam-scan vs Marg-bill
# cross-verification runs ON THE EVENT — when a purchase export lands (the push) and whenever the
# scans have changed since the last match (seen on the next opening of the hub or the scan-links
# page) — never as a 22:30 batch. And "received-but-not-yet-in-Marg quantities count as stock in
# transit for the reorder engine".
REMATCH_SEEN_KEY = "purchase.rematch_seen"
IN_TRANSIT_DAYS = 14


def _scan_fingerprint():
    """(count, max id) of pharmacy scans -- changes whenever a scan lands or is removed."""
    acon = _assets_con()
    if acon is None:
        return None
    try:
        r = acon.execute("SELECT COUNT(*), COALESCE(MAX(id),0) FROM bills WHERE kind='Pharmacy'").fetchone()
        return "%d:%d" % (r[0], r[1])
    except Exception:                                      # noqa: BLE001
        return None
    finally:
        acon.close()


def _rematch_if_changed(con, who="page"):
    """Re-match only when the scans have changed since the last match. Cheap when nothing moved."""
    fp = _scan_fingerprint()
    if fp is None:
        return None
    try:
        con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        r = con.execute("SELECT value FROM setting WHERE key=?", (REMATCH_SEEN_KEY,)).fetchone()
    except Exception:                                      # noqa: BLE001
        r = None
    if r is not None and r[0] == fp:
        return None
    out = _rematch(con, who)
    con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (REMATCH_SEEN_KEY, fp))
    con.commit()
    return out


def _rematch_after_push(con):
    """A push that stored bills or lines re-matches at once. Never lets the push fail for it."""
    try:
        _rematch(con, "push")
        fp = _scan_fingerprint()
        if fp:
            con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (REMATCH_SEEN_KEY, fp))
            con.commit()
    except Exception:                                      # noqa: BLE001
        pass


def _in_transit(con, today=None):
    """{norm(item): dict(units, order_id, vendor)} -- quantities RECEIVED on an order within IN_TRANSIT_DAYS
    for which Marg has not yet shown a purchase line from that stockist on or after the receipt date.
    They are on the shelf but not in the stock snapshot yet; the engine counts them as stock."""
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=IN_TRANSIT_DAYS)).isoformat()
    out = {}
    try:
        rows = con.execute(
            "SELECT l.item, COALESCE(l.supplied, l.packs) AS got, l.pack_size, o.vendor, o.id AS oid, o.received_at "
            "FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
            "WHERE o.status='received' AND o.received_at >= ? AND COALESCE(l.supplied, l.packs) > 0", (since,)).fetchall()
    except Exception:                                      # noqa: BLE001
        return out
    for r in rows:
        seen = con.execute(
            "SELECT 1 FROM purchase_line l WHERE l.supplier_norm=? AND l.item=? AND l.bill_date >= ? AND " + EFF_LINE + " LIMIT 1",
            (supplier_key(r["vendor"]), r["item"], (r["received_at"] or "")[:10])).fetchone()
        if seen:
            continue
        k = norm(r["item"])
        e = out.setdefault(k, dict(units=0, order_id=r["oid"], vendor=r["vendor"]))
        e["units"] += int(r["got"]) * int(r["pack_size"] or 1)
    return out


# ====================================================================== S225 rev 10: new items, recorded and highlighted
# The owner (spec §6): "new medicines added should be recorded and highlighted to me". An item first seen in a
# purchase export after the pharmacy's earliest stock snapshot on this server, or in a stock snapshot without ever
# having been in an earlier one, is logged once (first seen, where, which stockist) and the hub shows this month's
# count with the list. The log is the record; a row is never rewritten once written.
def _ensure_new_items(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_new_item (
        item_norm  TEXT PRIMARY KEY,
        item       TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        seen_in    TEXT NOT NULL,
        supplier   TEXT,
        packing    TEXT,
        logged_at  TEXT NOT NULL,
        note       TEXT)""")
    con.commit()


def _known_items(con):
    """Every item the server already knew: any stock snapshot before the newest one, and any purchase line
    dated before this month. Items in the earliest snapshot are the baseline -- nothing there is 'new'."""
    known = set()
    if _table_exists(con, "stock_snapshot"):
        dates = sorted({r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=_as_on_key)
        for d in dates[:-1] if len(dates) > 1 else dates:
            for r in con.execute("SELECT item FROM stock_snapshot WHERE as_on=?", (d,)):
                known.add(norm(r[0]))
    for r in con.execute("SELECT item_norm FROM purchase_new_item"):
        known.add(r[0])
    return known


def _log_new_items(con, month=None):
    """Find and log items not seen before. Idempotent: an item is logged once. Returns the rows logged now."""
    _ensure_new_items(con)
    month = month or dt.date.today().strftime("%Y-%m")
    known = _known_items(con)
    logged = []
    # purchase lines this month
    try:
        rows = con.execute(
            "SELECT l.item, l.packing, l.supplier_norm, MIN(l.bill_date) AS first FROM purchase_line l WHERE " + EFF_LINE +
            " AND l.bill_date >= ? GROUP BY l.item ORDER BY first", (month + "-01",)).fetchall()
    except Exception:                                      # noqa: BLE001
        rows = []
    names = {r[0]: r[1] for r in con.execute("SELECT supplier_norm, MAX(supplier) FROM purchase_bill GROUP BY supplier_norm")}
    for r in rows:
        k = norm(r["item"])
        if k in known:
            continue
        con.execute("INSERT OR IGNORE INTO purchase_new_item (item_norm,item,first_seen,seen_in,supplier,packing,logged_at) "
                    "VALUES (?,?,?,?,?,?,?)", (k, r["item"], r["first"] or month + "-01", "purchase",
                                               names.get(r["supplier_norm"]) or r["supplier_norm"] or "", r["packing"] or "", now_iso()))
        known.add(k)
        logged.append(r["item"])
    # the newest snapshot vs the ones before it
    if _table_exists(con, "stock_snapshot"):
        dates = sorted({x[0] for x in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=_as_on_key)
        if len(dates) > 1:
            newest = dates[-1]
            for r in con.execute("SELECT item, packing FROM stock_snapshot WHERE as_on=?", (newest,)):
                k = norm(r[0])
                if k in known:
                    continue
                d = newest
                try:
                    d = dt.datetime.strptime(newest, "%d-%m-%Y").date().isoformat()
                except ValueError:
                    pass
                con.execute("INSERT OR IGNORE INTO purchase_new_item (item_norm,item,first_seen,seen_in,supplier,packing,logged_at) "
                            "VALUES (?,?,?,?,?,?,?)", (k, r[0], d, "stock", "", r[1] or "", now_iso()))
                known.add(k)
                logged.append(r[0])
    if logged:
        _audit(con, "system", "new_items", "", dict(n=len(logged), month=month))
    con.commit()
    return logged


def _new_items_card(con, prefix, month=None):
    month = month or dt.date.today().strftime("%Y-%m")
    try:
        _log_new_items(con, month)
        rows = con.execute("SELECT * FROM purchase_new_item WHERE first_seen >= ? ORDER BY first_seen DESC, item",
                           (month + "-01",)).fetchall()
    except Exception:                                      # noqa: BLE001
        return ""
    if not rows:
        return ('<div class="card"><h2>New items</h2><div class="kv" style="max-width:240px"><b>0</b>'
                '<span>new medicines this month</span></div></div>')
    lis = "".join('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td class="muted">%s</td></tr>'
                  % (_esc(r["item"]), _esc(_human(r["first_seen"])), _esc(r["supplier"] or "—"), _esc(r["packing"] or ""),
                     "first bought" if r["seen_in"] == "purchase" else "first on the shelf") for r in rows)
    return ('<div class="card"><h2>New items</h2><div class="kv" style="max-width:240px"><b>%d</b>'
            '<span>new medicine%s this month — first seen on this server</span></div>'
            '<div class="scroll"><table><tr><th>Item</th><th>First seen</th><th>Stockist</th><th>Packing</th><th></th></tr>%s</table></div>'
            '<div class="muted">The salt of a new item is not yet on this server (Amir\'s salt list, §8 item 6, is owed) — the item is '
            'listed here so it is not missed.</div></div>' % (len(rows), "" if len(rows) == 1 else "s", lis))


# ====================================================================== S225 rev 11: Amir's salt WORK LIST, server-side
# The owner (spec §6): "Amir's salt correction list should be available as Excel download with him and me, and A4 print
# also". His answers of 28-Aug (S207) already turned the 154 suspects into a WORK LIST for Amir -- rename 2 salts, create
# 38, change 77 items, 7 waiting on the doctor, 1 cleanup; 68 were already right and are not asked again. THAT list is
# what lives here: pushed once from D:\Downloads\Sanjeevni_Salt_Fix_for_Amir.xlsx (push_salts.py), then Amir ticks each
# row DONE on the page (audited, with his name), the doctor answers the 7 waiting rows, and Excel / A4 are made from the
# record. A later push never un-ticks a row or overwrites an answer.
SALT_USERS_KEY = "purchase.salt_users"
SALT_SECTIONS = (("rename", "1 · Rename these salts first", ("Old name (in Marg now)", "Rename it to", "Why")),
                 ("create", "2 · Create these salt names (exact spelling)", ("Salt name to create", "Items needing it", "Which items")),
                 ("change", "3 · Change the salt on these items", ("Item", "Salt now (wrong)", "Change to")),
                 ("waiting", "4 · Waiting on Dr Manoj — the correct salt", ("Item", "Salt Marg has now", "Correct salt")),
                 ("cleanup", "5 · Cleanups", ("What", "What to do", "")))


def _ensure_salts(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_salt_task (
        id         INTEGER PRIMARY KEY,
        section    TEXT NOT NULL,
        seq        INTEGER NOT NULL,
        a          TEXT NOT NULL,
        b          TEXT,
        c          TEXT,
        done       INTEGER NOT NULL DEFAULT 0,
        done_by    TEXT,
        done_at    TEXT,
        answer     TEXT,
        answer_by  TEXT,
        answer_at  TEXT,
        source_md5 TEXT,
        pushed_at  TEXT,
        UNIQUE(section, a))""")
    con.execute("CREATE TABLE IF NOT EXISTS purchase_salt_name (salt TEXT PRIMARY KEY)")
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_salt_marg (
        item_norm TEXT PRIMARY KEY, item TEXT NOT NULL, salt TEXT NOT NULL, as_on TEXT NOT NULL, source_md5 TEXT)""")
    con.execute("DELETE FROM purchase_salt_task WHERE section IN ('rename','create','change') AND (b IS NULL OR b='')")   # 11b: note lines are not tasks
    con.commit()


def _store_marg_salts(con, b):
    """The fresh SALT WISE ITEM LIST from Marg: item -> salt, as on a date. Replaces the previous list whole."""
    rows = b.get("marg_items")
    if not isinstance(rows, list) or not rows:
        return 0
    as_on = str(b.get("marg_as_on") or dt.date.today().isoformat())[:10]
    con.execute("DELETE FROM purchase_salt_marg")
    n = 0
    for r in rows:
        if not isinstance(r, dict) or not str(r.get("item") or "").strip() or not str(r.get("salt") or "").strip():
            continue
        con.execute("INSERT OR REPLACE INTO purchase_salt_marg (item_norm,item,salt,as_on,source_md5) VALUES (?,?,?,?,?)",
                    (norm(r["item"]), str(r["item"]).strip()[:120], str(r["salt"]).strip().upper()[:120], as_on, str(b.get("marg_md5") or "")[:32]))
        n += 1
    _audit(con, "push_salts", "salts_marg", str(b.get("marg_md5") or "")[:8], dict(items=n, as_on=as_on))
    con.commit()
    return n


def _marg_says(con, task, marg, salts_present):
    """One honest word from Marg's own list for a task: what it shows today."""
    if not marg:
        return ("", "")
    sec, a, b = task["section"], (task["a"] or "").upper(), (task["b"] or "").upper()
    if sec == "rename":
        if b in salts_present and a not in salts_present:
            return ("done", "renamed")
        return ("not yet", "old name still in Marg" if a in salts_present else "neither name in Marg")
    if sec == "create":
        return ("done", "salt exists") if a in salts_present else ("not yet", "salt not in Marg")
    if sec == "change":
        now = marg.get(norm(a))
        if now is None:
            return ("", "item not in Marg's list")
        return ("done", "now " + now) if now == (task["c"] or "").upper() else ("not yet", "still " + now)
    if sec == "waiting":
        now = marg.get(norm(a))
        return ("", "Marg has it under " + now) if now else ("", "item not in Marg's list")
    return ("", "")


def _salt_allowed(u, con):
    """The doctor always; otherwise only a login named in setting purchase.salt_users (seeded 'amir'). Fail-closed."""
    if _is_doctor(u):
        return True
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (SALT_USERS_KEY,)).fetchone()
    except Exception:                                      # noqa: BLE001
        return False
    allow = set(p.strip().lower() for p in re.split(r"[,;\s]+", str((r[0] if r else "") or "")) if p.strip())
    who = str(_who(u) or "").strip().lower()
    return bool(who) and who in allow


def _store_salts(con, b):
    """Store the work list's rows and the salt names. A DONE tick or an answer already on the server wins.
    Returns (stored, kept)."""
    tasks, salts = b.get("tasks"), b.get("salts")
    n = kept = 0
    for tsk in (tasks if isinstance(tasks, list) else []):
        if not isinstance(tsk, dict) or tsk.get("section") not in [s[0] for s in SALT_SECTIONS] or not str(tsk.get("a") or "").strip():
            continue
        sec, a = tsk["section"], str(tsk["a"]).strip()[:160]
        if sec in ("rename", "create", "change") and not str(tsk.get("b") or "").strip():
            continue                                                  # 11b: a note line, not a task
        row = con.execute("SELECT done, answer FROM purchase_salt_task WHERE section=? AND a=?", (sec, a)).fetchone()
        if row and (row[0] or (row[1] or "")):
            kept += 1
        con.execute("INSERT INTO purchase_salt_task (section,seq,a,b,c,source_md5,pushed_at) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(section,a) DO UPDATE SET seq=excluded.seq, b=excluded.b, c=excluded.c, source_md5=excluded.source_md5, pushed_at=excluded.pushed_at",
                    (sec, int(tsk.get("seq") or 0), a, str(tsk.get("b") or "")[:200], str(tsk.get("c") or "")[:200],
                     str(b.get("source_md5") or "")[:32], now_iso()))
        n += 1
    for s in (salts if isinstance(salts, list) else []):
        s = str(s or "").strip()[:120]
        if s:
            con.execute("INSERT OR IGNORE INTO purchase_salt_name (salt) VALUES (?)", (s,))
    _audit(con, "push_salts", "salts", str(b.get("source_md5") or "")[:8], dict(tasks=n, kept=kept, salts=len(salts or [])))
    con.commit()
    return n, kept


@bp.route("/api/salts", methods=["POST"])
def api_salts():
    u, err = _machine_auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    if not (isinstance(b.get("tasks"), list) and b.get("tasks")) and not (isinstance(b.get("marg_items"), list) and b.get("marg_items")):
        return jsonify(ok=False, error="malformed", reason="tasks or marg_items must be a non-empty list"), 400
    con = _db()
    _ensure(con)
    _ensure_salts(con)
    n = kept = 0
    if isinstance(b.get("tasks"), list) and b.get("tasks"):
        n, kept = _store_salts(con, b)
    m = _store_marg_salts(con, b)
    return jsonify(ok=True, stored=n, kept=kept, marg_items=m)


@bp.route("/api/salt_task", methods=["POST"])
def api_salt_task():
    """Amir (or the doctor) ticks a row DONE (or un-ticks it, with a note); the doctor answers a WAITING row."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _ensure_salts(con)
    if not _salt_allowed(u, con):
        return _refuse("The salt list is for Dr Manoj and Amir.")
    b = request.get_json(silent=True) or {}
    tid = _int_or_none(b.get("id"))
    row = con.execute("SELECT * FROM purchase_salt_task WHERE id=?", (tid,)).fetchone() if tid else None
    if row is None:
        return jsonify(ok=False, error="no_such_task"), 404
    action = str(b.get("action") or "")
    if action == "done":
        done = 1 if b.get("done") in (True, 1, "1", "true", "on") else 0
        con.execute("UPDATE purchase_salt_task SET done=?, done_by=?, done_at=? WHERE id=?",
                    (done, _who(u) if done else None, now_iso() if done else None, tid))
        _audit(con, _who(u), "salt_done" if done else "salt_undone", tid, dict(section=row["section"], a=row["a"]))
        con.commit()
        return jsonify(ok=True, done=done)
    if action == "answer":
        if not _is_doctor(u):
            return _refuse("Only Dr Manoj answers a waiting row.")
        if row["section"] != "waiting":
            return jsonify(ok=False, error="not_waiting", message="Only a WAITING row takes an answer."), 409
        ans = str(b.get("answer") or "").strip()[:120]
        if not ans:
            return jsonify(ok=False, error="malformed", message="pick or type the correct salt"), 400
        con.execute("INSERT OR IGNORE INTO purchase_salt_name (salt) VALUES (?)", (ans,))
        con.execute("UPDATE purchase_salt_task SET answer=?, answer_by=?, answer_at=? WHERE id=?", (ans, _who(u), now_iso(), tid))
        _audit(con, _who(u), "salt_answer", tid, dict(a=row["a"], answer=ans, was=row["answer"] or ""))
        con.commit()
        return jsonify(ok=True, answer=ans)
    return jsonify(ok=False, error="malformed", message="action done|answer"), 400


def _salt_tasks(con):
    return [dict(r) for r in con.execute("SELECT * FROM purchase_salt_task ORDER BY section, seq, id").fetchall()]


SALT_JS = """
async function saltDone(id, box){ const j = await post(P + '/api/salt_task', {action:'done', id:id, done: box.checked}); if (!j) box.checked = !box.checked; else location.reload(); }
async function saltAnswer(id){ const el = document.getElementById('ans' + id); const j = await post(P + '/api/salt_task', {action:'answer', id:id, answer: el.value}); if (j) location.reload(); }
"""


@bp.route("/page/salts")
def page_salts():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _ensure_salts(con)
    if not _salt_allowed(u, con):
        return _refuse("The salt list is for Dr Manoj and Amir.")
    doctor = _is_doctor(u)
    prefix = request.script_root + _url_prefix
    tasks = _salt_tasks(con)
    names = [r[0] for r in con.execute("SELECT salt FROM purchase_salt_name ORDER BY salt")]
    dl = "".join("<option value=\"%s\">" % _esc(s) for s in names)
    marg = {r[0]: r[1] for r in con.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
    marg_as_on = con.execute("SELECT MAX(as_on) FROM purchase_salt_marg").fetchone()[0] if marg else None
    salts_present = set(marg.values())
    cards = []
    total = done_n = marg_done = 0
    for key, title, cols in SALT_SECTIONS:
        rows = [tk for tk in tasks if tk["section"] == key]
        if not rows:
            continue
        d = sum(1 for tk in rows if tk["done"])
        total += len(rows); done_n += d
        trs = []
        for tk in rows:
            if key == "waiting":
                third = ('<b class="ok">%s</b> <small class="muted">by %s</small>' % (_esc(tk["answer"]), _esc(tk["answer_by"] or ""))) if tk["answer"] else (
                    ('<input id="ans%d" list="salts" placeholder="pick or type" style="width:14em"> <button class="sm p" onclick="saltAnswer(%d)">Save</button>' % (tk["id"], tk["id"]))
                    if doctor else '<span class="muted">waits for Dr Manoj</span>')
            else:
                third = _esc(tk["c"] or "")
            ms, mtxt = _marg_says(con, tk, marg, salts_present)
            if ms == "done":
                marg_done += 1
            mcell = ('<span class="chip ok">Marg: done</span>' if ms == "done" else ('<span class="chip warn">Marg: not yet</span>' if ms == "not yet" else "")) + \
                    ((' <small class="muted">%s</small>' % _esc(mtxt)) if mtxt else "")
            trs.append('<tr%s><td class="noprint"><input type="checkbox"%s onchange="saltDone(%d,this)"></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                       '<td><small class="muted">%s</small></td></tr>'
                       % (' class="done"' if tk["done"] else "", " checked" if tk["done"] else "", tk["id"], _esc(tk["a"]), _esc(tk["b"] or ""), third, mcell,
                          ("done by %s · %s" % (_esc(tk["done_by"] or ""), _esc(_hhmm_ist_full(tk["done_at"] or "")))) if tk["done"] else ""))
        cards.append('<div class="card"><h2>%s <span class="chip">%d / %d ticked</span></h2><div class="scroll"><table><tr><th class="noprint">Done</th><th>%s</th><th>%s</th><th>%s</th><th>Marg says%s</th><th></th></tr>%s</table></div></div>'
                     % (_esc(title), d, len(rows), _esc(cols[0]), _esc(cols[1]), _esc(cols[2]), (" <small>(list of %s)</small>" % _esc(_human(marg_as_on))) if marg_as_on else "", "".join(trs)))
    body = ('<h1>Salt corrections — Amir\'s work list</h1><div class="muted">Dr Manoj\'s answers of 28-Aug, as a list to work through in order. '
            '<b>%d of %d ticked</b>%s. Tick a row when it is done in Marg — your name and the time are recorded; the <b>Marg says</b> column is '
            'Marg\'s own salt list, read back, so a tick and Marg can be compared. '
            '<a href="%s/salts.xlsx"><button class="sm noprint">Download Excel</button></a> '
            '<a href="%s/salts.pdf" target="_blank"><button class="sm noprint">Print A4</button></a></div>'
            '<datalist id="salts">%s</datalist>%s<style>tr.done td{color:var(--muted);text-decoration:line-through} tr.done td:first-child,tr.done td:last-child{text-decoration:none}</style>'
            % (done_n, total, (" · <b>Marg confirms %d</b> done in its list of %s" % (marg_done, _esc(_human(marg_as_on)))) if marg_as_on else " (no Marg list pushed yet)", prefix, prefix, dl,
               "".join(cards) or '<div class="card muted">Nothing pushed yet — run push_salts.py on manojz.</div>'))
    return _page("Salt corrections", body, SALT_JS)


def _xlsx_bytes(sheets):
    """A minimal .xlsx with nothing but the standard library (inline strings). sheets = [(name, header, rows), ...]."""
    import zipfile
    from xml.sax.saxutils import escape as x
    def col(n):
        s = ""
        while True:
            s = chr(65 + n % 26) + s
            n = n // 26 - 1
            if n < 0:
                return s
    def sheet_xml(header, rows):
        out = []
        for i, r in enumerate([header] + list(rows)):
            cells = "".join('<c r="%s%d" t="inlineStr"><is><t>%s</t></is></c>' % (col(j), i + 1, x(str("" if v is None else v))) for j, v in enumerate(r))
            out.append('<row r="%d">%s</row>' % (i + 1, cells))
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData>%s</sheetData></worksheet>' % "".join(out))
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>%s</sheets></workbook>'
          % "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (x(n[:31]), i + 1, i + 1) for i, (n, _h, _r) in enumerate(sheets)))
    wb_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>'
               % "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1) for i in range(len(sheets))))
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>%s</Types>'
          % "".join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(len(sheets))))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("xl/workbook.xml", wb); z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        for i, (_n, h, r) in enumerate(sheets):
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), sheet_xml(h, r))
    return buf.getvalue()


def _salt_sheets(con):
    tasks = _salt_tasks(con)
    out = []
    for key, title, cols in SALT_SECTIONS:
        rows = [tk for tk in tasks if tk["section"] == key]
        if not rows:
            continue
        hdr = (cols[0], cols[1], cols[2] or "", "Done", "Done by", "Done at") if key != "waiting" else (cols[0], cols[1], "Correct salt (Dr Manoj)", "Answered by", "Answered at", "Done")
        body = []
        for tk in rows:
            if key == "waiting":
                body.append((tk["a"], tk["b"] or "", tk["answer"] or "", tk["answer_by"] or "", _hhmm_ist_full(tk["answer_at"]) if tk["answer_at"] else "", "DONE" if tk["done"] else ""))
            else:
                body.append((tk["a"], tk["b"] or "", tk["c"] or "", "DONE" if tk["done"] else "", tk["done_by"] or "", _hhmm_ist_full(tk["done_at"]) if tk["done_at"] else ""))
        out.append((title.split("·", 1)[-1].strip()[:31], hdr, body))
    return out


def _salt_guard():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return None, None, err
    con = _db()
    _ensure(con)
    _ensure_salts(con)
    if not _salt_allowed(u, con):
        return None, None, _refuse("The salt list is for Dr Manoj and Amir.")
    return u, con, None


@bp.route("/salts.xlsx")
def salts_xlsx():
    u, con, err = _salt_guard()
    if err:
        return err
    sheets = _salt_sheets(con) or [("Salt corrections", ("nothing pushed yet",), [])]
    return _xlsx_bytes(sheets), 200, {"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                      "Content-Disposition": 'attachment; filename="Sanjeevni_Salt_Fix_for_Amir_%s.xlsx"' % dt.date.today().isoformat(),
                                      "Cache-Control": "no-store"}


@bp.route("/salts.pdf")
def salts_pdf():
    u, con, err = _salt_guard()
    if err:
        return err
    try:
        import clinic_day_pdf as cdp
    except ImportError:
        return jsonify(ok=False, error="no_pdf_writer", message="clinic_day_pdf.py (S224) is not beside this app."), 501
    L, R, TOP, BOT = 30.0, 565.28, 805.0, 40.0
    pdf = cdp._PDF("Salt corrections")
    state = {"pg": 0, "y": 0}
    def new_page():
        state["pg"] += 1
        pdf.new_page()
        pdf.text(L, TOP - 14, "Sanjeevni Medicos — salt corrections, Amir's work list (Dr Manoj's answers of 28-Aug-2026)", 11, bold=True)
        pdf.text(R, TOP - 14, "%s · page %d" % (dt.date.today().strftime("%d-%b-%Y"), state["pg"]), 9, align="r", gray=0.35)
        state["y"] = TOP - 36
    new_page()
    tasks = _salt_tasks(con)
    for key, title, cols in SALT_SECTIONS:
        rows = [tk for tk in tasks if tk["section"] == key]
        if not rows:
            continue
        if state["y"] < BOT + 40:
            new_page()
        pdf.text(L, state["y"], title, 10.5, bold=True)
        state["y"] -= 14
        pdf.text(L + 14, state["y"], cols[0].upper(), 7.5, bold=True, gray=0.35); pdf.text(230, state["y"], cols[1].upper(), 7.5, bold=True, gray=0.35)
        pdf.text(400, state["y"], (cols[2] or "").upper(), 7.5, bold=True, gray=0.35)
        pdf.line(L, state["y"] - 3, R, state["y"] - 3, 0.4, 0.6)
        state["y"] -= 13
        for tk in rows:
            if state["y"] < BOT + 10:
                new_page()
            pdf.text(L, state["y"], "[x]" if tk["done"] else "[ ]", 8.5, bold=True, gray=0.2 if tk["done"] else 0.0)
            pdf.text(L + 14, state["y"], cdp._fit(tk["a"], 8.5, 210), 8.5, bold=not tk["done"], gray=0.45 if tk["done"] else 0.0)
            pdf.text(230, state["y"], cdp._fit(tk["b"] or "", 8, 165), 8, gray=0.45 if tk["done"] else 0.1)
            third = tk["answer"] or "________________" if key == "waiting" else (tk["c"] or "")
            pdf.text(400, state["y"], cdp._fit(third, 8.5, 160), 8.5, bold=(key == "waiting" and bool(tk["answer"])) or key == "change", gray=0.45 if tk["done"] else 0.0)
            state["y"] -= 12
        state["y"] -= 10
    return pdf.build(), 200, {"Content-Type": "application/pdf", "Cache-Control": "no-store", "Content-Disposition": 'inline; filename="salt_corrections.pdf"'}
