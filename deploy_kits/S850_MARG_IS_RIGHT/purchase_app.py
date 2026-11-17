#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
purchase_app.py -- S224: Marg's purchases, on the box.  (rev 14, S380 / Session 281, 23-Sep-2026)

REV 14 (S380, 23-Sep, F-616 / D605 -- the owner, having finalised August and printed it: "Only the
vendor payment sheet came out, remaining five pages were blank. The check letter did not get printed and
in the payment details sheet in the lower part, my signature line, name, etc. part is also missing").
The month's papers are now ONE PACK, printed from one button at /page/pay/<month>/pack: the covering
letter (portrait), the annexure the bank gets (landscape), the payment sheet (portrait), each on its own
sheet and nothing blank between them. The annexure and the sheet carry For SANJEEVNI MEDICOS / Authorized
Signatory / <name>. The pay page's own print emits the annexure alone, collapsed with display:none so it
can no longer leave five empty sheets behind it. The letter's date, cheque number and the signatory name
stay typable after FINAL -- they are the letter's words, never a figure of the month.

REV 13 (S371, 22-Sep, F-614 -- the owner: "add 6 rupees in kedar and 39 in lk, and it will be final"):
    a bill marked WRONG resolves ITSELF when Marg's next bill-wise or supplier-wise export carries the
    amount that was marked right (within Rs 1) -- verdict CORRECT, reason names the export, audit row
    'verdict_resolved'. And a WRONG bill keeps its Correct button until the month is final, so a person can
    always clear it by hand. Before this, the button left with the disagreement and the month could never
    finalise.

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
import hmac                                            # S258


def _tok_ok(given, expected):
    """S258: constant-time token compare (F-470). False when either side is empty."""
    try:
        return bool(expected) and bool(given) and hmac.compare_digest(str(given), str(expected))
    except Exception:                                  # noqa: BLE001
        return False
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
    # S407 (D623): the NEFT-messages module rides on this app; fail-soft -- the purchase book never waits for it
    try:
        import supplier_msg                                        # noqa: PLC0415
        supplier_msg.init(app, db_getter, require_fn, unit=unit, url_prefix=url_prefix)
    except Exception as _ex_sm:                                    # noqa: BLE001
        import sys as _sys                                         # noqa: PLC0415
        print("supplier_msg NOT mounted: %s" % _ex_sm, file=_sys.stderr)
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


# S533 (A4): the DAY of a purchase_export row, from Marg's own stamp (YYYYMMDD-HHMMSS) or else its received_at -- the ONE
# expression (amir_day reads it from here); {p} is the table alias prefix ('' or 'e.').
EXPORT_DAY_SQL = ("CASE WHEN {p}export_stamp GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-*' THEN substr({p}export_stamp,1,4)||'-'||"
                  "substr({p}export_stamp,5,2)||'-'||substr({p}export_stamp,7,2) ELSE substr(COALESCE({p}export_stamp, {p}received_at), 1, 10) END")


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
    # S533 (A4): a bill's FIRST SIGHT -- the Marg-stamp day of the first purchase export (of any type) that carried it, set by
    # _store_bills on insert. The bills already here are back-filled once from the bill-wise export their row still names (the
    # only day the data holds), else their bill date.
    if "first_seen_day" not in have:
        con.execute("ALTER TABLE purchase_bill ADD COLUMN first_seen_day TEXT")
    con.execute("UPDATE purchase_bill SET first_seen_day = COALESCE((SELECT " + EXPORT_DAY_SQL.format(p="e.") + " FROM purchase_export e "
                "WHERE e.md5 = purchase_bill.bw_md5), substr(bill_date, 1, 10)) WHERE first_seen_day IS NULL")
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
    if _tok_ok(request.headers.get("X-Finance-Marg"), _marg_token):             # S258
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


# ---- S795_PART_EXPORT_GUARD (12-Nov-2026, Sanjeevni session 434): a part list may not retire a fuller export ----
# 11-Nov-2026: two bill-wise reports of 1-11 Nov arrived 15 seconds apart -- 29 bills, then 4.  "Same period, the later stamp
# wins" let the 4-bill list retire the 29-bill one, and 25 of the month's bills stopped being effective (the scan pairing said
# "no bill on the server yet" for bills that were there).  A report with fewer than half the rows of a live, older report it
# would retire -- and more than two rows short of it -- is a PART list: it is kept, marked as retired by that fuller report,
# and nothing is read from it.  The next full report retires the older one as before.
S795_HALF = 0.5
S795_GAP = 2


def _s795_fuller(con, typ, pf, pt, stamp, n_rows):
    """The md5 of the live, older export of this type inside this period that the incoming one is only a PART of, or None."""
    try:
        r = con.execute(
            "SELECT md5, COALESCE(n_rows, 0) FROM purchase_export WHERE type=? AND period_from>=? AND period_to<=? "
            "AND superseded_by IS NULL AND export_stamp<? ORDER BY COALESCE(n_rows, 0) DESC, export_stamp DESC LIMIT 1",
            (typ, pf, pt, stamp)).fetchone()
    except Exception:                                          # noqa: BLE001 -- a push never fails for this
        return None
    if not r:
        return None
    big = int(r[1] or 0)
    return r[0] if (n_rows < S795_HALF * big and big - n_rows > S795_GAP) else None
# ---- end S795_PART_EXPORT_GUARD (the function) ----


@bp.route("/api/push", methods=["POST"])
def api_push():
    u, err = _machine_auth()
    if err:
        return err
    b = request.get_json(silent=True)
    if not isinstance(b, dict):
        return jsonify(ok=False, error="malformed", reason="body is not a JSON object"), 400
    if str(b.get("type") or "").upper() == "SALE_BILL":
        # S240 (Sanjeevni item 3): the sale bill's own money row, sent by push_sale_bills.py on
        # manojz. Handled entirely by sale_bill_door -> sale_bill.py; touches no purchase table.
        import sale_bill_door
        out, code = sale_bill_door.handle(_db(), b, _unit, now_iso())
        return jsonify(out), code
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
    part_of = _s795_fuller(con, typ, pf, pt, stamp, len(rows))    # S795: a part list is kept, never counted, retires nothing
    if part_of:
        con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,"
                    "export_stamp,received_at,n_rows,grand_amount_p,superseded_by) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (md5, typ, str(b.get("file") or "")[:200], pf, pt, stamp, now_iso(),
                     len(rows), _int_or_none(b.get("grand_amount_p")), part_of))
        con.commit()
        return jsonify(ok=True, stored=False, reason="part_export")
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
    try:                                                       # S773 (F-1233): a bill number Marg fused onto the item name,
        import purchase_unspill                                # noqa: PLC0415 -- split off by evidence (a real bill of the
        purchase_unspill.unspill(con, by="push")               # same supplier), logged; beside this file
    except Exception as _ex_s773:                              # noqa: BLE001 -- never fails a push: the lines stay as they came
        if not con.in_transaction:                             # ...unless the push's own writes were lost with it: never "stored"
            raise
        import sys as _sys_s773                                # noqa: PLC0415
        print("purchase_unspill skipped: %s" % _ex_s773, file=_sys_s773.stderr)
    _redate_lines(con)
    if typ in ("BILLWISE", "SUPPLIERWISE"):
        _resolve_wrong(con, md5=md5, stamp=stamp)                  # S371 (F-614)
    _audit(con, "push_purchases", "push", md5, dict(type=typ, period=[pf, pt], rows=n,
                                                     superseded=[r[0] for r in rivals]))
    con.commit()
    _rematch_after_push(con)                                   # S225 rev 9: live, not nightly
    return jsonify(ok=True, stored=True, reason="new", rows=n)


class _Malformed(Exception):
    pass


def _resolve_wrong(con, md5=None, stamp=None, who="marg re-export"):
    """S371 (F-614): every WRONG bill whose live Marg amount is now the amount marked right becomes
    CORRECT. Limited to the bills the export `md5` touched when given; over every WRONG bill otherwise.
    Returns the resolved bills as (id, supplier, bill_no, amount_p)."""
    q = ("SELECT b.id, b.supplier, b.bill_no, b.amount_p, b.wrong_amount_p, b.bw_amount_p, b.sw_amount_p, "
         "b.bw_md5, b.sw_md5, b.month FROM purchase_bill b WHERE b.verdict='WRONG' AND b.wrong_amount_p IS NOT NULL")
    args = ()
    if md5:
        q += " AND (b.bw_md5=? OR b.sw_md5=?)"
        args = (md5, md5)
    out = []
    for r in con.execute(q, args).fetchall():
        st = _month_status(con, r["month"] or "")
        if st["status"] == "final":
            continue
        live = con.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL AND md5 IN (?,?)",
                           (r["bw_md5"] or "", r["sw_md5"] or "")).fetchall()
        live = {x[0] for x in live}
        sw = r["sw_amount_p"] if (r["sw_md5"] in live and r["sw_amount_p"] is not None) else None
        bw = r["bw_amount_p"] if (r["bw_md5"] in live and r["bw_amount_p"] is not None) else None
        now_p = sw if sw is not None else (bw if bw is not None else r["amount_p"])
        if now_p is None or abs(int(now_p) - int(r["wrong_amount_p"])) > AGREE_P:
            continue
        reason = "resolved: Marg's re-export%s carries %s, the amount marked right" % (
            (" " + stamp) if stamp else "", _r(int(now_p)))
        con.execute("UPDATE purchase_bill SET verdict='CORRECT', verdict_by=?, verdict_at=?, reason=? WHERE id=?",
                    (who, now_iso(), reason, r["id"]))
        _audit(con, who, "verdict_resolved", r["id"],
               dict(before="WRONG", wrong_amount_p=r["wrong_amount_p"], now_p=int(now_p), export=md5, stamp=stamp))
        out.append((r["id"], r["supplier"], r["bill_no"], int(now_p)))
    return out


_S604_TWIN_RE = re.compile(r"^twin of bill (\d+)\b")
_S604_KEY_TABLES = ("purchase_line", "amir_bill_answer", "amir_bill_disposition", "amir_self_wait", "amir_claim")


def _s604_carries(con, key, bno):
    """S604: the first table that names the bill (supplier key, bill number), or '' -- a missing table names nothing.
    purchase_scan_alias carries no bill number: any alias on the key counts."""
    for t in _S604_KEY_TABLES:
        try:
            if con.execute("SELECT 1 FROM %s WHERE supplier_norm=? AND bill_no=? LIMIT 1" % t, (key, bno)).fetchone():
                return t
        except sqlite3.Error:
            continue
    try:
        if con.execute("SELECT 1 FROM purchase_scan_alias WHERE supplier_norm=? LIMIT 1", (key,)).fetchone():
            return "purchase_scan_alias"
    except sqlite3.Error:
        pass
    return ""


def _s604_bill_lookup(con, typ, md5, key, bno, d, amount_p):
    """S604 (F-955) -- the rows _store_bills matches an incoming bill against, as (id, bill_date, date_src, supplier).
    1. The exact key (supplier_norm, bill_no), as before -- but a row retired as 'twin of bill N' (both report columns empty) is
       read as bill N: a re-export carrying the clipped name lands on the real bill and never revives the twin.
    2. No live row has the exact key: the ONE row of the same bill number and date whose OTHER report carries the same amount,
       whose column for THIS report is empty or holds another export (a re-export), and whose key is a word-boundary prefix of
       the incoming one or the other way round -- Marg's supplier-wise report clips a 32-letter name ('BASS PHARMA DISTRIBUTORS
       PVT' | 'LTD29-09-2026'). It is joined, audited 'twin_joined'; a stored shorter key is renamed to the longer one only when
       nothing else names (short key, bill_no). The UPDATE branch of _store_bills then keeps the longer name and the bill-wise
       date, and never changes supplier_norm."""
    col = "bw_md5" if typ == "BILLWISE" else "sw_md5"
    ocol, oamt = ("sw_md5", "sw_amount_p") if typ == "BILLWISE" else ("bw_md5", "bw_amount_p")
    have = []
    for r in con.execute("SELECT id, bill_date, date_src, supplier, bw_md5, sw_md5, reason FROM purchase_bill "
                         "WHERE supplier_norm=? AND bill_no=?", (key, bno)).fetchall():
        m = _S604_TWIN_RE.match(r[6] or "") if (r[4] is None and r[5] is None) else None
        if m:
            real = con.execute("SELECT id, bill_date, date_src, supplier FROM purchase_bill WHERE id=?",
                               (int(m.group(1)),)).fetchone()
            if real is not None:
                have.append((real[0], real[1], real[2], real[3]))
                _audit(con, "push_purchases", "twin_joined", real[0],
                       dict(incoming=key, bill_no=bno, bill_date=d, md5=md5, type=typ, via="retired twin %d" % r[0]))
                continue
        have.append((r[0], r[1], r[2], r[3]))
    if have:
        return have
    cands = []
    for r in con.execute("SELECT id, bill_date, date_src, supplier, supplier_norm, %s, %s, %s FROM purchase_bill "
                         "WHERE bill_no=? AND bill_date=? AND supplier_norm<>?" % (oamt, ocol, col), (bno, d, key)).fetchall():
        other = r[4] or ""
        long_, short_ = (key, other) if len(key) > len(other) else (other, key)
        if not (short_ and long_.startswith(short_ + " ")):
            continue
        if r[5] is None or int(r[5]) != int(amount_p) or not r[6] or r[7] == md5:
            continue
        cands.append(r)
    if len(cands) != 1:
        return []
    r = cands[0]
    other, renamed, why = r[4], False, ""
    if len(key) > len(other):
        why = _s604_carries(con, other, bno)
        if not why:
            con.execute("UPDATE purchase_bill SET supplier_norm=? WHERE id=?", (key, r[0]))
            renamed = True
    _audit(con, "push_purchases", "twin_joined", r[0],
           dict(incoming=key, stored=other, bill_no=bno, bill_date=d, md5=md5, type=typ, renamed=renamed,
                kept_name=("%s names (%s, %s)" % (why, other, bno)) if why else ""))
    return [(r[0], r[1], r[2], r[3])]


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
        have = _s604_bill_lookup(con, typ, md5, key, bno, d, cash + credit)   # S604 (F-955): the exact key, a retired twin, a clipped name
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
            con.execute(("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,"
                         "month,cash_p,credit_p,amount_p,source_md5,%s,%s,date_src,first_seen_day) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,(SELECT " + EXPORT_DAY_SQL.format(p="") + " FROM purchase_export WHERE md5 = ?))")
                        % (col, amt),
                        (key, sup, bno, d, d[:7], cash, credit, cash + credit, md5, md5,
                         cash + credit, typ, md5))           # S533: first sight = the day of the export that first carried it
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
            k2 = con.execute("SELECT DISTINCT b.supplier_norm FROM purchase_bill b WHERE b.bill_no=? "     # S827: live bills only
                             "AND b.bill_date=? AND " + EFF_BILL, (bno, d)).fetchall()
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
    for r in con.execute("SELECT b.supplier_norm, b.bill_no, b.bill_date FROM purchase_bill b "     # S827 (F-1243): the bills of the
                         "WHERE b.bill_date IS NOT NULL AND " + EFF_BILL + " ORDER BY b.bill_date"):   # live exports only
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
    _line_owner_s282(con, by_no)
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
    s574_on = book_on(con)                                     # S574: switch ON -> into the one record, never a replace; OFF -> as before
    for name, phone in pairs.items():
        name = str(name or "").strip()
        if not name:
            continue
        if s574_on and _s574_push_one(con, name, phone):
            n += 1
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
    signed = []          # S604 (F-956 B): the bills whose positive lines count NEGATIVE -- Marg's own minus sign on the bill
    iw = 0
    for b in bills:
        t = _bill_lines(b, sets, stray)
        if t is None:
            no_lines.append(b)
            continue
        used.add((t["supplier_norm"], t["bill_no"]))
        net = t["net_p"]
        sg = b["marg_p"] < 0 and net > 0              # Marg prints a return's lines as a purchase; the bill carries the minus
        if sg:
            net = -net
            signed.append(b["id"])
        iw += net
        d = net - b["marg_p"]
        x = dict(bill=b, net_p=net, gross_p=t["gross_p"], n=t["n"], diff_p=d)
        if d > AGREE_P and not sg:
            returns.append(x)
        elif d < -AGREE_P or d > AGREE_P:             # a signed bill that still differs is offered a verdict, never a "return"
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
    wrong = [b for b in bills if b["verdict"] == "WRONG"]
    # S371 (F-614): a WRONG bill keeps its Correct button until the month is final
    needs_verdict = {x["bill"]["id"] for x in short} | {b["id"] for b in disagree} | {b["id"] for b in wrong}
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
                can_finalise=can, reasons=reasons, story=story, head=head, signed=signed)


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


# ====================================================================== S604: the month-end reports, and the ONE lock gate
# The owner, 20-Oct-2026 08:25: "The vendor payment kit should specifically ask for the final uploads of the REQUIRED purchase
# reports as text files and should give confirmation when these files are received by it." A report's arrival is its
# purchase_export row (read here only); a refusal is its mi_file row; the lock is _lock_gate (api_finalise, the month page's button
# and note, the hub's 'ready to finalise' and the card's green line all read it). _month_summary never calls any of these
# (_verify_statement calls _month_summary: a call back would recurse -- R1-B1).
_S604_REPORTS = (
    ("SUPPLIERWISE", ("SUPPLIERWISE",), "supplier-wise statement", "SUPPLIER WISE PURCHASE STATEMENT"),
    ("BILLWISE", ("BILLWISE",), "bill-wise statement", "BILL WISE PURCHASE STATEMENT"),
    ("ITEMS", ("ITEMWISE", "BILLITEMWISE"), "item lines", "SUPPLIER/ITEM WISE PURCHASE STATEMENT"),
)
_S604_REFUSED = "the medical PC refused it: PURCHASE text"
_S604_STOP_RE = re.compile(r"PURCHASE text -- the reader refused it \(line (\d+)\)$")


def _s604_last_day(month):
    """'2026-09' -> '2026-09-30' (the month's own last day; the old test was the 28th)."""
    return "%s-%02d" % (month, _days_in_month(month))


def _s604_dt(ts):
    """A stored time as a naive IST datetime: '+05:30' (mi_file) converted; naive (purchase_export, now_iso) read as IST."""
    try:
        d = dt.datetime.fromisoformat(str(ts).strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if d.tzinfo is not None:
        d = d.astimezone(IST).replace(tzinfo=None)
    return d


def _s604_dmy(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


def _s604_period(pf, pt):
    """('2026-09-01', '2026-09-30') -> '01\u201330 Sep'; across months '01 Sep\u201303 Oct'."""
    try:
        a, b = dt.date.fromisoformat(pf), dt.date.fromisoformat(pt)
    except (TypeError, ValueError):
        return "%s to %s" % (pf, pt)
    if (a.year, a.month) == (b.year, b.month):
        return "%02d\u2013%02d %s" % (a.day, b.day, a.strftime("%b"))
    return "%02d %s\u2013%02d %s" % (a.day, a.strftime("%b"), b.day, b.strftime("%b"))


def _month_reports(con, month, s=None):
    """S604 -- the three reports month M needs, one entry each, from purchase_export alone: the newest LIVE export whose period
    covers the 1st..the last day (supplier-wise, bill-wise: by export stamp, with its row count as bills; item lines: ITEMWISE or
    BILLITEMWISE, the newest arrival, and s['no_lines'] / s['gap_dates'] -- no row count). s = _month_summary(con, month) when
    given; computed only when not (never from inside _month_summary)."""
    if s is None:
        s = _month_summary(con, month)
    first, last = month + "-01", _s604_last_day(month)
    out = []
    for key, types, label, title in _S604_REPORTS:
        rows = [dict(r) for r in con.execute(
            "SELECT md5, type, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p FROM purchase_export "
            "WHERE type IN (%s) AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
            "ORDER BY export_stamp DESC, received_at DESC" % ",".join("?" * len(types)), tuple(types) + (first, last))]
        e = dict(key=key, label=label, title=title, first=first, last=last, state="not yet", export=None, covering=rows)
        if rows:
            pick = rows[0] if key != "ITEMS" else max(rows, key=lambda r: (_s604_dt(r["received_at"]) or dt.datetime.min))
            e.update(state="received", export=pick)
        if key == "ITEMS":
            e.update(no_lines=len(s["no_lines"]), gap_dates=list(s["gap_dates"]))
        out.append(e)
    return out


def _s604_refusal(con, month, reps):
    """The newest purchase refusal from the medical PC (mi_file REFUSED, 'the medical PC refused it: PURCHASE text ...') that came
    after the month's last day AND after the newest arrival among the three reports' covering exports -- times compared as
    parsed datetimes (+05:30 against naive IST). One plain line, or ''. The server cannot tell which report it was (type '')."""
    try:
        rows = con.execute("SELECT received_at, reason FROM mi_file WHERE verdict='REFUSED' AND reason LIKE ?",
                           (_S604_REFUSED + "%",)).fetchall()
    except sqlite3.Error:
        return ""
    last = dt.date.fromisoformat(_s604_last_day(month))
    got = [x for x in (_s604_dt(r["received_at"]) for e in reps for r in e["covering"]) if x is not None]
    newest = max(got) if got else None
    best = None
    for r in rows:
        t = _s604_dt(r[0])
        if t is None or t.date() <= last or (newest is not None and t <= newest):
            continue
        if best is None or t > best[0]:
            best = (t, str(r[1] or ""))
    if best is None:
        return ""
    t, reason = best
    at = t.strftime("%H:%M") + ("" if t.date() == dt.datetime.now(IST).date() else " on " + t.strftime("%d-%b"))
    m = _S604_STOP_RE.search(reason)
    if m:
        return ("The medical PC refused a purchase report at %s \u2014 it could not read it (line %s). Nothing for you to redo."
                % (at, m.group(1)))
    rest = reason[len(_S604_REFUSED):].strip().lstrip("-").strip()
    first = re.split(r" \(|;| -- ", rest, 1)[0].strip().rstrip(".") or "no reason given"
    return "The medical PC refused a purchase report at %s: %s." % (at, first)


def _lock_gate(con, month, s):
    """S604 -- THE lock gate, (can, reasons): _month_summary's own reasons, plus one per required report not received, plus --
    only when the supplier-wise statement is received -- the cross-check's first problem when it does not agree. s is
    _month_summary(con, month), computed by the caller; nothing here calls _month_summary (R1-B1). A FINAL month is not asked."""
    reasons = list(s["reasons"])
    reps = _month_reports(con, month, s)
    for e in reps:
        if e["state"] != "received":
            reasons.append("the %s for %s %s not reached the server"
                           % (e["label"], _s604_period(e["first"], e["last"]), "have" if e["key"] == "ITEMS" else "has"))
    if reps[0]["state"] == "received":
        v = _verify_statement(con, month, s)
        if not v["ok"]:
            reasons.append("the cross-check against the supplier-wise statement does not agree: %s"
                           % (v["problems"][0] if v["problems"] else "see the check on the payment page"))
    return (not reasons), reasons


def _story_gated(s, gate):
    """The hub's / month page's story with 'ready to finalise' only when the one gate is open."""
    st = s["story"]
    tail = "; ready to finalise."
    if s["can_finalise"] and not gate[0] and st.endswith(tail):
        st = st[:-len(tail)] + "; the lock waits for the month-end reports and the cross-check."
    return st


def _s604_reports_card(con, month, s, final):
    """The card at the top of /page/pay/<M> (owner English; whoever sees the page sees it)."""
    try:
        reps = _month_reports(con, month, s)
        refused = _s604_refusal(con, month, reps)
        gate = (False, []) if final else _lock_gate(con, month, s)
    except Exception as ex:                                        # noqa: BLE001
        return ('<!--s604card--><div class="card" id="s604reports"><h2>Month-end reports</h2><div class="muted">the reports card '
                'is unavailable (%s)</div></div><!--/s604card-->' % _esc(str(ex)[:120]))
    span = "FROM %s TO %s" % (_s604_dmy(reps[0]["first"]), _s604_dmy(reps[0]["last"]))
    lines = []
    for e in reps:
        x, cls = e["export"], ""
        if e["state"] == "received":
            txt = "Received %s \u00b7 %s" % (_hhmm_ist_full(x["received_at"]), _s604_period(x["period_from"], x["period_to"]))
            if e["key"] != "ITEMS":
                txt += " \u00b7 %s" % _plural(int(x["n_rows"] or 0), "bill")
            if e["key"] == "SUPPLIERWISE" and x["grand_amount_p"]:
                g = int(x["grand_amount_p"])
                if abs(g - s["marg_p"]) <= AGREE_P:
                    txt += " \u00b7 its total %s agrees with the sheet" % _r(g)
                else:
                    txt += " \u00b7 its total %s \u2014 the sheet adds up to %s (see the check below)" % (_r(g), _r(s["marg_p"]))
                    cls = "warn"
            if e["key"] == "ITEMS" and e["no_lines"]:
                txt += (" \u2014 but %s still %s no item lines (%s): export %s, %s, as a TEXT file"
                        % (_plural(e["no_lines"], "bill"), "has" if e["no_lines"] == 1 else "have",
                           _dates_text(e["gap_dates"]), e["title"], span))
                cls = "warn"
        else:
            txt = "Not yet \u2014 export from Marg as a TEXT file: %s, %s" % (e["title"], span)
            cls = "warn"
        lines.append('<div class="s604r" style="margin:6px 0"><b>%s</b> \u2014 <span class="%s">%s</span></div>'
                     % (_esc(e["label"][:1].upper() + e["label"][1:]), cls, _esc(txt)))
    if gate[0]:
        lines.append('<div class="ok" style="margin:8px 0"><b>All three reports are in and agree \u2014 the month can be '
                     'locked.</b></div>')
    if refused:
        lines.append('<div class="warn" style="margin:8px 0">%s</div>' % _esc(refused))
    if dt.datetime.now(IST).date() <= dt.date.fromisoformat(reps[0]["last"]):
        lines.append('<div class="muted">The month is not over yet \u2014 export these after %s.</div>'
                     % _esc(_human(reps[0]["last"])))
    return ('<!--s604card--><div class="card" id="s604reports"><h2>Month-end reports for %s</h2>%s'
            '<div class="muted" style="margin-top:6px">Each report shows here within about a quarter of an hour of being exported. '
            'Exporting the same report again, with nothing changed in Marg, adds nothing \u2014 the time above stays.</div>'
            '</div><!--/s604card-->' % (_esc(_month_name(month)), "".join(lines)))


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
    can, why = _lock_gate(con, month, s)                       # S604: the lock asks for the three reports and an agreeing cross-check
    if not can:
        return jsonify(ok=False, error="cannot_finalise", month=month, reasons=why), 409
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
    rows = acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND COALESCE(status,'')<>'rejected' ORDER BY id DESC LIMIT 2000"   # S409: a duplicate never reaches the match
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


def _scan_age(bill_date):
    """S403: days since the bill's date (its arrival, as Marg dates it); 0 when unreadable."""
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(bill_date or "")[:10])).days
    except ValueError:
        return 0


def _scan_overdue(bill_date, days=3):
    """S403 (D618): a bill unscanned three days after arrival turns red -- on the month page, on the scan-links page
    and on the Purchase orders screen (porders.py reads the same rule)."""
    return _scan_age(bill_date) > days


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


def plan_line(it, cad_days, dead_after=None):               # S470 (B.8): order.dead_after_days, handed in by order_rules.plan
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
    if strips and it["days_since_sale"] > (dead_after or DEAD_AFTER_DAYS):
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
    if action == "staff_send":                       # S662: the third door CLOSED -- an order goes only from the one order list
        msg = ("Orders now go from the one order list (Order karna hai), one WhatsApp per order." if _is_doctor(u)
               else "Order ab 'Order karna hai' list se hi jaata hai.")
        return jsonify(ok=False, error="send_via_order_list", message=msg), 409
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


# ==========================================================================================================================================
# S574_PHONEBOOK_ONE_RECORD (18-Oct-2026, the owner's "Proceed with the build" 06:19 IST) -- THE ONE READER of a dealer's number (charter 2).
# Every page, message and check that needs a number asks book_number(con, name, use) -- use 'call' (a Call button, a tel: link), 'order'
# (where a WhatsApp order goes), 'pay' (a NEFT or cheque notice) -- or book_record / book_numbers / book_shown for a list. _phone_for stays as
# the 'order' wrapper, so porders.py and order_rules.py are unchanged. The switch purchase.book_one_record.on ('0' until the owner's tap):
#   OFF -- the lookup as before S574, exactly: the row whose vendor_norm is supplier_key(name), its phone (numbers 1-2 for a list); no pick.
#   ON  -- that row; a row merged into another -> that one record (one hop); a bill name with no row of its own -> the bank sheet's record by
#          purchase_vendor_alias (live: RAVI MEDICAL AGENCY); numbers 1-4; the owner's pick for the use when its slot holds a number, else
#          the first number.
# ==========================================================================================================================================
BOOK_ON_KEY = "purchase.book_one_record.on"
BOOK_SLOTS = ("phone", "phone2", "phone3", "phone4")
BOOK_USES = ("call", "order", "pay")


def book_on(con):
    """The switch. Anything but '1' (no row, an unreadable table) is OFF."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (BOOK_ON_KEY,)).fetchone()
    except sqlite3.Error:
        return False
    return bool(r) and str(r[0] or "").strip() == "1"


def _book_row(con, key):
    """purchase_vendor_contact's row for a vendor_norm, as a dict (whatever the connection's row factory); None when there is none."""
    try:
        cur = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,))
        r = cur.fetchone()
    except sqlite3.Error:
        return None
    return dict(zip([d[0] for d in cur.description], tuple(r))) if r is not None else None


def book_record(con, vendor):
    """The one record (a dict) for a Marg name, a bill name, a bank sheet's name or a vendor_norm, or None. '_s574_on' in it says
    whether it was read with the switch ON."""
    k = supplier_key(vendor)
    rec = _book_row(con, k)
    on = book_on(con)
    if on:
        if rec is None:
            try:
                a = con.execute("SELECT register_norm FROM purchase_vendor_alias WHERE bill_norm=?", (k,)).fetchone()
            except sqlite3.Error:
                a = None
            rec = _book_row(con, a[0]) if a else None
        if rec is not None and rec.get("merged_into"):
            rec = _book_row(con, rec["merged_into"]) or rec
    if rec is not None:
        rec["_s574_on"] = on
    return rec


def book_numbers(rec):
    """[(slot, number)] for the slots that hold a number, in slot order: 1-4 when the record was read with the switch ON, 1-2 when OFF
    (a number 3 or 4 saved while ON never leaks into an OFF reader)."""
    if not rec:
        return []
    slots = BOOK_SLOTS if rec.get("_s574_on") else BOOK_SLOTS[:2]
    return [(i + 1, rec.get(s)) for i, s in enumerate(slots) if rec.get(s)]


def _book_pick(rec, use):
    try:
        p = int(rec.get("%s_pick" % use))
    except (TypeError, ValueError):
        return None
    return p if 1 <= p <= 4 else None


def book_number(con, vendor, use="order"):
    """The number for one use ('call' | 'order' | 'pay'): the picked slot's number when that pick is set and its slot holds a number,
    else the first number, else ''. Switch OFF: the row's phone, exactly as _phone_for answered before S574."""
    rec = book_record(con, vendor)
    if rec is None:
        return ""
    if not rec.get("_s574_on"):
        return rec.get("phone") or ""
    nums = book_numbers(rec)
    pick = _book_pick(rec, use) if use in BOOK_USES else None
    got = dict(nums).get(pick) if pick else None
    return got or (nums[0][1] if nums else "")


def book_shown(con, vendor):
    """The numbers a sender's page or paper prints under the dealer's name: switch OFF numbers 1-2 (as before); ON the Calls number,
    then the Order WhatsApp number when it is another."""
    rec = book_record(con, vendor)
    if rec is None:
        return []
    if not rec.get("_s574_on"):
        return [n for _s, n in book_numbers(rec)]
    call, wa = book_number(con, vendor, "call"), book_number(con, vendor, "order")
    return [x for x in (call, "" if wa == call else wa) if x]


def _phone_for(con, vendor):
    """S574: the Order WhatsApp number, by the one reader (porders.py, order_rules.py and order_sheet's checks call this)."""
    return book_number(con, vendor, "order")


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


def _watch_row(con):
    """S240 (Sanjeevni item 1): the latest day export_watch.py judged, or None."""
    if not _table_exists(con, "export_watch"):
        return None
    return con.execute("SELECT day, verdict, missing, note, checked_at FROM export_watch "
                       "ORDER BY day DESC LIMIT 1").fetchone()


_WATCH_LABEL = {"BILLWISE": "PURCHASE BILL WISE", "SUPPLIERWISE": "PURCHASE SUPPLIER WISE for last month (month-end)",
                "LINES": "PURCHASE BILL ITEM WISE (or SUPPLIER/ITEM WISE)", "STOCK": "STOCK CLOSING"}


def _watch_card(con, staff=False):
    """The missed-export line. Owner (hub): every verdict, plain English. Amir (salts page,
    staff=True): only a red day, in Hinglish -- the staff-facing language rule."""
    r = _watch_row(con)
    if r is None:
        return ""
    try:
        missing = [_WATCH_LABEL.get(k, k) for k in json.loads(r[2] or "[]")]
    except ValueError:
        missing = []
    day = _human(r[0]) if r[0] else "?"
    if staff:
        if r[1] != "red":
            return ""
        return ('<div class="card" style="border-color:var(--bad)"><b class="bad">%s ki Marg export poori '
                'nahi aayi.</b> Baaki: <b>%s</b>. Marg se abhi export kar dijiye (1 tareekh se aaj tak).</div>'
                % (_esc(day), _esc(", ".join(missing))))
    if r[1] == "red":
        return ('<div class="card" style="border-color:var(--bad)"><b class="bad">Amir punched in on %s, but '
                'these Marg exports did not arrive:</b> %s.</div>' % (_esc(day), _esc(", ".join(missing))))
    if r[1] == "unknown":
        return ('<div class="card"><span class="warn">Amir\'s exports for %s: cannot tell yet</span> '
                '<span class="muted">&middot; %s</span></div>' % (_esc(day), _esc(r[3] or "")))
    if r[1] == "ok":
        return ('<div class="card"><span class="ok">Amir\'s Marg exports for %s: everything expected arrived.</span>'
                ' <span class="muted">%s</span></div>' % (_esc(day), _esc(r[3] or "")))
    return ""


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


@bp.route("/", strict_slashes=False)
def page_root():
    """S243: the bare prefix -> the hub. Both /finance/purchase and
    /finance/purchase/ land here; the app's own gate has already run."""
    return redirect(request.script_root + _url_prefix + "/page/hub", code=302)


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
        story = s["story"] if st == "FINAL" else _story_gated(s, _lock_gate(con, m, s))       # S604: the one gate
        try:                                                   # S749: the register's words for the month
            pc = _s749_hub_words(con, m)
        except Exception as _e749:                             # noqa: BLE001
            pc = '<span class="warn">not read (%s)</span>' % _esc(str(_e749)[:60])
        rows.append('<tr><td><a href="%s/page/month/%s">%s</a></td><td class="n"><b>%s</b>%s</td>'
                    '<td class="n">%s</td><td class="n">%d</td><td class="n">%d</td>'
                    '<td class="n %s">%d</td><td class="n %s">%d</td><td>%s</td>'
                    '<td><span class="chip %s">%s</span></td></tr>'
                    '<tr><td colspan="9" class="muted" style="padding-top:2px;padding-bottom:12px">%s</td></tr>'
                    % (prefix, m, _esc(_month_name(m)), _r(s["marg_p"]),
                       "" if s["basis"] == "supplier-wise" else '<div class="muted">bill-wise</div>',
                       _r(s["itemwise_p"]), len(s["bills"]), len(s["returns"]),
                       "warn" if s["no_lines"] else "", len(s["no_lines"]),
                       "bad" if s["wrong"] else "", s["wrong"], pc,
                       "ok" if st == "FINAL" else "warn", st, _esc(story)))
    months = ('<div class="card"><h2>Months</h2><div class="muted">The Marg total is the supplier-wise '
              'report, final for month-end. Item-wise is NET (after discount), each bill\'s lines counted '
              'once; a bill whose lines add up to more than the bill carries a purchase return, as Marg '
              'reports it.</div>'
              '<div class="scroll"><table><tr><th>Month</th>'
              '<th class="n">Marg total (supplier-wise)</th><th class="n">Item-wise net</th><th class="n">Bills</th>'
              '<th class="n">Returns</th><th class="n">No lines</th>'
              '<th class="n">Wrong</th><th>Purchase check</th><th>Status</th></tr>%s</table></div>%s</div>'
              % ("".join(rows), '' if rows else '<div class="muted">No purchase bills have arrived yet.</div>'))
    try:                                                       # S749: counted months only, the register's words, the step view the way in
        scan = _s749_hub_scan_card(con, prefix)
    except Exception as _e749:                                 # noqa: BLE001
        scan = '<div class="card"><h2>Purchase check</h2><div class="warn">not read (%s)</div></div>' % _esc(str(_e749)[:80])
    n_open = con.execute("SELECT COUNT(*) FROM purchase_order WHERE status IN ('draft','sent')").fetchone()[0]
    orders = ('<div class="card"><h2>Orders</h2><div class="kv" style="max-width:240px"><b>%d</b>'
              '<span>open orders (draft or sent)</span></div>'
              '<div><a href="%s/page/orders">Make this week\'s order</a></div></div>' % (n_open, prefix))
    body = ('<h1>Marg Purchases</h1><div class="muted">Sanjeevni Medicos &middot; what Marg says was '
            'bought, checked bill by bill. Signed in as %s%s.</div>%s%s%s%s%s%s'
            % (_esc(_who(u)), " (doctor)" if _is_doctor(u) else (" (view only)" if _is_viewer_only(u) else ""),
               _watch_card(con), months, _feed_card(con), _stock_card(con), scan, orders + _new_items_card(con, prefix)))
    return _page("Marg Purchases", body)




# ===================================================================== S261
# THE NEFT SHEET, INSIDE THE SYSTEM
#
# The month page answers "what does Marg say was bought". This is the other
# thing: the sheet the payment is actually made from. Until now it lived in a
# workbook on the owner's PC, prefilled by a script from an export, and that is
# how a draft carrying last month's numbers could sit in the payment folder for
# two weeks looking finished.
#
# THE ORDER IS THE OWNER'S, 14-Sep-2026: prepare the sheet first, then verify it
# against the supplier-wise statement, then lock it.
#
#   1  PREPARE.  The system fills everything it knows: each vendor, the bills
#      split into the two fortnights the sheet has always used, the month's
#      total, and which lane the vendor is paid through. Carry-forward is the
#      one thing it does not know -- July was settled outside this system -- so
#      it is typed here and says so.
#   2  VERIFY.  The supplier-wise purchase statement is the cross-check, not a
#      gate to tick: the check compares what was prepared against Marg's own
#      supplier-wise export of the same month -- its bill count, its per-bill
#      amounts and its OWN PRINTED GRAND TOTAL -- and either says it agrees to
#      the rupee or names exactly what differs. Every run is kept.
#   3  LOCK.  Finalise the month and the figures stop moving; the advice file
#      and its covering letter are built from this and from nothing else.
#
# A vendor whose account is not confirmed on this server is never in the NEFT
# total. They are a cheque, said out loud, with the one screen that fixes it.
# A small difference is flagged and never swallowed.

PAY_SHEET = """CREATE TABLE IF NOT EXISTS purchase_pay_line (
  month         TEXT NOT NULL,
  vendor_norm   TEXT NOT NULL,
  carry_fwd_p   INTEGER,
  paid_p        INTEGER,
  note          TEXT,
  updated_by    TEXT,
  updated_at    TEXT,
  PRIMARY KEY (month, vendor_norm)
);
CREATE TABLE IF NOT EXISTS purchase_pay_check (
  id       INTEGER PRIMARY KEY,
  month    TEXT NOT NULL,
  at       TEXT NOT NULL,
  who      TEXT NOT NULL,
  ok       INTEGER NOT NULL,
  detail   TEXT
);
CREATE INDEX IF NOT EXISTS ix_ppc_month ON purchase_pay_check(month, id);"""

_pay_done = False


def _pay_ensure(con):
    """The two small tables the sheet needs, created on first request and never
    at import (F-303). One holds what a person types; one holds every run of the
    verification, appended, never overwritten."""
    global _pay_done
    if _pay_done:
        return
    con.executescript(PAY_SHEET)
    con.commit()
    _pay_done = True


def _bank_cols(con):
    try:
        return {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    except sqlite3.Error:
        return set()


def _vendor_bank(con):
    """supplier_norm -> dict(route, why). NEFT only when an account is on this
    server AND confirmed. Everything else is a cheque, said out loud."""
    out = {}
    cols = _bank_cols(con)
    if not cols or "vendor_norm" not in cols:
        return out
    has_acct, has_st = "acct_no" in cols, "bank_status" in cols
    sel = "vendor_norm, vendor" + (", acct_no" if has_acct else "") + (", bank_status" if has_st else "")
    try:
        rows = con.execute("SELECT %s FROM purchase_vendor_contact" % sel).fetchall()
    except sqlite3.Error:
        return out
    for r in rows:
        acct = (r[2] or "").strip() if has_acct else ""
        st = ((r[3] if (has_st and has_acct) else (r[2] if has_st else "")) or "").strip().upper()
        if acct and st == "VERIFIED":
            out[r[0]] = {"route": "NEFT", "why": "account confirmed"}
        elif acct:
            out[r[0]] = {"route": "CHEQUE", "why": "account on file, not confirmed yet"}
        else:
            out[r[0]] = {"route": "CHEQUE", "why": "no account on this server"}
    return out


def _pay_typed(con, month):
    """What a person has typed on this month's sheet."""
    _pay_ensure(con)
    out = {}
    for r in con.execute("SELECT vendor_norm, carry_fwd_p, paid_p, note, updated_by, updated_at "
                         "FROM purchase_pay_line WHERE month=?", (month,)):
        out[r[0]] = {"carry_p": r[1], "paid_p": r[2], "note": r[3] or "",
                     "by": r[4] or "", "at": r[5] or ""}
    return out


def _fortnight(iso):
    """The sheet has always split a month at the 15th. Bills with no date sit in
    the second half rather than vanishing -- and they are flagged anyway."""
    try:
        return 1 if int(iso[8:10]) <= 15 else 2
    except (TypeError, ValueError, IndexError):
        return 2


def _pay_rows(con, month):
    """THE SHEET. One row per vendor: the two fortnights, the month, what was
    carried in, what is payable, and how it is paid."""
    s = _month_summary(con, month)
    bank = _vendor_bank(con)
    typed = _pay_typed(con, month)
    ret_by = {x["bill"]["id"]: x for x in s["returns"]}
    short_by = {x["bill"]["id"]: x for x in s["short"]}
    signed_ids = set(s.get("signed") or [])                    # S604 (F-956 B)
    groups, cur = [], None
    for b in s["bills"]:
        if b["supplier_norm"] != cur:
            cur = b["supplier_norm"]
            info = bank.get(cur) or {"route": "CHEQUE", "why": "no account on this server"}
            ty = typed.get(cur) or {}
            groups.append({"norm": cur, "name": b["supplier"], "bills": [], "total_p": 0,
                           "f1_p": 0, "f2_p": 0, "route": info["route"], "why": info["why"],
                           "flags": 0, "carry_p": ty.get("carry_p"), "paid_p": ty.get("paid_p"),
                           "note": ty.get("note", ""), "by": ty.get("by", ""), "at": ty.get("at", "")})
        g = groups[-1]
        t = _bill_lines(b, s["sets"], s["stray"])
        flag = ""
        if b["verdict"] == "WRONG":
            flag = "marked wrong — should be %s" % _r(b["wrong_amount_p"])
        elif b["id"] in ret_by:
            flag = ("the lines add up to %s, %s more than the bill — Marg reports a purchase "
                    "return against it. Worth opening: it may be an entry that needs correcting."
                    % (_r(ret_by[b["id"]]["net_p"]), _r(ret_by[b["id"]]["diff_p"])))
        elif b["id"] in short_by:
            flag = ("the lines add up to %s LESS than the bill — a line is missing from the "
                    "export, or the bill is wrong. Check the bill." % _r(-short_by[b["id"]]["diff_p"]))
        elif b["disagree_p"]:
            flag = ("bill-wise says %s and supplier-wise says %s — the two Marg reports disagree."
                    % (_r(b["bw_p"]), _r(b["sw_p"])))
        elif b["id"] in signed_ids:
            flag = "a purchase return — Marg prints its lines as a purchase; counted as a return."
        note = "" if t else "the item lines for this bill have not arrived yet."
        g["bills"].append({"id": b["id"], "no": b["bill_no"], "date": b["bill_date"],
                           "amount_p": b["marg_p"], "net_p": (t["net_p"] if t else None),
                           "lines": (t["n"] if t else 0), "flag": flag, "note": note})
        g["total_p"] += b["marg_p"]
        if _fortnight(b["bill_date"]) == 1:
            g["f1_p"] += b["marg_p"]
        else:
            g["f2_p"] += b["marg_p"]
        if flag:
            g["flags"] += 1
    for g in groups:
        g["payable_p"] = g["total_p"] + (g["carry_p"] or 0)
    return s, groups


def _verify_statement(con, month, s=None):
    """STEP 2 -- the supplier-wise statement as the cross-check.

    Not a tick-box: it reads Marg's own supplier-wise export of this month and
    holds the prepared sheet against it three ways -- every bill carried by it,
    the per-bill amounts where bill-wise and supplier-wise both exist, and the
    export's OWN PRINTED GRAND TOTAL. Anything that does not line up is named."""
    if s is None:                                              # S604: the gate passes its own summary (no second build, no recursion)
        s = _month_summary(con, month)
    bills = s["bills"]
    problems, notes = [], []
    sw = con.execute(
        "SELECT md5, file, export_stamp, n_rows, grand_amount_p FROM purchase_export "
        "WHERE type='SUPPLIERWISE' AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
        "ORDER BY export_stamp DESC LIMIT 1", (month + "-01", _s604_last_day(month))).fetchone()
    if sw is None:
        problems.append("No supplier-wise purchase statement for this month has reached the server. "
                        "Take it out of Marg — supplier, bill number, bill date, amount — "
                        "and it will arrive by itself within about ten minutes.")
        return {"ok": False, "problems": problems, "notes": notes, "export": None,
                "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": None}

    without = [b for b in bills if b["sw_p"] is None]
    if without:
        problems.append("%s on the sheet %s not carried by that statement: %s."
                        % (_plural(len(without), "bill"), "is" if len(without) == 1 else "are",
                           _name_some(without, lambda b: "%s (%s)" % (b["bill_no"], b["supplier"]))))
    dis = [b for b in bills if b["disagree_p"]]
    if dis:
        problems.append("%s where bill-wise and supplier-wise disagree: %s."
                        % (_plural(len(dis), "bill"),
                           _name_some(dis, lambda b: "%s %s vs %s"
                                      % (b["bill_no"], _r(b["bw_p"]), _r(b["sw_p"])))))
    printed = sw["grand_amount_p"]
    if printed:
        if abs(printed - s["marg_p"]) > AGREE_P:
            problems.append("The statement prints its own grand total as %s; the sheet adds up to "
                            "%s — a difference of %s."
                            % (_r(printed), _r(s["marg_p"]), _r(abs(printed - s["marg_p"]))))
        else:
            notes.append("The statement's own printed grand total is %s — the sheet agrees with "
                         "it to the rupee." % _r(printed))
    else:
        notes.append("That statement did not carry a printed grand total, so the comparison is "
                     "bill by bill only.")
    notes.append("Statement: %s, taken %s, %s row%s."
                 % (_esc(sw["file"]), _esc(sw["export_stamp"]), sw["n_rows"],
                    "" if sw["n_rows"] == 1 else "s"))
    return {"ok": not problems, "problems": problems, "notes": notes, "export": dict(sw),
            "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": printed}


def _pay_last_check(con, month):
    _pay_ensure(con)
    r = con.execute("SELECT at, who, ok, detail FROM purchase_pay_check WHERE month=? "
                    "ORDER BY id DESC LIMIT 1", (month,)).fetchone()
    return dict(r) if r else None


@bp.route("/api/pay-verify", methods=["POST"])
def api_pay_verify():
    """Run the verification and keep the run. Never changes a figure."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    if not re.match(r"^\d{4}-\d{2}$", month):
        return jsonify(ok=False, error="malformed", message="month as YYYY-MM"), 400
    con = _db()
    _ensure(con)
    v = _verify_statement(con, month)
    con.execute("INSERT INTO purchase_pay_check (month, at, who, ok, detail) VALUES (?,?,?,?,?)",
                (month, now_iso(), _who(u), 1 if v["ok"] else 0,
                 json.dumps({"problems": v["problems"], "notes": v["notes"],
                             "total_p": v["total_p"], "printed_p": v["printed_p"]},
                            ensure_ascii=False)))
    _audit(con, _who(u), "pay_verify", month, {"ok": v["ok"], "problems": len(v["problems"])})
    con.commit()
    return jsonify(ok=True, verified=v["ok"], problems=v["problems"], notes=v["notes"])


@bp.route("/api/pay-line", methods=["POST"])
def api_pay_line():
    """The one thing a person types on this sheet: what an earlier month left
    outstanding, what has been paid, and a note. The doctor's rule stands -- a
    final month does not move."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor = str(b.get("vendor_norm") or "")
    if not re.match(r"^\d{4}-\d{2}$", month) or not vendor:
        return jsonify(ok=False, error="malformed", message="month and vendor_norm"), 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    if _month_status(con, month)["status"] == "final":
        return _refuse("This month is FINAL. The doctor must reopen it first.")

    bad = []

    def money(key):
        v = b.get(key + "_p")
        n = _int_or_none(v)
        if n is not None:
            return n
        typed = str(b.get(key) if b.get(key) is not None else "").strip()
        raw = typed.replace(",", "").replace("₹", "").replace(" ", "")
        if raw.endswith("/-"):                                 # S604 (F-954): '400/-' as it is written on paper
            raw = raw[:-2]
        if raw[:1] in ("\u2212", "\u2013"):                    # S604: the minus a phone types (U+2212), or a dash (U+2013)
            raw = "-" + raw[1:]
        if raw == "":
            return None
        try:
            f = float(raw)
            if f != f or abs(f) == float("inf"):
                raise ValueError(raw)
            return int(round(f * 100))
        except ValueError:
            bad.append((key, typed[:40]))
            return None

    carry, paid = money("carry_fwd"), money("paid")
    if bad:                                                    # S604: refused with words, never saved blank
        what = {"carry_fwd": "Carried in", "paid": "Paid"}
        return jsonify(ok=False, error="malformed",
                       message="That figure could not be read: %s. Type a number such as 400 or -400; nothing was saved."
                       % "; ".join("%s \u201c%s\u201d" % (what.get(k, k), t) for k, t in bad)), 400
    before = con.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? "
                         "AND vendor_norm=?", (month, vendor)).fetchone()
    if "note" in b:                                            # S604: the note is written only when the request carries it
        note = str(b.get("note") or "").strip()[:300]
    else:
        note = (before["note"] if before else None) or ""
    at = now_iso()
    con.execute("INSERT INTO purchase_pay_line (month, vendor_norm, carry_fwd_p, paid_p, note, "
                "updated_by, updated_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(month, vendor_norm) "
                "DO UPDATE SET carry_fwd_p=excluded.carry_fwd_p, paid_p=excluded.paid_p, "
                "note=excluded.note, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, vendor, carry, paid, note or None, _who(u), at))
    _audit(con, _who(u), "pay_line", "%s %s" % (month, vendor),
           {"carry_fwd_p": carry, "paid_p": paid, "note": note,
            "before": dict(before) if before else None})
    con.commit()
    payable = None
    try:
        payable = next((g["payable_p"] for g in _pay_rows(con, month)[1] if g["norm"] == vendor), None)
    except Exception:                                          # noqa: BLE001
        payable = None
    return jsonify(ok=True, month=month, vendor_norm=vendor, carry_fwd_p=carry, paid_p=paid, payable_p=payable,
                   payable=_r(payable) if payable is not None else "", updated_at=at, updated_by=_who(u))


@bp.route("/api/bill-lines")
def api_bill_lines():
    """The item lines of ONE bill -- the third level. Read only."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    try:
        bid = int(request.args.get("bill") or 0)
    except ValueError:
        return jsonify(ok=False, error="bad_bill"), 400
    con = _db()
    _ensure(con)
    b = con.execute("SELECT * FROM purchase_bill WHERE id=?", (bid,)).fetchone()
    if not b:
        return jsonify(ok=False, error="no_such_bill"), 404
    b = dict(b)
    sets = _line_sets(con, b["month"])
    t = _bill_lines(b, sets, _stray_sets(_bills_for_month(con, b["month"]), sets))
    if not t:
        return jsonify(ok=True, lines=[], n=0, net="—",
                       note="No item lines have arrived for this bill yet.")
    rows = con.execute(
        "SELECT item, packing, batch, expiry, qty, free, rate_p, discount_pct, "
        "COALESCE(net_amount_p, amount_p) FROM purchase_line WHERE source_md5=? AND bill_no=? "
        "AND (supplier_norm=? OR supplier_norm IS NULL) AND line_type=? ORDER BY id",
        (t["md5"], b["bill_no"], b["supplier_norm"], t["line_type"])).fetchall()
    out = [{"item": r[0], "packing": r[1] or "", "batch": r[2] or "", "expiry": r[3] or "",
            "qty": r[4], "free": r[5], "rate": _r(r[6]), "disc": r[7], "amount": _r(r[8])}
           for r in rows]
    return jsonify(ok=True, lines=out, net=_r(t["net_p"]), n=t["n"])


def _neft_state_s407(con, month):
    """S407 (D623): the month's NEFT state from supplier_msg (fail-soft: None when the module is absent)."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.state(con, month)
    except Exception:                                              # noqa: BLE001
        return None


def _neft_chip_s407(st, g):
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.chip(st, g)
    except Exception:                                              # noqa: BLE001
        return ""


def _neft_card_s407(con, u, month, prefix, final, groups):
    """S407: 'NEFT done (bank SMS received)' for the owner; the same state in Hindi for the staff; the suppliers' messages."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.pay_card(con, u, month, prefix, final, groups)
    except Exception as ex:                                        # noqa: BLE001
        return '<div class="card"><h2>NEFT</h2><div class="muted">the NEFT card is unavailable (%s)</div></div>' % _esc(str(ex)[:120])


def _s604_saved_words(g):
    """S604 (F-954): 'Saved 20-Oct 07:54 by manoj \u2014 payable now \u20b90', from the pay line's own updated_at / updated_by."""
    w = "Saved %s by %s \u2014 payable now %s" % (_hhmm_ist_full(g["at"]), g.get("by") or "?", _r(g["payable_p"]))
    if g.get("note"):
        w += " \u00b7 note: %s" % g["note"]
    return w


def _pay_sheet_table(groups, prefix, month, editable):
    """The sheet as a sheet -- the thing that is printed and signed."""
    rows = []
    for g in groups:
        carry = ("" if g["carry_p"] is None else "%d" % int(round(g["carry_p"] / 100.0)))
        paid = ("" if g["paid_p"] is None else "%d" % int(round(g["paid_p"] / 100.0)))
        inp = ('<input class="pin" id="cf_%s" value="%s" '
               'onchange="payline(\'%s\',this)" data-v="%s">'
               % (_esc(g["norm"]), carry, _esc(g["norm"]), _esc(g["norm"]))) if editable else (
               _r(g["carry_p"]) if g["carry_p"] is not None else "—")
        pin = ('<input class="pin" id="pd_%s" value="%s" inputmode="numeric" '
               'onchange="payline(\'%s\',this)">' % (_esc(g["norm"]), paid, _esc(g["norm"]))
               ) if editable else (_r(g["paid_p"]) if g["paid_p"] is not None else "—")
        rows.append('<tr><td>%s%s</td><td class="n">%s</td><td class="n">%s</td>'
                    '<td class="n">%s</td><td class="n">%s</td><td class="n" id="py_%s">%s</td>'
                    '<td class="n">%s</td></tr>'
                    % (_esc(g["name"]),
                       ' <span class="chip warn">CHEQUE</span>' if g["route"] != "NEFT" else "",
                       _r(g["f1_p"]), _r(g["f2_p"]), _r(g["total_p"]), inp,
                       _esc(g["norm"]), _r(g["payable_p"]), pin))
        if editable and g.get("at"):                           # S604 (F-954): what was saved, by whom (never on the printed pack)
            rows.append('<tr class="s604saved"><td colspan="7" class="muted" style="padding-top:0">%s</td></tr>'
                        % _esc(_s604_saved_words(g)))
    tot_f1 = sum(g["f1_p"] for g in groups)
    tot_f2 = sum(g["f2_p"] for g in groups)
    tot = sum(g["total_p"] for g in groups)
    tot_c = sum(g["carry_p"] or 0 for g in groups)
    tot_pay = sum(g["payable_p"] for g in groups)
    tot_paid = sum(g["paid_p"] or 0 for g in groups)
    rows.append('<tr><th>TOTAL</th><th class="n">%s</th><th class="n">%s</th><th class="n">%s</th>'
                '<th class="n">%s</th><th class="n">%s</th><th class="n">%s</th></tr>'
                % (_r(tot_f1), _r(tot_f2), _r(tot), _r(tot_c) if tot_c else "—",
                   _r(tot_pay), _r(tot_paid) if tot_paid else "—"))
    return ('<div class="scroll"><table class="sheet"><tr><th>Vendor</th>'
            '<th class="n">1st–15th</th><th class="n">16th–end</th>'
            '<th class="n">%s</th><th class="n">Carried in</th><th class="n">Payable</th>'
            '<th class="n">Paid</th></tr>%s</table></div>'
            % (_esc(_month_name(month)), "".join(rows)))


@bp.route("/page/pay/<month>")
def page_pay(month):
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    s, groups = _pay_rows(con, month)
    prefix = request.script_root + _url_prefix
    final = s["status"]["status"] == "final"
    editable = (not final) and (not _is_viewer_only(u))

    neft_p = sum(g["payable_p"] for g in groups if g["route"] == "NEFT")
    cheq = [g for g in groups if g["route"] != "NEFT"]
    cheq_p = sum(g["payable_p"] for g in cheq)
    flagged = sum(g["flags"] for g in groups)

    # ---------------------------------------------------------- 1 · the sheet
    _neft_st = _neft_state_s407(con, month)                        # S407: amber / green / red beside every NEFT vendor
    cards = []
    for i, g in enumerate(groups):
        chips = ""
        if g["route"] != "NEFT":
            chips += ' <span class="chip warn">CHEQUE</span>'
        else:
            chips += _neft_chip_s407(_neft_st, g)
        if g["flags"]:
            chips += ' <span class="chip warn">CHECK</span>'
        bills = []
        for b in g["bills"]:
            fl = ' <span class="chip warn">CHECK</span>' if b["flag"] else ""
            bills.append(
                '<div class="payb"><button class="plain" onclick="bl(%d)">'
                '<span class="bno">%s</span><span class="bdt muted">%s%s</span>'
                '<span class="bam">%s</span></button>'
                '<div class="paybd" id="bl%d"><div class="muted">Bill %s &middot; %s &middot; '
                'Marg amount %s &middot; item-wise (after discount) %s &middot; %d line%s</div>%s'
                '<div class="lines muted">Open to load the bill\'s own lines.</div></div></div>'
                % (b["id"], _esc(b["no"]), _human(b["date"]), fl, _r(b["amount_p"]), b["id"],
                   _esc(b["no"]), _human(b["date"]), _r(b["amount_p"]),
                   _r(b["net_p"]) if b["net_p"] is not None else "—",
                   b["lines"], "" if b["lines"] == 1 else "s",
                   ('<div class="warn" style="margin:6px 0">%s</div>' % _esc(b["flag"])) if b["flag"]
                   else ('<div class="muted" style="margin:6px 0">%s</div>' % _esc(b["note"]))
                   if b["note"] else ""))
        strip = ('<div class="vstrip muted">1st–15th <b>%s</b> &nbsp;&middot;&nbsp; '
                 '16th–end <b>%s</b> &nbsp;&middot;&nbsp; carried in <b>%s</b> '
                 '&nbsp;&middot;&nbsp; payable <b>%s</b> &nbsp;&middot;&nbsp; %s</div>'
                 % (_r(g["f1_p"]), _r(g["f2_p"]),
                    _r(g["carry_p"]) if g["carry_p"] is not None else "not typed yet",
                    _r(g["payable_p"]), _esc(g["why"])))
        cards.append(
            '<div class="payv"><button class="plain vhead" onclick="pv(%d,this)">'
            '<span class="car">&#9656;</span><span class="vn">%s%s<span class="muted vb">%d bill%s'
            '</span></span><span class="va">%s</span></button><div class="payl" id="pv%d">%s%s</div></div>'
            % (i, _esc(g["name"]), chips, len(g["bills"]), "" if len(g["bills"]) == 1 else "s",
               _r(g["payable_p"]), i, strip, "".join(bills)))

    sheet_card = (
        '<div class="card"><h2>1 &middot; The sheet</h2><div class="muted">One line per vendor, '
        'prepared from this server\'s own figures. Open a vendor for its bills; open a bill for the '
        'bill. <b>Carried in</b> is the only thing typed here — what an earlier month left '
        'outstanding, which was settled outside this system and which it therefore does not know.</div>'
        '%s<h3>The sheet as it prints</h3>%s</div>'
        % ("".join(cards), _pay_sheet_table(groups, prefix, month, editable)))

    # ----------------------------------------------------- 2 · the verification -- S749: run by the server, no tap
    verify_card = _s749_verify_card(con, month, s)

    # ------------------------------------------------------------ 3 · cheques
    if cheq:
        rows = "".join(
            '<tr><td>%s</td><td class="muted">%s</td><td class="n">%s</td>'
            '<td><a href="%s/page/book">add / confirm the account</a></td></tr>'
            % (_esc(g["name"]), _esc(g["why"]), _r(g["payable_p"]), prefix) for g in cheq)
        cheque_card = (
            '<div class="card"><h2>Paid by cheque — not in the NEFT file (%d)</h2>'
            '<div class="muted">A vendor whose account is not confirmed on this server is never put '
            'into the bank advice file. Write a cheque, and log it. The moment the account is added '
            'and confirmed on the phone book page, that vendor moves to the NEFT lane by itself.</div>'
            '<div class="scroll"><table><tr><th>Vendor</th><th>Why</th><th class="n">Payable</th>'
            '<th>&nbsp;</th></tr>%s</table></div></div>' % (len(cheq), rows))
    else:
        cheque_card = ('<div class="card"><h2>Paid by cheque</h2><div class="muted">Nobody this '
                       'month — every vendor with a bill has a confirmed account.</div></div>')

    strip = ('<div class="card"><div class="grid">'
             '<div class="kv"><b>%s</b><span>%s purchases</span></div>'
             '<div class="kv"><b>%s</b><span>payable by NEFT</span></div>'
             '<div class="kv"><b>%s</b><span>payable by cheque</span></div>'
             '<div class="kv"><b>%d</b><span>flagged</span></div></div></div>'
             % (_r(s["marg_p"]), _esc(_month_name(month)), _r(neft_p), _r(cheq_p), flagged))

    nextcard = _s749_lock_card(con, month, s, final, (False, []) if final else _lock_gate(con, month, s))      # S749: the one gate

    body = (_s749_strip(con, month, "pay") + '<h1>Vendor payments — %s</h1><div class="muted">Sanjeevni Medicos &middot; the sheet '
            'this month is paid from. To check the bills themselves, open '
            '<a href="%s/page/month/%s">the purchase audit for this month</a>.'
            '</div>%s%s%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _s604_reports_card(con, month, s, final) +                                         # S604: the month-end reports
               _s446_earlier_card(con, month, prefix) + _pay_months_nav_s264(con, month, prefix),   # S446: an earlier month's baaki
               _pack_bar_s380(prefix, month),
               strip, _neft_card_s407(con, u, month, prefix, final, groups), sheet_card, verify_card,
               _cheque_card_s270(con, month, prefix, groups, _cheque_writer_s284(u, con)),
               nextcard,
               _advice_card_s265(con, month, prefix, final),
               _letter_card_s266(con, month, prefix, final,
                                 _advice_rows_s265(con, month)[1])))
    return _page("Vendor payments — %s" % _month_name(month), body,
                 PAY_JS.replace("__MONTH__", month))


@bp.route("/page/pay")
def page_pay_latest():
    """A stable address for the tile: the newest month that has bills."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    ms = _months(con, 1)
    if not ms:
        return _page("Vendor payments", '<h1>Vendor payments</h1><div class="muted">No purchase '
                     'bills have arrived yet.</div>')
    return redirect((request.script_root + _url_prefix) + "/page/pay/" + ms[0])


# One link, added without touching a single existing line: the nav helper is
# wrapped rather than edited, so every purchase screen gains the way in and the
# format string that builds the nav is left exactly as it was.
_book_nav_before_s261 = _book_nav


def _book_nav(prefix):                                          # noqa: F811
    try:
        return _book_nav_before_s261(prefix) + (
            '<a href="%s/page/pay">Vendor payments</a>' % prefix)
    except Exception:                                           # noqa: BLE001
        return ""


PAY_JS = """
function pv(i,el){var d=document.getElementById('pv'+i);
 d.classList.toggle('open');el.classList.toggle('open');}
function bl(id){var d=document.getElementById('bl'+id);
 var was=d.classList.contains('open');d.classList.toggle('open');
 if(was||d.dataset.done)return;d.dataset.done='1';
 var box=d.querySelector('.lines');box.textContent='loading the bill\\u2026';
 fetch(P+'/api/bill-lines?bill='+id).then(function(r){return r.json();}).then(function(j){
  if(!j.ok||!j.lines.length){box.textContent=j.note||'No item lines for this bill.';return;}
  var h='<div class="scroll"><table><tr><th>Item</th><th>Batch</th><th>Expiry</th><th class="n">Qty</th>'
   +'<th class="n">Free</th><th class="n">Rate</th><th class="n">Disc</th><th class="n">Amount</th></tr>';
  j.lines.forEach(function(l){h+='<tr><td>'+esc(l.item)+(l.packing?' <span class="muted">'+esc(l.packing)+'</span>':'')
   +'</td><td>'+esc(l.batch)+'</td><td>'+esc(l.expiry)+'</td><td class="n">'+(l.qty==null?'':l.qty)
   +'</td><td class="n">'+(l.free?l.free:'')+'</td><td class="n">'+l.rate+'</td><td class="n">'
   +(l.disc?l.disc+'%':'')+'</td><td class="n">'+l.amount+'</td></tr>';});
  h+='</table></div><div class="muted" style="margin-top:6px">'+j.n+' line'+(j.n==1?'':'s')
   +', '+j.net+' after discount.</div>';
  box.innerHTML=h;box.classList.remove('muted');
 }).catch(function(){box.textContent='could not load the bill just now.';});}
function payline(v,el){
 var cf=document.getElementById('cf_'+v), pd=document.getElementById('pd_'+v);
 el.disabled=true;
 fetch(P+'/api/pay-line',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({month:'__MONTH__',vendor_norm:v,
   carry_fwd:cf?cf.value:'',paid:pd?pd.value:''})})
 .then(function(r){return r.json();}).then(function(j){
  el.disabled=false;
  if(!j.ok){alert(j.message||'could not save that');return;}
  var sv=document.createElement('span');sv.className='ok';sv.textContent=' Saved \\u2014 payable now '+(j.payable||'');
  el.parentNode.appendChild(sv);
  setTimeout(function(){location.reload();},1200);
 }).catch(function(){el.disabled=false;alert('could not save that just now');});}
function payverify(m){
 var out=document.getElementById('vout');out.innerHTML='<div class="muted">checking\\u2026</div>';
 fetch(P+'/api/pay-verify',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({month:m})}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){out.innerHTML='<div class="bad">'+esc(j.message||'could not check')+'</div>';return;}
  location.reload();
 }).catch(function(){out.innerHTML='<div class="bad">could not check just now</div>';});}
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
"""

PAY_CSS = """
.payv{border-top:1px solid var(--line)}
.payv:first-child{border-top:0}
button.plain{display:flex;width:100%;align-items:center;gap:10px;background:none;border:0;
 padding:11px 2px;text-align:left;font:inherit;color:inherit;cursor:pointer;border-radius:0}
.vhead .car{color:var(--muted);transition:transform .15s}
.vhead.open .car{transform:rotate(90deg)}
.vn{flex:1;min-width:0;font-weight:600}
.vb{display:block;font-weight:400;font-size:12.5px}
.va{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.payl{display:none;padding:0 0 8px 22px}
.payl.open{display:block}
.vstrip{padding:6px 0 10px;font-size:13px}
.payb{border-top:1px dotted var(--line)}
.payb .bno{font-weight:600;min-width:84px}
.payb .bdt{flex:1;font-size:13px}
.payb .bam{font-variant-numeric:tabular-nums;white-space:nowrap}
.paybd{display:none;padding:8px 0 10px 8px}
.paybd.open{display:block}
.paybd table{font-size:13px}
table.sheet{font-size:13.5px}
table.sheet th{white-space:nowrap}
input.pin{width:92px;font:inherit;text-align:right;padding:4px 6px;border:1px solid var(--line);
 border-radius:6px;background:#fffbe6}
"""

CSS = CSS + PAY_CSS


# ===================================================================== S270
# THE CHEQUE REGISTER
#
# D513 has two halves. The first was built at S261-S263: a vendor who is not on
# the authorised NEFT register never enters the NEFT file, and is named on the
# sheet as a cheque. The second half has been a promise until now -- "and the
# cheque is logged". Nowhere logged it. A cheque left the clinic and the only
# record of its number was the counterfoil in a drawer.
#
# This is that register. Cheque number, the date it was written, the payee, the
# vendor it settles and the amount -- against the month, beside the NEFT lane.
#
# THREE THINGS IT DOES THAT A COUNTERFOIL CANNOT
#
#   1  IT REFUSES A NUMBER USED TWICE.  A live cheque number is unique in this
#      register. Two cheques written on one number is the single error a paper
#      book never catches and a bank always does, weeks later.
#   2  IT RECONCILES TO THE SHEET.  The sheet says what the cheque lane owes.
#      The register says what has actually been written. The difference is named
#      on the page, with the vendors still waiting, and it is never swallowed.
#   3  IT IS APPENDED, NEVER ERASED.  A cheque entered wrongly is VOIDED with a
#      reason and stays on the register for ever -- the same rule as the flags.
#
# A DELIBERATE DEPARTURE, AND WHY
#
# Every other write on this sheet refuses once the month is FINAL. This one does
# not, and must not: a cheque is written AFTER the month locks, which is the
# whole point of locking. Logging a cheque records something that has already
# happened -- it moves no figure on the sheet, and the sheet's own lock is
# untouched. The month is shown on every row so a late entry is never silent.

CHEQUE_SQL = """CREATE TABLE IF NOT EXISTS purchase_cheque (
  id           INTEGER PRIMARY KEY,
  month        TEXT NOT NULL,
  vendor_norm  TEXT NOT NULL,
  vendor       TEXT NOT NULL,
  payee        TEXT NOT NULL,
  cheque_no    TEXT NOT NULL,
  cheque_date  TEXT NOT NULL,
  amount_p     INTEGER NOT NULL,
  bank         TEXT,
  note         TEXT,
  handed_at    TEXT,
  handed_by    TEXT,
  created_at   TEXT NOT NULL,
  created_by   TEXT NOT NULL,
  voided_at    TEXT,
  voided_by    TEXT,
  void_reason  TEXT
);
CREATE INDEX IF NOT EXISTS ix_pchq_month  ON purchase_cheque(month);
CREATE INDEX IF NOT EXISTS ix_pchq_vendor ON purchase_cheque(vendor_norm);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pchq_live_no
  ON purchase_cheque(cheque_no) WHERE voided_at IS NULL;"""

_cheque_done = False


def _cheque_ensure(con):
    """Created on first request, never at import (F-303). The partial unique
    index is the register's one real check: a cheque number may be reused only
    after the cheque carrying it has been voided."""
    global _cheque_done
    if _cheque_done:
        return
    con.executescript(CHEQUE_SQL)
    con.commit()
    _cheque_done = True


def _cheque_rows_s270(con, month=None):
    """Every cheque, newest first. month=None means the whole register."""
    _cheque_ensure(con)
    if month:
        q = ("SELECT * FROM purchase_cheque WHERE month=? "
             "ORDER BY voided_at IS NOT NULL, cheque_date DESC, id DESC")
        rs = con.execute(q, (month,)).fetchall()
    else:
        q = ("SELECT * FROM purchase_cheque "
             "ORDER BY voided_at IS NOT NULL, cheque_date DESC, id DESC")
        rs = con.execute(q).fetchall()
    return [dict(r) for r in rs]


def _cheque_by_vendor_s270(con, month):
    """vendor_norm -> the live cheques settling that vendor this month."""
    out = {}
    for r in _cheque_rows_s270(con, month):
        if r["voided_at"]:
            continue
        out.setdefault(r["vendor_norm"], []).append(r)
    return out


def _cheque_recon_s270(con, month, groups):
    """What the sheet owes on the cheque lane against what has been written.

    Returns owed_p, written_p, gap_p and the vendors still without a live
    cheque. A vendor part-paid by cheque is NOT counted as settled -- the gap
    is per vendor and the page says so."""
    live = _cheque_by_vendor_s270(con, month)
    cheq = [g for g in groups if g["route"] != "NEFT"]
    owed_p = sum(g["payable_p"] for g in cheq)
    written_p = sum(c["amount_p"] for cs in live.values() for c in cs)
    waiting = []
    for g in cheq:
        got = sum(c["amount_p"] for c in live.get(g["norm"], []))
        if got < g["payable_p"]:
            waiting.append({"vendor": g["name"], "vendor_norm": g["norm"],
                            "payable_p": g["payable_p"], "written_p": got,
                            "short_p": g["payable_p"] - got})
    extra = [{"vendor_norm": k, "written_p": sum(c["amount_p"] for c in v)}
             for k, v in live.items()
             if not any(g["norm"] == k for g in cheq)]
    return {"owed_p": owed_p, "written_p": written_p, "gap_p": owed_p - written_p,
            "waiting": waiting, "extra": extra, "n_live": sum(len(v) for v in live.values())}


def _cheque_parse_date_s270(raw):
    """Accepts yyyy-mm-dd and the dd-mm-yyyy the owner's eye reads. Returns ISO
    or None. It never guesses between the two: a four-digit run decides which
    end the year is on."""
    s = str(raw or "").strip().replace("/", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s)
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12) or not (2000 <= y <= 2099) or d < 1:
        return None
    dim = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]
    if d > dim:
        return None
    return "%04d-%02d-%02d" % (y, mo, d)


@bp.route("/api/cheque", methods=["POST"])
def api_cheque_s270():
    """Log one cheque. Deliberately allowed on a FINAL month -- see the note at
    the head of this block. It writes no figure the sheet reads."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _cheque_writer_s284(u, _db()):
        return _refuse("Only a cheque writer may log a cheque.")
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor_norm = str(b.get("vendor_norm") or "").strip()
    vendor = str(b.get("vendor") or vendor_norm).strip()
    payee = str(b.get("payee") or vendor).strip()[:120]
    cheque_no = str(b.get("cheque_no") or "").strip()[:40]
    bank = str(b.get("bank") or "").strip()[:80]
    note = str(b.get("note") or "").strip()[:300]
    if not re.match(r"^\d{4}-\d{2}$", month) or not vendor_norm:
        return jsonify(ok=False, error="malformed", message="month and vendor_norm"), 400
    if not cheque_no:
        return _refuse("A cheque needs its number. That is the whole point of the register.")
    iso = _cheque_parse_date_s270(b.get("cheque_date"))
    if not iso:
        return _refuse("That date could not be read. Write it as 14-09-2026 or 2026-09-14.")

    amt = _int_or_none(b.get("amount_p"))
    if amt is None:
        raw = str(b.get("amount") or "").replace(",", "").replace("₹", "").strip()
        try:
            amt = int(round(float(raw) * 100))
        except ValueError:
            amt = None
    if amt is None or amt <= 0:
        return _refuse("A cheque needs an amount above zero.")

    con = _db()
    _ensure(con)
    _pay_ensure(con)
    _cheque_ensure(con)

    clash = con.execute("SELECT id, month, vendor, cheque_date FROM purchase_cheque "
                        "WHERE cheque_no=? AND voided_at IS NULL",
                        (cheque_no,)).fetchone()
    if clash:
        return _refuse("Cheque %s is already on the register — %s, %s, for %s. "
                       "Void that one first if this is a correction."
                       % (cheque_no, clash["month"], clash["cheque_date"], clash["vendor"]))

    cur = con.execute(
        "INSERT INTO purchase_cheque (month, vendor_norm, vendor, payee, cheque_no, "
        "cheque_date, amount_p, bank, note, created_at, created_by) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (month, vendor_norm, vendor, payee, cheque_no, iso, amt,
         bank or None, note or None, now_iso(), _who(u)))
    _audit(con, _who(u), "cheque_logged", "%s %s" % (month, vendor_norm),
           {"cheque_no": cheque_no, "date": iso, "amount_p": amt, "payee": payee})
    con.commit()
    return jsonify(ok=True, id=cur.lastrowid, cheque_no=cheque_no, cheque_date=iso, amount_p=amt)


@bp.route("/api/cheque-mark", methods=["POST"])
def api_cheque_mark_s270():
    """Handed over, or voided. Nothing is ever deleted: a void keeps the row,
    its number and its reason, and only then frees the number for reuse."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _cheque_writer_s284(u, _db()):
        return _refuse("Only a cheque writer may mark a cheque.")
    b = request.get_json(silent=True) or {}
    cid = _int_or_none(b.get("id"))
    what = str(b.get("what") or "").strip()
    if cid is None or what not in ("handed", "unhanded", "void"):
        return jsonify(ok=False, error="malformed", message="id and what"), 400
    con = _db()
    _ensure(con)
    _cheque_ensure(con)
    row = con.execute("SELECT * FROM purchase_cheque WHERE id=?", (cid,)).fetchone()
    if not row:
        return _refuse("No such cheque on the register.")
    if row["voided_at"]:
        return _refuse("Cheque %s is already voided. A voided row never changes again."
                       % row["cheque_no"])

    if what == "void":
        if _is_viewer_only(u):
            return _refuse("Only the doctor or a checker may void a cheque.")
        reason = str(b.get("reason") or "").strip()[:300]
        if not reason:
            return _refuse("A void needs a reason, in your own words.")
        con.execute("UPDATE purchase_cheque SET voided_at=?, voided_by=?, void_reason=? "
                    "WHERE id=?", (now_iso(), _who(u), reason, cid))
        _audit(con, _who(u), "cheque_void", str(cid),
               {"cheque_no": row["cheque_no"], "reason": reason})
    elif what == "handed":
        con.execute("UPDATE purchase_cheque SET handed_at=?, handed_by=? WHERE id=?",
                    (now_iso(), _who(u), cid))
        _audit(con, _who(u), "cheque_handed", str(cid), {"cheque_no": row["cheque_no"]})
    else:
        con.execute("UPDATE purchase_cheque SET handed_at=NULL, handed_by=NULL WHERE id=?",
                    (cid,))
        _audit(con, _who(u), "cheque_unhanded", str(cid), {"cheque_no": row["cheque_no"]})
    con.commit()
    return jsonify(ok=True, id=cid, what=what)


def _cheque_card_s270(con, month, prefix, groups, editable):
    """The card that replaces the bare 'Paid by cheque' list on the sheet: the
    same vendors, each now carrying its cheque or the one line that logs it."""
    _cheque_ensure(con)
    cheq = [g for g in groups if g["route"] != "NEFT"]
    rec = _cheque_recon_s270(con, month, groups)
    live = _cheque_by_vendor_s270(con, month)

    if not cheq and not rec["n_live"]:
        return ('<style>%s</style>' % CHEQUE_CSS
                + '<div class="card"><h2>Paid by cheque</h2><div class="muted">Nobody this month '
                '— every vendor with a bill has a confirmed account. '
                '<a href="%s/page/cheques">The cheque register</a> holds every cheque ever '
                'written here.</div></div>' % prefix)

    rows = []
    for g in cheq:
        mine = live.get(g["norm"], [])
        got = sum(c["amount_p"] for c in mine)
        if mine:
            written = "".join(
                '<div class="chqline"><b>%s</b> <span class="muted">%s</span> '
                '<span class="n">%s</span>%s</div>'
                % (_esc(c["cheque_no"]), _esc(_dmy_s270(c["cheque_date"])), _r(c["amount_p"]),
                   ' <span class="chip">handed over</span>' if c["handed_at"] else "")
                for c in mine)
        else:
            written = '<div class="muted">no cheque logged yet</div>'
        short = g["payable_p"] - got
        state = ""
        if mine and short > 0:
            state = ' <span class="chip warn">%s still to write</span>' % _r(short)
        elif mine and short < 0:
            state = ' <span class="chip warn">%s more than payable</span>' % _r(-short)

        form = ""
        if editable:
            v = _esc(g["norm"])
            form = (
                '<div class="chqform">'
                '<input id="cno_%s" class="pin w" placeholder="cheque no">'
                '<input id="cdt_%s" class="pin w" placeholder="dd-mm-yyyy">'
                '<input id="cpe_%s" class="pin wide" placeholder="payee on the cheque" value="%s">'
                '<input id="cam_%s" class="pin" placeholder="amount" value="%s">'
                '<button class="p" onclick="chqadd(\'%s\')">Log it</button></div>'
                % (v, v, v, _esc(g["name"]), v, ("%.2f" % (max(short, 0) / 100.0)), v))

        rows.append('<div class="chqv"><div class="chqhead"><span class="vn">%s</span>'
                    '<span class="va">%s</span>%s</div>'
                    '<div class="muted small">%s</div>%s%s</div>'
                    % (_esc(g["name"]), _r(g["payable_p"]), state,
                       _esc(g["why"]), written, form))

    if rec["gap_p"] > 0:
        head = ('<div class="bad">%s of this month’s cheque lane has no cheque against it '
                'yet — %d vendor%s waiting.</div>'
                % (_r(rec["gap_p"]), len(rec["waiting"]), "" if len(rec["waiting"]) == 1 else "s"))
    elif rec["gap_p"] < 0:
        head = ('<div class="bad">The cheques written come to %s more than this month’s '
                'cheque lane. Check the register.</div>' % _r(-rec["gap_p"]))
    else:
        head = ('<div class="ok">Every rupee on this month’s cheque lane has a cheque '
                'against it.</div>')

    return ('<div class="card"><h2>Paid by cheque — not in the NEFT file (%d)</h2>'
            '<div class="muted">A vendor whose account is not confirmed on this server is never '
            'put into the bank advice file. Write a cheque, and log it here — number, date '
            'and the payee as written. The moment the account is added and confirmed on the '
            '<a href="%s/page/book">phone book page</a>, that vendor moves to the NEFT lane by '
            'itself.</div>%s%s'
            '<div class="muted" style="margin-top:8px">Owed %s &middot; written %s &middot; '
            '<a href="%s/page/cheques/%s">the cheque register for this month</a></div></div>'
            % (len(cheq), prefix, head, "".join(rows),
               _r(rec["owed_p"]), _r(rec["written_p"]), prefix, month))


def _dmy_s270(iso):
    """The owner reads dates day-first. Stored ISO, shown dd-mm-yyyy."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(iso or ""))
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else (iso or "")


@bp.route("/page/cheques")
@bp.route("/page/cheques/<month>")
def page_cheques_s270(month=None):
    """The register's own screen. Read by anyone who may open the sheet."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if month is not None and not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    _cheque_ensure(con)
    prefix = request.script_root + _url_prefix
    editable = _cheque_writer_s284(u, con)

    months = _cheque_months_s271(con)
    rows = _cheque_rows_s270(con, month)

    strip = ['<a class="mtab%s" href="%s/page/cheques">Every cheque</a>'
             % ("" if month else " on", prefix)]
    for m in months:
        strip.append('<a class="mtab%s" href="%s/page/cheques/%s">%s</a>'
                     % (" on" if m == month else "", prefix, m, _esc(_month_name(m))))
    strip_html = '<div class="card"><div class="mtabs">%s</div></div>' % "".join(strip)

    live = [r for r in rows if not r["voided_at"]]
    total_p = sum(r["amount_p"] for r in live)
    handed = sum(1 for r in live if r["handed_at"])

    recon = ""
    if month:
        s, groups = _pay_rows(con, month)
        rec = _cheque_recon_s270(con, month, groups)
        if rec["gap_p"] > 0:
            wait = "".join('<div class="kvline"><b>%s</b><span>%s still to write</span></div>'
                           % (_esc(w["vendor"]), _r(w["short_p"])) for w in rec["waiting"])
            recon = ('<div class="card"><h2>Against the sheet</h2>'
                     '<div class="bad">The sheet puts %s on the cheque lane this month. '
                     '%s has been written. %s is still owed.</div>%s'
                     '<div class="muted" style="margin-top:8px">'
                     '<a href="%s/page/pay/%s">the payment sheet for this month</a></div></div>'
                     % (_r(rec["owed_p"]), _r(rec["written_p"]), _r(rec["gap_p"]), wait,
                        prefix, month))
        else:
            recon = ('<div class="card"><h2>Against the sheet</h2>'
                     '<div class="ok">The sheet puts %s on the cheque lane this month, and %s '
                     'has been written. Nothing is owed.</div>'
                     '<div class="muted" style="margin-top:8px">'
                     '<a href="%s/page/pay/%s">the payment sheet for this month</a></div></div>'
                     % (_r(rec["owed_p"]), _r(rec["written_p"]), prefix, month))

    if rows:
        trs = []
        for r in rows:
            cls = ' class="void"' if r["voided_at"] else ""
            mark = ""
            if r["voided_at"]:
                mark = ('<span class="chip warn">VOID</span> <span class="muted">%s</span>'
                        % _esc(r["void_reason"] or ""))
            elif editable:
                mark = ('<button class="plainbtn" onclick="chqmark(%d,\'%s\')">%s</button>'
                        % (r["id"], "unhanded" if r["handed_at"] else "handed",
                           "handed over" if r["handed_at"] else "mark handed"))
            elif r["handed_at"]:
                mark = '<span class="chip">handed over</span>'
            vd = ""
            if editable and not r["voided_at"]:
                vd = ('<button class="plainbtn warn" onclick="chqvoid(%d,\'%s\')">void</button>'
                      % (r["id"], _esc(r["cheque_no"])))
            trs.append(
                '<tr%s><td class="mono">%s</td><td>%s</td><td>%s</td><td class="muted">%s</td>'
                '<td class="muted">%s</td><td class="n">%s</td><td>%s</td><td>%s</td></tr>'
                % (cls, _esc(r["cheque_no"]), _esc(_dmy_s270(r["cheque_date"])),
                   _esc(r["payee"]), _esc(r["vendor"]), _esc(r["month"]),
                   _r(r["amount_p"]), mark, vd))
        table = ('<div class="scroll"><table><tr><th>Cheque</th><th>Written on</th><th>Payee</th>'
                 '<th>Vendor</th><th>Month</th><th class="n">Amount</th><th>&nbsp;</th>'
                 '<th>&nbsp;</th></tr>%s</table></div>' % "".join(trs))
    else:
        table = ('<div class="muted">No cheque has been logged%s yet. They are logged from the '
                 'payment sheet, on the vendor the cheque settles.</div>'
                 % ((" for %s" % _month_name(month)) if month else ""))

    body = ('<style>' + CHEQUE_CSS + '</style>'
            '<h1>Cheque register%s</h1>'
            '<div class="muted">Sanjeevni Medicos &middot; every cheque written to a vendor who '
            'is not on the NEFT lane — number, date, payee and the month it settles. '
            'Nothing here is ever deleted; a wrong entry is voided with a reason and stays.</div>'
            '%s%s'
            '<div class="card"><div class="grid">'
            '<div class="kv"><b>%d</b><span>cheques%s</span></div>'
            '<div class="kv"><b>%s</b><span>their total</span></div>'
            '<div class="kv"><b>%d</b><span>handed over</span></div>'
            '<div class="kv"><b>%d</b><span>voided</span></div></div></div>'
            '<div class="card"><h2>The register</h2>%s'
            '<div class="noprint" style="margin-top:10px">'
            '<button class="p" onclick="window.print()">Print this</button></div></div>'
            % ((" — %s" % _esc(_month_name(month))) if month else "",
               strip_html, recon,
               len(live), (" in %s" % _esc(_month_name(month))) if month else " on record",
               _r(total_p), handed, len(rows) - len(live), table))
    return _page("Cheque register", body, CHEQUE_JS.replace("__MONTH__", month or ""))


CHEQUE_JS = """
var M270='__MONTH__';
function chqadd(v){
 var g=function(p){var e=document.getElementById(p+v);return e?e.value:'';};
 var b={month:M270,vendor_norm:v,vendor:'',payee:g('cpe_'),cheque_no:g('cno_'),
        cheque_date:g('cdt_'),amount:g('cam_')};
 if(!b.cheque_no){alert('The cheque number, please \\u2014 that is what the register is for.');return;}
 fetch(P+'/api/cheque',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not log that cheque');return;}
  location.reload();
 }).catch(function(){alert('could not log that cheque just now');});}
function chqmark(id,what){
 fetch(P+'/api/cheque-mark',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({id:id,what:what})}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not do that');return;}
  location.reload();
 }).catch(function(){alert('could not do that just now');});}
function chqvoid(id,no){
 var why=prompt('Voiding cheque '+no+'. Why? (this stays on the register)');
 if(why==null||!why.trim())return;
 fetch(P+'/api/cheque-mark',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({id:id,what:'void',reason:why})})
 .then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not void that');return;}
  location.reload();
 }).catch(function(){alert('could not void that just now');});}
"""

CHEQUE_CSS = """
.ok{color:#2f6b45}
.chqv{border-top:1px solid var(--line);padding:10px 0}
.chqv:first-of-type{border-top:0}
.chqhead{display:flex;gap:10px;align-items:baseline}
.chqhead .vn{flex:1;font-weight:600}
.chqhead .va{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.small{font-size:12.5px}
.chqline{font-size:13.5px;padding:3px 0}
.chqline .n{font-variant-numeric:tabular-nums}
.chqform{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}
input.pin.w{width:120px;text-align:left}
input.pin.wide{width:210px;text-align:left;flex:1 1 180px}
.mtabs{display:flex;flex-wrap:wrap;gap:6px}
a.mtab{display:inline-block;padding:5px 11px;border:1px solid var(--line);border-radius:18px;
 font-size:13px;text-decoration:none}
a.mtab.on{border-color:var(--ink);font-weight:600}
tr.void td{opacity:.55;text-decoration:line-through}
tr.void td:last-child,tr.void td:nth-last-child(2){text-decoration:none}
td.mono{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
button.plainbtn{background:none;border:0;padding:2px 0;font:inherit;font-size:12.5px;
 color:var(--muted);cursor:pointer;text-decoration:underline}
button.plainbtn.warn{color:#a33}
.kvline{display:flex;gap:10px;justify-content:space-between;padding:3px 0;font-size:13.5px}
.kvline b{font-weight:600}
"""

# The sheet's own script gains the three cheque functions, so the form on the
# payment sheet works there too. page_pay already substitutes __MONTH__.
# PAY_JS reaches ONLY the payment sheet, so nothing else grows by a byte.
PAY_JS = PAY_JS + CHEQUE_JS

# THE SHARED STYLESHEET IS DELIBERATELY NOT TOUCHED (F-478).
# An earlier draft did `CSS = CSS + CHEQUE_CSS`, and the walk caught it on the
# box: /hub, /scans, /orders and /book each grew by exactly 1,287 bytes -- four
# screens with nothing to do with cheques, carrying cheque CSS. The style now
# travels with the two things that need it and with nothing else.


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
    gate = (False, []) if final else _lock_gate(con, month, s)          # S604: the one gate
    s749 = _s749_states(con, month)                                       # S749: the register's word and whose/next per bill
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
    signed_ids = set(s.get("signed") or [])                    # S604 (F-956 B)
    for name, bills in groups:
        out.append('<tr><th colspan="9" style="text-transform:none;font-size:14px;color:var(--ink);'
                   'padding-top:14px">%s</th></tr>' % _esc(name))
        for b in bills:
            t = _bill_lines(b, s["sets"], s["stray"])
            tot, n = (t["net_p"], t["n"]) if t else (0, 0)
            lk = links.get(b["id"])
            if lk:
                scan = '<a href="%s/bills/%d" target="_blank">scan %s</a>' % (_assets_url, lk[0], lk[1].lower())
            elif _scan_overdue(b["bill_date"]):                # S403 (D618): unscanned 3 days after arrival = red
                scan = '<span class="bad">no scan \u2014 %d days</span>' % _scan_age(b["bill_date"])
            else:
                scan = '<span class="muted">no scan</span>'
            v = b["verdict"] or ""
            if v == "WRONG":
                vh = ('<span class="chip bad">WRONG</span> <span class="muted">should be %s: %s</span>'
                      % (_r(b["wrong_amount_p"]), _esc(b["reason"])))
            elif v == "CORRECT":
                vh = '<span class="chip ok">Correct</span>' + (
                    ' <span class="muted">%s</span>' % _esc(b["reason"])
                    if (b["reason"] or "").startswith("resolved:") else "")     # S371
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
            elif b["id"] in signed_ids:
                vh = ('<span class="ok">agrees</span> <span class="muted">a purchase return \u2014 Marg prints its lines as a '
                      'purchase; counted as a return</span>')
            else:
                vh = '<span class="ok">agrees</span>'
            btn = ""
            if not final and not viewer and not doctor and b["id"] in s["needs_verdict"]:      # S749: not on the doctor's view
                btn = ('<span class="noprint"> <button class="sm" onclick="verdict(%d,\'CORRECT\')">Correct</button>'
                       ' <button class="sm" onclick="verdict(%d,\'WRONG\')">Wrong</button></span>' % (b["id"], b["id"]))
            sw_, sn_, _sk = s749.get(b["id"]) or ("\u2014", "", "")            # S749
            out.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                       '<td class="n">%d</td><td>%s</td><td><b>%s</b></td><td class="muted">%s</td><td>%s%s</td></tr>'
                       % (_human(b["bill_date"]), _esc(b["bill_no"]), _r(b["marg_p"]), _r(tot) if n else "\u2014",
                          n, scan, _esc(sw_), _esc(sn_), vh, btn))
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
                "bad" if s["wrong"] else "", s["wrong"], s["to_check"], _esc(s["story"] if final else _story_gated(s, gate))))
    if final:
        st = ('<div class="note"><b>FINAL</b> \u2014 %s, %s IST.%s</div>'
              % (_esc(s["status"]["finalised_by"]), _esc(_when_ist(s["status"]["finalised_at"])),
                 ' <button class="sm noprint" onclick="reopen(\'%s\')">reopen</button>' % month if doctor else ""))
    else:
        if gate[0]:
            st = ('<div class="note"><b>PROVISIONAL</b> \u2014 ready to finalise. %s</div>'
                  % ('<button class="p noprint" onclick="finalise(\'%s\')">FINALISE %s</button>' % (month, _esc(_month_name(month)))
                     if doctor else '<span class="muted">Only the doctor can finalise.</span>'))
        else:
            st = ('<div class="note"><b>PROVISIONAL</b> \u2014 cannot finalise yet:<ul>%s</ul>%s</div>'
                  % ("".join("<li>%s</li>" % _esc(r) for r in gate[1]),
                     '<span class="muted">The FINALISE button appears for the doctor once these are cleared.</span>'))
    body = (_s749_strip(con, month, "month") + '<h1>%s \u2014 purchases</h1><div class="muted">This is the purchase audit \u2014 one row per Marg bill. To pay the month, open <b><a href="%s/page/pay/%s">the payment sheet for %s</a></b>. The amount is Marg\'s '
            'supplier-wise figure (bill-wise while supplier-wise is not yet exported). Item-wise is the NET '
            '(after discount) sum of that bill\'s lines, from the latest export that carries the bill.</div><div class="card">%s%s</div><div class="card"><div class="scroll">'
            '<table><tr><th>Date</th><th>Bill</th><th class="n">Amount</th><th class="n">Item-wise (net)</th>'
            '<th class="n">Lines</th><th>Scan</th><th>Purchase check</th><th>Next \u00b7 whose</th><th>Check</th></tr>%s</table></div>%s</div>'
            % (_esc(_month_name(month)), request.script_root + _url_prefix, month,
               _esc(_month_name(month)), recon, st, "".join(out) or
               '<tr><td colspan="9" class="muted">No bills for this month.</td></tr>', und))
    return _page("%s purchases" % _month_name(month), body)


def _scan_from_s409(con):
    """S409 (D625): the owner's ruling -- pharmacy bill scanning starts from setting porders.scan_from (01-Sep-2026)."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.scan_from'").fetchone()
        v = str(r[0]).strip() if r and r[0] else ""
        return v if re.match(r"^\d{4}-\d{2}-\d{2}$", v) else "2026-09-01"
    except sqlite3.Error:
        return "2026-09-01"


@bp.route("/page/scans")
def page_scans():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    _rematch_if_changed(con, "scans")                          # S225 rev 9
    if request.args.get("legacy") != "1":
        return _s454_register_page(con, u)                     # S454 (7.1): the month's register; ?legacy=1 keeps the old tables
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
    bills = con.execute("SELECT b.* FROM purchase_bill b WHERE b.bill_date>=? AND " + EFF_BILL +      # S409: from porders.scan_from
                        " ORDER BY b.bill_date DESC, b.supplier", (_scan_from_s409(con),)).fetchall()
    un_s = [s for s in scans if s["id"] not in linked]
    un_b = [b for b in bills if b["id"] not in linked_bills]
    why = _scan_state_s439(con)                                # S439 (F-661): why each unmatched scan has no link
    hint = {}                                                  # S439: bill id -> the open scan that is probably this bill
    for _sid in sorted(why):
        if why[_sid].get("hint_bill") and _sid not in linked:
            hint.setdefault(why[_sid]["hint_bill"], _sid)
    btn = ('<button class="p noprint" onclick="rematch()">Re-match now</button>'
           if not _is_viewer_only(u) else "")
    t1 = "".join('<tr><td><a href="%s/bills/%d" target="_blank">#%d</a></td><td>%s</td><td>%s</td>'
                 '<td>%s</td><td class="n">%s</td><td class="muted">%s / %s</td><td>%s</td></tr>'
                 % (_assets_url, s["id"], s["id"], _esc(s["vendor"]), _esc(s["bill_no"]),
                    _human(s["bill_date"]) if s["bill_date"] else "—", _r(s["amount_p"]),
                    _esc(s["status"]), _esc(s["ocr_status"]),
                    _esc((why.get(s["id"]) or {}).get("detail") or "not checked yet \u2014 the next match says why")) for s in un_s)
    t2 = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td><a href="%s/page/month/%s">%s</a></td><td>%s</td></tr>'
                 % (_human(b["bill_date"]), _esc(b["supplier"]), _esc(b["bill_no"]), _r(b["amount_p"]),
                    prefix, b["month"], _esc(_month_name(b["month"] or "")),
                    ('<a href="%s/bills/%d" target="_blank">scan #%d</a> <span class="muted">is probably this bill \u2014 read differently, do not scan again</span>'
                     % (_assets_url, hint[b["id"]], hint[b["id"]])) if b["id"] in hint else "") for b in un_b)
    body = ('<h1>Scan links</h1><div class="muted">Pharmacy scans in the asset app, paired with Marg\'s '
            'bills. EXACT = vendor, bill number (its last digits) and amount agree; PROBABLE = bill number and amount, or vendor '
            'and bill number, or vendor, date (within 3 days) and amount. A second scan of a bill is marked, never linked twice; '
            'every scan still open says why (S439).</div><div class="card"><div class="row spread"><div>'
            '<b>%d</b> links stored &middot; <b>%d</b> scans with no Marg bill &middot; <b>%d</b> Marg '
            'bills with no scan</div>%s</div></div>'
            '<div class="card"><h2>Scans with no Marg bill (%d)</h2><div class="scroll"><table><tr><th>Scan</th>'
            '<th>Vendor</th><th>Bill no</th><th>Date</th><th class="n">Amount</th><th>Status / OCR</th><th>Why it is not linked</th></tr>%s</table></div></div>'
            '<div class="card"><h2>Marg bills with no scan (%d)</h2><div class="scroll"><table><tr><th>Date</th>'
            '<th>Supplier</th><th>Bill no</th><th class="n">Amount</th><th>Month</th><th>A scan already here?</th></tr>%s</table></div></div>'
            % (len(linked_bills), len(un_s), len(un_b), btn, len(un_s),
               t1 or '<tr><td colspan="7" class="muted">none</td></tr>', len(un_b),
               t2 or '<tr><td colspan="6" class="muted">none</td></tr>'))
    red = [b for b in un_b if _scan_overdue(b["bill_date"])]          # S403 (D618): the same red list as the Purchase orders screen
    if red:
        body = body.replace('<div class="card"><h2>Scans with no Marg bill',
                            '<div class="card"><h2 class="bad">Unscanned 3 days after arrival (%d)</h2><div class="muted">Reception scans these from the '
                            'Purchase orders screen (Bill scan karo); the intake opens with the vendor, bill number and amount filled in.</div>'
                            '<div class="scroll"><table><tr><th>Date</th><th>Supplier</th><th>Bill no</th><th class="n">Amount</th><th class="n">Days</th></tr>%s</table></div></div>'
                            '<div class="card"><h2>Scans with no Marg bill' % (len(red), "".join(
                                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n bad">%d</td></tr>'
                                % (_human(b["bill_date"]), _esc(b["supplier"]), _esc(b["bill_no"]), _r(b["amount_p"]), _scan_age(b["bill_date"])) for b in red)), 1)
    body = _scan_flow_s440(con, body)                          # S440 (D640): the BACK bar, the five groups of Scan ka kaam (read-only), the up-arrow
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
    _as_s417, snap_s417 = _latest_snapshot(con)               # S417: the stock in the order's own unit
    orth_s417 = _ortho_set(con)
    for i, v in enumerate(plan["vendors"]):
        phone = "" if viewer else book_number(con, v["vendor"], "call")      # S574: a tel: link rings the Calls number
        tel = (' &middot; <a href="tel:%s">call %s</a>' % (_esc(phone), _esc(phone))) if phone else ""
        lines = "".join(
            '<tr><td>%s%s</td><td class="n">%s</td><td class="n"><b>%d</b> %s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%.1f</td><td class="n">%s</td><td class="muted">%s%s</td></tr>'
            % (_esc(l["item"]), ' <span class="chip warn">confirm</span>' if l["confirm"] else "",
               _esc(_stock_of(l, snap_s417, orth_s417)), l["order_strips"], _esc(_uw(l)), _esc(l["pack_size"]), _r(l["rate_p"]),
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
        phone = "" if viewer else book_number(con, o["vendor"], "call")      # S574: a tel: link rings the Calls number
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


# S417 (F-636, 26-Sep-2026): the stock beside an order, in the order's own unit. The owner, first day on the order pages: "the orders page
# shows the stock in tablets and the order in strips -- confusing." Strips + loose from the item's pack size (the spine's reading,
# stock_snapshot.pack_size / packing -- the packing text decides when the pack size says 1); pieces for an orthotic; bottles / tubes / units
# where the packing is not a strip; a pack size nobody knows prints the raw count WITH its unit word, never a bare number. The WhatsApp
# text (the D-decided format) is untouched.
def _pack_from_packing(packing):
    m = re.match(r"^\s*\d+\s*\*\s*(\d+)", str(packing or ""))
    return int(m.group(1)) if (m and int(m.group(1)) > 1) else 0


def stock_text(units, pack_size, packing, ortho=False):
    """124 units of a 10-strip -> '12 strips + 4'; an orthotic -> '3 pcs'; a syrup -> '3 bottles'; unknown pack -> '5 units'."""
    try:
        n = int(round(float(units or 0)))
    except (TypeError, ValueError):
        n = 0
    neg, a = n < 0, abs(n)
    if ortho:
        return "%s%d pc%s" % ("\u2212" if neg else "", a, "" if a == 1 else "s")
    try:
        size = int(pack_size or 0)
    except (TypeError, ValueError):
        size = 0
    if size <= 1:
        size = _pack_from_packing(packing)
    if size > 1:
        s, loose = divmod(a, size)
        txt = "%d strip%s" % (s, "" if s == 1 else "s") + ((" + %d" % loose) if loose else "")
        return ("\u2212(%s)" % txt) if neg else txt
    return "%s%d %s" % ("\u2212" if neg else "", a, _unit_word(packing, 1, a))


def _ortho_set(con):
    """S417: the orthotics of the section map (norm keys) -- their stock reads in pieces."""
    try:
        return {norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")}
    except Exception:                                               # noqa: BLE001
        return set()


def _stock_of(l, snap, orth):
    """S417: a plan line's stock in words (the snapshot gives the packing the line does not carry)."""
    s = snap.get(norm(l["item"])) or {}
    return stock_text(l.get("on_hand"), l.get("pack_size") or s.get("pack_size"), l.get("packing") or s.get("packing"), norm(l["item"]) in orth)


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
    orth = _ortho_set(con)                                      # S417
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
                              stock_text=stock_text(l["on_hand"], l["pack_size"], s.get("packing"), norm(l["item"]) in orth),   # S417
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
        rows = "".join('<tr><td>%s</td><td class="n">%s</td><td class="n"><b>%d</b> %s</td></tr>'
                       % (_esc(l["item"]), _esc(l.get("stock_text") or l["on_hand"]), l["qty"], _unit_word(l["packing"], l["pack_size"], l["qty"]))
                       for l in v["lines"])
        if v["no_vendor"]:
            btns = '<span class="muted">No stockist on record for these &mdash; ask Dr Manoj.</span>'
        elif v["has_phone"]:
            phones = book_shown(con, v["vendor"])                 # S574: the one reader (OFF: numbers 1-2, as before)
            btns = (" ".join(                                            # S662: no Send button -- the order list sends
'<a href="tel:%s"><button>Call%s</button></a>' % (_esc(_wa_digits(p)), (" %d" % (k + 1)) if len(phones) > 1 else "")
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
    body = ('<h1>Order medicines</h1><div class="muted">Stock as on %s. Orders are not sent from this page: they go from the '
            'one order list (<b>Order karna hai</b>), one WhatsApp per order. '
            '<b>Call</b> rings the stockist. <b>Print A4</b> is for the reception printer. When the goods come, '
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


S574_COLS = (("phone3", "TEXT"), ("phone4", "TEXT"), ("email1", "TEXT"), ("email2", "TEXT"), ("call_pick", "INTEGER"),
             ("order_pick", "INTEGER"), ("pay_pick", "INTEGER"), ("display_name", "TEXT"), ("merged_into", "TEXT"))
S574_TABLES = ("CREATE TABLE IF NOT EXISTS purchase_vendor_premerge (id INTEGER PRIMARY KEY AUTOINCREMENT, merged_at TEXT, merged_by TEXT, "
               "bill_norm TEXT, register_norm TEXT, bill_row_json TEXT, register_row_json TEXT, undone_at TEXT, undone_by TEXT)",
               "CREATE TABLE IF NOT EXISTS purchase_book_change (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, who TEXT, vendor_norm TEXT, "
               "what TEXT, old4 TEXT, new4 TEXT)")


def _ensure_book(con):
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    for col, typ in BOOK_COLS + S574_COLS:                     # S574: numbers 3-4, two emails, the three picks, the name kept, the merge
        if col not in have:
            con.execute("ALTER TABLE purchase_vendor_contact ADD COLUMN %s %s" % (col, typ))
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for sql in S574_TABLES:                                    # S574: the two rows as they stood before a merge (kept for undo); the changes
        con.execute(sql)
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?, '0', ?)",
                (BOOK_ON_KEY, "S574: one record per dealer -- '1' from the owner's tap on the phone book page; '0' reads the book as before S574"))
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


S574_OWNER_ACTIONS = ("add", "phones", "picks", "merge", "unmerge", "switch")
S574_USE_WORDS = (("call", "Calls"), ("order", "Order WhatsApp"), ("pay", "Payment msg"))
S574_UNDO_CLOSED = "Undo is closed: numbers were changed after the merge."
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _s574_d10(s):
    """A number's last 10 digits -- how two numbers are compared; '' when it has fewer."""
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""


def _s574_4(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-4:] if d else ""


def _s574_change(con, who, vendor_norm, what, old="", new=""):
    """One line of the book's change list -- the last 4 digits only, never a full number."""
    con.execute("INSERT INTO purchase_book_change (at, who, vendor_norm, what, old4, new4) VALUES (?,?,?,?,?,?)",
                (now_iso(), who or "", vendor_norm or "", what, _s574_4(old), _s574_4(new)))


def _s574_mobile(s):
    """A number saved from the one-record page: 10 digits starting 6-9 (91 or 0 in front dropped); '' for a blank."""
    d = _clean_phone(s)
    if d and not re.match(r"^[6-9]\d{9}$", d):
        raise ValueError("a mobile number is 10 digits starting 6, 7, 8 or 9")
    return d


def _s574_email(s):
    v = str(s or "").strip()[:120]
    if v and (v.count("@") != 1 or not EMAIL_RE.match(v)):
        raise ValueError("an email has one @ and a dot after it")
    return v


def _book_save(con, u, b):
    """One door. Audit by field name and last-4 only. S574: numbers, picks, adding a supplier, the merge, its undo and the switch are
    Dr Manoj's alone, switch ON or OFF (the owner, 18-Oct 05:57 IST: staff hand him the number); bank and verify as before. A write names
    the record by its vendor_norm (the one-record page posts it); with the switch ON a write to a merged-away row lands on its one record."""
    action = str(b.get("action") or "")
    who = _who(u)
    if action in S574_OWNER_ACTIONS and not _is_doctor(u):
        return _refuse("Numbers are changed only by Dr Manoj.")
    if action in ("merge", "unmerge", "switch"):
        return _s574_owner_act(con, who, action, b)
    vendor = str(b.get("vendor") or "").strip()[:120]
    vn = str(b.get("vendor_norm") or "").strip()[:160]
    if action == "add" or not vn:
        if not vendor:
            return jsonify(ok=False, error="malformed", message="stockist name required"), 400
        key = supplier_key(vendor)
    else:
        key = vn
    on = book_on(con)
    row = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,)).fetchone()
    if on and row is not None and action != "add" and row["merged_into"]:
        one = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (row["merged_into"],)).fetchone()
        if one is not None:
            row, key = one, one["vendor_norm"]
    try:
        if action == "add":
            if row is not None or (on and book_record(con, vendor) is not None):
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
            _s574_change(con, who, key, "added", "", p1)
            con.commit()
            return jsonify(ok=True, vendor=vendor, bank_status=status)
        if row is None:
            return jsonify(ok=False, error="no_such_vendor", message="%s is not in the book." % (vendor or vn)), 404
        if action == "phones":
            if on:
                ps = [_s574_mobile(b.get(s)) for s in BOOK_SLOTS]
                ems = [_s574_email(b.get(e)) for e in ("email1", "email2")]
            else:
                ps, ems = [_clean_phone(b.get("phone")), _clean_phone(b.get("phone2"))], []
            if not ps[0]:
                return jsonify(ok=False, error="malformed", message="the first phone number is required"), 400
            if on:
                con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, email1=?, email2=?, source='server', "
                            "updated_at=? WHERE vendor_norm=?", tuple(ps) + tuple(ems) + (now_iso(), key))
            else:
                con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, source='server', updated_at=? WHERE vendor_norm=?",
                            (ps[0], ps[1], now_iso(), key))
            _audit(con, who, "book_phones", key, dict(vendor=row["vendor"], phone=_last4(ps[0]), phone2=_last4(ps[1]),
                                                      was=_last4(row["phone"]), was2=_last4(row["phone2"]),
                                                      **(dict(phone3=_last4(ps[2]), phone4=_last4(ps[3]), was3=_last4(row["phone3"]),
                                                              was4=_last4(row["phone4"]), emails=len([e for e in ems if e])) if on else {})))
            for i, n in enumerate(ps):
                if re.sub(r"\D", "", row[BOOK_SLOTS[i]] or "") != re.sub(r"\D", "", n or ""):
                    _s574_change(con, who, key, "phones: number %d" % (i + 1), row[BOOK_SLOTS[i]], n)
            for i, e in enumerate(ems):
                if (row["email%d" % (i + 1)] or "") != e:
                    _s574_change(con, who, key, "phones: email %d" % (i + 1))
            con.commit()
            return jsonify(ok=True)
        if action == "picks":
            if not on:
                return jsonify(ok=False, error="switch_off", message="Turn on one record per dealer first."), 409
            vals = {}
            for use in BOOK_USES:
                v = b.get("%s_pick" % use)
                if v in (None, "", 0, "0"):
                    vals[use] = None
                    continue
                try:
                    vals[use] = int(v)
                except (TypeError, ValueError):
                    vals[use] = 0
                if not 1 <= vals[use] <= 4:
                    raise ValueError("a pick is number 1, 2, 3 or 4")
            before = {use: book_number(con, key, use) for use in BOOK_USES}
            con.execute("UPDATE purchase_vendor_contact SET call_pick=?, order_pick=?, pay_pick=?, updated_at=? WHERE vendor_norm=?",
                        (vals["call"], vals["order"], vals["pay"], now_iso(), key))
            for use, word in S574_USE_WORDS:
                if row["%s_pick" % use] != vals[use]:
                    _s574_change(con, who, key, "%s: %s" % (word, ("number %d" % vals[use]) if vals[use] else "number 1"),
                                 before[use], book_number(con, key, use))
            _audit(con, who, "book_picks", key, dict(vendor=row["vendor"], **vals))
            con.commit()
            return jsonify(ok=True, saved=True)
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
    return jsonify(ok=False, error="malformed", message="action add|phones|picks|bank|verify|merge|unmerge|switch"), 400


# ---- S574: the merge (the owner's tap only; charter 10: keyed, idempotent, nothing deleted) ----------------------------------------------
def _s574_pending(con):
    """[(Marg's row, the bank sheet's row)] -- the alias pairs where both rows exist and neither is merged yet, by bill_norm."""
    out = []
    try:
        pairs = con.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias ORDER BY bill_norm").fetchall()
    except sqlite3.Error:
        return out
    for bill_norm, reg_norm in pairs:
        mb, rg = _book_row(con, bill_norm), _book_row(con, reg_norm)
        if mb and rg and bill_norm != reg_norm and not mb.get("merged_into") and not rg.get("merged_into"):
            out.append((mb, rg))
    return out


def _s574_name_options(mb, rg):
    """The names the owner may keep: Marg's name with its town dropped (the existing cutter, _acct_name_s265 -- the default), the bank
    sheet's name, Marg's name as printed."""
    out = []
    for x in (_acct_name_s265("", mb.get("vendor"), mb.get("vendor_norm")), rg.get("vendor"), mb.get("vendor")):
        x = " ".join(str(x or "").split())
        if x and x not in out:
            out.append(x)
    return out


def _s574_merge_pair(con, who, mb, rg, name):
    """One pair: the two rows as they stand into purchase_vendor_premerge first; the bank sheet's row keeps its own numbers in their
    slots and takes Marg's numbers that it lacks (by the digits) into its empty slots, up to 4; when the two first numbers differ, all
    three picks name the slot of Marg's first number (what every reader used before the merge); the name kept; Marg's row gets
    merged_into and nothing else. The register row's vendor, acct_name and bank fields are not touched. Returns the numbers left out."""
    t = now_iso()
    con.execute("INSERT INTO purchase_vendor_premerge (merged_at, merged_by, bill_norm, register_norm, bill_row_json, register_row_json) "
                "VALUES (?,?,?,?,?,?)", (t, who, mb["vendor_norm"], rg["vendor_norm"], json.dumps(mb, ensure_ascii=False),
                                         json.dumps(rg, ensure_ascii=False)))
    slots = [rg.get(s) for s in BOOK_SLOTS]
    have = {_s574_d10(x) for x in slots if _s574_d10(x)}
    extra = []
    for p in (mb.get("phone"), mb.get("phone2")):
        d = _s574_d10(p)
        if not d or d in have:
            continue
        free = [i for i, x in enumerate(slots) if not str(x or "").strip()]
        if free:
            slots[free[0]] = str(p).strip()
            have.add(d)
        else:
            extra.append(p)
    picks = (rg.get("call_pick"), rg.get("order_pick"), rg.get("pay_pick"))
    first = _s574_d10(mb.get("phone"))
    if first and first != _s574_d10(rg.get("phone")):
        k = next((i + 1 for i, x in enumerate(slots) if _s574_d10(x) == first), None)
        if k:
            picks = (k, k, k)
    con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, call_pick=?, order_pick=?, pay_pick=?, "
                "display_name=?, updated_at=? WHERE vendor_norm=?", tuple(slots) + tuple(picks) + (name, t, rg["vendor_norm"]))
    con.execute("UPDATE purchase_vendor_contact SET merged_into=? WHERE vendor_norm=?", (rg["vendor_norm"], mb["vendor_norm"]))
    for p in extra:
        _s574_change(con, who, rg["vendor_norm"], "merge: a fifth number left out (%s)" % mb["vendor"], "", p)
    _s574_change(con, who, rg["vendor_norm"], "merged")
    return extra


def _s574_merged(con):
    """The merges standing: premerge rows not undone whose Marg row is still merged into that record."""
    out = []
    try:
        rows = con.execute("SELECT id, merged_at, bill_norm, register_norm, register_row_json FROM purchase_vendor_premerge "
                           "WHERE undone_at IS NULL ORDER BY id").fetchall()
    except sqlite3.Error:
        return out
    for r in rows:
        mb = _book_row(con, r[2])
        if mb and mb.get("merged_into") == r[3]:
            out.append(dict(id=r[0], merged_at=r[1], bill_norm=r[2], register_norm=r[3], register_row_json=r[4]))
    return out


def _s574_undo_closed(con, merged):
    """True once any change line other than 'merged' stands for a merged record after its merge (rule 5: his later edits are kept)."""
    for p in merged:
        m = con.execute("SELECT MAX(id) FROM purchase_book_change WHERE vendor_norm=? AND what='merged'", (p["register_norm"],)).fetchone()
        if con.execute("SELECT 1 FROM purchase_book_change WHERE vendor_norm IN (?,?) AND id>? AND what<>'merged' LIMIT 1",
                       (p["register_norm"], p["bill_norm"], (m[0] if m and m[0] else 0))).fetchone():
            return True
    return False


def _s574_owner_act(con, who, action, b):
    """The doctor's three taps: switch (on / off), merge (all pending pairs), unmerge (every standing merge, refused once closed)."""
    if action == "switch":
        on = str(b.get("on") if b.get("on") is not None else "").strip().lower() in ("1", "true", "on")
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (BOOK_ON_KEY, "1" if on else "0", "S574: one record per dealer"))
        _s574_change(con, who, "", "one record per dealer: %s" % ("ON" if on else "OFF"))
        _audit(con, who, "book_switch", BOOK_ON_KEY, dict(on=on))
        con.commit()
        return jsonify(ok=True, on=on)
    if not book_on(con):
        return jsonify(ok=False, error="switch_off", message="Turn on one record per dealer first."), 409
    if action == "merge":
        names = b.get("names") if isinstance(b.get("names"), dict) else {}
        done, extra = [], []
        try:
            for mb, rg in _s574_pending(con):
                opts = _s574_name_options(mb, rg)
                want = " ".join(str(names.get(rg["vendor_norm"]) or "").split())
                extra += [(rg["vendor_norm"], x) for x in _s574_merge_pair(con, who, mb, rg, want if want in opts else opts[0])]
                done.append(rg["vendor_norm"])
            _audit(con, who, "book_merge", "", dict(n=len(done), records=done, left_out=len(extra)))
            con.commit()
        except sqlite3.Error:
            con.rollback()
            raise
        return jsonify(ok=True, merged=len(done), left_out=[dict(vendor_norm=k, number=_last4(x)) for k, x in extra])
    merged = _s574_merged(con)
    if not merged:
        return jsonify(ok=False, error="nothing_merged", message="Nothing is merged."), 409
    if _s574_undo_closed(con, merged):
        return jsonify(ok=False, error="undo_closed", message=S574_UNDO_CLOSED), 409
    try:
        for p in merged:
            rj = json.loads(p["register_row_json"] or "{}")
            con.execute("UPDATE purchase_vendor_contact SET phone=?, phone2=?, phone3=?, phone4=?, call_pick=?, order_pick=?, pay_pick=?, "
                        "display_name=?, updated_at=? WHERE vendor_norm=?",
                        tuple(rj.get(s) for s in BOOK_SLOTS) + (rj.get("call_pick"), rj.get("order_pick"), rj.get("pay_pick"),
                                                                rj.get("display_name"), now_iso(), p["register_norm"]))
            con.execute("UPDATE purchase_vendor_contact SET merged_into=NULL WHERE vendor_norm=? AND merged_into=?", (p["bill_norm"], p["register_norm"]))
            con.execute("UPDATE purchase_vendor_premerge SET undone_at=?, undone_by=? WHERE id=?", (now_iso(), who, p["id"]))
            _s574_change(con, who, p["register_norm"], "merge undone")
        _audit(con, who, "book_unmerge", "", dict(n=len(merged)))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return jsonify(ok=True, undone=len(merged))


# ---- S574: Marg's push into the one record (switch ON) ------------------------------------------------------------------------------------
def _s574_push_one(con, name, phone):
    """True when the name has a record (it is then handled here): a number already in a slot -> only updated_at; else into the first
    empty slot ('from Marg'); all four full -> nothing written, one 'marg_extra' line per dealer and number. Never a replace, never the
    vendor's name, never a pick, never a row for a merged name. False -> no record: the caller inserts as before."""
    rec = book_record(con, name)
    if rec is None:
        return False
    key = rec["vendor_norm"]
    raw = str(phone or "").strip()
    d = _s574_d10(raw)
    if not d or d in {_s574_d10(rec.get(s)) for s in BOOK_SLOTS}:
        con.execute("UPDATE purchase_vendor_contact SET updated_at=? WHERE vendor_norm=?", (now_iso(), key))
        return True
    free = [s for s in BOOK_SLOTS if not str(rec.get(s) or "").strip()]
    if free:
        con.execute("UPDATE purchase_vendor_contact SET %s=?, updated_at=? WHERE vendor_norm=?" % free[0], (raw, now_iso(), key))
        _s574_change(con, "push_purchases", key, "from Marg", "", raw)
        return True
    if not con.execute("SELECT 1 FROM purchase_book_change WHERE vendor_norm=? AND what='marg_extra' AND new4=?", (key, _s574_4(raw))).fetchone():
        _s574_change(con, "push_purchases", key, "marg_extra", "", raw)
    return True


def _s574_marg_extra(con):
    """[(vendor_norm, last-4)] -- Marg's numbers the full records could not take, while no later number edit stands for that dealer."""
    try:
        return [(r[0], r[1]) for r in con.execute(
            "SELECT c.vendor_norm, c.new4 FROM purchase_book_change c WHERE c.what='marg_extra' AND NOT EXISTS (SELECT 1 FROM "
            "purchase_book_change p WHERE p.vendor_norm=c.vendor_norm AND p.what LIKE 'phones%' AND p.id>c.id) ORDER BY c.id")]
    except sqlite3.Error:
        return []


# ---- the phone book page's parts (one copy each: the OFF page and the one-record page both draw them) --------------------------------------
def _book_src_txt(r):
    return ("added by " + _esc(r["added_by"]) if (r["added_by"] and r["added_by"] != "neft_import_s225") else
            "from the NEFT records (04-Sep)" if (r["source"] or "") == "neft_import" else
            "from Marg / manojz" if (r["source"] or "manojz") != "server" else "edited here")


def _book_bank_cell(r, i, doctor, may_bank):
    """The bank block of a row, as the page has drawn it since S225 (rev 12), with its Add/Edit and Verify. S584 (F-914, rule 13): the
    'add / edit bank details' button and its form slots are drawn only when may_bank (= _s452_may_advice: the owner and Shavez) -- the
    save door refuses 'bank' / 'verify' for anyone else, so Darpan sees the chip and the masked lines, and no button."""
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
    if not may_bank:
        return "%s%s" % ("".join(bank_lines), chip)
    return ('%s%s <button class="sm noprint" onclick="bookForm(%d,\'bank\')">%s bank details</button>'
            '<div class="inl noprint" id="inl-bank-%d" hidden></div><div class="inl noprint" id="inl-verify-%d" hidden></div>'
            % ("".join(bank_lines), chip, i, "edit" if has_bank else "add", i, i))


def _book_add_form(doctor):
    return ('<div class="card" id="addform"><h3>Add a new stockist</h3><div class="grid">'
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


def _s574_switch_line(con):
    on = book_on(con)
    return ('<div class="note noprint" id="s574switch"><b>One record per dealer: %s</b> — <button class="sm%s" onclick="s574Switch(%d)">%s</button>'
            '<span class="bad" id="msg-switch" hidden></span></div>' % ("ON" if on else "OFF", "" if on else " p", 0 if on else 1,
                                                                       "Turn off" if on else "Turn on"))


S574_FIND_JS = r"""
function s574Find(){
  const q = (document.getElementById('s574q').value || '').trim().toUpperCase();
  for (const tr of document.querySelectorAll('#s574book tr[data-q]')) tr.hidden = !!q && tr.dataset.q.indexOf(q) < 0;
}
"""

S574_JS = S574_FIND_JS + r"""
async function s574Post(body, msgEl, reload){
  if (msgEl){ msgEl.className = 'muted'; msgEl.textContent = 'saving...'; msgEl.hidden = false; }
  const r = await fetch(P + '/api/book', {method:'POST', headers:{'Content-Type':'application/json'},
                                          credentials:'same-origin', body: JSON.stringify(body||{})});
  let j = {}; try { j = await r.json(); } catch(e) {}
  if (!r.ok || j.ok === false){
    if (msgEl){ msgEl.className = 'bad'; msgEl.textContent = j.message || j.error || ('HTTP ' + r.status); msgEl.hidden = false; }
    return null;
  }
  if (reload) location.reload();
  return j;
}
function s574Switch(on){ s574Post({action:'switch', on:on}, document.getElementById('msg-switch'), true); }
function s574Merge(){
  const names = {};
  for (const s of document.querySelectorAll('#s574merge select[data-reg]')) names[s.dataset.reg] = s.value;
  s574Post({action:'merge', names:names}, document.getElementById('msg-merge'), true);
}
function s574Undo(){ s574Post({action:'unmerge'}, document.getElementById('msg-undo'), true); }
async function s574Picks(i){
  const b = {action:'picks', vendor_norm:BOOKV[i]};
  for (const u of ['call','order','pay']){ const s = document.getElementById('pk-' + u + '-' + i); b[u + '_pick'] = s ? s.value : ''; }
  const m = document.getElementById('msg-pk-' + i);
  const j = await s574Post(b, m, false);
  if (j && m){ m.className = 'ok'; m.textContent = '✓ Saved'; m.hidden = false; }
}
function s574Edit(i){
  const d = document.getElementById('inl-s574-' + i); if (!d) return;
  if (!d.hidden){ d.hidden = true; d.innerHTML = ''; return; }
  const b = BOOK[BOOKV[i]] || {};
  d.innerHTML = '<div class="grid">' + bookField('Number 1 (10 digits)', 'phone', b.phone, 'numeric') +
      bookField('Number 2 (blank for none)', 'phone2', b.phone2, 'numeric') + bookField('Number 3 (blank for none)', 'phone3', b.phone3, 'numeric') +
      bookField('Number 4 (blank for none)', 'phone4', b.phone4, 'numeric') + bookField('Email 1 (blank for none)', 'email1', b.email1, 'email') +
      bookField('Email 2 (blank for none)', 'email2', b.email2, 'email') + '</div><div class="row" style="margin-top:8px">' +
      '<button class="p sm" onclick="s574Save(' + i + ')">Save</button><button class="sm" onclick="s574Edit(' + i + ')">Cancel</button>' +
      '<span class="bad" id="msg-s574-' + i + '" hidden></span></div>';
  d.hidden = false;
  const first = d.querySelector('input'); if (first) first.focus();
}
function s574Save(i){
  const d = document.getElementById('inl-s574-' + i); const m = document.getElementById('msg-s574-' + i);
  const b = {action:'phones', vendor_norm:BOOKV[i]};
  for (const el of d.querySelectorAll('input')) b[el.name] = el.value.trim();
  for (const k of ['phone','phone2','phone3','phone4']){
    const v = (b[k] || '').replace(/\D/g, '').replace(/^91(?=\d{10}$)/, '').replace(/^0(?=\d{10}$)/, '');
    if (v && !/^[6-9]\d{9}$/.test(v)){ m.textContent = 'A mobile number is 10 digits starting 6, 7, 8 or 9.'; m.hidden = false; return; }
  }
  for (const k of ['email1','email2']){
    const v = b[k] || '';
    if (v && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)){ m.textContent = 'An email has one @ and a dot after it.'; m.hidden = false; return; }
  }
  if (!b.phone){ m.textContent = 'Number 1 is required.'; m.hidden = false; return; }
  s574Post(b, m, true);
}
"""


def _s574_page(con, u, doctor):
    """S574 -- the phone book, one record per dealer (switch ON; mock-up v2 screen 2, in the live page's look). The doctor: everything;
    Shavez: the book to read and the bank details' Add/Edit as before; Darpan: the book to read. The screen follows the door (rule 13)."""
    rows = _book_rows(con)
    may_bank = _s452_may_advice(con, u)                        # S584 (F-914): the door's own test, read once; the screen follows it
    if not may_bank:                                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    also = {}
    for r in rows:
        if r.get("merged_into"):
            also.setdefault(r["merged_into"], []).append(r["vendor"])
    live = sorted((r for r in rows if not r.get("merged_into")), key=lambda r: (r.get("display_name") or r["vendor"] or "").upper())
    keys = [r["vendor_norm"] for r in live]
    names = {r["vendor_norm"]: (r.get("display_name") or r["vendor"]) for r in rows}
    book_json = {r["vendor_norm"]: dict(phone=r["phone"] or "", phone2=r["phone2"] or "", phone3=r.get("phone3") or "", phone4=r.get("phone4") or "",
                                        email1=r.get("email1") or "", email2=r.get("email2") or "", acct_name=r["acct_name"] or "",
                                        acct_no=r["acct_no"] or "", ifsc=r["ifsc"] or "", bank_branch=r["bank_branch"] or "",
                                        upi_id=r["upi_id"] or "") for r in live}
    trs = []
    for i, r in enumerate(live):
        name = r.get("display_name") or r["vendor"]
        others = []
        for x in [r["vendor"]] + also.get(r["vendor_norm"], []):   # S584 (F-913): a name joins 'also' only when norm(x) != norm(name) -- never the record's own spelling
            if x and norm(x) != norm(name) and all(norm(x) != norm(o) for o in others):
                others.append(x)
        nums = book_numbers(dict(r, _s574_on=True))
        if nums:
            ph = " · ".join('<small class="muted">%d</small> <a href="tel:%s">%s</a>' % (s, _esc(n), _esc(n)) for s, n in nums)
        else:
            ph = '<span class="warn">no number yet</span>'
        em = " · ".join(_esc(r.get(e)) for e in ("email1", "email2") if r.get(e))
        picks = ""
        if doctor and len(nums) >= 2:
            sel = []
            for use, word in S574_USE_WORDS:
                cur = _book_pick(r, use)
                opts = ['<option value=""%s>Number 1</option>' % ("" if cur in dict(nums) else " selected")]
                opts += ['<option value="%d"%s>Number %d · …%s</option>' % (s, " selected" if cur == s else "", s, _esc(_s574_4(n))) for s, n in nums]
                sel.append('<label><small class="muted">%s</small> <select id="pk-%s-%d" onchange="s574Picks(%d)">%s</select></label>'
                           % (word, use, i, i, "".join(opts)))
            picks = ('<div class="row noprint" style="margin-top:6px">%s<span class="ok" id="msg-pk-%d" hidden></span></div>' % (" ".join(sel), i))
        elif doctor:
            picks = '<div><small class="muted">Calls · Order WhatsApp · Payment msg: Number 1</small></div>'
        edit = ('<br><button class="sm noprint" onclick="s574Edit(%d)">Edit</button><div class="inl noprint" id="inl-s574-%d" hidden></div>'
                % (i, i)) if doctor else ""
        q = " ".join([name, r["vendor"] or ""] + others).upper()
        trs.append('<tr data-q="%s"><td><b>%s</b>%s<br><small class="muted">%s</small></td><td>%s%s%s%s</td><td>%s</td></tr>'
                   % (_esc(q), _esc(name), ('<br><small class="muted">also: %s</small>' % _esc(", ".join(others))) if others else "",
                      _book_src_txt(r), ph, ('<br><small class="muted">%s</small>' % em) if em else "", picks, edit, _book_bank_cell(r, i, doctor, may_bank)))
    head = []
    if doctor:
        head.append(_s574_switch_line(con))
        pend = _s574_pending(con)
        if pend:
            prow = []
            for mb, rg in pend:
                opts = _s574_name_options(mb, rg)
                first = _s574_d10(mb.get("phone"))
                note = ""
                if first and first != _s574_d10(rg.get("phone")):
                    k = next((j + 1 for j, s in enumerate(BOOK_SLOTS) if _s574_d10(rg.get(s)) == first), None)
                    note = ('<div class="warn"><small>Numbers differ: Marg\'s …%s is %s of the bank sheet\'s record. Calls, Order WhatsApp and '
                            'Payment msg will all use it, as they do today.</small></div>'
                            % (_esc(_s574_4(first)), ("number %d" % k) if k else "added as a number"))
                prow.append('<tr><td>%s<br><small class="muted">%s</small></td><td>%s<br><small class="muted">%s</small></td>'
                            '<td><select data-reg="%s">%s</select>%s</td></tr>'
                            % (_esc(mb["vendor"]), _esc(" · ".join("…" + _s574_4(x) for x in (mb.get("phone"), mb.get("phone2")) if x) or "no number"),
                               _esc(rg["vendor"]), _esc(" · ".join("…" + _s574_4(rg.get(s)) for s in BOOK_SLOTS if rg.get(s)) or "no number"),
                               _esc(rg["vendor_norm"]), "".join('<option%s>%s</option>' % (" selected" if j == 0 else "", _esc(x)) for j, x in enumerate(opts)),
                               note))
            head.append('<div class="card noprint" id="s574merge"><h2>%d dealers are in the book twice</h2><div class="muted">Marg\'s name on the '
                        'left, the bank sheet\'s name on the right (you linked them on 14-Sep). <b>Merge all</b> joins each pair into one record: '
                        'the bank details are not touched, both rows\' numbers are kept (up to 4), and calls, WhatsApp orders and payment messages '
                        'go to the numbers they go to today. It can be undone until a number is changed.</div><div class="scroll"><table><tr>'
                        '<th>Marg\'s name</th><th>Bank sheet\'s name</th><th>Name to keep</th></tr>%s</table></div><div class="row" '
                        'style="margin-top:8px"><button class="p" onclick="s574Merge()">Merge all %d</button><span class="bad" id="msg-merge" hidden>'
                        '</span></div></div>' % (len(pend), "".join(prow), len(pend)))
        merged = _s574_merged(con)
        if merged:
            when = _hhmm_ist_full(merged[-1]["merged_at"] or "")
            if _s574_undo_closed(con, merged):
                head.append('<div class="muted" id="s574undo">%d dealers joined into one record (%s). %s</div>' % (len(merged), _esc(when), S574_UNDO_CLOSED))
            else:
                head.append('<div class="muted noprint" id="s574undo">%d dealers joined into one record (%s). <a href="#" onclick="s574Undo();return false">'
                            'Undo the merge</a> <span class="bad" id="msg-undo" hidden></span></div>' % (len(merged), _esc(when)))
        for vn, n4 in _s574_marg_extra(con):
            head.append('<div class="note" data-s574="marg_extra">Marg has another number for %s (…%s)</div>' % (_esc(names.get(vn, vn)), _esc(n4)))
    try:
        ch = con.execute("SELECT at, who, vendor_norm, what, old4, new4 FROM purchase_book_change ORDER BY id DESC LIMIT 100").fetchall()
    except sqlite3.Error:
        ch = []
    chtr = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (_esc(_hhmm_ist_full(c[0] or "")), _esc(c[1]), _esc(names.get(c[2], c[2]) if c[2] else "—"), _esc(c[3]),
                      _esc(("%s → %s" % (("…" + c[4]) if c[4] else "—", ("…" + c[5]) if c[5] else "—")) if (c[4] or c[5]) else ""))
                   for c in ch)
    body = ('<h1>Stockist phone book</h1><div class="muted">One record per dealer: up to 4 mobile numbers and 2 emails each. %s Bank '
            'details stay on this server only and are shown in full here because this page is the source for the bulk NEFT file — it opens '
            'for Dr Manoj, Darpan and Shavez only. A bank detail added or changed by anyone but Dr Manoj is <b>UNVERIFIED</b> until he taps '
            'Verify; payments will refuse an unverified account.</div>%s'
            '<style>.inl{margin-top:8px;padding:10px;border:1px solid var(--line);border-radius:8px;background:#f6f8fb}'
            '.inl label{display:block;font-size:12.5px;color:var(--muted)}.inl input{width:100%%}</style>'
            '<div class="card noprint"><input id="s574q" placeholder="Search a dealer" oninput="s574Find()" style="width:100%%"></div>'
            '<div class="card"><div class="scroll"><table id="s574book"><tr><th>Dealer</th><th>Numbers</th><th>Bank</th></tr>%s</table></div></div>%s'
            '<div class="card" id="s574changes"><h2>Changes</h2><div class="scroll"><table><tr><th>When</th><th>Who</th><th>Dealer</th><th>What</th>'
            '<th>Number</th></tr>%s</table></div></div>'
            % ("Calls, Order WhatsApp and Payment msg use number 1 unless you pick another; the emails are kept for reference (nothing sends email)."
               if doctor else "Numbers are changed only by Dr Manoj.", "".join(head),
               "".join(trs) or '<tr><td colspan="3" class="muted">nobody in the book yet</td></tr>', _book_add_form(doctor) if doctor else "",
               chtr or '<tr><td colspan="5" class="muted">no change yet</td></tr>'))
    return _page("Stockist phone book", body, BOOK_JS + (S574_JS if doctor else S574_FIND_JS)
                 + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(keys)))


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
    body = request.get_json(silent=True) or {}
    if not _s452_may_advice(con, u):                           # S454 (8, D663): bank details are the owner's and Shavez's
        if str(body.get("action") or "") in ("bank", "verify"):
            return _refuse("Bank details are for Dr Manoj and Shavez.")
        body = {k: v for k, v in body.items() if k not in BANK_FIELDS}
    return _book_save(con, u, body)


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
    if book_on(con):                                            # S574: one record per dealer (the owner's switch)
        return _s574_page(con, u, doctor)
    rows = _book_rows(con)
    may_bank = _s452_may_advice(con, u)                        # S584 (F-914)
    if not may_bank:                                           # S454 (8, D663): account numbers and IFSC for the owner and Shavez only
        rows = [_s454_mask_bank(r) for r in rows]
    vendors = [r["vendor"] for r in rows]
    book_json = {r["vendor"]: dict(phone=r["phone"] or "", phone2=r["phone2"] or "", acct_name=r["acct_name"] or "",
                                   acct_no=r["acct_no"] or "", ifsc=r["ifsc"] or "", bank_branch=r["bank_branch"] or "",
                                   upi_id=r["upi_id"] or "") for r in rows}
    trs = []
    n_nophone = 0
    for i, r in enumerate(rows):
        src_txt = _book_src_txt(r)
        if r["phone"]:
            phones = '<a href="tel:%s">%s</a>%s' % (_esc(r["phone"]), _esc(r["phone"]),
                                                   (' · <a href="tel:%s">%s</a>' % (_esc(r["phone2"]), _esc(r["phone2"]))) if r["phone2"] else "")
        else:
            n_nophone += 1
            phones = '<span class="warn">no number yet</span>'
        numbtn = ('<br><button class="sm noprint" onclick="bookForm(%d,\'phones\')">%s numbers</button>'      # S574: the door is the doctor's
                  '<div class="inl noprint" id="inl-phones-%d" hidden></div>' % (i, "edit" if r["phone"] else "add", i)) if doctor else ""
        trs.append('<tr><td><b>%s</b><br><small class="muted">%s</small></td><td>%s%s</td><td>%s</td></tr>'
                   % (_esc(r["vendor"]), src_txt, phones, numbtn, _book_bank_cell(r, i, doctor, may_bank)))
    add = _book_add_form(doctor) if doctor else ""             # S574: adding a supplier is the doctor's (the door refuses anyone else)
    nophone = ('<div class="note noprint"><b>%d stockist%s without a phone number yet</b> — their bank details came from the NEFT '
               'records; tap <i>add numbers</i> on the row when you have the number.</div>' % (n_nophone, "s" if n_nophone != 1 else "")
               if (n_nophone and doctor) else "")                    # S574: it asks for a tap only the doctor has
    body = ('<h1>Stockist phone book</h1><div class="muted">Two numbers per stockist; bank details stay on this server only and are '
            'shown in full here because this page is the source for the bulk NEFT file — it opens for Dr Manoj, Darpan and Shavez only. '
            'A bank detail added or changed by anyone but Dr Manoj is <b>UNVERIFIED</b> until he taps Verify; payments will refuse an '
            'unverified account. Details on record from the NEFT files stand as accepted (the owner, 04-Sep).</div>%s'
            '<style>.inl{margin-top:8px;padding:10px;border:1px solid var(--line);border-radius:8px;background:#f6f8fb}'
            '.inl label{display:block;font-size:12.5px;color:var(--muted)}.inl input{width:100%%}</style>'
            '<div class="card"><div class="scroll"><table><tr><th>Stockist</th><th>Phones</th><th>Bank</th></tr>%s</table></div></div>%s'
            % (nophone, "".join(trs) or '<tr><td colspan="3" class="muted">nobody in the book yet</td></tr>', add))
    if doctor:                                                  # S574: the doctor's one line -- One record per dealer: OFF -- Turn on
        body = _s574_switch_line(con) + body
    return _page("Stockist phone book", body, BOOK_JS + (S574_JS if doctor else "") + "const BOOK=%s;const BOOKV=%s;" % (json.dumps(book_json), json.dumps(vendors)))


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
        from urllib.parse import quote                         # noqa: PLC0415
        return ('<a href="/scanapp/intake?lane=pharmacy&vendor=%s" target="_blank"><button class="sm">Scan the bill</button></a>'   # S403: the intake opens pre-filled
                '<br><small class="muted">note on the scan: %s · ₹%s</small>%s'
                % (quote(str(o["vendor"] or ""), safe=""), _esc(o["vendor"]), _esc(_r(o["total_p"])[1:]), note))
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
        import hashlib as _h_s454                                  # noqa: PLC0415 -- S454 (D668): a supplier / number / amount filled in later
        z = _h_s454.md5()                                          # (the OCR is a background job) changes the fingerprint too
        for x in acon.execute("SELECT id, COALESCE(vendor,''), COALESCE(bill_no,''), COALESCE(total_amount,''), COALESCE(status,'') "
                              "FROM bills WHERE kind='Pharmacy' ORDER BY id"):
            z.update(("%s|%s|%s|%s|%s\n" % tuple(x)).encode("utf-8", "replace"))
        return "%d:%d:%s" % (r[0], r[1], z.hexdigest()[:12])
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
            '<datalist id="salts">%s</datalist>%s%s<style>tr.done td{color:var(--muted);text-decoration:line-through} tr.done td:first-child,tr.done td:last-child{text-decoration:none}</style>'
            % (done_n, total, (" · <b>Marg confirms %d</b> done in its list of %s" % (marg_done, _esc(_human(marg_as_on)))) if marg_as_on else " (no Marg list pushed yet)", prefix, prefix, dl, _watch_card(con, staff=True),
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


# =====================================================================
# S263 -- ONE FIRM, TWO NAMES.
#
# The bank details for 22 vendors were imported from the April-July 2026 NEFT
# advice sheets at S225, under the NAME THE BANK KNOWS. Marg's bills carry the
# name the VENDOR PRINTS. For 14 of them the two are not the same string, so a
# bill has never once landed on its own account row: they have all been falling
# to the cheque lane while their details sat on the server, correct and
# unreachable. August alone routed Rs 2,22,608 to cheques for this reason.
#
# THE FIX IS A LINK, NOT A COPY. One account still lives in exactly one row; the
# bill's name simply points at it. No account number is duplicated, so there is
# no second copy to go stale, and when Marg renames a supplier again the answer
# is one more row in this table -- not a re-import.
#
# Every pair below was confirmed by the owner on 14-Sep-2026 after the finding
# was put to him, including ESS KAY AGENCIES EXTN, which he checked against the
# bank himself ("verified, correct bank, name on bill is ESS KAY AGENCIES EXTN").
#
# NOT LINKED, deliberately: RAMA MEDICOSE and AGARWAL SURGICALS AND MEDICALS have
# no details anywhere and stay on the cheque lane by his ruling until they come.
#
# NO ACCOUNT NUMBER APPEARS IN THIS FILE, and none ever will: bank numbers do not
# enter the repository. A new vendor's account is carried on the install line and
# written straight into the database by seed_account_s263.py.
# =====================================================================

_ALIAS_S263 = (
    # the name on Marg's bill            the name on the account row
    ("KEDAR PHARMACEUTICAL",             "KEDAR PHARMA"),
    ("GUNINA PHARMACEUTICALS PVT LTD",   "GUNINA PHARMACEUTICALS"),
    ("L.K. DRUG HOUSE",                  "LK DRUG HOUSE"),
    ("SHRADDHA MEDICOSE",                "SHRADDHA MEDICOS"),
    ("YOGENDRA AGENCIES",                "YOGENDRA"),
    ("JUBILEE AGENCIES",                 "JUBLI AGENCY"),
    ("YUVIKA SURGICALS",                 "YUVIKA SURGICAL"),
    ("ESS KAY AGENCIES EXTN",            "ESS KAY AGENCIES"),
    ("RADHA MEDICAL & SCIENTIFIC",       "RADHA MEDICAL AND SCIENTIFIC"),
    ("DRUG DEAL",                        "DRUG DEALS"),
    ("RAVI MEDICAL AGENCY",              "RAVI MEDICAL AGENCIES"),
    ("SAISUN PHARMA PVT. LTD",           "SAISUN PHARMA PRIVATE LIMITED"),
    ("VERMA BROS. AND CO",               "VERMA BROS.AND CO"),
    ("SCIENTIFIC&MEDICAL AID CENTRE",    "SCIENTIFIC & MEDICAL AID CENTRE"),
)

def _alias_ensure_s263(con):
    """The link table. Idempotent: running it on every request must change
    nothing after the first time."""
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_vendor_alias (
        bill_norm     TEXT PRIMARY KEY,
        register_norm TEXT NOT NULL,
        who           TEXT,
        at            TEXT)""")
    for bill_norm, reg_norm in _ALIAS_S263:
        con.execute("INSERT OR IGNORE INTO purchase_vendor_alias "
                    "(bill_norm, register_norm, who, at) VALUES (?,?,?,?)",
                    (bill_norm, reg_norm, "owner (S263, 14-Sep-2026)", now_iso()))
    con.commit()


_vendor_bank_before_s263 = _vendor_bank


def _vendor_bank(con):                                            # noqa: F811
    """As before, and then: a bill name that is linked to a confirmed account
    row inherits that row's NEFT lane, and SAYS WHOSE ROW IT IS. A link to a row
    with no confirmed account changes nothing -- it cannot invent a lane."""
    try:
        _alias_ensure_s263(con)
    except sqlite3.Error:
        pass
    out = _vendor_bank_before_s263(con)
    try:
        rows = con.execute("SELECT bill_norm, register_norm "
                           "FROM purchase_vendor_alias").fetchall()
    except sqlite3.Error:
        return out
    for bill_norm, reg_norm in rows:
        src = out.get(reg_norm)
        if not src or src.get("route") != "NEFT":
            continue
        cur = out.get(bill_norm)
        if cur and cur.get("route") == "NEFT":
            continue
        out[bill_norm] = {"route": "NEFT",
                          "why": "account confirmed — on the register as %s" % reg_norm}
    return out
# ---------------------------------------------------------------------------
# S264 -- the months, on the sheet itself.
#
# /page/pay lands on the newest month and had no way out of it. This is that way
# out: every month the purchase book actually holds, as one tap each, with the
# month being read marked and not a link. Styled inline on purpose -- the page's
# stylesheet is not touched by this kit.
# ---------------------------------------------------------------------------

_NAV_ON_S264 = ("display:inline-block;padding:4px 11px;border-radius:999px;"
                "background:var(--ink);color:#fff;font-weight:600;font-size:13px")
_NAV_OFF_S264 = ("display:inline-block;padding:4px 11px;border-radius:999px;"
                 "border:1px solid var(--line);text-decoration:none;font-size:13px")


def _short_month_s264(m):
    """Aug 26 -- the strip has to fit a phone, so the long name is not used here."""
    try:
        y, mm = m.split("-")
        return "%s %s" % (("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                           "Sep", "Oct", "Nov", "Dec")[int(mm) - 1], y[2:])
    except Exception:
        return m


def _pay_months_nav_s264(con, month, prefix):
    try:
        months = _months(con)
    except Exception:
        return ""
    if not months:
        return ""
    if month not in months:
        months = sorted(set(months) | {month}, reverse=True)
    out = []
    for m in months:
        label = _esc(_short_month_s264(m))
        if m == month:
            out.append('<span style="%s">%s</span>' % (_NAV_ON_S264, label))
        else:
            out.append('<a href="%s/page/pay/%s" style="%s">%s</a>'
                       % (prefix, m, _NAV_OFF_S264, label))
    return ('<div class="card" data-s264="months" style="padding:9px 12px"><div '
            'style="display:flex;flex-wrap:wrap;gap:7px;align-items:center">%s</div></div>'
            % "".join(out))


# =====================================================================
# S265 -- THE ADVICE, EXACTLY AS THE BANK GETS IT.
#
# The owner's ask, 14-Sep-2026: "We should be able to see the exact preview of
# the Excel sheet here as we send it to the bank, because it is printed on blank
# paper A4 and also emailed to the bank from the email account linked to the
# bank account."
#
# So this is not a summary of the advice -- it is the advice. The same four
# letterhead lines, the same seven columns in the same order, the same wording
# ("NEFT", "Vendor Payment"), the same alphabetical order by account name, and
# the same total in the Amount column, as every NEFT ADVICE sheet from April to
# July 2026. Printing this page gives the paper copy; the file for the email is
# built from these same rows.
#
# NO NUMBER FROM THE LETTERHEAD IS IN THIS FILE (F-185). The four printed lines
# are the firm's own stationery; the shop's mobile is not here -- it is handed in
# on the install line and kept in purchase_pay_config. Absent, the line is simply
# not printed and the card says so rather than printing a wrong one.
# =====================================================================

ADVICE_HEAD_S265 = (
    ("GSTIN", "09AAIHM6109G1Z4"),
)
ADVICE_FIRM_S265 = "SANJEEVNI MEDICOS"
ADVICE_ADDR_S265 = "35G/15B, Rampur Bagh, Bareilly (U.P.) - 243001"
ADVICE_DL_S265 = "DL NO. :858/R-20/2014/BLY, 858/RB-21/2014/BLY"


def _pay_config_s265(con, key, default=""):
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_config (
            key TEXT PRIMARY KEY, value TEXT, at TEXT)""")
        r = con.execute("SELECT value FROM purchase_pay_config WHERE key=?", (key,)).fetchone()
        return (r[0] if r and r[0] else default)
    except sqlite3.Error:
        return default


def _acct_name_s265(acct_name, vendor, vendor_norm):
    """The name the bank prints. The account name when the server has one; else
    the vendor's own name with Marg's trailing town dropped -- "JANTA
    PHARMACEUTICALS BAREILLY" is "JANTA PHARMACEUTICALS" on the advice, which is
    what every sheet from April to July 2026 carries. The town is only dropped
    when the normalised name says it is a town: nothing is guessed."""
    nm = " ".join((acct_name or "").split())
    if nm:
        return nm
    nm = " ".join((vendor or "").split())
    norm = " ".join((vendor_norm or "").split())
    if (norm and nm.upper().startswith(norm) and len(nm) > len(norm)
            and nm[len(norm)] == " "):
        # only a whole extra WORD is dropped -- "VERMA BROS.AND CO." keeps its
        # full stop, because what follows the normalised name is not a space
        nm = nm[:len(norm)].strip()
    return nm or norm


def _advice_accounts_s265(con):
    """vendor_norm on the BILL -> the account row it is paid into, following the
    S263 link. Returns only rows that actually carry a confirmed account."""
    out = {}
    cols = _bank_cols(con)
    if not {"vendor_norm", "acct_no", "bank_status"} <= set(cols):
        return out
    name_col = "acct_name" if "acct_name" in cols else "vendor"
    ifsc_col = "ifsc" if "ifsc" in cols else None
    rows = con.execute("SELECT vendor_norm, vendor, COALESCE(acct_no,''), "
                       "COALESCE(bank_status,''), COALESCE(%s,''), %s "
                       "FROM purchase_vendor_contact"
                       % (name_col, ("COALESCE(%s,'')" % ifsc_col) if ifsc_col else "''")
                       ).fetchall()
    reg = {}
    for vn, vendor, acct, status, acct_name, ifsc in rows:
        if (acct or "").strip() and (status or "").strip().upper() == "VERIFIED":
            reg[vn] = {"acct": acct.strip(),
                       "name": _acct_name_s265(acct_name, vendor, vn),
                       "ifsc": (ifsc or "").strip().upper()}
    out.update(reg)
    try:
        for bill_norm, reg_norm in con.execute(
                "SELECT bill_norm, register_norm FROM purchase_vendor_alias"):
            if bill_norm not in out and reg_norm in reg:
                out[bill_norm] = reg[reg_norm]
    except sqlite3.Error:
        pass
    return out


def _advice_rows_s265(con, month):
    """The lines of the advice, in the bank's own order: alphabetical by the name
    on the account, exactly as every sheet from April to July 2026."""
    s, groups = _pay_rows(con, month)
    acc = _advice_accounts_s265(con)
    rows, missing, paise = [], [], False
    for g in groups:
        if g["payable_p"] <= 0:
            continue
        if g["route"] != "NEFT":
            continue
        a = acc.get(g["norm"])
        if not a:
            missing.append(g["name"])
            continue
        if g["payable_p"] % 100:
            paise = True
        rows.append({"acct": a["acct"], "name": a["name"], "ifsc": a["ifsc"],
                     "rupees": int(round(g["payable_p"] / 100.0)),
                     "vendor": g["name"]})
    rows.sort(key=lambda r: r["name"].upper())
    for i, r in enumerate(rows, 1):
        r["sr"] = i
    return rows, sum(r["rupees"] for r in rows), missing, paise


def _signoff_s380(con, role="Authorized Signatory"):
    """S380: the block the owner signs. The firm's name, the rule he signs on, what he signs as, and his
    own name -- typed once into purchase_pay_config.signatory_name and never again. With no name typed
    the rule and the words still print, so the paper is signable the day it is installed."""
    name = _pay_config_s265(con, "signatory_name", "")
    return ('<div class="sgnoff"><div class="s1">For %s</div><div class="sline"></div>'
            '<div class="s2">%s</div>%s</div>'
            % (_esc(ADVICE_FIRM_S265), _esc(role),
               ('<div class="s3">%s</div>' % _esc(name)) if name else ""))


def _advice_paper_s380(con, month, signoff=True):
    """THE ANNEXURE ITSELF -- the one renderer. The card on the payment sheet shows this, the pack prints
    this, and the two therefore cannot drift apart. Same letterhead, same seven columns, same order, same
    total as every file sent since April 2026; S380 adds the sign-off under the total."""
    rows, total, missing, paise = _advice_rows_s265(con, month)
    mob = _pay_config_s265(con, "shop_mobile", "")
    head_right = ("(M) %s" % _esc(mob)) if mob else (
        '<span class="muted">mobile not set on this server</span>')
    trs = []
    for r in rows:
        trs.append('<tr><td class="c">%d</td><td class="c">NEFT</td><td class="mono">%s</td>'
                   '<td>%s</td><td class="mono">%s</td><td class="n">%s</td>'
                   '<td>Vendor Payment</td></tr>'
                   % (r["sr"], _esc(r["acct"]), _esc(r["name"]), _esc(r["ifsc"]),
                      _rupees_s266(r["rupees"])))
    if not trs:
        trs.append('<tr><td colspan="7" class="muted">No vendor is payable by NEFT '
                   'this month.</td></tr>')
    return ('<div id="advice_s265"><div class="lh"><div class="lh1">%s</div>'
            '<div class="lh2">%s</div><div class="firm">%s</div><div class="lh2">%s</div></div>'
            '<div class="scroll"><table class="adv"><tr><th class="c">Sr. No.</th>'
            '<th class="c">Txn. type</th><th>Credit Account Number</th>'
            '<th>Credit Account Name</th><th>IFSC</th><th class="n">Amount</th>'
            '<th>Narration</th></tr>%s'
            '<tr class="tot"><td colspan="5" class="n">Total</td><td class="n">%s</td><td></td>'
            '</tr></table></div>%s</div>'
            % ("GSTIN: %s&nbsp;&nbsp;&nbsp;&nbsp;%s" % (_esc(ADVICE_HEAD_S265[0][1]), head_right),
               _esc(ADVICE_DL_S265), _esc(ADVICE_FIRM_S265), _esc(ADVICE_ADDR_S265),
               "".join(trs), _rupees_s266(total),
               _signoff_s380(con) if signoff else ""))


def _advice_card_s265(con, month, prefix, final):
    rows, total, missing, paise = _advice_rows_s265(con, month)
    warn = ""
    if missing:
        warn += ('<div class="warn">Left out of the advice \u2014 no confirmed account: %s. '
                 'They are on the cheque list above.</div>'
                 % _esc(", ".join(sorted(missing))))
    if paise:
        warn += ('<div class="warn">One or more payables carry paise; the advice is '
                 'rounded to the rupee, as the bank file has always been.</div>')
    if not final:
        warn += ('<div class="warn">DRAFT \u2014 this month is not locked yet. Lock it before '
                 'this is printed or emailed.</div>')
    return (ADVICE_CSS_S265 +
            '<div class="card" id="advcard_s380"><h2>4 &middot; The advice, exactly as the bank gets it</h2>'
            '<div class="muted">The same sheet you print on blank A4 and email to the bank '
            '&mdash; same lines, same columns, same order. '
            '<a class="p noprint" href="%s/page/pay/%s/pack?print=1" target="_blank">Print the bank pack</a> '
            '<button class="sm noprint" onclick="window.print()">print this sheet alone</button> '
            '<a class="p noprint" href="%s/page/pay/%s/advice.xlsx">Download the file for the email</a></div>%s%s</div>'
            % (prefix, month, prefix, month, warn, _advice_paper_s380(con, month)))


ADVICE_TABLE_CSS_S380 = """<style>
#advice_s265 .lh{padding:2px 0 10px}
#advice_s265 .lh1{font-size:12px}
#advice_s265 .lh2{font-size:12px}
#advice_s265 .firm{font-size:19px;font-weight:700;letter-spacing:.3px;padding:2px 0}
table.adv{width:100%;border-collapse:collapse;font-size:12.5px}
table.adv th,table.adv td{border:1px solid #9a9a9a;padding:4px 6px;text-align:left;
  vertical-align:top;white-space:nowrap}
table.adv th{background:#eee;font-weight:700;text-transform:none;font-size:12px}
table.adv td.c,table.adv th.c{text-align:center}
table.adv td.n,table.adv th.n{text-align:right}
table.adv td.mono{font-variant-numeric:tabular-nums}
table.adv tr.tot td{font-weight:700}
.sgnoff{padding-top:34px}
.sgnoff .s1{font-weight:600}
.sgnoff .sline{border-bottom:1px solid #333;width:240px;height:40px}
.sgnoff .s2{font-size:12.5px;padding-top:4px}
.sgnoff .s3{font-weight:600;padding-top:2px}
@media print{
  table.adv th,table.adv td{padding:2px 6px}
  .sgnoff{padding-top:12px;break-inside:avoid;page-break-inside:avoid}
  .sgnoff .sline{height:30px}
}
</style>"""

# S380 (F-616). The pay page's own print. The old rule hid the page with
# `body *{visibility:hidden}` -- which paints nothing but KEEPS every hidden card's layout, so the page
# still filled six sheets and five came out blank. display:none collapses them instead, and only the
# advice card is put back. Nothing else on that page prints; the whole pack prints from /pack.
ADVICE_CSS_S265 = ADVICE_TABLE_CSS_S380 + """<style>
@media print{
  @page{size:A4 landscape;margin:12mm}
  .wrap > *{display:none!important}
  .wrap > #advcard_s380{display:block!important;border:none;padding:0;margin:0}
  #advcard_s380 > h2,#advcard_s380 > .muted,#advcard_s380 > .warn{display:none!important}
  table.adv th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>"""



# =====================================================================
# S266 -- THE COVERING LETTER.
#
# The advice does not go to the bank on its own: it goes with a signed letter
# authorising the debit. This is that letter, word for word as the one Sanjeevni
# has always sent, with three things filled in instead of typed:
#
#   the date        -- today in IST, or whatever he sets
#   the cheque no.  -- the one thing only he knows; typed here, kept per month
#   the amount      -- taken from the advice, never retyped
#
# TWO TYPOS IN THE ORIGINAL ARE FIXED, and said out loud here so nobody thinks
# the letter drifted: the September file read "SEPTEMBAR", and the subject line
# ended "transactions.S" with a stray capital.
#
# NO ACCOUNT NUMBER IS IN THIS FILE (F-185). The firm's own debit account is
# handed in on the install line and kept in purchase_pay_config, exactly as the
# shop's mobile is. Absent, the letter prints a blank to fill by hand and says so.
# =====================================================================

LETTER_BANK_S266 = ("The Manager", "YES Bank Limited", "Rampur Garden,", "Bareilly.")
LETTER_SUB_S266 = "Sub : Authorization to execute Multiple NEFT/RTGS transactions."
LETTER_BODY_S266 = (
    "I authorize YES BANK to execute multiple debits to my account no (%s) vide "
    "cheque number %s for an amount of Rs. %s/ towards NEFT/RTGS request. We agree "
    "for a separate debits to our <b>account</b> basis the type of transactions in "
    "a single file.")
LETTER_TAIL_S266 = "Please process the request as per the enclosed/attached annexure."


def _rupees_s266(n):
    """The bank's own sheets write the amount with NO separators at all -- the
    July file says 97930 and the letter says Rs. 472527/. Anything prettier is
    drift, so this prints the plain integer, and the advice uses it too."""
    try:
        return str(int(round(float(n))))
    except (TypeError, ValueError):
        return str(n)


def _letter_ensure_s266(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_letter (
        month TEXT PRIMARY KEY, date_text TEXT, cheque_no TEXT,
        updated_by TEXT, updated_at TEXT)""")


def _letter_today_s266():
    """SEPTEMBER 14, 2026 -- the form the letter has always used, in IST."""
    now = dt.datetime.now(IST)
    return "%s %d, %d" % (now.strftime("%B").upper(), now.day, now.year)


def _letter_values_s266(con, month):
    _letter_ensure_s266(con)
    r = con.execute("SELECT date_text, cheque_no FROM purchase_pay_letter WHERE month=?",
                    (month,)).fetchone()
    date_text = (r[0] if r and r[0] else "") or _letter_today_s266()
    cheque = (r[1] if r and r[1] else "") or ""
    return date_text, cheque


def _letter_html_s266(con, month, total, standalone=False):
    date_text, cheque = _letter_values_s266(con, month)
    acct = _pay_config_s265(con, "debit_account", "")
    mob = _pay_config_s265(con, "shop_mobile", "")
    acct_h = _esc(acct) if acct else '<span class="blank">____________________</span>'
    cheque_h = _esc(cheque) if cheque else '<span class="blank">____________</span>'
    head_right = ("(M) %s" % _esc(mob)) if mob else ""
    bank = "".join("<div>%s</div>" % _esc(x) for x in LETTER_BANK_S266)
    return (
        '<div id="letter_s266"%s><div class="lh"><div class="lh1">GSTIN: %s&nbsp;&nbsp;&nbsp;&nbsp;%s'
        '</div><div class="lh2">%s</div><div class="firm">%s</div><div class="lh2">%s</div></div>'
        '<div class="dt">Date: %s</div>'
        '<div class="to">%s</div>'
        '<div class="sub">%s</div>'
        '<p class="bd">%s</p>'
        '<p class="bd">%s</p>'
        '<div class="sg"><div>For Authorized Signatory:-</div>'
        '<div class="sgn">For SANJEEVNI MEDICOS</div></div></div>'
        % (' class="standalone"' if standalone else "",
           _esc(ADVICE_HEAD_S265[0][1]), head_right, _esc(ADVICE_DL_S265),
           _esc(ADVICE_FIRM_S265), _esc(ADVICE_ADDR_S265),
           _esc(date_text), bank, _esc(LETTER_SUB_S266),
           LETTER_BODY_S266 % (acct_h, cheque_h, _rupees_s266(total)),
           _esc(LETTER_TAIL_S266)))


def _letter_card_s266(con, month, prefix, final, total):
    date_text, cheque = _letter_values_s266(con, month)
    acct = _pay_config_s265(con, "debit_account", "")
    warn = ""
    if not cheque:
        warn += ('<div class="warn">No cheque number yet &mdash; the letter prints a blank '
                 'line for it.</div>')
    if not acct:
        warn += ('<div class="warn">The debit account is not set on this server, so the '
                 'letter prints a blank there too.</div>')
    if not final:
        warn += ('<div class="warn">DRAFT &mdash; this month is not locked yet.</div>')
    return (LETTER_CSS_S266 +
            '<div class="card" id="lettercard_s380"><h2>5 &middot; The covering letter</h2>'
            '<div class="muted">Word for word as it has always gone, with the date, the '
            'cheque number and the amount filled in from this sheet. It prints with the annexure and '
            'this payment sheet as one pack. '
            '<a class="p" href="%s/page/pay/%s/pack?print=1" target="_blank">Print the bank pack</a> '
            '<a href="%s/page/pay/%s/letter" target="_blank">or this letter alone</a>'
            '</div>%s'
            '<div class="letterset noprint"><label>Date <input class="pin" id="lt_date" '
            'value="%s"></label><label>Cheque number <input class="pin" id="lt_cheque" '
            'value="%s" placeholder="e.g. 115257"></label>'
            '<label>Signature name <input class="pin" id="lt_sign" style="width:200px;text-align:left" '
            'value="%s" placeholder="the name under your signature"></label>'
            '<button class="sm" onclick="saveletter()">save</button>'
            '<span class="muted">Amount: <b>Rs. %s/</b> &mdash; taken from the advice above, '
            'never typed.</span></div>'
            '<div class="letterprev">%s</div></div>'
            '<script>function saveletter(){'
            'fetch(P+"/api/pay-letter",{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({month:"%s",date_text:document.getElementById("lt_date").value,'
            'cheque_no:document.getElementById("lt_cheque").value,'
            'signatory:document.getElementById("lt_sign").value})})'
            '.then(function(r){return r.json();}).then(function(j){'
            'if(!j.ok){alert(j.message||"could not save");return;}location.reload();})'
            '.catch(function(){alert("could not save just now");});}</script>'
            % (prefix, month, prefix, month, warn, _esc(date_text), _esc(cheque),
               _esc(_pay_config_s265(con, "signatory_name", "")),
               _rupees_s266(total), _letter_html_s266(con, month, total), month))


@bp.route("/page/pay/<month>/letter")
def page_pay_letter(month):
    """The letter on its own, portrait A4, nothing else on the paper."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    rows, total, missing, paise = _advice_rows_s265(con, month)
    body = ('<div class="noprint" style="padding-bottom:10px">'
            '<button class="p" onclick="window.print()">Print this letter</button> '
            '<span class="muted">A4, portrait. The advice itself prints from the '
            'payment sheet.</span></div>%s%s'
            % (LETTER_CSS_S266 + LETTER_PAGE_CSS_S266,
               _letter_html_s266(con, month, total, standalone=True)))
    return _page("Covering letter — %s" % _month_name(month), body)


@bp.route("/api/pay-letter", methods=["POST"])
def api_pay_letter():
    """The date and the cheque number, kept per month and audited. The amount is
    never accepted from the browser -- it comes from the advice."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    if not re.match(r"^\d{4}-\d{2}$", month):
        return jsonify(ok=False, error="malformed", message="month"), 400
    con = _db()
    _ensure(con)
    _letter_ensure_s266(con)
    # S380 (D605): the date, the cheque number and the signature name are the LETTER'S OWN WORDS, not a
    # figure of the month. He types them when the payment is actually made -- which is after the month is
    # locked -- so FINAL no longer refuses them. Every write is audited below exactly as before, and no
    # figure on the sheet becomes writable: api/pay-line and every other door keep their own FINAL gate.
    date_text = str(b.get("date_text") or "").strip()[:60]
    cheque = str(b.get("cheque_no") or "").strip()[:40]
    if "signatory" in b:
        sign = str(b.get("signatory") or "").strip()[:80]
        con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_config (
            key TEXT PRIMARY KEY, value TEXT, at TEXT)""")
        was = _pay_config_s265(con, "signatory_name", "")
        con.execute("INSERT INTO purchase_pay_config (key, value, at) VALUES ('signatory_name',?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, at=excluded.at",
                    (sign or None, now_iso()))
        if sign != was:
            _audit(con, _who(u), "pay_signatory", month, {"name": sign, "before": was})
    before = con.execute("SELECT date_text, cheque_no FROM purchase_pay_letter WHERE month=?",
                         (month,)).fetchone()
    con.execute("INSERT INTO purchase_pay_letter (month, date_text, cheque_no, updated_by, "
                "updated_at) VALUES (?,?,?,?,?) ON CONFLICT(month) DO UPDATE SET "
                "date_text=excluded.date_text, cheque_no=excluded.cheque_no, "
                "updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, date_text or None, cheque or None, _who(u), now_iso()))
    _audit(con, _who(u), "pay_letter", month,
           {"date_text": date_text, "cheque_no": cheque,
            "before": dict(before) if before else None})
    con.commit()
    return jsonify(ok=True)


LETTER_CSS_S266 = """<style>
#letter_s266{max-width:720px;font-size:14px;line-height:1.55}
#letter_s266 .lh{padding:2px 0 16px}
#letter_s266 .lh1,#letter_s266 .lh2{font-size:12px}
#letter_s266 .firm{font-size:19px;font-weight:700;letter-spacing:.3px;padding:2px 0}
#letter_s266 .dt{padding:6px 0 16px}
#letter_s266 .to div{line-height:1.5}
#letter_s266 .sub{padding:16px 0 12px;font-weight:600}
#letter_s266 p.bd{margin:0 0 12px}
#letter_s266 .sg{padding-top:26px}
#letter_s266 .sgn{padding-top:34px;font-weight:600}
#letter_s266 .blank{letter-spacing:1px}
.letterset{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px 0 12px}
.letterset label{display:flex;gap:6px;align-items:center;font-size:13px}
.letterprev{border:1px dashed var(--line);border-radius:10px;padding:16px 18px}
</style>"""

# The page-level rules live ONLY on the letter's own page. They must never reach
# the payment sheet: that page prints the ADVICE, in landscape, and a stray
# @page rule here would turn it portrait.
LETTER_PAGE_CSS_S266 = """<style>
@page{size:A4 portrait;margin:16mm}
@media print{
  body *{visibility:hidden!important}
  #letter_s266.standalone,#letter_s266.standalone *{visibility:visible!important}
  #letter_s266.standalone{position:absolute;left:0;top:0;width:100%;max-width:none}
  .noprint{display:none!important}
}
</style>"""


# =====================================================================
# S267 -- THE FILE FOR THE EMAIL.
#
# The advice is printed from the page and it is also EMAILED to the bank, from
# the account linked to it. So it has to exist as a workbook, and it has to be
# the bank's own workbook -- not a lookalike:
#
#   sheet named Sheet2, as every file since April 2026 is
#   the same four letterhead lines, merged the same way (A1:C1, A3:G3, A4:G4)
#   the same seven headers, the first two carrying their leading newline
#   account numbers written as TEXT, so 088851000012 keeps its leading zero
#   amounts as whole numbers, General format, no separators
#   the total as a real =SUM() formula, with its value cached so it shows
#   the same column widths, the same row heights, A4 landscape, fit to page
#
# WRITTEN WITH THE STANDARD LIBRARY ALONE. A .xlsx is a zip of XML, and this
# builds it directly -- no openpyxl, no xlsxwriter, nothing to install on the
# box and nothing to go missing at month end.
# =====================================================================

import zipfile as _zip_s267

_XLSX_CT_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.styles+xml"/></Types>')

_XLSX_RELS_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')

_XLSX_WB_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Sheet2" sheetId="1" r:id="rId1"/></sheets></workbook>')

_XLSX_WBRELS_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/styles" Target="styles.xml"/></Relationships>')

# 0 plain · 1 bold · 2 firm name · 3 header (bold, boxed, wrapped) · 4 boxed
# 5 boxed centred · 6 boxed right · 7 boxed bold right
_XLSX_STYLES_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="3">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="16"/><name val="Calibri"/></font>'
    '</fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
    '<border><left style="thin"/><right style="thin"/><top style="thin"/>'
    '<bottom style="thin"/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="8">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment vertical="bottom" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="center"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="right"/></xf>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="right"/></xf>'
    '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
    '</cellStyles></styleSheet>')

_XLSX_COLS_S267 = ((1, 5.5546875), (2, 8.6640625), (3, 25.109375), (4, 31.88671875),
                   (5, 13.33203125), (6, 10.33203125), (7, 16.0))


def _x_esc_s267(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _x_cell_s267(ref, value, style=0, numeric=False, formula=None, cached=None):
    st = ' s="%d"' % style if style else ""
    if formula is not None:
        return ('<c r="%s"%s><f>%s</f><v>%s</v></c>'
                % (ref, st, _x_esc_s267(formula), _x_esc_s267(cached)))
    if value is None or value == "":
        return '<c r="%s"%s/>' % (ref, st)
    if numeric:
        return '<c r="%s"%s><v>%s</v></c>' % (ref, st, _x_esc_s267(value))
    return ('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (ref, st, _x_esc_s267(value)))


def _advice_xlsx_s267(con, month):
    """The bank's workbook, byte for byte in shape with the ones already sent."""
    rows, total, missing, paise = _advice_rows_s265(con, month)
    mob = _pay_config_s265(con, "shop_mobile", "")
    cols = "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i, i, w)
                   for i, w in _XLSX_COLS_S267)
    out = []
    out.append('<row r="1">' + _x_cell_s267("A1", "GSTIN: %s" % ADVICE_HEAD_S265[0][1], 1)
               + _x_cell_s267("G1", (" (M) %s" % mob) if mob else "", 1) + '</row>')
    out.append('<row r="2">' + _x_cell_s267("A2", ADVICE_DL_S265, 1) + '</row>')
    out.append('<row r="3" ht="52.8" customHeight="1">'
               + _x_cell_s267("A3", ADVICE_FIRM_S265, 2) + '</row>')
    out.append('<row r="4">' + _x_cell_s267("A4", ADVICE_ADDR_S265, 1) + '</row>')
    heads = ["\nSr. No.", "\nTxn. type", "Credit Account Number", "Credit Account Name",
             "IFSC", "Amount", "Narration"]
    out.append('<row r="5" ht="43.2" customHeight="1">'
               + "".join(_x_cell_s267("%s5" % chr(65 + i), h, 3)
                         for i, h in enumerate(heads)) + '</row>')
    r = 6
    for line in rows:
        out.append('<row r="%d">' % r
                   + _x_cell_s267("A%d" % r, line["sr"], 5, numeric=True)
                   + _x_cell_s267("B%d" % r, "NEFT", 5)
                   + _x_cell_s267("C%d" % r, line["acct"], 4)
                   + _x_cell_s267("D%d" % r, line["name"], 4)
                   + _x_cell_s267("E%d" % r, line["ifsc"], 4)
                   + _x_cell_s267("F%d" % r, line["rupees"], 6, numeric=True)
                   + _x_cell_s267("G%d" % r, "Vendor Payment", 4) + '</row>')
        r += 1
    last = r - 1
    if rows:
        out.append('<row r="%d">' % r
                   + "".join(_x_cell_s267("%s%d" % (chr(65 + i), r), "", 4) for i in range(5))
                   + _x_cell_s267("F%d" % r, None, 7, formula="SUM(F6:F%d)" % last,
                                  cached=total)
                   + _x_cell_s267("G%d" % r, "", 4) + '</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>'
        '<dimension ref="A1:G%d"/><sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/><cols>%s</cols><sheetData>%s</sheetData>'
        '<mergeCells count="3"><mergeCell ref="A1:C1"/><mergeCell ref="A3:G3"/>'
        '<mergeCell ref="A4:G4"/></mergeCells>'
        '<pageMargins left="0.7086614173228347" right="0.7086614173228347" top="0.75" '
        'bottom="0.75" header="0.3" footer="0.3"/>'
        '<pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="1"/>'
        '</worksheet>' % (r, cols, "".join(out)))
    buf = io.BytesIO()
    with _zip_s267.ZipFile(buf, "w", _zip_s267.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _XLSX_CT_S267)
        z.writestr("_rels/.rels", _XLSX_RELS_S267)
        z.writestr("xl/workbook.xml", _XLSX_WB_S267)
        z.writestr("xl/_rels/workbook.xml.rels", _XLSX_WBRELS_S267)
        z.writestr("xl/styles.xml", _XLSX_STYLES_S267)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue(), total, missing


def _advice_filename_s267(month):
    """NEFT ADVICE SEPTEMBER 2026.xlsx for AUGUST's purchases -- S380: the bank's files carry the month
    the money is PAID in, which is the month after the purchases (D604), never the purchase month."""
    try:
        y, m = month.split("-")
        y, m = (int(y) + 1, 1) if int(m) == 12 else (int(y), int(m) + 1)
        y, m = str(y), str(m)
        name = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
                "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")[int(m) - 1]
        return "NEFT ADVICE %s %s.xlsx" % (name, y)
    except Exception:
        return "NEFT ADVICE %s.xlsx" % month


@bp.route("/page/pay/<month>/advice.xlsx")
def page_pay_advice_xlsx(month):
    """The attachment for the email. Built from the sheet, never maintained."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    if not _s452_may_advice(con, u):                           # S452: the bank file carries full account numbers -- the owner and the senders
        return _refuse("Yeh file sirf doctor sahab aur Shavez ke liye hai.")
    blob, total, missing = _advice_xlsx_s267(con, month)
    _audit(con, _who(u), "pay_advice_xlsx", month, {"total": total, "left_out": missing})
    con.commit()
    return blob, 200, {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="%s"' % _advice_filename_s267(month)}


def _cheque_months_s271(con):
    """The months the register offers.

    S270 built this strip from the cheques already logged, which meant a month
    that owed money on the cheque lane and had nothing written against it was
    unreachable -- the register hid its own most useful state. It is now every
    month that has a cheque, UNION every month the purchase book knows, newest
    first. _months() is wrapped because a box without the book must still get a
    working register rather than a 500."""
    got = [r[0] for r in con.execute(
        "SELECT DISTINCT month FROM purchase_cheque ORDER BY month DESC").fetchall()]
    try:
        more = [m for m in (_months(con) or []) if m]
    except Exception:
        more = []
    return sorted(set(got) | set(more), reverse=True)


def _line_owner_s282(con, by_no):
    """F-494: a line whose (bill_no, bill_date) names MORE THAN ONE bill.

    Marg numbers bills per vendor, so two suppliers can share a bill number on
    one day; rev 2 above leaves such a line with no supplier. The ITEMWISE export
    carries the supplier, and the same line is in it: same bill number, same
    date, same item, same amount. The line is given to the ONE supplier ITEMWISE
    names for that exact line, provided that supplier is one of the candidates.
    None, two, or a stranger -> the line stays unowned. Returns lines placed."""
    placed = 0
    for r in con.execute("SELECT id, bill_no, bill_date, item, amount_p FROM purchase_line "
                         "WHERE supplier_norm IS NULL AND bill_no IS NOT NULL AND "
                         "bill_date IS NOT NULL").fetchall():
        cands = {c[0] for c in (by_no.get(r[1]) or []) if c[1] == r[2]}
        if len(cands) < 2:
            continue
        w = {x[0] for x in con.execute(
            "SELECT DISTINCT supplier_norm FROM purchase_line WHERE line_type='ITEMWISE' AND "
            "supplier_norm IS NOT NULL AND bill_no=? AND bill_date=? AND item=? AND amount_p IS ?",
            (r[1], r[2], r[3], r[4])).fetchall()}
        if len(w) == 1 and w <= cands:
            con.execute("UPDATE purchase_line SET supplier_norm=? WHERE id=?", (w.pop(), r[0]))
            placed += 1
    return placed


CHEQUE_USERS_KEY = "purchase.cheque_users"


def _cheque_writer_s284(u, con):
    """D524: who may WRITE the cheque register -- log a cheque, mark it handed over,
    void it. A maker or checker of the medical unit, exactly as before. Otherwise
    ONLY a login named in setting purchase.cheque_users (Shavez, by the owner's word
    of 15-Sep). Fail-closed: a missing or unreadable setting admits no viewer. This
    grants nothing else -- the sheet's carry-forward, the verification, the lock and
    the phone book keep their own gates."""
    if not _is_viewer_only(u):
        return True
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (CHEQUE_USERS_KEY,)).fetchone()
    except Exception:
        return False
    raw = (r[0] if r else "") or ""
    names = set(p.strip().lower() for p in re.split(r"[,;\s]+", str(raw)) if p.strip())
    who = str(_who(u) or "").strip().lower()
    return bool(who) and who in names


# =====================================================================
# S380 -- THE PACK (F-616, D605).
#
# The month's payment does not go to the bank as one paper. It goes as three, and until today only one of
# them could be printed:
#
#   1  the covering letter        -- portrait, signed, carrying the cheque number
#   2  the annexure               -- landscape, the seven columns the bank reads
#   3  the payment sheet          -- portrait, vendor by vendor, what he checked before he signed
#
# They print here in that order, each on its own paper, and the print dialog opens by itself when the
# page is opened with ?print=1 -- one click from the payment sheet. The orientation is per paper, by
# named @page rules, so the annexure is landscape in the same job where the letters are portrait.
#
# NOTHING IS RE-CALCULATED HERE. The letter comes from _letter_html_s266, the annexure from
# _advice_paper_s380 and the sheet from _pay_sheet_table -- the same three renderers the payment sheet
# itself shows. A paper that printed differently from the screen would be worse than no paper at all.
# =====================================================================

PACK_CSS_S380 = """<style>
@page port{size:A4 portrait;margin:14mm}
@page land{size:A4 landscape;margin:10mm}
.paper{border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:0 0 18px;background:#fff}
.paper .ph{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);
  font-weight:600;padding-bottom:10px;border-bottom:1px dashed var(--line);margin-bottom:14px}
.paper .shhead{padding:0 0 12px}
.paper .shhead .firm{font-size:19px;font-weight:700;letter-spacing:.3px}
.paper .shhead .sub{font-size:12.5px;color:var(--muted)}
@media print{
  .wrap{max-width:none;padding:0;margin:0}
  .paper{border:0;border-radius:0;padding:0;margin:0;break-after:page;page-break-after:always}
  .paper:last-child{break-after:auto;page-break-after:auto}
  .paper.port{page:port}
  .paper.land{page:land}
  .paper .scroll{overflow:visible}
  table.adv th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  table.sheet{width:100%;font-size:11px}
  table.sheet th,table.sheet td{padding:2px 5px}
  table.sheet td:first-child{white-space:nowrap}
  table.sheet .chip{padding:0 4px;font-size:9.5px}
}
</style>"""


def _pack_bar_s380(prefix, month):
    """The one button, at the top of the payment sheet where he starts."""
    return ('<div class="card noprint"><h2>Print the month\u2019s papers</h2>'
            '<div class="muted">Three sheets in one go, in the order the bank gets them \u2014 the '
            'covering letter, the annexure, and this payment sheet \u2014 each on its own paper, '
            'nothing blank in between.</div>'
            '<div style="margin-top:10px"><a class="p" href="%s/page/pay/%s/pack?print=1" '
            'target="_blank">Print the bank pack</a> &nbsp;'
            '<a href="%s/page/pay/%s/pack" target="_blank">look at it first</a></div></div>'
            % (prefix, month, prefix, month))


@bp.route("/page/pay/<month>/pack")
def page_pay_pack_s380(month):
    """The three papers, one below the other, one per sheet of A4."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    prefix = request.script_root + _url_prefix
    s, groups = _pay_rows(con, month)
    rows, total, missing, paise = _advice_rows_s265(con, month)
    final = s["status"]["status"] == "final"
    date_text, cheque = _letter_values_s266(con, month)

    warn = ""
    if not final:
        warn += ('<div class="warn noprint">DRAFT \u2014 %s is not locked yet. Lock it before these '
                 'papers go to the bank.</div>' % _esc(_month_name(month)))
    if not cheque:
        warn += ('<div class="warn noprint">No cheque number has been typed for this month, so the '
                 'letter prints a blank line for it. Type it on the payment sheet, under '
                 '<b>5 &middot; The covering letter</b> \u2014 it can be typed after the month is '
                 'locked.</div>')
    if not _pay_config_s265(con, "signatory_name", ""):
        warn += ('<div class="warn noprint">No signature name is set, so the papers print the rule and '
                 '<b>Authorized Signatory</b> with no name under it. Type it once in the same place.</div>')
    if missing:
        warn += ('<div class="warn noprint">Not on the annexure \u2014 no confirmed account: %s. '
                 'They are paid by cheque.</div>' % _esc(", ".join(sorted(missing))))

    bar = ('<div class="noprint" style="padding-bottom:12px">'
           '<button class="p" onclick="window.print()">Print all three</button> &nbsp;'
           '<a href="%s/page/pay/%s">back to the payment sheet</a>'
           '<div class="muted" style="margin-top:6px">A4. Paper 1 the covering letter, portrait &middot; '
           'paper 2 the annexure, landscape &middot; paper 3 the payment sheet, portrait. Leave the '
           'browser\u2019s scale at 100%% and its headers and footers off.</div></div>'
           % (prefix, month))

    body = (bar + warn + PACK_CSS_S380 + LETTER_CSS_S266 + ADVICE_TABLE_CSS_S380 +
            '<div class="paper port"><div class="ph noprint">Paper 1 &mdash; the covering letter</div>'
            '%s</div>'
            '<div class="paper land"><div class="ph noprint">Paper 2 &mdash; the annexure, exactly as '
            'the bank gets it</div>%s</div>'
            '<div class="paper port"><div class="ph noprint">Paper 3 &mdash; the payment sheet</div>'
            '<div class="shhead"><div class="firm">%s</div>'
            '<div class="sub">Vendor payments &mdash; %s &middot; the sheet this month was paid from'
            '</div></div>%s%s</div>'
            % (_letter_html_s266(con, month, total),
               _advice_paper_s380(con, month),
               _esc(ADVICE_FIRM_S265), _esc(_month_name(month)),
               _pay_sheet_table(groups, prefix, month, False),
               _signoff_s380(con, "Checked and authorised")))
    js = ("window.addEventListener('load',function(){setTimeout(function(){window.print();},400);});"
          if request.args.get("print") else "")
    return _page("Bank pack \u2014 %s" % _month_name(month), body, js)


# ======================================================================================================================
# S439_SCANS_SMS_SCROLL (30-Sep-2026, session 283, F-661) -- THE MATCHER READS WHAT OCR ACTUALLY WRITES
#
# The owner, 30-Sep: "Yesterday reception scanned all medical bills of September, but the system is showing very few."
# 77 pharmacy scans stood captured and 26 were linked. The S403 grades wanted the bill number letter for letter and the
# vendor as Marg spells it; OCR reads the PRINTED bill:
#   * the bill number with its prefix and zeros -- scan "A000166", Marg "166"; "GPPL-26-64906" / "64906"; "NOT015521" /
#     "15521"; "SF 003051" / "3051"; "18112 (NOT015878)" / "15878";
#   * the vendor misspelt ("KEDAR PHAMACEUTICAL", "SUNINA / CUNINA / QUNINA PHARMACEUTICALS", "SHIVAZ") or the BUYER read
#     as the vendor ("M/S SANJEEVNI MEDICOS");
#   * the year of the date off ("2024-09-14", "2036-09-14").
# So, from here:
#   BILL TAIL    both sides keep the digit runs of the bill number, zeros dropped, a financial-year suffix ("2026-27")
#                set aside; the LAST run is the number, an earlier run of 3+ digits stays as a second candidate.
#   VENDOR       resolved ONCE per scan to a supplier on the server: Marg's own names, both sides of the owner's S263
#                links, the spellings learned here, then a token-set similarity >= 0.70 that must beat the next supplier
#                by 0.10 (a trade word -- PHARMA, AGENCIES, MEDICOS -- weighs 0.3, and a NAME word must pair at 0.80).
#                A link made through similarity learns the spelling (purchase_scan_alias, audited "S439 learned from
#                scan <id>"). SANJEEV* / a bare MEDICOS* is the buyer: vendor unknown, bill tail + amount only.
#   DATE         a year outside this and last financial year is not believed (never blocks a link; its day and month
#                still break ties); vendor + date + amount takes +-3 days.
#   GRADES       1 EXACT    vendor+bill+amount                (S403, as it was)
#                2 EXACT    bill_tail+vendor+amount~2%
#                3 PROBABLE bill+amount~2%                    (S403, as it was)
#                4 PROBABLE bill_tail+amount~2%
#                5 PROBABLE bill_tail+vendor                  (the amount off, or not read)
#                6 PROBABLE vendor+date+amount                (S403's, the date now +-3 days)
#   THE PASS     _rematch() no longer wipes the links. A stored link STAYS while its scan and bill are still there and
#                still match; every captured, unlinked pharmacy scan is then tried, the strongest rule first. A scan
#                whose best bill already has a scan is a second scan of the same paper: dup_cand in purchase_scan_state,
#                NEVER a second link. Every link written is audited (scan_link: grade + rule); a second run links 0.
#                It runs at every Marg purchase push (_rematch_after_push, as since S225), when the scans change
#                (_rematch_if_changed), nightly at 23:59 by cron ("purchase_app.py rematch") and once at install.
#   WHY          every scan still open says why on the scan-links page: no bill on the server yet / vendor unknown /
#                amount differs / no digits read / bill number differs / already scanned. A bill that an open scan
#                probably belongs to says so in the list below it, so nobody is asked to scan it again.
# assets.db stays READ ONLY here (the asset app is the parent's): the duplicate candidate and the reasons live in
# finance.db (purchase_scan_state). The learned spellings live in purchase_scan_alias, NOT in purchase_vendor_alias:
# that table decides which bank account a bill is paid into (S263) and an OCR misreading has no business there.
# ======================================================================================================================
import difflib as _difflib_s439

S439_FY_RE = re.compile(r"(?<!\d)20\d\d\s*[-/]\s*(?:20)?\d\d(?!\d)")
S439_STOP = frozenset(("PVT", "PRIVATE", "LTD", "LIMITED", "MS", "PL", "EXTN", "EXT", "AND", "CO", "THE",
                       "BAREILLY", "BAREILL", "BAREIL", "BAREI"))
S439_TRADE = ("PHARMACEUTICALS", "PHARMACEUTICAL", "PHARMA", "MEDICAL", "MEDICALS", "MEDICOS", "MEDICOSE", "AGENCIES",
              "AGENCY", "SURGICALS", "SURGICAL", "FORMULATIONS", "DISTRIBUTORS", "ENTERPRISES", "TRADERS", "SCIENTIFIC",
              "CHEMIST", "DRUGGIST", "DRUG", "HOUSE", "CENTRE", "AID", "WHOLE", "SALE", "WHOLESALE", "BROS", "STORES",
              "HEALTHCARE")
S439_BUYER = ("SANJEEVNI", "SANJEEVANI", "SANJIVANI")
S439_SIM_MIN = 0.70            # the token-set similarity a vendor must reach ...
S439_SIM_MARGIN = 0.10         # ... and the lead it must have over the next supplier
S439_NAME_MIN = 0.80           # a NAME word must pair this well; trade words alone never make a vendor
S439_DATE_DAYS = 3
S439_HINT_DAYS = 60            # a bill is named as an open scan's likely bill only this near the scan
S439_WHY = {"dup": "already scanned", "no_bill_yet": "no bill on the server yet", "vendor_unknown": "vendor unknown",
            "amount_differs": "amount differs", "no_digits": "no digits read", "number_differs": "bill number differs"}
_trade_memo_s439 = {}


def _bill_tails_s439(s):
    """The digit runs of a bill number, zeros dropped, the LAST run first: 'GPPL-26-64906' -> ['64906'];
    'A000166' -> ['166']; '18112 (NOT015878)' -> ['15878', '18112']; 'YS/0585/2026-27' -> ['585']."""
    t = str(s if s is not None else "")
    runs = [r.lstrip("0") for r in re.findall(r"\d+", S439_FY_RE.sub(" ", t))]
    runs = [r for r in runs if r]
    if not runs:
        runs = [r for r in (x.lstrip("0") for x in re.findall(r"\d+", t)) if r]
    if not runs:
        return []
    out = [runs[-1]]
    for r in reversed(runs[:-1]):
        if len(r) >= 3 and r not in out:
            out.append(r)
    return out


def _tok_sim_s439(a, b):
    if a == b:
        return 1.0
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return 0.9
    return _difflib_s439.SequenceMatcher(None, a, b).ratio()


def _trade_word_s439(w):
    """PHARMA, AGENCIES, MEDICOS ... and their misspellings ('PHAMACEUTICAL'): words many suppliers share."""
    if w not in _trade_memo_s439:
        _trade_memo_s439[w] = (w in S439_TRADE) or any(_tok_sim_s439(w, g) >= 0.85 for g in S439_TRADE)
    return _trade_memo_s439[w]


def _vendor_tokens_s439(s):
    """Upper case, letters only, initials joined ('L.K.' -> 'LK'), M/S, PVT, LTD, EXTN and the city dropped."""
    t = re.sub(r"\bM\s*/\s*S\b\.?", " ", str(s or "").upper())
    out, run = [], ""
    for w in re.findall(r"[A-Z]+", t):
        if len(w) == 1:
            run += w
            continue
        if len(run) > 1:
            out.append(run)
        run = ""
        out.append(w)
    if len(run) > 1:
        out.append(run)
    while len(out) > 1 and out[-1] in _CITY_TAILS:
        out.pop()
    return [w for w in out if w not in S439_STOP]


def _vendor_sim_s439(a, b):
    """Token-set similarity of two vendor names, 0..1: every word finds its best partner on the other side
    (spelling-tolerant), a trade word weighs 0.3, the two directions are averaged. 0 unless a NAME word of one pairs
    with a name word of the other at S439_NAME_MIN -- two names that share only 'PHARMACEUTICALS' are not alike."""
    if not a or not b:
        return 0.0
    an = [t for t in a if not _trade_word_s439(t)]
    bn = [t for t in b if not _trade_word_s439(t)]
    if not an or not bn or max(_tok_sim_s439(x, y) for x in an for y in bn) < S439_NAME_MIN:
        return 0.0

    def side(p, q):
        num = den = 0.0
        for t in p:
            w = 0.3 if _trade_word_s439(t) else 1.0
            num += w * max(_tok_sim_s439(t, u) for u in q)
            den += w
        return num / den
    return (side(a, b) + side(b, a)) / 2.0


def _is_buyer_s439(toks):
    """The buyer's own name read as the vendor: SANJEEV* (any spelling), or a bare MEDICOS* with no name beside it."""
    for t in toks:
        if t.startswith(("SANJEEV", "SANJIV", "SANJEV")) or max(_tok_sim_s439(t, x) for x in S439_BUYER) >= 0.8:
            return True
    return (not [t for t in toks if not _trade_word_s439(t)]) and any(t.startswith("MEDICOS") for t in toks)


# ---------------------------------------------------------------------------------------------------------------------
# S440_SCAN_FLOW (30-Sep-2026, D640, F-662): WHAT A PERSON DECIDED ABOUT A SCAN RIDES EVERY PASS
# The staff's "Scan ka kaam" (porders.py) lets a person answer what the matcher could not: "yes, this is that bill" /
# "no, it is not"; "this is the supplier"; "the paper says Rs X". Those answers live in purchase_scan_state (additive
# columns, below) and the pass must not wipe them -- until now it deleted the table and wrote it again. So:
#   * a link of grade CONFIRMED stays while its scan and bill exist (the rules are not asked again);
#   * a bill a person refused for a scan (hint_no) is never matched or hinted to it again;
#   * a chosen supplier stands in for the vendor OCR could not read; the paper amount stands in for the scan's;
#   * dup_ok marks a paper a person recognised as a second scan of a linked one;
#   * likely_bill names the bill the reason sentence speaks of, also when that bill already has a scan;
#   * a LINKED scan keeps its row (why 'linked') when a person decided something about it.
S440_STATE_COLS = (("likely_bill", "INTEGER"), ("confirmed_by", "TEXT"), ("confirmed_at", "TEXT"), ("paper_amount", "INTEGER"),
                   ("chosen_vendor", "TEXT"), ("hint_no", "TEXT"), ("amount_state", "TEXT"), ("dup_ok", "INTEGER"))
S440_DECIDED = ("confirmed_by", "confirmed_at", "paper_amount", "chosen_vendor", "hint_no", "amount_state", "dup_ok")


def _decisions_s440(con):
    """{scan id: what a person decided} -- only the rows that carry a decision."""
    out = {}
    try:
        for r in con.execute("SELECT asset_bill_id, %s FROM purchase_scan_state" % ", ".join(S440_DECIDED)).fetchall():
            d = {k: r[i + 1] for i, k in enumerate(S440_DECIDED)}
            if any(v not in (None, "") for v in d.values()):
                d["no"] = {int(x) for x in str(d.get("hint_no") or "").split(",") if x.strip().isdigit()}
                out[r[0]] = d
    except sqlite3.Error:
        pass
    return out


def _apply_decisions_s440(scans, dec, ctx):
    suppliers = set(ctx["canon"].values())
    for s in scans:
        d = dec.get(s["id"])
        if not d:
            continue
        if d.get("paper_amount") is not None:
            s["amount_p"] = int(d["paper_amount"])             # the amount a person read ON THE PAPER
        if d.get("chosen_vendor") and d["chosen_vendor"] in suppliers:
            s["_vendor"] = (d["chosen_vendor"], "chosen", 1.0)
        s["_no"] = d["no"]


def _state_put_s440(con, sid, why, detail, first, bid, hint, stamp, likely, d):
    d = d or {}
    con.execute("INSERT OR REPLACE INTO purchase_scan_state (asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill, checked_at, likely_bill, "
                "confirmed_by, confirmed_at, paper_amount, chosen_vendor, hint_no, amount_state, dup_ok) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, why, detail, first, bid, hint, stamp, likely, d.get("confirmed_by"), d.get("confirmed_at"), d.get("paper_amount"),
                 d.get("chosen_vendor"), d.get("hint_no"), d.get("amount_state"), d.get("dup_ok")))


def _scan_flow_s440(con, body):
    """The owner's Scan links page inside the scan flow: the BACK bar first (to ?from=, else the portal's tile hub), the
    five groups the staff work through on Purchase orders (read-only here), the floating up-arrow."""
    frm = str(request.args.get("from") or "")
    back = frm if (frm.startswith("/") and not frm.startswith("//") and len(frm) <= 300 and not re.search(r"[\\\r\n\"'<>]", frm)) else "/portal"
    bar = ('<div id="s440bar" style="position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;'
           'padding:6px 10px;margin:0 0 10px;border-radius:0 0 8px 8px"><a id="s440back" href="%s" style="display:flex;align-items:center;'
           'justify-content:center;min-height:44px;padding:0 20px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;'
           'text-decoration:none">← BACK</a><span style="margin-left:auto;font-weight:600">Scan links</span></div>' % _esc(back))
    up = ('<button id="s440up" aria-label="back to top" onclick="window.scrollTo({top:0,behavior:\'smooth\'})" style="position:fixed;right:14px;bottom:18px;'
          'width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;display:none;z-index:70;cursor:pointer">↑</button>'
          '<script>window.addEventListener("scroll",function(){var b=document.getElementById("s440up");if(b)b.style.display=(window.pageYOffset>window.innerHeight)?"block":"none"});</script>')
    groups = ""
    try:
        import porders                                         # noqa: PLC0415 -- beside this file; fail-soft: the tables below never wait for it
        k = porders.scan_work(con)

        def grp(title, rows, open_=False):
            if not rows:
                return ""
            return ('<details%s style="margin:6px 0"><summary style="cursor:pointer"><b>%s</b> (%d)</summary><ul style="margin:6px 0 2px 18px;padding:0">%s</ul></details>'
                    % (" open" if open_ else "", title, len(rows), "".join("<li>%s</li>" % r for r in rows)))
        g1 = ["%s bill %s · %s · %s · %d days%s" % (_esc(" ".join(str(x["vendor"]).split())), _esc(x["bill_no"]), _esc(x["date_text"]), _esc(x["amount"]), x["age"],
                                                       (" — <span class=\"bad\">entered twice in Marg (%s): on the WRONG list</span>" % _esc(" / ".join(x["double_nos"]))) if x.get("double") else "")
              for x in k["scan"]]
        g1 += ["%s — the order was received %s; its bill is not in Marg yet" % (_esc(x["vendor"]), _esc(x.get("received_text") or "")) for x in k.get("received") or []]
        g2 = ["scan %s reads '%s' · %s → %s bill %s (%s, %s)%s" % (_esc(x["stamp"]), _esc(x["scan_no"] or "nothing"), _esc(x["scan_amount"]), _esc(x["vendor"]), _esc(x["bill_no"]),
                                                                       _esc(x["date_text"]), _esc(x["amount"]),
                                                                       (" — that bill already has scan %s: a second scan?" % _esc(x.get("taken_stamp") or "")) if x.get("taken_by") else "")
              for x in k["confirm"]]
        g3 = ["scan %s reads '%s' · %s · %s" % (_esc(x["stamp"]), _esc(x["scan_vendor"] or "nothing"), _esc(x["scan_no"] or "no number"), _esc(x["scan_amount"])) for x in k["vendor"]]
        g4 = ["scan %s → %s bill %s: the scan reads %s, Marg %s" % (_esc(x["stamp"]), _esc(x["vendor"]), _esc(x["bill_no"]), _esc(x["scan_amount"]), _esc(x["amount"])) for x in k["amount"]]
        g5 = ["scan %s · %s · %s · %s — %s" % (_esc(x["stamp"]), _esc(x["scan_vendor"] or "no vendor"), _esc(x["scan_no"] or "no number"), _esc(x["scan_amount"]), _esc(x.get("note_en") or ""))
              for x in k["wait"]]
        c = k["counts"]
        groups = ('<div class="card" id="s440groups"><h2>Scan work — what the staff see on Purchase orders (%d to act on)</h2><div class="muted">Read-only here; each line carries its '
                  'buttons on <a href="/finance/porders?from=%s/page/scans">Purchase orders</a>. To scan %d · Is this the bill? %d · Choose the supplier %d · Match the amount %d · '
                  'Waiting for Marg %d · second scans %d.</div>%s%s%s%s%s</div>'
                  % (k["n"], request.script_root + _url_prefix, c["scan"], c["confirm"], c["vendor"], c["amount"], c["wait"], c["dup"],
                     grp("To scan (Scan karo)", g1), grp("Is this the bill? (Yahi bill hai?)", g2, True), grp("Choose the supplier (Supplier chuno)", g3, True),
                     grp("Match the amount (Amount milao)", g4, True), grp("Waiting for Marg (Marg ka intezaar)", g5)))
    except Exception:                                          # noqa: BLE001
        groups = ""
    i = body.find('<div class="card"><h2')
    if groups and i >= 0:
        body = body[:i] + groups + body[i:]
    else:
        body = body + groups
    return bar + _s446_sarvam_card(con) + _s452_amir_list_line(con) + body + up      # S446 (D650): Sarvam, one line · S452: Amir's list


def _ensure_s439(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_scan_state (
        asset_bill_id INTEGER PRIMARY KEY,        -- assets.db bills.id: a pharmacy scan with no link
        why           TEXT NOT NULL,              -- dup | no_bill_yet | vendor_unknown | amount_differs | no_digits | number_differs
        detail        TEXT,                       -- the sentence the scan-links page shows
        dup_cand      INTEGER,                    -- the scan ALREADY linked to the bill this one matched (never a second link)
        dup_bill      INTEGER,                    -- that purchase_bill.id
        hint_bill     INTEGER,                    -- an unscanned bill this scan probably belongs to (number or amount read differently)
        checked_at    TEXT NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_scan_alias (
        ocr_norm      TEXT PRIMARY KEY,           -- the vendor as OCR spelt it (supplier_key)
        supplier_norm TEXT NOT NULL,              -- the supplier on Marg's bills it was matched to
        scan_id       INTEGER,
        who           TEXT,                       -- 'S439 learned from scan <id>'
        at            TEXT)""")
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_scan_state)")}      # S440 (D640): what a person decided -- additive columns
    for col, typ in S440_STATE_COLS:
        if col not in have:
            con.execute("ALTER TABLE purchase_scan_state ADD COLUMN %s %s" % (col, typ))


def _vendor_ctx_s439(con, bills):
    """Every known spelling of every supplier -> the supplier's key on Marg's bills: Marg's own names, both sides of
    the owner's S263 links (READ only), and what this matcher has learned from scans."""
    canon = {}
    for b in bills:
        k = supplier_key(b["supplier"])
        if k:
            canon.setdefault(k, k)
    try:
        for r in con.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias").fetchall():
            c = canon.get(supplier_key(r[0]))
            if c and supplier_key(r[1]):
                canon.setdefault(supplier_key(r[1]), c)
    except sqlite3.Error:
        pass
    suppliers = set(canon.values())
    learned = {}
    try:
        for r in con.execute("SELECT ocr_norm, supplier_norm FROM purchase_scan_alias").fetchall():
            if r[1] in suppliers:
                learned[r[0]] = r[1]
    except sqlite3.Error:
        pass
    return dict(canon=canon, learned=learned, toks={k: _vendor_tokens_s439(k) for k in canon}, memo={})


def _vendor_resolve_s439(text, ctx):
    """The vendor on a scan -> (supplier key or None, how, score); how = exact | learned | similar | buyer | unknown | empty."""
    text = str(text or "")
    if text in ctx["memo"]:
        return ctx["memo"][text]
    toks = _vendor_tokens_s439(text)
    k = supplier_key(text)
    if not toks:
        out = (None, "empty", 0.0)
    elif _is_buyer_s439(toks):
        out = (None, "buyer", 0.0)
    elif k in ctx["canon"]:
        out = (ctx["canon"][k], "exact", 1.0)
    elif k in ctx["learned"]:
        out = (ctx["learned"][k], "learned", 1.0)
    else:
        best, same = {}, None
        for sp, st in ctx["toks"].items():
            if sorted(set(st)) == sorted(set(toks)):
                same = ctx["canon"][sp]                    # only the punctuation differs ('PVT. LTD.', '(EXTN)')
                break
            sc = _vendor_sim_s439(toks, st)
            if sc > best.get(ctx["canon"][sp], 0.0):
                best[ctx["canon"][sp]] = sc
        if same:
            out = (same, "exact", 1.0)
        else:
            ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
            top, sc = ranked[0] if ranked else (None, 0.0)
            second = ranked[1][1] if len(ranked) > 1 else 0.0
            out = ((top, "similar", round(sc, 3)) if top and sc >= S439_SIM_MIN and sc - second >= S439_SIM_MARGIN
                   else (None, "unknown", round(sc, 3)))
    ctx["memo"][text] = out
    return out


def _fy_window_s439(today=None):
    """The first day of LAST financial year to the last day of THIS one: the years an OCR date may carry."""
    today = today or dt.date.today()
    y = today.year if today.month >= 4 else today.year - 1
    return dt.date(y - 1, 4, 1), dt.date(y + 1, 3, 31)


def _date_or_none_s439(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def _prep_s439(scans, bills, ctx):
    win = _fy_window_s439()
    for b in bills:
        b["_skey"] = supplier_key(b["supplier"])
        b["_tails"] = _bill_tails_s439(b["bill_no"])
        b["_date"] = _date_or_none_s439(b["bill_date"])
    for s in scans:
        s["_tails"] = _bill_tails_s439(s["bill_no"])
        s["_vendor"] = _vendor_resolve_s439(s["vendor"], ctx)
        d = _date_or_none_s439(s["bill_date"])
        s["_md"] = (d.month, d.day) if d else None             # the day and month still break ties when the year is off
        s["_date"] = d if (d and win[0] <= d <= win[1]) else None


def _date_gap_s439(s, b):
    """Days between the scan's date and the bill's; an unbelievable year lends its day and month to the bill's year.
    9999 when nothing can be compared."""
    bd = b["_date"]
    if bd is None:
        return 9999
    if s["_date"] is not None:
        return abs((s["_date"] - bd).days)
    if s["_md"]:
        try:
            return abs((dt.date(bd.year, s["_md"][0], s["_md"][1]) - bd).days)
        except ValueError:
            return 9999
    return 9999


def _match_s439(s, b):
    """One scan against one Marg bill -> (rank, grade, rule) or None. The six rules are in the header above."""
    if b["id"] in s.get("_no", ()):                           # S440: a person said this scan is NOT this bill
        return None
    sa, ba = s["amount_p"], b["amount_p"]
    canon, how, _sc = s["_vendor"]
    vend = how != "buyer" and (_vendor_match(s["vendor"], b["supplier"]) or (canon is not None and canon == b["_skey"]))
    bno = bool(s["bill_no"]) and s["bill_no"] == b["bill_no"]
    tail = bool(s["_tails"]) and bool(b["_tails"]) and b["_tails"][0] in s["_tails"]
    near1 = sa is not None and abs(sa - ba) <= 100
    near2 = sa is not None and abs(sa - ba) <= max(100, int(round(0.02 * ba)))
    if vend and bno and near1:
        return 1, "EXACT", "vendor+bill+amount"
    if vend and tail and near2:
        return 2, "EXACT", "bill_tail+vendor+amount~2%"
    if bno and near2:
        return 3, "PROBABLE", "bill+amount~2%"
    if tail and near2:
        return 4, "PROBABLE", "bill_tail+amount~2%"
    if vend and tail:
        return 5, "PROBABLE", "bill_tail+vendor"
    if (vend and near1 and s["_date"] is not None and b["_date"] is not None
            and abs((s["_date"] - b["_date"]).days) <= S439_DATE_DAYS):
        return 6, "PROBABLE", "vendor+date+amount"
    return None


def _tie_s439(s, b):
    """Among bills one rule allows: the bill's number is the scan's LAST digit run first, then the same vendor, then
    the nearer date, then the nearer amount."""
    canon = s["_vendor"][0]
    primary = 0 if (s["_tails"] and b["_tails"] and b["_tails"][0] == s["_tails"][0]) else 1
    vend = 0 if (canon is not None and canon == b["_skey"]) else 1
    return (primary, vend, _date_gap_s439(s, b), abs((s["amount_p"] or 0) - b["amount_p"]))


def _why_s439(s, bills, taken, last_date):
    """Why a scan has no link -> (why, the sentence for the page, hint bill id or None)."""
    tails, amt = s["_tails"], s["amount_p"]
    canon, how, _sc = s["_vendor"]
    no = s.get("_no", ())                                     # S440: bills a person refused for this scan are never named again
    s["_likely"] = None                                       # S440: the bill the sentence names, also when it already has a scan

    def lab(b):
        return "%s bill %s (%s, %s)" % (b["_skey"], b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))

    def also(b):
        return " — that bill already has scan #%d" % taken[b["id"]] if b["id"] in taken else ""

    scanned = _date_or_none_s439(s.get("created_at"))
    last = _date_or_none_s439(last_date)
    fresh = s["_date"] is not None and last is not None and s["_date"] > last     # dated after Marg's last bill on the server

    def gap(b):
        """Days from the bill to the scan -- by the date on the paper or the day it was scanned, whichever is nearer."""
        g = [abs((d - b["_date"]).days) for d in (s["_date"], scanned) if d is not None and b["_date"] is not None]
        return min(g) if g else 9999

    def near(b):
        return (1 if b["id"] in taken else 0, gap(b), abs((amt or 0) - b["amount_p"]), b["id"])

    def likely(b):
        """The same supplier's bill of this amount to the rupee -- or within 2% when the numbers are nearly the same digits."""
        d = abs(amt - b["amount_p"])
        if d <= 100:
            return True
        return bool(d <= max(100, int(round(0.02 * b["amount_p"]))) and tails and b["_tails"]
                    and _difflib_s439.SequenceMatcher(None, tails[0], b["_tails"][0]).ratio() >= 0.8)

    if not tails and amt is None:
        return "no_digits", "no digits read — OCR found neither a bill number nor an amount on this scan", None
    # a bill is named as the scan's likely bill only when it is within S439_HINT_DAYS of the scan: an April bill that
    # happens to carry the same number or amount is a coincidence, not a hint
    if canon is None:
        same = [b for b in bills if tails and b["_tails"] and b["_tails"][0] in tails and gap(b) <= S439_HINT_DAYS and b["id"] not in no]
        if same:
            b = min(same, key=near)
            s["_likely"] = b["id"]
            hint = None if b["id"] in taken else b["id"]
            if amt is None:
                return "no_digits", "no digits read — no amount on the scan; %s carries the same number%s" % (lab(b), also(b)), hint
            return ("amount_differs", "amount differs — the scan reads %s; %s on the server%s" % (_r(amt), lab(b), also(b)), hint)
    elif amt is not None and not fresh:
        close = [b for b in bills if b["_skey"] == canon and likely(b) and gap(b) <= S439_HINT_DAYS and b["id"] not in no]
        if close:
            b = min(close, key=near)
            s["_likely"] = b["id"]
            more = (" (%d bills of this supplier carry this amount; this is the nearest)" % len(close)) if len(close) > 1 else ""
            return ("number_differs", "bill number differs — the scan reads '%s' (%s); the likely bill is %s%s%s"
                    % (s["bill_no"] or "nothing", _r(amt), lab(b), more, also(b)), None if b["id"] in taken else b["id"])
    if not tails:
        return "no_digits", "no digits read — OCR found no bill number on this scan", None
    if canon is None:
        if how == "buyer":
            return ("vendor_unknown", "vendor unknown — OCR read the buyer's own name as the vendor, and no bill on the "
                    "server has number %s with this amount" % tails[0], None)
        return ("vendor_unknown", "vendor unknown — '%s' is not a supplier on the server, and no bill has number %s with "
                "this amount" % (str(s["vendor"] or "")[:40] or "nothing read", tails[0]), None)
    return ("no_bill_yet", "no bill on the server yet — %s has no bill %s here; Marg's bills on the server end at %s"
            % (canon, tails[0], _human(last_date) if last_date else "—"), None)


_rematch_before_s439 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S439: the scan-vs-bill pass (the header above). Stored links stay; every unlinked pharmacy scan is tried, the
    strongest rule first; a second scan of a linked bill is marked, never linked; every open scan gets its reason.
    Returns None when the asset app's database is not reachable, else the counts (new = links written this run)."""
    acon = _assets_con()
    if acon is None:
        return None
    scans = _scans(acon)
    acon.close()
    _ensure_s439(con)
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    ctx = _vendor_ctx_s439(con, bills)
    _prep_s439(scans, bills, ctx)
    dec = _decisions_s440(con)                                 # S440 (D640): what a person decided about a scan rides every pass
    _apply_decisions_s440(scans, dec, ctx)
    sby = {s["id"]: s for s in scans}
    bby = {b["id"]: b for b in bills}
    # 1 · a stored link stays while its scan and its bill are still there and still match
    taken, linked, dropped = {}, set(), 0
    for r in con.execute("SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link ORDER BY linked_at, bill_id").fetchall():
        b, s = bby.get(r[0]), sby.get(r[1])
        if b is not None and s is not None and r[1] not in linked:   # S454 (5): a link that exists is never undone by the rules; they only give it its state
            taken[r[0]] = r[1]
            linked.add(r[1])
            continue
        con.execute("DELETE FROM purchase_scan_link WHERE bill_id=?", (r[0],))
        con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (r[0], r[1]))
        _audit(con, who, "scan_unlink", r[0], dict(scan=r[1], kit="S439", why=(
            "the bill left the live exports" if b is None else "the scan is gone or rejected" if s is None
            else "the scan and the bill no longer match")))
        dropped += 1
    # 2 · every unlinked scan: the bills its BEST rule allows, the nearest first
    cand = {}
    for s in scans:
        if s["id"] in linked:
            continue
        hits = []
        for b in bills:
            m = _match_s439(s, b)
            if m:
                hits.append((m[0], _tie_s439(s, b), b["id"], m[1], m[2]))
        if hits:
            hits.sort()
            cand[s["id"]] = [h for h in hits if h[0] == hits[0][0]]
    # 3 · the strongest rule first; a bill takes ONE scan -- a scan whose best bill is taken is a second scan of it
    new, dups = [], {}
    for rank in sorted({v[0][0] for v in cand.values()}):
        for tie, sid, bid, grade, rule in sorted((h[1], sid, h[2], h[3], h[4]) for sid, v in cand.items() if v[0][0] == rank for h in v):
            if sid in linked or bid in taken:
                continue
            s, b = sby[sid], bby[bid]
            cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                              (bid, sid, grade, rule, now_iso()))
            if not cur.rowcount:                                   # another pass linked this bill a moment ago (the cron and a page at once)
                taken[bid] = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (bid,)).fetchone()[0]
                linked.add(taken[bid])
                continue
            con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
            _audit(con, who, "scan_link", bid, dict(scan=sid, grade=grade, rule=rule, supplier=b["_skey"], bill_no=b["bill_no"], kit="S439"))
            taken[bid] = sid
            linked.add(sid)
            new.append((sid, bid, grade, rule))
            canon, how, sc = s["_vendor"]
            if how == "similar" and canon == b["_skey"]:          # the link proved the spelling: learn it, once
                cur = con.execute("INSERT OR IGNORE INTO purchase_scan_alias (ocr_norm, supplier_norm, scan_id, who, at) VALUES (?,?,?,?,?)",
                                  (supplier_key(s["vendor"]), canon, sid, "S439 learned from scan %d" % sid, now_iso()))
                if cur.rowcount:
                    _audit(con, who, "alias_learn", supplier_key(s["vendor"]), dict(supplier=canon, score=sc, note="S439 learned from scan %d" % sid))
        for sid, v in cand.items():
            if v[0][0] == rank and sid not in linked:
                dups[sid] = (taken[v[0][2]], v[0][2], v[0][4])
    try:                                                       # S454 (5): the auto-link -- the ONE unscanned bill of the supplier with this amount
        new += _s454_autolink(con, who, scans, bills, taken, linked, dups)
    except Exception as _e_s454:                               # noqa: BLE001 -- the pass never fails for it
        _audit(con, who, "auto_link_error", "", dict(error=str(_e_s454)[:200], kit="S454"))
    for s in scans:                                            # S440: a person recognised this paper as a second scan of a linked one
        d = dec.get(s["id"]) or {}
        if d.get("dup_ok") and s["id"] not in linked and s["id"] not in dups:
            bid = next((bb for bb, sc in taken.items() if sc == d["dup_ok"]), None)
            if bid is not None:
                dups[s["id"]] = (d["dup_ok"], bid, "reception confirmed")
    # 4 · the reason of every scan still open
    before = {}
    for r in con.execute("SELECT asset_bill_id, dup_cand FROM purchase_scan_state").fetchall():
        before[r[0]] = r[1]
    con.execute("DELETE FROM purchase_scan_state")
    last_date = max([b["bill_date"] for b in bills if b["bill_date"]] or [None])
    stamp, reasons = now_iso(), {}
    for s in scans:
        sid = s["id"]
        if sid in linked:
            continue
        if sid in dups:
            first, bid, rule = dups[sid]
            b = bby[bid]
            why, hint = "dup", None
            detail = ("already scanned — a second scan of %s bill %s (%s): that bill is linked to scan #%d"
                      % (b["_skey"], b["bill_no"], _human(b["bill_date"]), first))
            if before.get(sid) != first:
                _audit(con, who, "scan_dup", bid, dict(scan=sid, dup_cand=first, rule=rule, kit="S439"))
        else:
            first, bid = None, None
            why, detail, hint = _why_s439(s, bills, taken, last_date)
        reasons[why] = reasons.get(why, 0) + 1
        _state_put_s440(con, sid, why, detail, first, bid, hint, stamp, s.get("_likely"), dec.get(sid))    # S440: the decisions are written back
    for sid, d in dec.items():                                 # S440: a LINKED scan keeps what a person decided about it
        if sid in linked and sid in sby:
            _state_put_s440(con, sid, "linked", "linked", None, None, None, stamp, None, d)
    _audit(con, who, "rematch", "", dict(links=len(taken), new=len(new), dups=len(dups), dropped=dropped, scans=len(scans), bills=len(bills)))
    con.commit()
    return dict(links=len(taken), new=len(new), new_links=new, dups=len(dups), dropped=dropped, reasons=reasons,
                scans=len(scans), bills=len(bills),
                unmatched_scans=[s for s in scans if s["id"] not in linked],
                unscanned_bills=[b for b in bills if b["id"] not in taken])


def _scan_state_s439(con):
    """{scan id: why / detail / dup_cand / hint_bill} as the last pass left it; {} before the first pass."""
    try:
        return {r[0]: dict(why=r[1], detail=r[2], dup_cand=r[3], dup_bill=r[4], hint_bill=r[5]) for r in con.execute(
            "SELECT asset_bill_id, why, detail, dup_cand, dup_bill, hint_bill FROM purchase_scan_state").fetchall()}
    except sqlite3.Error:
        return {}


def _cli_s439(argv):
    """python3 -B purchase_app.py rematch [--list] -- the nightly pass (root cron, 23:59) and the install's first run.
    One line of counts; --list adds every scan still open with its reason. Exit 0 also when the asset app's database
    is not reachable (the line says so): the pass simply waits for the next night."""
    global _assets_db

    def say(line):
        try:
            print(line)
        except UnicodeEncodeError:                     # a cron shell with no UTF-8 locale
            print(line.encode("ascii", "replace").decode("ascii"))
    if len(argv) < 2 or argv[1] != "rematch":
        say("usage: purchase_app.py rematch [--list]")
        return 2
    _assets_db = os.environ.get("ASSETS_DB", _assets_db)
    con = sqlite3.connect(os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db")), timeout=60)
    con.row_factory = sqlite3.Row
    _ensure(con)
    r = _rematch(con, os.environ.get("REMATCH_WHO", "nightly"))
    if r is None:
        say("S439 rematch %s: the asset app's database is not reachable -- nothing matched" % now_iso())
        return 0
    fp = _scan_fingerprint()
    if fp:
        con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (REMATCH_SEEN_KEY, fp))
        con.commit()
    say("S439 rematch %s: %d new link(s) · %d links stored · %d pharmacy scans · %d still open (%s)%s"
        % (now_iso(), r["new"], r["links"], r["scans"], len(r["unmatched_scans"]),
           " · ".join("%s %d" % (S439_WHY.get(k, k), v) for k, v in sorted(r["reasons"].items())) or "none",
           (" · %d stale link(s) dropped" % r["dropped"]) if r["dropped"] else ""))
    if "--list" in argv:
        for sid, bid, grade, rule in r["new_links"]:
            b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (bid,)).fetchone()
            say("  linked  scan #%d -> %s bill %s (%s, %s)  %s  %s" % (sid, supplier_key(b[0]), b[1], _human(b[2]), _r(b[3]), grade, rule))
        st = _scan_state_s439(con)
        for s in sorted(r["unmatched_scans"], key=lambda x: x["id"]):
            say("  open    scan #%d  %s" % (s["id"], (st.get(s["id"]) or {}).get("detail") or ""))
    return 0



# ==========================================================================================================================================
# S446_AMIR_STAGES_BILLS (02-Oct-2026, D650 / F-680): the scanned medicine bills as FILES for Marg's own digital entry; Marg overrules
# Sarvam; the earlier month's unfinished work above the payment sheet.
#   * (S533: scans_to_enter retired -- step 2 reads scans_for_amir)
#   * GET /finance/purchase/api/scan-file/<id>      the stored scan, read only from the asset app's store, named
#                                                    <SUPPLIER>_<billno>_<dd-mm-yyyy>.pdf -- Amir and the owner only (setting
#                                                    purchase.scan_file_users, default 'amir'; the medical checker always)
#   * GET /finance/purchase/api/scan-files/today.zip  today's of them, one zip
#   * The trial (setting purchase.sarvam_trial_until): for every scan LINKED to a Marg bill, field by field -- supplier (alias-aware),
#     bill number (digit tail), date, total (within Rs 1), and the item lines Sarvam read (name, qty, rate, batch, expiry) against
#     Marg's item-wise lines -- kept in purchase_sarvam_check. Wherever they differ Marg's figure is the bill's; this comparison
#     only counts. The owner: one line on the Scan links page, a monthly Needs-you line, the drill-down /page/sarvam?month=.
#   * The payment sheet: "Pichhle mahine ka baaki: N" above the month while an earlier month holds unsent supplier messages
#     or NEFT lines with no NEFT recorded; one tap opens that month.
# ==========================================================================================================================================
S446_SARVAM_DDL = ("CREATE TABLE IF NOT EXISTS purchase_sarvam_check (asset_bill_id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, month TEXT, "
                   "checked_at TEXT NOT NULL, supplier_ok INTEGER, billno_ok INTEGER, date_ok INTEGER, total_ok INTEGER, items_read INTEGER, "
                   "items_wrong INTEGER, all_ok INTEGER, detail TEXT)")


def _s446_setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] not in (None, "") else default
    except sqlite3.Error:
        return default


def _s446_uploads():
    return os.environ.get("ASSETS_UPLOADS") or os.path.join(os.path.dirname(os.path.abspath(_assets_db)), "uploads")


def _s446_linked(con):
    try:
        return {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        return set()


def _s446_name(r):
    sup = re.sub(r"[^A-Z0-9]+", "_", str(r.get("vendor") or "SUPPLIER").upper()).strip("_")[:40] or "SUPPLIER"
    bno = re.sub(r"[^A-Za-z0-9]+", "", str(r.get("bill_no") or "")) or "nobill"
    d = _iso(r.get("bill_date")) or _iso_any(r.get("bill_date")) or ""
    return "%s_%s_%s.pdf" % (sup, bno, (d[8:10] + "-" + d[5:7] + "-" + d[:4]) if len(d) == 10 else "nodate")


def _s446_files_ok(con, u):
    if _is_doctor(u):
        return True
    who = str((u or {}).get("user") or "").strip().lower()
    allow = {x.strip().lower() for x in _s446_setting(con, "purchase.scan_file_users", "amir").split(",") if x.strip()}
    return bool(who) and who in allow


def _s446_file_bytes(sid, kinds=("Pharmacy",)):           # S753: kinds -- the s738 viewer serves a dealer's Summary too
    """(name, bytes) of one captured pharmacy scan -- read only, from the asset app's store; None when it is not one."""
    acon = _assets_con()
    if acon is None:
        return None
    try:
        r = acon.execute("SELECT id, vendor, bill_no, bill_date, source_stored FROM bills WHERE id=? AND kind IN (%s) AND status='captured'"
                         % ",".join("?" * len(kinds)), (int(sid),) + tuple(str(k) for k in kinds)).fetchone()
    finally:
        acon.close()
    if r is None or not r["source_stored"]:
        return None
    base = os.path.realpath(_s446_uploads())
    p = os.path.realpath(os.path.join(base, os.path.basename(str(r["source_stored"]))))
    if not p.startswith(base + os.sep) or not os.path.isfile(p):
        return None
    with open(p, "rb") as fh:
        return _s446_name(dict(r)), fh.read()


@bp.route("/api/scan-file/<int:sid>")
def api_s446_scan_file(sid):
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    if not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    kind, item = _s452_lookup(con, sid)                        # S452 (F-686): only a bill Marg does not have, and not one held for reception
    if kind in ("linked", "held"):
        return _s452_small_page(kind)
    got = _s446_file_bytes(sid) if kind == "list" else None
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    from flask import Response                                 # noqa: PLC0415
    return Response(got[1], mimetype="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % item["name"], "Cache-Control": "no-store"})


@bp.route("/api/scan-files/today.zip")
def api_s446_scan_zip():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    if not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    import zipfile                                              # noqa: PLC0415
    from flask import Response                                 # noqa: PLC0415
    buf = io.BytesIO()
    names = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for s in scans_for_amir(con)["list"]:                  # S452 (F-686): the same rule as the list
            if not s["today"]:
                continue
            got = _s446_file_bytes(s["id"])
            if got is None:
                continue
            n = s["name"]
            while n in names:
                n = n[:-4] + "_%d.pdf" % s["id"]
            names.add(n)
            z.writestr(n, got[1])
    return Response(buf.getvalue(), mimetype="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="BILLS_%s.zip"' % dt.date.today().strftime("%d-%m-%Y"), "Cache-Control": "no-store"})


# ---------------------------------------------------------------- the Sarvam trial: Marg overrules
def _s446_digits(s):
    return re.sub(r"\D", "", str(s or "")).lstrip("0")


def _s446_name_norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()


def _s446_exp(s):
    """An expiry as MM/YY whatever its shape ('01/28', '1-2028', '2028-01', 'JAN-28'), or ''."""
    t = str(s or "").strip().upper()
    if not t:
        return ""
    mons = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
    m = re.match(r"^([A-Z]{3})\W*(\d{2,4})$", t)
    if m and m.group(1) in mons:
        return "%02d/%s" % (mons[m.group(1)], m.group(2)[-2:])
    m = re.match(r"^(\d{4})\W(\d{1,2})(\W\d{1,2})?$", t)
    if m:
        return "%02d/%s" % (int(m.group(2)), m.group(1)[-2:])
    m = re.match(r"^(\d{1,2})\W(\d{2,4})$", t)
    if m:
        return "%02d/%s" % (int(m.group(1)), m.group(2)[-2:])
    return t


def _s446_supplier_ok(con, scan_vendor, bill):
    if not scan_vendor:
        return False
    if _vendor_match(scan_vendor, bill["supplier"]):
        return True
    k = supplier_key(scan_vendor)
    try:
        r = con.execute("SELECT supplier_norm FROM purchase_scan_alias WHERE ocr_norm=?", (k,)).fetchone()
        if r and r[0] and (r[0] == bill["supplier_norm"] or _vendor_match(r[0], bill["supplier"])):
            return True
    except sqlite3.Error:
        pass
    return False


def _s446_compare_one(con, acon, link):
    import difflib                                              # noqa: PLC0415
    bill = con.execute("SELECT * FROM purchase_bill WHERE id=?", (link["bill_id"],)).fetchone()
    scan = acon.execute("SELECT id, vendor, bill_no, bill_date, total_amount FROM bills WHERE id=?", (link["asset_bill_id"],)).fetchone()
    if bill is None or scan is None:
        return None
    chosen = None
    try:
        r = con.execute("SELECT chosen_vendor FROM purchase_scan_state WHERE asset_bill_id=?", (scan["id"],)).fetchone()
        chosen = r[0] if r else None
    except sqlite3.Error:
        chosen = None
    sup_ok = _s446_supplier_ok(con, scan["vendor"], bill) or (bool(chosen) and chosen == bill["supplier_norm"])
    a, b = _s446_digits(scan["bill_no"]), _s446_digits(bill["bill_no"])
    bno_ok = bool(a and b) and (a == b or (len(b) >= 3 and a.endswith(b)) or (len(a) >= 3 and b.endswith(a)))
    sd = _iso(scan["bill_date"]) or _iso_any(scan["bill_date"])
    date_ok = bool(sd) and sd == bill["bill_date"]
    try:
        st = int(round(float(scan["total_amount"]) * 100)) if scan["total_amount"] not in (None, "") else None
    except (TypeError, ValueError):
        st = None
    total_ok = st is not None and abs(st - int(bill["amount_p"] or 0)) <= 100
    items = [dict(r) for r in acon.execute("SELECT item_name, quantity, rate, batch, expiry FROM bill_items WHERE bill_id=?", (scan["id"],))]
    # Marg's own lines of this bill, from the newest export that carries them
    ml = [dict(r) for r in con.execute("SELECT item, qty, free, rate_p, batch, expiry, source_md5 FROM purchase_line WHERE supplier_norm=? AND bill_no=? "
                                       "AND bill_date=? ORDER BY id", (bill["supplier_norm"], bill["bill_no"], bill["bill_date"]))]
    if ml:
        newest = ml[-1]["source_md5"]
        ml = [x for x in ml if x["source_md5"] == newest]
    detail, wrong = [], 0
    for it in items:
        nm = _s446_name_norm(it.get("item_name"))
        best, score = _s454_learnt_line(con, bill, nm, ml)            # S454 P5 (11.2): the supplier's learnt name first
        for x in ([] if best is not None else ml):
            sc = difflib.SequenceMatcher(None, nm, _s446_name_norm(x["item"])).ratio()
            if sc > score:
                best, score = x, sc
        row = dict(scan_item=it.get("item_name"), marg_item=(best or {}).get("item"), score=round(score, 2), bad=[])
        if best is None or score < 0.6:
            row["bad"].append("name")
        else:
            try:
                if it.get("quantity") not in (None, "") and abs(float(it["quantity"]) - float(best["qty"] or 0)) > 0.001:
                    row["bad"].append("qty")
            except (TypeError, ValueError):
                row["bad"].append("qty")
            try:
                if it.get("rate") not in (None, "") and best.get("rate_p") is not None:
                    r1, r2 = float(it["rate"]), float(best["rate_p"]) / 100.0
                    if abs(r1 - r2) > max(0.01, 0.01 * r2):
                        row["bad"].append("rate")
            except (TypeError, ValueError):
                row["bad"].append("rate")
            if (it.get("batch") or "").strip() and (best.get("batch") or "").strip() and \
                    re.sub(r"\W", "", str(it["batch"]).upper()) != re.sub(r"\W", "", str(best["batch"]).upper()):
                row["bad"].append("batch")
            if (it.get("expiry") or "").strip() and (best.get("expiry") or "").strip() and _s446_exp(it["expiry"]) != _s446_exp(best["expiry"]):
                row["bad"].append("expiry")
        wrong += bool(row["bad"])
        detail.append(row)
    allok = sup_ok and bno_ok and date_ok and total_ok and wrong == 0
    con.execute("INSERT OR REPLACE INTO purchase_sarvam_check (asset_bill_id, bill_id, month, checked_at, supplier_ok, billno_ok, date_ok, total_ok, "
                "items_read, items_wrong, all_ok, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (scan["id"], bill["id"], bill["bill_date"][:7], now_iso(), int(sup_ok), int(bno_ok), int(date_ok), int(total_ok), len(items), wrong,
                 int(allok), json.dumps(dict(scan=dict(vendor=scan["vendor"], bill_no=scan["bill_no"], date=sd, total_p=st),
                                             marg=dict(supplier=bill["supplier"], bill_no=bill["bill_no"], date=bill["bill_date"], total_p=bill["amount_p"]),
                                             items=detail[:60]))))
    return allok


def sarvam_compare(con):
    """Every linked scan compared once (again when its link moves). Returns how many rows were written."""
    con.execute(S446_SARVAM_DDL)
    acon = _assets_con()
    if acon is None:
        return 0
    n = 0
    try:
        have = {r[0]: r[1] for r in con.execute("SELECT asset_bill_id, bill_id FROM purchase_sarvam_check")}
        for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link").fetchall():
            if have.get(r[1]) == r[0]:
                continue
            if _s446_compare_one(con, acon, dict(bill_id=r[0], asset_bill_id=r[1])) is not None:
                n += 1
    finally:
        acon.close()
    if n:
        con.commit()
    return n


def sarvam_summary(con, month):
    con.execute(S446_SARVAM_DDL)
    r = con.execute("SELECT COUNT(*), SUM(all_ok), SUM(1-supplier_ok), SUM(1-billno_ok), SUM(1-date_ok), SUM(1-total_ok), "
                    "SUM(CASE WHEN items_wrong>0 THEN 1 ELSE 0 END), SUM(CASE WHEN items_read>0 THEN 1 ELSE 0 END) FROM purchase_sarvam_check WHERE month=?",
                    (month,)).fetchone()
    k = ("n", "agreed", "supplier_wrong", "billno_wrong", "date_wrong", "total_wrong", "items_wrong", "items_read")
    return {k[i]: int(r[i] or 0) for i in range(len(k))}


def _s446_trial_months(con):
    until = _s446_setting(con, "purchase.sarvam_trial_until", "")
    if not until or dt.date.today().isoformat() > until:
        return [], until
    t = dt.date.today()
    prev = (t.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    return [prev, t.strftime("%Y-%m")], until


def _s446_sarvam_text(month, s):
    return ("%s: %d bill%s · Sarvam agreed fully on %d · supplier wrong %d · bill no. wrong %d · date wrong %d · total wrong %d · items wrong %d (of %d with items read)"
            % (_month_name(month), s["n"], "" if s["n"] == 1 else "s", s["agreed"], s["supplier_wrong"], s["billno_wrong"], s["date_wrong"],
               s["total_wrong"], s["items_wrong"], s["items_read"]))


def sarvam_lines(con):
    """The owner's monthly Needs-you summary while the trial runs (info lines; the drill-down is Marg Purchases -> Scan links)."""
    out = []
    try:
        months, until = _s446_trial_months(con)
        if not months:
            return out
        sarvam_compare(con)
        for m in months:
            s = sarvam_summary(con, m)
            if s["n"]:
                out.append(dict(cls="info", target="porders", text="Scan reading trial (Marg overrules until %s) -- %s" % (until, _s446_sarvam_text(m, s))))
    except Exception:                                          # noqa: BLE001
        return out
    return out


def _s446_sarvam_card(con):
    """One line on the owner's Scan links page."""
    try:
        months, until = _s446_trial_months(con)
        if not months:
            return ""
        sarvam_compare(con)
        prefix = request.script_root + _url_prefix
        parts = []
        for m in months:
            s = sarvam_summary(con, m)
            if s["n"]:
                parts.append('<a href="%s/page/sarvam?month=%s">%s</a>' % (prefix, m, _esc(_s446_sarvam_text(m, s))))
        if not parts:
            return ""
        return ('<div class="card" id="s446sarvam"><h2>Scan reading against Marg (trial until %s: Marg overrules)</h2><div class="muted">%s</div></div>'
                % (_esc(until), "<br>".join(parts)))
    except Exception:                                          # noqa: BLE001
        return ""


@bp.route("/page/sarvam")
def page_s446_sarvam():
    u, err = _person("checker")
    if err:
        return err
    con = _db()
    _ensure(con)
    sarvam_compare(con)
    month = str(request.args.get("month") or dt.date.today().strftime("%Y-%m"))[:7]
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    s = sarvam_summary(con, month)
    rows = []
    for r in con.execute("SELECT asset_bill_id, supplier_ok, billno_ok, date_ok, total_ok, items_read, items_wrong, all_ok, detail FROM purchase_sarvam_check "
                         "WHERE month=? ORDER BY all_ok, asset_bill_id", (month,)):
        d = json.loads(r[8] or "{}")
        sc, mg = d.get("scan") or {}, d.get("marg") or {}
        r = _s454_sarvam_row(r, sc, mg, d)                          # S454 (7.4, F-690): the counter's own reading of each field
        yn = lambda v: "" if v else ' class="bad"'                  # noqa: E731
        bad_items = "; ".join("%s (%s)" % (x.get("scan_item") or "?", ", ".join(k for k in (x.get("bad") or []) if k not in ("batch", "expiry")))
                              for x in (d.get("items") or []) if [k for k in (x.get("bad") or []) if k not in ("batch", "expiry")])   # S454: not batch / expiry
        rows.append('<tr><td>%d</td><td%s>%s / %s</td><td%s>%s / %s</td><td%s>%s / %s</td><td%s>%s / %s</td><td>%d read, %d wrong%s</td></tr>'
                    % (r[0], yn(r[1]), _esc(sc.get("vendor")), _esc(mg.get("supplier")), yn(r[2]), _esc(sc.get("bill_no")), _esc(mg.get("bill_no")),
                       yn(r[3]), _esc(sc.get("date")), _esc(mg.get("date")), yn(r[4]),
                       _r(sc["total_p"]) if sc.get("total_p") is not None else "-", _r(mg.get("total_p") or 0), r[5], r[6],
                       ("<br><span class=muted>%s</span>" % _esc(bad_items[:400])) if bad_items else ""))
    body = ('<h1>Scan reading against Marg — %s</h1><div class="muted">%s. Each cell: what the scan reader read / what Marg holds. '
            'Marg\'s figure is the bill\'s; this page only counts.</div><div class="card"><div class="scroll"><table>'
            '<tr><th>scan</th><th>supplier</th><th>bill no.</th><th>date</th><th>total</th><th>items</th></tr>%s</table></div></div>'
            % (_esc(_month_name(month)), _esc(_s446_sarvam_text(month, s)), "".join(rows) or "<tr><td colspan=6>none</td></tr>"))
    body += ('<div class="muted" id="s454items"><a href="%s/page/items?month=%s">Items check — do the bills add up line by line? (%s)</a></div>'   # S454 P5
             % (request.script_root + _url_prefix, month, _esc(_month_name(month))))
    _s850_js = ""
    try:                                                       # S850 (D993 b-c, D995): the line verdicts and the corrections kept
        import marg_right as _s850                            # noqa: PLC0415 -- beside this file
        body += _s850.cards_html(con, month, request.script_root + _url_prefix)
        _s850_js = _s850.JS
    except Exception as _e850:                                 # noqa: BLE001 -- the page as it was before S850
        print("S850 cards failed: %r" % (_e850,), file=_sys_s781.stderr)
    return _page("Scan reading against Marg — %s" % _month_name(month), body, _s850_js)


# ---------------------------------------------------------------- the payment sheet: an earlier month's unfinished work
def _s446_earlier_card(con, month, prefix):
    try:
        out = []
        for m in [x for x in _months(con, 4) if x < month]:
            unsent = 0
            try:
                unsent = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE month=? AND status IN ('queued','failed') AND kind IN ('neft','cheque')",
                                         (m,)).fetchone()[0])          # S454: payment messages only (an order or test message is not the sheet's)
            except sqlite3.Error:
                unsent = 0
            nodone = 0
            try:
                st = con.execute("SELECT status FROM purchase_month WHERE month=?", (m,)).fetchone()
                ev = con.execute("SELECT COUNT(*) FROM purchase_neft_event WHERE month=?", (m,)).fetchone()[0]
                if st and st[0] == "final" and not ev:
                    _s, groups = _pay_rows(con, m)
                    nodone = sum(1 for g in groups if g["route"] == "NEFT" and g["payable_p"] > 0)
            except Exception:                                  # noqa: BLE001
                nodone = 0
            if unsent or nodone:
                bits = []
                if unsent:
                    bits.append("%d supplier message%s not sent" % (unsent, "" if unsent == 1 else "s"))
                if nodone:
                    bits.append("%d NEFT line%s with no NEFT recorded" % (nodone, "" if nodone == 1 else "s"))
                out.append((m, unsent + nodone, " · ".join(bits)))
        if not out:
            return ""
        return ('<div class="card" id="s446earlier" style="border:2px solid #b3261e"><h2>Pichhle mahine ka baaki: %d</h2>%s</div>'
                % (sum(x[1] for x in out), "".join('<div><a class="p" href="%s/page/pay/%s">%s — %s ›</a></div>' % (prefix, m, _esc(_month_name(m)), _esc(t))
                                                   for m, _n, t in out)))
    except Exception:                                          # noqa: BLE001
        return ""
# ---- S446_AMIR_STAGES_BILLS end ---------------------------------------------------------------------------------------------------------



# ==========================================================================================================================================
# S452_AMIR_PANEL_FIXES (02-Oct-2026, F-686) -- Amir's "Marg mein daalne ke bill" holds only bills that are NOT in Marg.
# The owner, 01-Oct: "The scanned medicine bills are simply made available to him at one place so he can upload them in the digital entry
# part of Marg ... That will be the final entry of the bill." S446 listed EVERY captured pharmacy scan with no Marg link -- near-matches
# reception had not answered, unread suppliers, the shop's own name read as the supplier -- and a bill uploaded again is a second purchase.
#   * scans_for_amir(con) -> {list, held}: a scan is LISTED only when the server finds no likely Marg bill for it and its supplier is known
#     -- S440's "Marg ka intezaar" group as purchase_scan_state holds it (the matcher runs first when the scans changed). A near-match
#     (Yahi bill hai?), an unread supplier (Supplier chuno), the buyer's own name, a second scan: HELD -- reception's Scan ka kaam first.
#   * Each listed line carries what is known: the stamp, the supplier (chosen, else matched, else as read), "scan: dd-mm, <who>", and the
#     bill date only when it lies within 60 days of the scan day. The file: <stamp>_<SUPPLIER>[_<billno>]_<dd-mm-yyyy>.pdf -- a bill number
#     not read is left out; a date outside the 60 days is replaced by the scan day.
#   * The download guard: a scan Marg's bill has reached since the page was drawn answers "Yeh bill Marg mein aa chuka hai"; a held scan
#     answers "reception ki jaanch mein". The zip of today's follows the same rule.
#   * The owner's Scan links page: "Amir's list: N to enter · M held for reception".
#   * The bank's NEFT advice file (full account numbers) is the owner's and the senders' (supplier_msg.senders) -- no staff login else.
# ==========================================================================================================================================
S452_DATE_DAYS = 60


def _s452_scan_rows():
    """The captured pharmacy scans, no duplicates of another (assets.db, READ ONLY); None when that database is not reachable."""
    acon = _assets_con()
    if acon is None:
        return None
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = ["id", "stamp_no", "vendor", "bill_no", "bill_date", "created_at", "total_amount"] + [c for c in ("dup_of", "submitted_by", "scanned_by", "created_by") if c in cols]   # S454: the amount read
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND status='captured' ORDER BY created_at, id" % ", ".join(sel))]
    finally:
        acon.close()
    return [r for r in rows if not r.get("dup_of")]


def _s452_name(stamp, supplier, bill_no, day_iso):
    st = re.sub(r"[^A-Za-z0-9-]+", "_", str(stamp or "")).strip("_") or "SCAN"
    sup = re.sub(r"[^A-Z0-9]+", "_", str(supplier or "").upper()).strip("_")[:40] or "SUPPLIER"
    bno = re.sub(r"[^A-Za-z0-9]+", "", str(bill_no or ""))
    d = str(day_iso or "")[:10]
    d = (d[8:10] + "-" + d[5:7] + "-" + d[:4]) if len(d) == 10 else dt.date.today().strftime("%d-%m-%Y")
    return "_".join([st, sup] + ([bno] if bno else []) + [d]) + ".pdf"


def _s683_final_months(con):
    """S683: the months the owner has finalised on the purchase page (purchase_month.status = 'final')."""
    try:
        return {str(r[0]) for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except sqlite3.Error:
        return set()


def _s683_hold(r, sup, cday, bdd, bills, taken, final):
    """S683 (the owner, 30-Oct 17:56 / 18:05): a scan S452 would list is HELD -- never on Amir's list -- when it is not clearly a bill
    missing from Marg.  r: the scan row; sup: its supplier key; cday: the scan day; bdd: the paper's bill date when within
    S452_DATE_DAYS of the scan, else None; bills: the live export's bills; taken: the bill ids that have a scan; final: finalised
    months.  -> the reason, or None (the scan stays on his list).  (No unscanned-bill-nearby rule: it hid genuine bills.)"""
    if cday is not None and cday.strftime("%Y-%m") in final and (bdd is None or bdd.strftime("%Y-%m") in final):
        return "month finalised"                         # the scan day's month, and the paper's when read near it
    stails = _bill_tails_s439(r.get("bill_no"))

    def gap(b):
        bd = _date_or_none_s439(b.get("bill_date"))
        g = [abs((d - bd).days) for d in (bdd, cday) if d is not None and bd is not None]
        return min(g) if g else 9999

    def same_no(b, tight):
        for x in stails:
            for y in _bill_tails_s439(b.get("bill_no")):
                if x == y or (min(len(x), len(y)) >= 4 and (x in y or y in x)):
                    return True
                if tight and min(len(x), len(y)) >= 3 and x[-3:] == y[-3:]:      # A0006678 read for A000678, days apart
                    return True
        return False
    mine = [b for b in bills if supplier_key(b.get("supplier")) == sup]
    hit = sorted((b for b in mine if stails and ((gap(b) <= S439_HINT_DAYS and same_no(b, False))
                                             or (gap(b) <= S439_DATE_DAYS and same_no(b, True)))), key=lambda b: (gap(b), b["id"]))
    if hit:
        b = hit[0]
        return ("in Marg: second scan of bill %s" if b["id"] in taken else "in Marg: bill %s not yet paired") % b["bill_no"]
    return None


def scans_for_amir(con):
    """{list: [scans to put into Marg], held: [scans waiting for reception], ok} -- the rule in the header above."""
    try:
        _rematch_if_changed(con, "S452 list")                  # a scan that changed is matched before it is shown to anyone
    except Exception:                                          # noqa: BLE001
        pass
    rows = _s452_scan_rows()
    if rows is None:
        return dict(list=[], held=[], ok=False)
    linked = _s446_linked(con)
    try:                                                       # S849 (D995): the scans answered 'not a purchase bill' (scan_ask.py)
        import scan_ask as _s849                              # noqa: PLC0415
        _s849_aside = _s849.aside_ids(con)
    except Exception:                                          # noqa: BLE001 -- without it, the list as before
        _s849_aside = set()
    try:
        _ensure_s439(con)
        st = {int(r["asset_bill_id"]): dict(r) for r in con.execute("SELECT * FROM purchase_scan_state")}
    except sqlite3.Error:
        st = {}
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    bill_ids = {b["id"] for b in bills}
    ctx = _vendor_ctx_s439(con, bills)
    suppliers = set(ctx["canon"].values())
    today = dt.date.today()
    out, held = [], []
    final = _s683_final_months(con)                             # S683: read once
    try:
        taken = {int(x[0]) for x in con.execute("SELECT bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        taken = set()
    taken |= {int(b["id"]) for b in bills if b.get("scan_bill_id")}
    for r in rows:
        sid = int(r["id"])
        if sid in linked or sid in _s849_aside:                # S849: a paper answered 'not a purchase bill' is never Amir's to enter
            continue
        s = st.get(sid) or {}
        why = s.get("why") or ""
        chosen = str(s.get("chosen_vendor") or "")
        cday = _date_or_none_s439(str(r.get("created_at") or "")[:10])
        item = dict(id=sid, stamp=r.get("stamp_no") or ("#%d" % sid), read_vendor=r.get("vendor") or "", bill_no=str(r.get("bill_no") or ""),
                    created_at=r.get("created_at") or "", scan_day=(cday.isoformat() if cday else ""),
                    scan_ddmm=(cday.strftime("%d-%m") if cday else "-"),
                    who=str(r.get("submitted_by") or r.get("scanned_by") or r.get("created_by") or ""), today=(cday == today))
        reason = None
        if why == "dup":
            reason = "second scan"
        elif why in ("number_differs", "amount_differs", "no_digits") and s.get("likely_bill") in bill_ids:
            reason = "near-match"
        elif why == "vendor_unknown" and not chosen:
            reason = "supplier unread"
        if reason is None and _s454_unread_row(r):                  # S454 (4.7, F-695): a paper with nothing read is never Amir's
            reason = "unread paper"
        sup = None
        if reason is None:
            if chosen and chosen != "-" and chosen in suppliers:
                sup = chosen
            else:
                k, how, _sc = _vendor_resolve_s439(r.get("vendor"), ctx)
                sup = k if how in ("exact", "learned", "similar") else None
            if not sup:
                reason = "supplier unknown"
        if reason:
            item["held"] = reason
            held.append(item)
            continue
        bd = _iso(r.get("bill_date")) or _iso_any(r.get("bill_date")) or ""
        bdd = _date_or_none_s439(bd)
        near = bdd is not None and cday is not None and abs((cday - bdd).days) <= S452_DATE_DAYS
        hold = _s683_hold(r, sup, cday, bdd if near else None, bills, taken, final)     # S683: only a bill clearly missing from Marg
        if hold:
            item["held"] = hold
            held.append(item)
            continue
        item.update(supplier=sup, bill_date=(bd if near else ""),
                    name=_s452_name(item["stamp"], sup, item["bill_no"], bd if near else (item["scan_day"] or today.isoformat())))
        out.append(item)
    return dict(list=out, held=held, ok=True)


def _s452_lookup(con, sid):
    """('list', item) | ('held', item) | ('linked', None) | (None, None) for one scan, by the same rule as the page."""
    r = scans_for_amir(con)
    for x in r["list"]:
        if x["id"] == int(sid):
            return "list", x
    for x in r["held"]:
        if x["id"] == int(sid):
            return "held", x
    if int(sid) in _s446_linked(con):
        return "linked", None
    return None, None


def _s452_small_page(kind):
    if kind == "linked":
        h, p = "Yeh bill Marg mein aa chuka hai", "Marg ki export mein yeh bill mil gaya hai — ise dobara Marg mein mat daaliye. List dobara kholiye: yeh line hat jayegi."
    else:
        h, p = "Yeh scan abhi reception ki jaanch mein hai", "Marg mein mat daaliye — reception ka jawab aane ke baad hi yeh list mein aayega."
    html = ('<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title></head><body style="margin:0;padding:16px;background:#fafafa;font:18px/1.5 system-ui,sans-serif">'
            '<div style="background:#fff;border:2px solid #8a6100;border-radius:10px;padding:14px"><h2 style="margin:0 0 8px">%s</h2><p>%s</p>'
            '<p><a href="/finance/amir/step/2">&larr; Wapas: Marg mein daalne ke bill</a></p></div></body></html>' % (_esc(h), _esc(h), _esc(p)))
    return html, 409, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


def _s452_amir_list_line(con):
    """One line on the owner's Scan links page."""
    try:
        r = scans_for_amir(con)
        if not r.get("ok"):
            return ""
        return ('<div class="card" id="s452amirlist"><div class="muted"><b>Amir\'s list: %d to enter · %d held for reception</b></div></div>'
                % (len(r["list"]), len(r["held"])))
    except Exception:                                          # noqa: BLE001
        return ""


def _s452_may_advice(con, u):
    """The bank's NEFT advice file carries full account numbers: the owner (the medical checker) and supplier_msg.senders only."""
    if _is_doctor(u):
        return True
    who = str((u or {}).get("user") or "").strip().lower()
    names = {w.strip().lower() for w in _s446_setting(con, "supplier_msg.senders", "manoj,shavez").split(",") if w.strip()}
    return bool(who) and who in names
# ---- S452_AMIR_PANEL_FIXES end ----------------------------------------------------------------------------------------------------------



# ==========================================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, F-695 / D668): a paper with no bill number and no amount read (or read as an Estimate, Challan or
# Quotation) is never on Amir's list or in its count -- reception is asked "Kya yeh dawa (pharmacy) ka bill hai?" first (porders_s454).
# The matcher's fingerprint (_scan_fingerprint) now also changes when a scan's supplier, number or amount is filled in after the scan was
# made (the OCR is a background job), so the matcher sees it at the next page or cron run.
# ==========================================================================================================================================
_S454_HEAD = re.compile(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", re.I)


def _s454_unread_row(r):
    no_no = not str(r.get("bill_no") or "").strip()
    no_amt = r.get("total_amount") in (None, "") or _float_or_none(r.get("total_amount")) in (None, 0.0)
    return bool((no_no and no_amt) or _S454_HEAD.search("%s %s" % (r.get("vendor") or "", r.get("bill_no") or "")))



# ==========================================================================================================================================
# S454_BILL_REGISTER part 2 (03-Oct-2026, S454 5 / 7 / 8; D650 D662 D663 D665; F-690 F-691) -- the rules live in scan_register.py.
#   * _match_s439: a scan pairs with a Marg bill by itself only when the pair is VERIFIED (the total agrees within the noise, the bill number
#     agrees, and the supplier or the date agrees). _rematch keeps every stored link (the rules only give it its state) and, after the rules,
#     the auto-link pairs a scan with the ONE unscanned bill of its supplier carrying its amount (audit auto_link, grade AUTO).
#   * _why_s439: a scan whose bill number agrees with a bill (its supplier agreeing or not read) names that bill as its likely bill --
#     "Is this the bill?" -- so it is never sent to Amir as a bill Marg does not have.
#   * /page/scans is the month's register (scan_register.page_body); POST /api/s454/nopaper -- the owner's "Accept without paper" / Undo.
#   * The Sarvam counter reads every field by the counter's rule (scan_register.sarvam).
#   * Vendor payments (/page/pay..., the letter, the annexure, the advice, the pack; /api/pay-letter, /api/pay-verify, /api/pay-line) open only
#     for the owner and supplier_msg.senders; the "Vendor payments" link is drawn for them only; the phone book shows anyone else the
#     account number's last four digits and no IFSC, and refuses them a bank edit.
# ==========================================================================================================================================
_S454_CX = None


def _s454_sr():
    import scan_register                                       # noqa: PLC0415 -- beside this file
    return scan_register


def _s454_cx():
    return _S454_CX if _S454_CX is not None else _s454_sr().Ctx(_db())


_rematch_before_s454 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S454: the S439 pass, with the rules' context loaded once for the pass."""
    global _S454_CX
    try:
        _S454_CX = _s454_sr().Ctx(con)
    except Exception:                                          # noqa: BLE001
        _S454_CX = None
    try:
        return _rematch_before_s454(con, who)
    finally:
        _S454_CX = None


_match_before_s454 = _match_s439


def _match_s439(s, b):                                            # noqa: F811
    """S454 (5): one scan against one Marg bill -> (1, 'EXACT', rule) when the pair is VERIFIED, else None."""
    if b["id"] in s.get("_no", ()):
        return None
    SR = _s454_sr()
    a = SR.agree(_s454_cx(), s, b)
    if SR.verified(a):
        return 1, "EXACT", "verified (S454 5): number + total%s" % ("".join(" + " + k for k in ("supplier", "date") if a[k] == "agree"))
    return None


_why_before_s454 = _why_s439


def _why_s439(s, bills, taken, last_date):                        # noqa: F811
    why, detail, hint = _why_before_s454(s, bills, taken, last_date)
    if why not in ("no_bill_yet", "vendor_unknown") or not s.get("bill_no"):
        return why, detail, hint
    SR = _s454_sr()
    cx = _s454_cx()
    canon = (s.get("_vendor") or (None,))[0]
    no = s.get("_no", ())
    scanned = _date_or_none_s439(s.get("created_at"))

    def gap(b):
        g = [abs((d - b["_date"]).days) for d in (s.get("_date"), scanned) if d is not None and b.get("_date") is not None]
        return min(g) if g else 9999
    cands = [b for b in bills if b["id"] not in no and SR.billno(s["bill_no"], b["bill_no"]) == "agree" and gap(b) <= S439_HINT_DAYS
             and (canon is None or canon == b.get("_skey") or SR.supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(s["id"])) == "agree")]
    if not cands:
        return why, detail, hint
    b = min(cands, key=lambda b: (1 if b["id"] in taken else 0, gap(b), abs((s.get("amount_p") or 0) - b["amount_p"]), b["id"]))
    s["_likely"] = b["id"]
    lab = "%s bill %s (%s, %s)" % (b.get("_skey") or supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))
    also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
    amt = s.get("amount_p")
    return ("amount_differs", "amount differs — the scan reads %s; %s carries the same number%s" % (_r(amt) if amt is not None else "no amount", lab, also),
            None if b["id"] in taken else b["id"])


def _s454_autolink(con, who, scans, bills, taken, linked, dups):
    """S454 (5): every unlinked scan (not a second scan) whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill
    of that supplier is paired with it (grade AUTO, audit auto_link). Returns the links made."""
    SR = _s454_sr()
    cx = _s454_cx()
    scan_from = _scan_from_s409(con)
    dup_ok = set()
    try:
        dup_ok = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_state WHERE dup_ok IS NOT NULL")}
    except sqlite3.Error:
        pass
    made = []
    for s in sorted(scans, key=lambda x: x["id"]):
        if s["id"] in linked or s["id"] in dups or s["id"] in dup_ok:
            continue
        b = SR.autolink_choice(cx, s, bills, taken, scan_from, refused=s.get("_no", ()))
        if not b:
            continue
        rule = "auto_link (S454 5): the only unscanned bill of this supplier with this amount"
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                          (b["id"], s["id"], "AUTO", rule, now_iso()))
        if not cur.rowcount:
            continue
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (s["id"], b["id"]))
        _audit(con, who, "auto_link", b["id"], dict(scan=s["id"], supplier=supplier_key(b["supplier"]), bill_no=b["bill_no"], amount_p=b["amount_p"],
                                                     scan_no=s.get("bill_no"), scan_date=s.get("bill_date"), kit="S454"))
        taken[b["id"]] = s["id"]
        linked.add(s["id"])
        made.append((s["id"], b["id"], "AUTO", "auto_link"))
    return made


def _s454_bar(month):
    return ('<div id="s440bar" style="position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;background:#1f3864;color:#fff;'
            'padding:6px 10px;margin:0 0 10px;border-radius:0 0 8px 8px"><a id="s440back" href="%s" style="display:flex;align-items:center;'
            'justify-content:center;min-height:44px;padding:0 20px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;'
            'text-decoration:none">← BACK</a><span style="margin-left:auto;font-weight:600">Purchase bills</span></div>' % _esc(_s454_back()))


def _s454_back():
    frm = str(request.args.get("from") or "")
    return frm if (frm.startswith("/") and not frm.startswith("//") and len(frm) <= 300 and not re.search(r"[\\\r\n\"'<>]", frm)) else "/portal"


def _s454_register_page(con, u):
    SR = _s454_sr()
    prefix = request.script_root + _url_prefix
    months = SR.months_with_bills(con)
    month = str(request.args.get("month") or (months[0] if months else dt.date.today().strftime("%Y-%m")))[:7]
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    if month not in months:
        months = sorted(set(months + [month]), reverse=True)
    try:
        sarvam_compare(con)
    except Exception:                                          # noqa: BLE001
        pass
    body = SR.page_body(con, month, prefix, _is_doctor(u), months)
    up = ('<button id="s440up" aria-label="back to top" onclick="window.scrollTo({top:0,behavior:\'smooth\'})" style="position:fixed;right:14px;bottom:18px;'
          'width:48px;height:48px;border-radius:24px;border:0;background:#1f3864;color:#fff;font-size:24px;display:none;z-index:70;cursor:pointer">↑</button>'
          '<script>window.addEventListener("scroll",function(){var b=document.getElementById("s440up");if(b)b.style.display=(window.pageYOffset>window.innerHeight)?"block":"none"});</script>')
    return _page("Purchase bills — %s" % SR.month_name(month), _s454_bar(month) + body + up)     # S440's bar and up-arrow, once each


@bp.route("/api/s454/nopaper", methods=["POST"])
def api_s454_nopaper():
    """The owner's tap on a "paper not found" row of a counted month: accept it without paper, or undo (audited)."""
    u, err = _person("checker")
    if err:
        return err
    con = _db()
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        bid = 0
    ok, msg = _s454_sr().accept_nopaper(con, _who(u), bid, bool(int(b.get("accept") or 0)))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


def sarvam_summary(con, month):                                  # noqa: F811
    """S454 (7.4, F-690): the month's linked bills by the counter's rule (the old keys kept for the pages that read them)."""
    s = _s454_sr().sarvam(con, month)
    m = s["misses"]
    return dict(n=s["n"], agreed=s["agreed"], supplier_wrong=m["supplier"], billno_wrong=m["billno"], date_wrong=m["date"], total_wrong=m["total"],
                items_wrong=s["items_read"] - s["items_right"], items_read=s["items_read"], items_right=s["items_right"])


def _s446_sarvam_text(month, s):                                 # noqa: F811
    return ("%s: %d bill%s · read right in full %d · supplier misread %d · bill no. misread %d · date misread %d · total misread %d · "
            "item lines %d of %d read right (batch and expiry are not judged from a scan)"
            % (_month_name(month), s["n"], "" if s["n"] == 1 else "s", s["agreed"], s["supplier_wrong"], s["billno_wrong"], s["date_wrong"],
               s["total_wrong"], s.get("items_right", s["items_read"] - s["items_wrong"]), s["items_read"]))


def _s454_sarvam_row(r, sc, mg, d):
    """One row of the Sarvam page, its four flags by the counter's rule, its item count without batch / expiry."""
    try:
        SR = _s454_sr()
        f = SR.sarvam_flags(_s454_sr().Ctx(_db()), dict(vendor=sc.get("vendor"), bill_no=sc.get("bill_no"), bill_date=sc.get("date"),
                                                         amount_p=sc.get("total_p")),
                            dict(supplier=mg.get("supplier") or "", bill_no=mg.get("bill_no"), bill_date=mg.get("date"), amount_p=mg.get("total_p") or 0))
        wrong = sum(1 for x in (d.get("items") or []) if [k for k in (x.get("bad") or []) if k not in ("batch", "expiry")])
        return (r[0], f["supplier_ok"], f["billno_ok"], f["date_ok"], f["total_ok"], r[5], wrong, int(all(f.values()) and not wrong), r[8])
    except Exception:                                          # noqa: BLE001
        return r


# ---- Vendor payments: the owner and supplier_msg.senders only (S454 8, D663)
S454_PAY_PATHS = ("/page/pay", "/api/pay-letter", "/api/pay-verify", "/api/pay-line")


@bp.before_request
def _s454_pay_gate():
    path = request.path or ""
    rel = path[len(_url_prefix):] if path.startswith(_url_prefix) else None
    if rel is None or not any(rel == p or rel.startswith(p + "/") for p in S454_PAY_PATHS):
        return None
    try:
        u, err = _require("checker", "maker", "viewer")
        if err or not u:
            return None                                        # the page's own gate answers a stranger
        if _s452_may_advice(_db(), u):
            return None
    except Exception:                                          # noqa: BLE001 -- fail closed: these pages carry account numbers
        pass
    return _refuse("Vendor payments sirf doctor sahab aur Shavez ke liye hai.")


_book_nav_before_s454 = _book_nav


def _book_nav(prefix):                                          # noqa: F811
    out = _book_nav_before_s454(prefix)
    try:
        u, err = _require("checker", "maker", "viewer")
        if err or not u or not _s452_may_advice(_db(), u):
            out = out.replace('<a href="%s/page/pay">Vendor payments</a>' % prefix, "")
    except Exception:                                          # noqa: BLE001
        out = out.replace('<a href="%s/page/pay">Vendor payments</a>' % prefix, "")
    return out


def _s454_mask_bank(r):
    d = {k: r[k] for k in r.keys()}
    d["acct_no"] = _last4(d.get("acct_no")) if d.get("acct_no") else ""
    d["ifsc"] = ""
    d["upi_id"] = ""
    return d
# ---- S454 part 2 end --------------------------------------------------------------------------------------------------------------------



# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.4, F-696): gap (3), proven by the data -- Marg's sale export prints 20 characters of an item's
# name, so _pace never found the sales of a stock item whose name is longer (55 such items on 03-Oct, not one with a pace) and plan() skipped
# them. Such an item now takes the pace of its 20-character name; items that share that name share it equally (approximate) -- on
# order.stock_basis = count (the default); on marg the plan stays today's, line for line. The other two
# suspected gaps were tested and not proven by the data (see the kit's report): not changed.
# ==========================================================================================================================================
_pace_before_s454 = _pace


def _pace(con, snap, today):                                       # noqa: F811
    out = _pace_before_s454(con, snap, today)
    try:
        r_ = con.execute("SELECT value FROM setting WHERE key='order.stock_basis'").fetchone()
        if r_ and str(r_[0] or "").strip() == "marg":
            return out                                         # on marg the plan is today's, line for line (S454 9.2)
        import item_alias as _ia                               # noqa: PLC0415
        clip = getattr(_ia, "SALE_CLIP", 20)
        fam = {}
        for k, s in snap.items():
            if len(str(s["item"])) > clip:
                fam.setdefault(norm(str(s["item"])[:clip]), []).append(k)
        if not fam:
            return out
        since = (today - dt.timedelta(days=PACE_DAYS)).isoformat()
        per, last = {}, {}
        for name, d, q, ret in con.execute("SELECT item_name, business_date, qty_raw, is_return FROM sale_line_item WHERE unit=? AND business_date>=? "
                                           "AND business_date<=?", (_unit, since, today.isoformat())):
            ck = norm(str(name)[:clip])
            if ck not in fam:
                continue
            size = (snap.get(fam[ck][0]) or {}).get("pack_size", 1)
            e = per.setdefault(ck, {"days": {}, "total": 0.0})
            u = _units(q, size) * (-1 if ret else 1)
            e["days"][d] = e["days"].get(d, 0.0) + u
            e["total"] += u
        for name, d in con.execute("SELECT item_name, MAX(business_date) FROM sale_line_item WHERE unit=? GROUP BY item_name", (_unit,)):
            ck = norm(str(name)[:clip])
            if ck in fam and (ck not in last or d > last[ck]):
                last[ck] = d
        for ck, members in fam.items():
            e = per.get(ck)
            n = len(members)
            for k in members:
                if k in out and out[k].get("rate_per_day"):
                    continue
                if e:
                    total = max(0.0, e["total"]) / n
                    peak = max(e["days"].values()) / n if e["days"] else 0.0
                    out[k] = dict(rate_per_day=total / PACE_DAYS, sell_days=sum(1 for v in e["days"].values() if v > 0),
                                  peak_share=(peak / total) if total > 0 else 0.0, approx_shared=n if n > 1 else 0)
                if ck in last:
                    try:
                        out.setdefault(k, dict(rate_per_day=0.0, sell_days=0, peak_share=0.0))["days_since_sale"] = (today - dt.date.fromisoformat(last[ck])).days
                    except ValueError:
                        pass
    except Exception:                                          # noqa: BLE001 -- the plan never fails for it: the old pace stands
        return out
    return out
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S454_BILL_REGISTER part 5 (03-Oct-2026, S454 11): the items. item_check.py holds the rules; here they meet the Sarvam check and the owner.
#   * the Sarvam check judges a scan's item name by the supplier's learnt names first (_s454_learnt_line, in _s446_compare_one)
#   * sarvam_compare: after each compare the learner runs over the VERIFIED links; a name newly learnt sends that supplier's rows to be
#     compared again, so the Sarvam page's item figure counts by the learnt names. Nothing here changes stock, an order or a bill.
#   * GET /page/items?month=YYYY-MM -- the items check (11.1), the owner only, English, phone width.
# ==========================================================================================================================================
def _s454_ic():
    import item_check                                         # noqa: PLC0415 -- beside this file
    return item_check


def _s454_learnt_line(con, bill, nm, ml):
    try:
        return _s454_ic().learnt_line(con, bill, nm, ml)
    except Exception:                                          # noqa: BLE001 -- the check never fails for it: the old matching stands
        return None, 0.0


_s454p5_compare_before = sarvam_compare


def sarvam_compare(con):                                          # noqa: F811
    """S446's compare, then the learner (S454 11.2); a supplier with a name newly learnt has its rows compared again."""
    n = _s454p5_compare_before(con)
    try:
        new = _s454_ic().learn(con)
    except Exception:                                          # noqa: BLE001
        new = []
    if new:
        sups = sorted({x["supplier_norm"] for x in new})
        con.execute("DELETE FROM purchase_sarvam_check WHERE bill_id IN (SELECT id FROM purchase_bill WHERE supplier_norm IN (%s))" % ",".join("?" * len(sups)), sups)
        con.commit()
        n += _s454p5_compare_before(con)
    return n


S488_ITEMS_JS = """
async function s488strike(b){ const j = await post(P + '/api/items/strike', {supplier_norm: b.dataset.s, scan_norm: b.dataset.n, marg_item: b.dataset.m, do: b.dataset.do}); if (j) location.reload(); }
"""


def _s454_items_body(con, month, prefix):
    IC = _s454_ic()
    r = IC.items_check(con, month)
    months = [m[0] for m in con.execute("SELECT DISTINCT COALESCE(month, substr(bill_date,1,7)) m FROM purchase_bill WHERE m IS NOT NULL ORDER BY m DESC LIMIT 4")]
    nav = " · ".join(('<b>%s</b>' % _esc(_month_name(m))) if m == month else '<a href="%s/page/items?month=%s">%s</a>' % (prefix, m, _esc(_month_name(m)))
                     for m in months)
    withl = r["n"] - r["nolines"]
    head = ("%s: %d of %d bill%s add up (the lines' value comes to the bill within %s); %d do%s not." % (
        _month_name(month), r["adds"], withl, "" if withl == 1 else "s", _r(r["noise_p"]), r["differs"], "es" if r["differs"] == 1 else ""))
    if r["nolines"]:
        head += " %d bill%s ha%s no lines on the server." % (r["nolines"], "" if r["nolines"] == 1 else "s", "s" if r["nolines"] == 1 else "ve")
    rows = []
    for b in r["rows"]:
        ls = "".join("<tr><td>%s</td><td>%s%s</td><td>%s</td><td>%s%%</td><td>%s%%</td><td>%s</td><td>%s</td></tr>" % (
            _esc(l["item"]), _esc("%g" % float(l["qty"] or 0)), (" + %g free" % float(l["free"])) if l.get("free") else "",
            _esc("%.2f" % (float(l["rate_p"] or 0) / 100.0)), _esc("%g" % float(l["disc"] or 0)), _esc("%g" % float(l["tax"] or 0)),
            _r(l["value_p"]), _r(l["marg_net_p"]) if l.get("marg_net_p") is not None else "-") for l in b["lines"])
        rows.append('<div class="card" data-bill="%d"><div><b>%s</b> · bill %s · %s</div><div>Bill %s · its lines come to %s · <b>%s%s</b></div>'
                    '<details><summary>%d line%s</summary><div class="scroll"><table><tr><th>item</th><th>qty</th><th>rate</th><th>disc.</th><th>tax</th>'
                    '<th>value</th><th>Marg\'s net</th></tr>%s</table></div></details></div>'
                    % (b["id"], _esc(b["supplier"]), _esc(b["bill_no"]), _esc(b["date"]), _r(b["amount_p"]), _r(b["value_p"]),
                       "+" if b["diff_p"] > 0 else "-", _r(abs(b["diff_p"])), len(b["lines"]), "" if len(b["lines"]) == 1 else "s", ls))
    learnt = IC.learnt(con)
    _bt = '<button style="font-size:12px;padding:2px 10px;margin-left:6px" onclick="s488strike(this)" data-s="%s" data-n="%s" data-m="%s" data-do="%s">%s</button>'   # S488 (D.2)
    ln = "".join("<li>%s: “%s” = %s %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"]),
                                                  _bt % (_esc(x["supplier_norm"]), _esc(x.get("scan_norm")), _esc(x["marg_item"]), "strike", "Wrong"))
                 for x in learnt)
    gone = IC.struck(con)
    ln_struck = ("<details><summary>Struck: %d</summary><ul>%s</ul></details>" % (len(gone), "".join(
        "<li>%s: “%s” = %s %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"]),
                                          _bt % (_esc(x["supplier_norm"]), _esc(x["scan_norm"]), _esc(x["marg_item"]), "back", "Put back"))
        for x in gone)))
    return ('<h1>Items check — %s</h1><div class="muted">%s</div><div class="card" id="s454itemshead"><b>%s</b><div class="muted">Each line\'s value is '
            'quantity × rate, less the discount, plus the tax, as Marg holds them; free goods are not charged. "Marg\'s net" is Marg\'s own figure '
            'for the line: where it differs from the value, something reached the bill that the line\'s columns do not show.</div></div>%s'
            '<div class="card" id="s454learnt"><b>Item names learnt from the suppliers\' bills: %d</b><div class="muted">Learnt from bills whose scan '
            'agrees with Marg (verified), line by line where the quantity and the rate agree. They change no stock, order or bill; the Sarvam '
            'page judges a name by them first. Tap Wrong on a name that is not the same item; it stops being used at once and can be put back.'
            '</div><ul>%s</ul>%s</div>'
            % (_esc(_month_name(month)), nav, _esc(head), "".join(rows) or '<div class="card">Every bill of the month adds up.</div>', len(learnt), ln,
               ln_struck))


@bp.route("/page/items")
def page_s454_items():
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):                                      # the owner's page (S454 11.1)
        return _refuse("This page is for the doctor only.")
    con = _db()
    _ensure(con)
    newest =con.execute("SELECT MAX(COALESCE(month, substr(bill_date,1,7))) FROM purchase_bill").fetchone()[0] or dt.date.today().strftime("%Y-%m")
    month = str(request.args.get("month") or newest)[:7]
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    return _page("Items check — %s" % _month_name(month), _s454_items_body(con, month, request.script_root + _url_prefix), S488_ITEMS_JS)


@bp.route("/api/items/strike", methods=["POST"])
def api_s488_items_strike():
    """S488 (D.2): the doctor marks a learnt item name Wrong (do=strike) or puts a struck one back (do=back). JSON in, {ok, message} out."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):                                      # the owner's page (S454 11.1)
        return _refuse("This is for the doctor only.")
    b = request.get_json(silent=True) or {}
    sn, nm, mi, do = (str(b.get(k) or "").strip() for k in ("supplier_norm", "scan_norm", "marg_item", "do"))
    if not sn or not nm or do not in ("strike", "back") or (do == "back" and not mi):
        return jsonify(ok=False, error="malformed", message="supplier_norm, scan_norm and do = strike | back (marg_item to put back)"), 400
    con = _db()
    _ensure(con)
    IC = _s454_ic()
    ok, msg = IC.strike(con, sn, nm, _who(u), mi or None) if do == "strike" else IC.unstrike(con, sn, nm, mi)
    if ok:
        try:                                                   # as sarvam_compare does for a newly learnt name: judged again
            con.execute("DELETE FROM purchase_sarvam_check WHERE bill_id IN (SELECT id FROM purchase_bill WHERE supplier_norm=?)", (sn,))
        except sqlite3.Error:
            pass
        _audit(con, _who(u), "s488_item_name_" + do, nm[:60], dict(supplier_norm=sn, marg_item=mi))
        con.commit()
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S454 part 5 end -------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S726_PURCHASE_RULES (06-Nov-2026, Sanjeevni session 393; D839, D840, F-1140 - F-1143) -- the rules still live in scan_register.py.
#   * _rematch: before the pass, every AUTO link that fails the S726 auto-link rule (scan_register.autolink_ok) is undone -- the link row
#     deleted, purchase_bill.scan_bill_id cleared, audit 'auto_link_undone' kit S726 -- ONLY when the bill's month or the scan's month is a
#     counted month (scan_register.month_class; October 2026 on). A link whose two months are both parked or hidden (September) is never
#     touched. The pass then pairs the scans again under the rules.
#   * _match_s439: after the verified pair, a scan pairs with a Marg bill on its bill number AND its full date (within S439_DATE_DAYS, the
#     year included) AND its supplier, that number being the only one of the supplier's bills in the window (grade PROBABLE, rule "number +
#     date + supplier (S726 1)"), whatever the totals -- the total then gives the state (Amount differs -> reception's amount question ->
#     Amir). Only for a bill or scan of a counted month. A finalised month's AUTO link is never undone.
#   * If the S726 context cannot be set up, the pass runs exactly as before S726 (nothing new refused, asked or paired).
#   * _s454_autolink: scan_register.autolink_pick -- a candidate S726 refuses is kept on the scan (_s726_cand) and _why_s439 makes it the
#     scan's likely bill ("number_differs"), which is the existing one-tap "Yahi bill hai?" of porders.scan_work. No new reception screen.
#     A pair whose bill and scan are both of a parked month (September) keeps the old auto-link: nothing is raised for it. A paper dated
#     after Marg's last bill is not asked about (its own bill is probably not entered yet): it waits for Marg's entry, as before. A paper of
#     a counted month is never asked against a bill of a month not counted: it waits for its own bill ("no_bill_yet"). A likely bill
#     whose number agrees is worded as an amount question ("amount_differs").
#   * GET /page/check?month=YYYY-MM -- the owner's step view (scan_register.check_body), the checker only; it writes nothing.
# ==========================================================================================================================================
_S726_PASS = None                                                 # set only while a pass runs: the months the S726 rules may act on


def _s726_bill_months():
    """{scan id: bill_month} from the asset app (READ ONLY); {} when the column or the database is not there."""
    acon = _assets_con()
    if acon is None:
        return {}
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        if "bill_month" not in cols:
            return {}
        return {int(r[0]): str(r[1] or "") for r in acon.execute("SELECT id, bill_month FROM bills WHERE kind='Pharmacy'")}
    except sqlite3.Error:
        return {}
    finally:
        acon.close()


def _s726_counted(con, ym):
    return bool(re.match(r"^\d{4}-\d\d$", str(ym or ""))) and _s454_sr().month_class(con, ym) == "counted"


def _s726_undo_plan(con, cx=None, scans=None, bills=None, bm=None):
    """READ ONLY: the AUTO links the S726 rule undoes -> [dict(bill, scan, why, bill_month, scan_month, supplier, bill_no, amount_p, final)];
    None when the asset app's database is not reachable. A link whose bill month and scan month are both not counted is never listed.
    A finalised bill month (purchase_month.status = 'final'): final_undo=True only when that bill month is NOT counted and the SCAN's month
    is counted -- the owner, 06-Nov 17:20 ("yes"): such a link is undone, it frees a counted paper; every other finalised-month link has
    final=True -- KEPT, listed only so the proof flags it."""
    SR = _s454_sr()
    if scans is None:
        acon = _assets_con()
        if acon is None:
            return None
        try:
            scans = _scans(acon)
        finally:
            acon.close()
    if bills is None:
        bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    cx = cx if cx is not None else SR.Ctx(con)
    bm = _s726_bill_months() if bm is None else bm
    final = _s683_final_months(con)
    sby = {s["id"]: s for s in scans}
    bby = {b["id"]: b for b in bills}
    out = []
    try:
        auto = con.execute("SELECT bill_id, asset_bill_id, linked_at FROM purchase_scan_link WHERE grade='AUTO' ORDER BY bill_id").fetchall()
    except sqlite3.Error:
        auto = []
    for r in auto:
        b, s = bby.get(r[0]), sby.get(r[1])
        if b is None or s is None:
            continue                                               # the S439 pass itself drops a link whose bill or scan is gone
        bmon = str(b.get("month") or str(b.get("bill_date") or "")[:7])
        smon = SR.scan_month(s, bm.get(int(s["id"])))
        if not (_s726_counted(con, bmon) or _s726_counted(con, smon)):
            continue                                               # September-only (parked, cleared by the owner): never changed
        before = SR._date(s.get("bill_date")) or SR._date(str(r[2] or "")[:10])
        ok, why = SR.autolink_ok(cx, s, b, bills, undo=True, before=before)
        if not ok:
            out.append(dict(bill=int(r[0]), scan=int(r[1]), why=why, bill_month=bmon, scan_month=smon, supplier=supplier_key(b["supplier"]),
                            bill_no=b["bill_no"], amount_p=b["amount_p"],
                            final=(bmon in final and not (not _s726_counted(con, bmon) and _s726_counted(con, smon))),
                            final_undo=(bmon in final and not _s726_counted(con, bmon) and _s726_counted(con, smon))))
    return out


def _s726_setup(con):
    """The pass's S726 context: the first counted month, the asset app's bill months, the bills by supplier and by id."""
    v = _s454_sr().setting(con, "purchase.register_from", "2026-10-01")
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    by_sup = {}
    for b in bills:
        by_sup.setdefault(supplier_key(b["supplier"]), []).append(b)
    return dict(first=(v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10"), bm=_s726_bill_months(), by_sup=by_sup,
                byid={b["id"]: b for b in bills})


_rematch_before_s726 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S726: the wrong amount-only links of a counted month undone first (never in a finalised month), then the S454 / S439 pass with the
    S726 rules. If the S726 context cannot be set up, the pass runs exactly as before S726 (no undo, no new refusal, question or pair)."""
    global _S726_PASS
    undone = []
    try:
        _S726_PASS = _s726_setup(con)
    except Exception as _e_set:                                # noqa: BLE001 -- fail toward the old behaviour entirely
        _S726_PASS = None
        try:
            _audit(con, who, "s726_setup_error", "", dict(error=str(_e_set)[:200], kit="S726"))
        except Exception:                                      # noqa: BLE001
            pass
    if _S726_PASS is not None:
        try:
            plan = _s726_undo_plan(con)
            for x in plan or []:
                if x.get("final"):
                    continue                                       # a finalised month is never changed -- unless it holds a counted paper
                cur = con.execute("DELETE FROM purchase_scan_link WHERE bill_id=? AND asset_bill_id=? AND grade='AUTO'", (x["bill"], x["scan"]))
                if not cur.rowcount:
                    continue
                con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (x["bill"], x["scan"]))
                _audit(con, who, "auto_link_undone", x["bill"], dict(scan=x["scan"], why=x["why"], supplier=x["supplier"], bill_no=x["bill_no"],
                                                                      amount_p=x["amount_p"], bill_month=x["bill_month"], scan_month=x["scan_month"],
                                                                      kit="S726", **({"note": "owner 06-Nov 17:20: frees a counted paper from a "
                                                                                      "finalised month"} if x.get("final_undo") else {})))
                undone.append(x)
            if undone:
                con.commit()
        except Exception as _e_s726:                           # noqa: BLE001 -- the pass never fails for it
            try:
                _audit(con, who, "auto_link_undo_error", "", dict(error=str(_e_s726)[:200], kit="S726"))
            except Exception:                                  # noqa: BLE001
                pass
    try:
        out = _rematch_before_s726(con, who)
    finally:
        _S726_PASS = None
    if isinstance(out, dict):
        out["undone"] = len(undone)
    return out


def _s726_pass_counted(ym):
    p = _S726_PASS
    return bool(p) and bool(re.match(r"^\d{4}-\d\d$", str(ym or ""))) and ym >= p["first"]


def _s726_bill_ym(b):
    return str(b.get("month") or str(b.get("bill_date") or "")[:7])


_match_before_s726 = _match_s439


def _match_s439(s, b):                                            # noqa: F811
    """S726 (1): the verified pair first (S454); then the bill number, the FULL date (within S439_DATE_DAYS, the year included) and the
    supplier agree, and that number is the only one of this supplier's bills in that window -> rank 2, PROBABLE, whatever the totals (the
    total gives the state). Only inside a pass, for a bill or a scan of a counted month."""
    m = _match_before_s726(s, b)
    if m or _S726_PASS is None or b["id"] in s.get("_no", ()):
        return m
    SR = _s454_sr()
    if SR.billno_compat(s.get("bill_no"), b["bill_no"]) != "agree":
        return None
    sd, bd = SR._date(s.get("bill_date")), SR._date(b.get("bill_date"))
    if sd is None or bd is None or abs((sd - bd).days) > S439_DATE_DAYS:
        return None                                                # the day and month alone are not the date (Oct-2025 is not Oct-2026)
    if not (_s726_pass_counted(_s726_bill_ym(b)) or _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"]))))):
        return None
    same = [x for x in _S726_PASS["by_sup"].get(supplier_key(b["supplier"]), []) if SR.billno_compat(s.get("bill_no"), x["bill_no"]) == "agree"
            and SR._date(x.get("bill_date")) is not None and abs((SR._date(x.get("bill_date")) - sd).days) <= S439_DATE_DAYS]
    if len(same) != 1:
        return None                                                # two series of one supplier carry this number: a question, not a pair
    cx = _s454_cx()
    if SR.supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(s["id"])) != "agree":
        return None                                                # a number and a day alone, with no supplier, stay a question
    return 2, "PROBABLE", "number + date + supplier (S726 1)"


def _s454_autolink(con, who, scans, bills, taken, linked, dups):      # noqa: F811
    """S454 (5) as S726 (F-1141) rules it: a scan pairs by itself with the ONE unscanned bill of its supplier carrying its amount only
    when scan_register.autolink_ok agrees (grade AUTO, audit auto_link); a candidate it refuses is kept on the scan as _s726_cand for
    _why_s439 -- reception's "is this the same bill?" -- unless that bill is of a month not counted while the scan's is (it then waits for
    its own bill). A pair of a parked month only keeps the old rule; with no S726 context (a setup fault) every pair keeps the old rule."""
    SR = _s454_sr()
    cx = _s454_cx()
    scan_from = _scan_from_s409(con)
    dup_ok = set()
    try:
        dup_ok = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_state WHERE dup_ok IS NOT NULL")}
    except sqlite3.Error:
        pass
    made = []
    for s in sorted(scans, key=lambda x: x["id"]):
        if s["id"] in linked or s["id"] in dups or s["id"] in dup_ok:
            continue
        b, cand, why = SR.autolink_pick(cx, s, bills, taken, scan_from, refused=s.get("_no", ()))
        rule = "auto_link (S726 1): the only bill of this supplier with this amount, in its month"
        if cand is not None:
            if _S726_PASS is None:
                b, cand = cand, None                               # no S726 context: the old rule, nothing new refused or asked
                rule = "auto_link (S454 5): the only unscanned bill of this supplier with this amount"
            else:
                bc = _s726_pass_counted(_s726_bill_ym(cand))
                sc = _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"]))))
                if not (bc or sc):
                    b, cand = cand, None                           # a parked month only (September): the old rule stands, nothing is asked
                    rule = "auto_link (S454 5, a parked month): the only unscanned bill of this supplier with this amount"
                elif sc and not bc:
                    cand = None                                    # a counted paper against a parked bill: no question; it waits for its own bill
        if cand is not None:
            s["_s726_cand"], s["_s726_why"] = cand["id"], why
        if not b:
            continue
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                          (b["id"], s["id"], "AUTO", rule, now_iso()))
        if not cur.rowcount:
            continue
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (s["id"], b["id"]))
        _audit(con, who, "auto_link", b["id"], dict(scan=s["id"], supplier=supplier_key(b["supplier"]), bill_no=b["bill_no"], amount_p=b["amount_p"],
                                                     scan_no=s.get("bill_no"), scan_date=s.get("bill_date"), kit="S726"))
        taken[b["id"]] = s["id"]
        linked.add(s["id"])
        made.append((s["id"], b["id"], "AUTO", "auto_link"))
    return made


_why_before_s726 = _why_s439
_S726_ASK = ("number_differs", "amount_differs", "no_digits")


def _why_s439(s, bills, taken, last_date):                        # noqa: F811
    """S726: (1) a scan whose amount-only pair S726 refused -- with no likely bill by the older rules -- names that bill as its likely bill
    ("number_differs"): reception's one-tap "Yahi bill hai?"; not when the paper is dated after Marg's last bill (it waits for Marg's
    entry). (2) A scan of a counted month is never asked against a bill of a month not counted (the BLOCKER of the review): it waits for
    its own bill ("no_bill_yet"). (3) A likely bill whose NUMBER agrees is worded as an amount question ("amount_differs").
    With no S726 context (outside a pass, or a setup fault) the older rules' answer stands as it is."""
    why, detail, hint = _why_before_s726(s, bills, taken, last_date)
    if _S726_PASS is None:
        return why, detail, hint
    SR = _s454_sr()
    cand = s.get("_s726_cand")
    if cand and not (why in _S726_ASK and s.get("_likely")):
        last = _date_or_none_s439(last_date)
        fresh = s.get("_date") is not None and last is not None and s["_date"] > last
        b = _S726_PASS["byid"].get(cand)
        if not fresh and b is not None and b["id"] not in s.get("_no", ()):
            s["_likely"] = b["id"]
            lab = "%s bill %s (%s, %s)" % (supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))
            also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
            why, detail, hint = ("number_differs", "is this the same bill? — the scan's amount %s is %s's, but %s (S726: not paired by itself)%s"
                                 % (_r(s.get("amount_p")) if s.get("amount_p") is not None else "—", lab, s.get("_s726_why") or "the rule refused it",
                                    also), None if b["id"] in taken else b["id"])
    lk = s.get("_likely")
    b = _S726_PASS["byid"].get(lk) if lk else None
    if b is None or why not in _S726_ASK:
        return why, detail, hint
    if _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"])))) and not _s726_pass_counted(_s726_bill_ym(b)):
        s["_likely"] = None
        return ("no_bill_yet", "waits for its own bill in Marg — the bill it reads like (%s %s, %s) is of %s, a month not counted (S726)"
                % (supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _s726_bill_ym(b)), None)
    if why == "number_differs" and SR.billno_compat(s.get("bill_no"), b["bill_no"]) == "agree":
        also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
        return ("amount_differs", "amount differs — the scan reads %s; %s bill %s (%s, %s) carries the same number%s (S726)"
                % (_r(s.get("amount_p")) if s.get("amount_p") is not None else "no amount", supplier_key(b["supplier"]), b["bill_no"],
                   _human(b["bill_date"]), _r(b["amount_p"]), also), hint)
    return why, detail, hint


def _s726_check_page(con, u):
    """S726 (D840): the owner's step view -- reads only (no pass on GET)."""
    SR = _s454_sr()
    prefix = request.script_root + _url_prefix
    months = SR.months_with_bills(con, 12)
    want = str(request.args.get("month") or "")
    if want and not re.match(r"^\d{4}-\d{2}$", want):
        return "bad month", 400
    if want:
        month, r = want, None
    else:
        month, r = SR.check_month(con, months)
    if month not in months:
        months = sorted(set(months + [month]), reverse=True)
    body = SR.check_body(con, month, prefix, months, r)
    return _page("Purchase check — %s" % SR.month_name(month), _s454_bar(month) + body)


@bp.route("/page/check")
def page_s726_check():
    """S726 (D840): the owner's step view of a month's purchase bills (English, phone-first). The checker only; it writes nothing."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("This is for the doctor only.")
    return _s726_check_page(_db(), u)
# ---- S726 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S736 (06-Nov-2026, Sanjeevni session 396, kit S736_RECEPTION_BILL_LIST; D840, D847): the owner's taps on the step view --------------
@bp.route("/api/s736/decide", methods=["POST"])
def api_s736_decide():
    """Second look (the paper's figure stands / the scan misread), Accept (a scan after two tries), Undo -- scan_register.s736_decide.
    The checker who is the doctor only, as /page/check."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("This is for the doctor only.")
    con = _db()
    b = request.get_json(silent=True) or {}
    try:
        ok, msg = _s454_sr().s736_decide(con, _who(u), b)
    except Exception as e:                                     # noqa: BLE001
        return jsonify(ok=False, error="failed", message=str(e)[:160]), 500
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S736 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S738 (06-Nov-2026, Sanjeevni session 396, kit S738_AMIR_CORRECTIONS; D839, D840): a scan shown in place -----------------------------
@bp.route("/api/s738/scan/<int:sid>")
def api_s738_scan(sid):
    """One captured pharmacy scan, INLINE (the owner's folded viewer on /page/check; Amir's 'Kaagaz dekhiye'). The doctor: any scan. Amir
    (purchase.scan_file_users): only a scan on his correction list (scan_register.s738_scan_ok). Read only."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    doc = _is_doctor(u)
    if not doc and not _s446_files_ok(con, u):
        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")
    if not _s454_sr().s738_scan_ok(con, sid, doc, str((u or {}).get("user") or "")):
        return _refuse("Yeh kaagaz aapki list par nahi hai.")
    got = _s446_file_bytes(sid, ("Pharmacy", "Summary"))    # S753: the folded viewer and 'Open the scan in a new tab' open a summary too
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    data = got[1]
    mt = ("application/pdf" if data[:4] == b"%PDF" else "image/jpeg" if data[:3] == b"\xff\xd8\xff" else "image/png" if data[:8] == b"\x89PNG\r\n\x1a\n"
          else "application/octet-stream")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(got[0] or "scan"))[:80] or "scan"
    from flask import Response                                 # noqa: PLC0415
    return Response(data, mimetype=mt, headers={"Content-Disposition": 'inline; filename="%s"' % name, "Cache-Control": "no-store",
                                                "X-Content-Type-Options": "nosniff"})
# ---- S738 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S740 (07-Nov-2026, Sanjeevni session 399, kit S740_PURCHASE_RETURNS): the owner's own taps on row 8 "Returns" of /page/check -------------
def _s740_owner():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return None, None, err
    if not _is_doctor(u):
        return None, None, _refuse("Only the doctor records or answers a return here.")
    return u, _db(), None


@bp.route("/api/s740/items")
def api_s740_items():
    """For "Record a return": the items bought from one dealer (the last 365 days), each with its last rate and unit. The doctor only. Read only."""
    u, con, err = _s740_owner()
    if err:
        return err
    sup = str(request.args.get("supplier") or "")[:120]
    return jsonify(ok=True, items=_s454_sr().s740_choices(con, sup) if sup else [])


@bp.route("/api/s740/record", methods=["POST"])
def api_s740_record():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s740_record(con, str(u.get("user") or ""), str(b.get("supplier") or "")[:120], str(b.get("item") or "")[:200], b.get("qty"))
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="refused", message=msg), 400)


@bp.route("/api/s740/flag", methods=["POST"])
def api_s740_flag():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        lid = int(b.get("loss") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_flag_put(con, str(u.get("user") or ""), lid, bool(b.get("yes")))
    return jsonify(ok=True, message=msg) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/cnlook", methods=["POST"])
def api_s740_cnlook():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_cn_look(con, str(u.get("user") or ""), bid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/same", methods=["POST"])
def api_s740_same():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_same_put(con, str(u.get("user") or ""), bid, bool(b.get("same")))
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/withdraw", methods=["POST"])
def api_s740_withdraw():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        oid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_withdraw(con, str(u.get("user") or ""), oid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/undo", methods=["POST"])
def api_s740_undo():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_undo_answer(con, str(u.get("user") or ""), bid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)
# ---- S740 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    import sys as _sys_s439
    _sys_s439.exit(_cli_s439(_sys_s439.argv))



# ---- S749 (08-Nov-2026, Sanjeevni session 405, kit S749_ONE_SOURCE; D865, D866; F-1181, F-1182, F-1183): one source, one language ---------
#  * F-1181 -- a line Marg could not name is matched by what it carries before it is called missing: an UNDATED item line (Marg's item-wise
#    export clips a long bill number -- 'L2678591' for GPPL2678591, or prints none) of the same supplier whose net adds up to ONE bill of the
#    month to the rupee, and whose number (when read) ends the bill's, is that bill's line set (_line_sets); it leaves the undated list
#    (_undated_lines) and the bill leaves "no item lines". Exactly one bill for one set; nothing written.
#  * The one lock gate (_lock_gate): _month_summary's reasons, the three reports, the cross-check -- AND the register's open rows (differences
#    → Amir, to confirm, with reception, you & Shavez, returns pending: scan_register.s749_lock_reasons). Every page reads this one gate.
#  * Step 2 of the payment sheet runs by itself: when the supplier-wise statement has arrived and no check has been kept for that very export,
#    the server keeps one (purchase_pay_check, who 'server'); the sheet shows the server's verdict -- no "Check it now" tap.
#  * The audit page: the register's state word and whose/next per bill; its Correct / Wrong buttons off the doctor's view (one place to decide:
#    his step view); the month strip. The hub: counted months only, the register's words per month, the step view as the way in.
#  * The owner's doors for the step view's inline actions (the doctor only): Confirm / ask reception / undo (owner-confirmed suppliers);
#    Not this bill (unpair) / the pick list / Pick the right bill (pair) / undo -- scan_register.s749_*. A Marg correction is proved only by
#    Amir's export (F-1162); no door here settles one.
KIT_S749 = "S749_ONE_SOURCE"
_line_sets_before_s749 = _line_sets
_undated_lines_before_s749 = _undated_lines


def _s749_digits(s):
    return re.sub(r"\D", "", str(s or "")).lstrip("0")


def _s749_clipped(con, month):
    """F-1181: {(supplier_norm, bill_no of the BILL): the set} and {the matched undated line ids}. One bill for one set, the amount to the rupee,
    the clipped number (when read) ending the bill's digits (or the bill's ending it)."""
    bills = con.execute("SELECT b.id, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p FROM purchase_bill b WHERE b.month=? AND " + EFF_BILL, (month,)).fetchall()
    if not bills:
        return {}, set()
    base = _line_sets_before_s749(con, month)
    bdicts = [dict(supplier_norm=b[1], bill_no=b[2], bill_date=b[3]) for b in bills]
    stray = _stray_sets(bdicts, base)
    have = {(b[1], b[2]) for b in bills if _bill_lines(dict(supplier_norm=b[1], bill_no=b[2], bill_date=b[3]), base, stray) is not None}
    groups, singles = {}, {}
    for l in _undated_lines_before_s749(con, month):
        net = int(l["net_amount_p"] if l["net_amount_p"] is not None else (l["amount_p"] or 0))
        k = (l["supplier_norm"], l["bill_no"], l["source_md5"])
        g = groups.setdefault(k, dict(supplier_norm=l["supplier_norm"], bill_no=l["bill_no"], line_type=l["line_type"], md5=l["source_md5"], stamp="",
                                      net_p=0, gross_p=0, n=0, ids=[], bill_date=None))
        g["net_p"] += net
        g["gross_p"] += int(l["amount_p"] or 0)
        g["n"] += 1
        g["ids"].append(int(l["id"]))
        singles[k + (int(l["id"]),)] = dict(supplier_norm=l["supplier_norm"], bill_no=l["bill_no"], line_type=l["line_type"], md5=l["source_md5"], stamp="",
                                           net_p=net, gross_p=int(l["amount_p"] or 0), n=1, ids=[int(l["id"])], bill_date=None)
    if not groups:
        return {}, set()
    for k, g in list(groups.items()):                          # a set whose lines together name no bill may still hold ONE line that names one --
        if g["n"] > 1 and _s749_digits(g["bill_no"]):           # only when the line carries a number (an amount alone names nothing)
            for sk, sg in singles.items():
                if sk[:3] == k:
                    groups[sk] = sg
    try:
        stamps = {r[0]: r[1] for r in con.execute("SELECT md5, export_stamp FROM purchase_export")}
    except sqlite3.Error:
        stamps = {}
    pairs = {}                                                 # bill id -> [group keys that fit]
    gfit = {}                                                  # group key -> [bill ids that fit]
    for b in bills:
        if (b[1], b[2]) in have:
            continue                                           # the bill has its dated lines: never a clipped match
        bd = _s749_digits(b[2])
        for k, g in groups.items():
            if g["supplier_norm"] and g["supplier_norm"] != b[1]:
                continue
            if abs(int(g["net_p"]) - int(b[4] or 0)) > AGREE_P:
                continue
            ld = _s749_digits(g["bill_no"])
            if ld and bd and not (bd.endswith(ld) or ld.endswith(bd)):
                continue
            pairs.setdefault(int(b[0]), []).append(k)
            gfit.setdefault(k, []).append(int(b[0]))
    sets, used, sets_by_bill = {}, set(), set()
    for b in sorted(bills, key=lambda b: int(b[0])):
        ks = [k for k in (pairs.get(int(b[0])) or []) if not (set(groups[k]["ids"]) & used)]
        whole = [k for k in ks if len(k) == 3]
        ks = whole if whole else ks                            # the whole set first; a single line only when no set fits
        if len(ks) != 1 or len([x for x in (gfit.get(ks[0]) or []) if x not in {bid for bid in sets_by_bill}]) != 1:
            continue
        g = groups[ks[0]]
        sets_by_bill.add(int(b[0]))
        sets[(b[1], b[2])] = dict(supplier_norm=b[1], bill_no=b[2], bill_date=b[3], line_type=g["line_type"], md5=g["md5"], stamp=stamps.get(g["md5"], ""),
                                  net_p=g["net_p"], gross_p=g["gross_p"], n=g["n"], clipped=g["bill_no"])
        used.update(g["ids"])
    return sets, used


def _line_sets(con, month):                                   # noqa: F811 -- S749 (F-1181): the clipped item-wise sets join the month's
    sets = _line_sets_before_s749(con, month)
    try:
        extra, _used = _s749_clipped(con, month)
        for k, t in extra.items():
            sets.setdefault(k, t)
    except Exception as e:                                     # noqa: BLE001 -- the sets stand as they were
        import sys as _sys                                     # noqa: PLC0415
        print("purchase_app S749 clipped sets: %r" % (e,), file=_sys.stderr)
    return sets


def _undated_lines(con, month=None):                          # noqa: F811 -- S749 (F-1181): a matched line is no longer undated
    rows = _undated_lines_before_s749(con, month)
    if not month:
        return rows
    try:
        _sets, used = _s749_clipped(con, month)
        return [l for l in rows if int(l["id"]) not in used] if used else rows
    except Exception as e:                                     # noqa: BLE001
        import sys as _sys                                     # noqa: PLC0415
        print("purchase_app S749 undated: %r" % (e,), file=_sys.stderr)
        return rows


_lock_gate_before_s749 = _lock_gate


def _lock_gate(con, month, s):                                # noqa: F811 -- S749: the register's open rows hold the lock too
    can, reasons = _lock_gate_before_s749(con, month, s)
    try:
        more = _s454_sr().s749_lock_reasons(con, month)
    except Exception as e:                                     # noqa: BLE001 -- fails CLOSED
        more = ["the purchase check could not be read (%s)" % str(e)[:80]]
    reasons = list(reasons) + ["the purchase check holds: %s" % m for m in more]
    return (not reasons), reasons


def _s749_states(con, month):
    try:
        return _s454_sr().s749_audit_states(con, month)
    except Exception:                                          # noqa: BLE001
        return {}


def _s749_strip(con, month, page):
    """The month strip for the audit page ('month') and the payment sheet ('pay'); the step view and the register draw their own."""
    prefix = request.script_root + _url_prefix
    try:
        SR = _s454_sr()
        return SR.s749_month_strip(con, month, lambda m: "%s/page/%s/%s" % (prefix, page, m), "s749ms_" + page)
    except Exception:                                          # noqa: BLE001
        return ""


def _s749_hub_words(con, m):
    """The hub's 'Purchase check' cell for a month: the register's words (counted months), 'parked' or 'locked'."""
    SR = _s454_sr()
    if SR.month_class(con, m) != "counted":
        return '<span class="muted">parked</span>'
    st = _month_status(con, m)
    if st.get("status") == "final":
        return '<span class="ok">locked %s</span>' % _esc(_when_ist(st.get("finalised_at"))[:6])
    n = SR.s749_month_open(con, m)
    return '<a href="%s/page/check?month=%s">%s</a>' % (request.script_root + _url_prefix, m, _esc(n["words"] + (" · NEFT on hold" if n["open"] else " · clear")))


def _s749_hub_scan_card(con, prefix):
    """The hub's scan card: counted months only (October onward), the register's words, the step view as the way in."""
    SR = _s454_sr()
    lines = []
    for m in SR.s749_months(con):
        if SR.month_class(con, m) != "counted":
            continue
        try:
            n = SR.s749_month_open(con, m)
            lines.append('<div><b>%s</b>: %s · <a href="%s/page/check?month=%s">the purchase check</a> · <a href="%s/page/scans?month=%s">the full list</a></div>'
                         % (_esc(_month_name(m)), _esc(n["words"]), prefix, m, prefix, m))
        except Exception as e:                                 # noqa: BLE001
            lines.append('<div><b>%s</b>: <span class="warn">not read (%s)</span></div>' % (_esc(_month_name(m)), _esc(str(e)[:60])))
    return ('<div class="card"><h2>Purchase check</h2><div class="muted">Counted months only (from %s). Every page reads the one list.</div>%s</div>'
            % (_esc(_month_name(SR.setting(con, "purchase.register_from", "2026-10-01")[:7])), "".join(lines) or '<div class="muted">No counted month yet.</div>'))


def _s749_auto_verify(con, month, s):
    """Step 2 run by the server: the cross-check against the newest supplier-wise statement, kept once per statement export. -> the verdict dict
    (ok, problems, notes, export, at, who) as the sheet shows it; None when no statement has arrived."""
    _pay_ensure(con)
    v = _verify_statement(con, month, s)
    exp = (v.get("export") or {}).get("md5") if v.get("export") else None
    if not exp:
        return None
    last = _pay_last_check(con, month)
    if (s.get("status") or {}).get("status") == "final":       # a final month keeps its last run; nothing is written for a late re-export
        return dict(v, at=(last or {}).get("at"), who=(last or {}).get("who") or "server")
    try:
        d = json.loads((last or {}).get("detail") or "{}")
    except ValueError:
        d = {}
    if not last or d.get("export") != exp or bool(last["ok"]) != bool(v["ok"]):
        con.execute("INSERT INTO purchase_pay_check (month, at, who, ok, detail) VALUES (?,?,?,?,?)",
                    (month, now_iso(), "server", 1 if v["ok"] else 0,
                     json.dumps({"problems": v["problems"], "notes": v["notes"], "total_p": v["total_p"], "printed_p": v["printed_p"], "export": exp,
                                 "kit": KIT_S749}, ensure_ascii=False)))
        _audit(con, "server", "pay_verify", month, {"ok": v["ok"], "problems": len(v["problems"]), "export": exp, "kit": KIT_S749})
        con.commit()
        last = _pay_last_check(con, month)
    return dict(v, at=(last or {}).get("at"), who=(last or {}).get("who") or "server")


def _s749_verify_card(con, month, s):
    v = _s749_auto_verify(con, month, s)
    if v is None:
        body = ('<div class="muted">Waiting for Marg\'s supplier-wise statement of this month. The moment it arrives the server holds the sheet '
                'against it -- every bill it carries, the per-bill amounts and its own printed grand total -- and says here whether they agree.</div>')
    elif v["ok"]:
        body = ('<div class="ok"><b>Verified against Marg\'s supplier-wise statement</b> — %s agrees, %s.</div>%s'
                '<div class="muted">Run by the server %s, when the statement arrived.</div>'
                % (_r(v["total_p"]), _plural(v["n_bills"], "bill"), "".join('<div class="muted">%s</div>' % _esc(x) for x in v["notes"]),
                   _esc(_hhmm_ist_full(v["at"])) if v.get("at") else "just now"))
    else:
        body = ('<div class="bad"><b>Held against the statement — these do not line up</b></div><ul>%s</ul>%s'
                '<div class="muted">Run by the server %s. A fresh export from Marg re-runs it by itself.</div>'
                % ("".join('<li>%s</li>' % _esc(x) for x in v["problems"]), "".join('<div class="muted">%s</div>' % _esc(x) for x in v["notes"]),
                   _esc(_hhmm_ist_full(v["at"])) if v.get("at") else "just now"))
    return ('<div class="card"><h2>2 &middot; Verified against the supplier-wise statement</h2>'
            '<div class="muted">Run by the server, not by a tap: Marg\'s own supplier-wise export of this month is read and the sheet is held '
            'against it three ways.</div>%s</div>' % body)


def _s749_lock_card(con, month, s, final, gate):
    if final:
        txt = 'This month is <b>final</b>: the figures are locked until it is reopened.'
    elif gate[0]:
        txt = ('<span class="ok">Ready to lock.</span> Finalise the month on <a href="%s/page/month/%s">its audit page</a>, and these figures lock.'
               % (request.script_root + _url_prefix, month))
    else:
        txt = ('Waits for: <ul>%s</ul><div class="muted">The same open items as your <a href="%s/page/check?month=%s">purchase check</a>, row 8.</div>'
               % ("".join("<li>%s</li>" % _esc(x) for x in gate[1]), request.script_root + _url_prefix, month))
    return ('<div class="card"><h2>3 &middot; Lock it</h2><div>%s</div><div class="muted">The NEFT total is what goes into the bank advice file and its '
            'covering letter, and they are built from this sheet and from nothing else.</div></div>' % txt)


def _s749_owner():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return None, None, err
    if not _is_doctor(u):
        return None, None, _refuse("This is for the doctor only.")
    return u, _db(), None


def _s749_int(b, k):
    try:
        return int(b.get(k) or 0)
    except (TypeError, ValueError):
        return 0


@bp.route("/api/s749/confirm", methods=["POST"])
def api_s749_confirm():
    """Confirm (yours) on the step view: {bill, decision: confirm | scan | undo} -- scan_register.s749_confirm_put. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s749_confirm_put(con, _who(u), _s749_int(b, "bill"), str(b.get("decision") or ""))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


@bp.route("/api/s749/unpair", methods=["POST"])
def api_s749_unpair():
    """Not this bill: {scan, bill} -- the pair undone, audited; the pick list follows. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s749_unpair(con, _who(u), _s749_int(b, "scan"), _s749_int(b, "bill"))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


@bp.route("/api/s749/pick")
def api_s749_pick():
    """The bills the owner may pair one scan with. The doctor only. Read only."""
    u, con, err = _s749_owner()
    if err:
        return err
    try:
        sid = int(request.args.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    opts = _s454_sr().s749_pick_options(con, sid) if sid else []
    return jsonify(ok=True, options=[dict(o, amount=_r(o["amount_p"])[1:]) for o in opts])


@bp.route("/api/s749/pair", methods=["POST"])
def api_s749_pair():
    """Pick the right bill: {scan, bill} -- the owner's own pair, audited, Undo. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s749_pair(con, _who(u), _s749_int(b, "scan"), _s749_int(b, "bill"))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


@bp.route("/api/s749/undo", methods=["POST"])
def api_s749_undo():
    """Undo of an unpair or a pair: {act}. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s749_undo_act(con, _who(u), _s749_int(b, "act"))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S749 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S750 (08-Nov-2026, Sanjeevni session 406, kit S750_MONTH_END; D849, F-1175): the month end on the purchase pages -----------------------
#  (1) THE LOCK GATE waits for the dealers' summaries too (through scan_register.s749_lock_reasons, wrapped by S750) -- D849: the month locks when Marg = the papers
#      and Marg = the dealers' summaries, and Marg's month-end re-export after the last correction is in (the three reports, the cross-check).
#  (2) THE PAYMENT SHEET: a 'Dealer's summary' column (the figure · agrees / differs / awaited / none given / accepted / carried); Payable
#      follows the dealer's figure when the line agrees or the owner accepted it; an amount the owner carried shows under next month's
#      Carried in when nothing was typed there. The owner's typed values are never rewritten (purchase_pay_line untouched).
#  (3) THE DEALER LEDGER /page/ledger (the dealers) and /page/ledger/<dealer>: the financial year first (April–March: purchases, returns, paid,
#      the balance; items × quantity), then one month per fold (newest open) -- the bills with their item lines folded, the returns, the
#      dealer's summary and its verdict, the payments (the NEFT with the bank's reference, the cheques, what was typed as paid) and the
#      balance; item quantities for the month. Read only; printable (?print=1 opens every fold). For the doctor and the senders
#      (_s452_may_advice), as the payment pages are. Reached from row 7, the sheet and the hub.
#  (4) THE DOORS /api/s750/answer, /api/s750/undo, /api/s750/dealer_of -- the doctor only (scan_register.s750_*).
#  Nothing here writes a Marg figure, a pay line or a message. Nothing here prints a phone number, an account number or a key.
KIT_S750 = "S750_MONTH_END"
_pay_rows_before_s750 = _pay_rows
_pay_sheet_table_before_s750 = _pay_sheet_table
_s749_hub_scan_card_before_s750 = _s749_hub_scan_card
# The lock gate needs no new wrapper: S749's _lock_gate reads scan_register.s749_lock_reasons, and S750 wraps THAT to carry the dealers'
# holds -- one source, one line each ('the purchase check holds: N dealer summaries awaited ...').


def _s750_sheet_info(con, month):
    try:
        return _s454_sr().s750_sheet(con, month) or {}
    except Exception as e:                                     # noqa: BLE001 -- the sheet stands as it was; the column says so
        return {"__error__": str(e)[:80]}


def _pay_rows(con, month):                                    # noqa: F811 -- S750: the dealer's figure on the sheet
    s, groups = _pay_rows_before_s750(con, month)
    info = _s750_sheet_info(con, month)
    err = info.pop("__error__", None)
    for g in groups:
        i = info.get(g["norm"])
        g["s750"] = dict(i) if i else (dict(state="", words="not read", figure_p=None, accepted_p=None, carried_out_p=0, carried_in_p=0, payable_p=None, holds=False, error=err)
                                       if err else None)
        if not i:
            continue
        if g.get("carry_p") is None and i.get("carried_in_p"):
            g["carry_p"] = int(i["carried_in_p"])
            g["s750_carry_auto"] = True
            g["payable_p"] = int(g.get("payable_p") or 0) + int(i["carried_in_p"])
        if i.get("payable_p") is not None:
            g["payable_p"] = int(i["payable_p"]) + int(g.get("carry_p") or 0)
    seen = {g["norm"] for g in groups}
    for k, i in info.items():                                 # a dealer with no bill this month but an amount carried in from the last
        if k in seen or not i.get("carried_in_p"):
            continue
        name = con.execute("SELECT supplier FROM purchase_bill WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (k,)).fetchone()
        bank = _vendor_bank(con).get(k) or {"route": "CHEQUE", "why": "no account on this server"}
        groups.append({"norm": k, "name": str(name[0]) if name else k, "bills": [], "total_p": 0, "f1_p": 0, "f2_p": 0, "route": bank["route"], "why": bank["why"],
                       "flags": 0, "carry_p": int(i["carried_in_p"]), "paid_p": None, "note": "", "by": "", "at": "", "payable_p": int(i["carried_in_p"]),
                       "s750": dict(i), "s750_carry_auto": True})
    return s, groups


def _s750_chip(i):
    if not i:
        return ""
    w = str(i.get("words") or "")
    cls = {"agrees": "ok", "accepted": "ok", "your Confirm": "ok", "none given": "", "carried": "warn"}.get(w, "warn" if w else "")
    return ' <span class="chip %s">%s</span>' % (cls, _esc(w)) if w else ""


def _pay_sheet_table(groups, prefix, month, editable):        # noqa: F811 -- S750: + the dealer's summary column
    rows = []
    for g in groups:
        auto = bool(g.get("s750_carry_auto"))
        carry = ("" if g["carry_p"] is None or auto else "%d" % int(round(g["carry_p"] / 100.0)))
        paid = ("" if g["paid_p"] is None else "%d" % int(round(g["paid_p"] / 100.0)))
        inp = ('<input class="pin" id="cf_%s" value="%s" placeholder="%s" '
               'onchange="payline(\'%s\',this)" data-v="%s">'
               % (_esc(g["norm"]), carry, ("%d" % int(round(g["carry_p"] / 100.0))) if auto else "", _esc(g["norm"]), _esc(g["norm"]))) if editable else (
               _r(g["carry_p"]) if g["carry_p"] is not None else "—")
        if auto:
            inp += '<div class="muted" style="font-size:11px">carried by you (row 7) · not typed; it leaves with your Undo</div>'
        pin = ('<input class="pin" id="pd_%s" value="%s" inputmode="numeric" '
               'onchange="payline(\'%s\',this)">' % (_esc(g["norm"]), paid, _esc(g["norm"]))
               ) if editable else (_r(g["paid_p"]) if g["paid_p"] is not None else "—")
        i = g.get("s750") or {}
        fig = i.get("accepted_p") if i.get("accepted_p") is not None else i.get("figure_p")
        summ = ((_r(fig) if fig is not None else "") + _s750_chip(i)) if i else '<span class="muted">—</span>'
        rows.append('<tr><td>%s%s</td><td class="n">%s</td><td class="n">%s</td>'
                    '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n" id="py_%s">%s</td>'
                    '<td class="n">%s</td></tr>'
                    % (_esc(g["name"]),
                       ' <span class="chip warn">CHEQUE</span>' if g["route"] != "NEFT" else "",
                       _r(g["f1_p"]), _r(g["f2_p"]), _r(g["total_p"]), summ, inp,
                       _esc(g["norm"]), _r(g["payable_p"]), pin))
        if editable and g.get("at"):                           # S604 (F-954): what was saved, by whom (never on the printed pack)
            rows.append('<tr class="s604saved"><td colspan="8" class="muted" style="padding-top:0">%s</td></tr>'
                        % _esc(_s604_saved_words(g)))
    tot_f1 = sum(g["f1_p"] for g in groups)
    tot_f2 = sum(g["f2_p"] for g in groups)
    tot = sum(g["total_p"] for g in groups)
    tot_c = sum(g["carry_p"] or 0 for g in groups)
    tot_pay = sum(g["payable_p"] for g in groups)
    tot_paid = sum(g["paid_p"] or 0 for g in groups)
    tot_s = sum((g.get("s750") or {}).get("accepted_p") if (g.get("s750") or {}).get("accepted_p") is not None else ((g.get("s750") or {}).get("figure_p") or 0) for g in groups)
    rows.append('<tr><th>TOTAL</th><th class="n">%s</th><th class="n">%s</th><th class="n">%s</th><th class="n">%s</th>'
                '<th class="n">%s</th><th class="n">%s</th><th class="n">%s</th></tr>'
                % (_r(tot_f1), _r(tot_f2), _r(tot), _r(tot_s) if tot_s else "—", _r(tot_c) if tot_c else "—",
                   _r(tot_pay), _r(tot_paid) if tot_paid else "—"))
    return ('<div class="scroll"><table class="sheet"><tr><th>Vendor</th>'
            '<th class="n">1st–15th</th><th class="n">16th–end</th>'
            '<th class="n">%s</th><th class="n">Dealer\'s summary</th><th class="n">Carried in</th><th class="n">Payable</th>'
            '<th class="n">Paid</th></tr>%s</table></div>'
            '<div class="muted">Dealer\'s summary: the dealer\'s own month figure (row 7 of <a href="%s/page/check?month=%s">the purchase check</a>). Payable follows it when '
            'the line agrees or you accepted it; a carried amount shows under next month\'s Carried in. <a href="%s/page/ledger">The dealer ledgers</a>.</div>'
            % (_esc(_month_name(month)), "".join(rows), _esc(prefix), _esc(month), _esc(prefix)))


def _s749_hub_scan_card(con, prefix):                         # noqa: F811 -- S750: the way to the ledgers
    h = _s749_hub_scan_card_before_s750(con, prefix)
    add = '<div style="margin-top:6px"><a href="%s/page/ledger">The dealer ledgers</a> — every dealer\'s bills, returns, summaries, payments and item quantities.</div>' % _esc(prefix)
    i = h.rfind("</div>")
    return (h[:i] + add + h[i:]) if i > 0 else h + add


# ------------------------------------------------------------------ the dealer ledger (read only)
def _s750_q(key):
    from urllib.parse import quote                            # noqa: PLC0415
    return quote(str(key or ""), safe="")


def _s750_fy(ym):
    """'2026-04' .. '2027-03' -> 'FY 2026-27'."""
    try:
        y, m = int(ym[:4]), int(ym[5:7])
    except (TypeError, ValueError):
        return ""
    y0 = y if m >= 4 else y - 1
    return "FY %d-%02d" % (y0, (y0 + 1) % 100)


def _s750_qty(ln):
    try:
        q = float(ln.get("qty") or 0) + float(ln.get("free") or 0)
    except (TypeError, ValueError):
        q = 0.0
    return -q if str(ln.get("direction") or "").upper() == "RETURN" else q


def _s750_fmt_q(q):
    return ("%d" % int(round(q))) if abs(q - round(q)) < 1e-6 else ("%.1f" % q)


def s750_ledger(con, key):
    """The one dealer's ledger -> dict(key, name, months=[month dicts newest first], fys={FY: dict}) -- bills with their item lines, the returns,
    the summary's verdict (counted months), the payments and the balance per month; item quantities per month and per financial year."""
    SR = _s454_sr()
    IC = _s454_ic()
    name_r = con.execute("SELECT supplier FROM purchase_bill WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
    name = str(name_r[0]) if name_r else key
    months = [str(r[0]) for r in con.execute("SELECT DISTINCT b.month FROM purchase_bill b WHERE b.supplier_norm=? AND %s ORDER BY b.month DESC" % EFF_BILL, (key,))]
    bank = (_vendor_bank(con).get(key) or {}).get("route") or "CHEQUE"
    out = dict(key=key, name=name, route=bank, months=[], fys={})
    for m in months:
        bills = [dict(r) for r in con.execute("SELECT b.* FROM purchase_bill b WHERE b.supplier_norm=? AND b.month=? AND %s ORDER BY b.bill_date, b.bill_no" % EFF_BILL, (key, m))]
        items_m, bl = {}, []
        for b in bills:
            try:
                lines = IC.marg_lines(con, b)
            except Exception:                                 # noqa: BLE001
                lines = []
            ln2 = []
            neg = int(b.get("amount_p") or 0) < 0             # Marg prints a purchase return's lines as a PURCHASE and puts the minus on the bill (F-956 B)
            for ln in lines:
                q = _s750_qty(ln)
                nm = str(ln.get("item") or "").strip() or "(unnamed)"
                try:
                    val = int(ln.get("net_amount_p") if ln.get("net_amount_p") is not None else (ln.get("amount_p") or 0))
                except (TypeError, ValueError):
                    val = 0
                if str(ln.get("direction") or "").upper() == "RETURN":
                    val = -abs(val)
                elif neg:
                    q, val = -abs(q), -abs(val)
                it = items_m.setdefault(nm, dict(item=nm, qty=0.0, amount_p=0, packing=str(ln.get("packing") or "")))
                it["qty"] += q
                it["amount_p"] += val
                ln2.append(dict(item=nm, qty=q, rate_p=ln.get("rate_p"), amount_p=val, batch=ln.get("batch"), expiry=ln.get("expiry"), packing=ln.get("packing")))
            bl.append(dict(id=int(b["id"]), bill_no=str(b.get("bill_no") or ""), date=str(b.get("bill_date") or ""), amount_p=int(b.get("amount_p") or 0),
                           lines=ln2, scan=b.get("scan_bill_id")))
        purchases_p = sum(x["amount_p"] for x in bl if x["amount_p"] > 0)
        returns_p = -sum(x["amount_p"] for x in bl if x["amount_p"] < 0)
        summ = None
        if SR.month_class(con, m) == "counted":
            try:
                for d in SR.s750_dealers(con, m):
                    if d["key"] == key:
                        summ = dict(state=d["state"], words=d["words"], why=d["why"], figure_p=(d.get("summary") or {}).get("figure_p"),
                                    scan=(d.get("summary") or {}).get("id"), answer=d.get("answer"))
            except Exception as e:                            # noqa: BLE001
                summ = dict(state="?", words="not read (%s)" % str(e)[:60], why=[], figure_p=None, scan=None, answer=None)
        try:
            pl = con.execute("SELECT carry_fwd_p, paid_p, note, updated_by, updated_at FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (m, key)).fetchone()
        except sqlite3.Error:
            pl = None
        typed_paid = int(pl["paid_p"]) if pl and pl["paid_p"] is not None else None
        carry_in = int(pl["carry_fwd_p"]) if pl and pl["carry_fwd_p"] is not None else None
        info = {}
        try:
            info = _s750_sheet_info(con, m).get(key) or {}
        except Exception:                                     # noqa: BLE001
            info = {}
        if carry_in is None and info.get("carried_in_p"):
            carry_in = int(info["carried_in_p"])
        payable = (int(info["payable_p"]) if info.get("payable_p") is not None else purchases_p - returns_p) + (carry_in or 0)
        cheques = []
        try:
            for r in con.execute("SELECT cheque_no, cheque_date, amount_p, bank, handed_at, voided_at FROM purchase_cheque WHERE month=? AND vendor_norm=? ORDER BY id", (m, key)):
                cheques.append(dict(no=str(r[0] or ""), date=str(r[1] or ""), amount_p=int(r[2] or 0), bank=str(r[3] or ""), handed_at=r[4], voided=bool(r[5])))
        except sqlite3.Error:
            pass
        neft = None
        if bank == "NEFT":
            try:                                              # READ ONLY: the event row itself (supplier_msg.state() writes -- never from a page)
                ev = con.execute("SELECT utr, sms_date, created_at, amount_p FROM purchase_neft_event WHERE month=? AND kind<>'rejected' ORDER BY id DESC LIMIT 1", (m,)).fetchone()
                if ev:
                    neft = dict(utr=str(ev[0] or ""), date=str(ev[1] or ev[2] or "")[:10], amount_p=ev[3])
            except sqlite3.Error:
                neft = None
        paid_p = typed_paid if typed_paid is not None else (payable if (neft and bank == "NEFT") else sum(c["amount_p"] for c in cheques if not c["voided"]))
        settled = False                                       # S755 (F-1189): a month before the register began was settled outside the system
        if typed_paid is None and m < str(_s454_sr().setting(con, "purchase.register_from", "2026-10-01"))[:7]:
            paid_p, settled = payable, True
        final = str((_month_status(con, m) or {}).get("status") or "") == "final"
        out["months"].append(dict(month=m, name=_month_name(m), bills=bl, purchases_p=purchases_p, returns_p=returns_p, summary=summ, carry_in_p=carry_in or 0,
                                  payable_p=payable, paid_p=paid_p, balance_p=payable - (paid_p or 0), cheques=cheques, neft=neft, typed_paid=typed_paid, final=final, settled=settled,
                                  items=sorted(items_m.values(), key=lambda x: (-x["qty"], x["item"])), n_lines=sum(len(x["lines"]) for x in bl)))
        fy = out["fys"].setdefault(_s750_fy(m), dict(fy=_s750_fy(m), months=0, purchases_p=0, returns_p=0, paid_p=0, payable_p=0, items={}, settled=0))
        fy["months"] += 1
        fy["settled"] += 1 if settled else 0                  # S755 (F-1189)
        fy["purchases_p"] += purchases_p
        fy["returns_p"] += returns_p
        fy["paid_p"] += paid_p or 0
        fy["payable_p"] += payable
        for it in items_m.values():
            t = fy["items"].setdefault(it["item"], dict(item=it["item"], qty=0.0, amount_p=0, packing=it["packing"]))
            t["qty"] += it["qty"]
            t["amount_p"] += it["amount_p"]
    for fy in out["fys"].values():
        fy["items"] = sorted(fy["items"].values(), key=lambda x: (-x["qty"], x["item"]))
        fy["balance_p"] = fy["payable_p"] - fy["paid_p"]
    return out


S750_LEDGER_CSS = """
#s750l{max-width:860px}
#s750l .fy{background:#f4f6f9;border:1px solid #dde3ec;border-radius:10px;padding:10px 12px;margin:8px 0}
#s750l .kv{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:15px}
#s750l .kv b{font-size:17px}
#s750l details.m{border-top:1px solid #e6e2dc;padding:4px 0}
#s750l details.m>summary{display:flex;justify-content:space-between;gap:10px;align-items:center;min-height:46px;cursor:pointer;list-style:none;font-size:17px}
#s750l details.m>summary::-webkit-details-marker{display:none}
#s750l details.m>summary .n{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:700}
#s750l details.b{margin:2px 0 2px 8px;font-size:14px}
#s750l details.b>summary{cursor:pointer;list-style:none;display:flex;gap:10px;justify-content:space-between;min-height:34px;align-items:center}
#s750l details.b>summary::-webkit-details-marker{display:none}
#s750l table.it{border-collapse:collapse;font-size:13px;margin:4px 0 6px 10px;font-variant-numeric:tabular-nums}
#s750l table.it th,#s750l table.it td{border-bottom:1px solid #eee;padding:2px 8px;text-align:left}
#s750l table.it td.n,#s750l table.it th.n{text-align:right;white-space:nowrap}
#s750l .pay{font-size:14px;color:#444;margin:4px 0}
#s750l .bal{font-weight:700}
#s750l .ok{color:#1f4d25}#s750l .bad{color:#8c1d18}#s750l .hold{color:#7a4a00}
#s750l .mut{color:#666;font-size:13px}
@media print{#s750l details{display:block}#s750l details>summary{list-style:none}#s750l .noprint{display:none}}
"""


def _s750_items_table(items, cap=60):
    if not items:
        return '<div class="mut">no item lines</div>'
    rows = "".join('<tr><td>%s</td><td class="mut">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                   % (_esc(it["item"]), _esc(it.get("packing") or ""), _esc(_s750_fmt_q(it["qty"])), _r(it["amount_p"])) for it in items[:cap])
    more = ('<tr><td colspan="4" class="mut">… %d more items</td></tr>' % (len(items) - cap)) if len(items) > cap else ""
    return '<table class="it"><tr><th>Item</th><th>Pack</th><th class="n">Qty (incl. free)</th><th class="n">Net</th></tr>%s%s</table>' % (rows, more)


def _s750_month_html(con, L, mo, prefix, open_, print_):
    bills_h = []
    for b in mo["bills"]:
        ret = b["amount_p"] < 0
        lines = "".join('<tr><td>%s</td><td class="mut">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                        % (_esc(ln["item"]), _esc(ln.get("batch") or ""), _esc(_s750_fmt_q(ln["qty"])), _r(ln["rate_p"]) if ln.get("rate_p") is not None else "—", _r(ln["amount_p"]))
                        for ln in b["lines"])
        tab = ('<table class="it"><tr><th>Item</th><th>Batch</th><th class="n">Qty</th><th class="n">Rate</th><th class="n">Net</th></tr>%s</table>' % lines) if lines else '<div class="mut" style="margin-left:10px">no item lines in Marg\'s item-wise export for this bill</div>'
        scan = (' · <a href="%s/api/s738/scan/%d" target="_blank" rel="noopener">scan</a>' % (_esc(prefix), int(b["scan"]))) if b.get("scan") else ""
        bills_h.append('<details class="b"%s><summary><span>%s%s · <b>%s</b>%s · %d item%s</span><span class="n%s">%s</span></summary>%s</details>'
                       % (" open" if print_ else "", "Purchase return " if ret else "", _esc(_human(b["date"])), _esc(b["bill_no"]), scan, len(b["lines"]), "" if len(b["lines"]) == 1 else "s",
                          " bad" if ret else "", _r(b["amount_p"]), tab))
    s = mo.get("summary")
    if s is None:
        summ = '<div class="pay">Dealer\'s summary: <span class="mut">not counted for this month (before %s)</span></div>' % _esc(_month_name(_s454_sr().setting(con, "purchase.register_from", "2026-10-01")[:7]))
    else:
        cls = {"agrees": "ok", "differs": "bad", "awaited": "hold", "unreadable": "hold", "unknown": "hold"}.get(s["state"], "")
        why = ("<div class='mut'>" + "<br>".join(_esc(w) for w in (s.get("why") or [])[:5]) + "</div>") if s.get("why") else ""
        summ = '<div class="pay">Dealer\'s summary: <span class="%s">%s</span>%s%s</div>' % (cls, _esc(s["words"]), (' · <a href="%s/api/s738/scan/%d" target="_blank" rel="noopener">the paper</a>' % (_esc(prefix), int(s["scan"]))) if s.get("scan") else "", why)
    pays = []
    if mo.get("neft"):
        pays.append("NEFT %s%s" % (_esc(_human(mo["neft"]["date"])) if mo["neft"].get("date") else "", (" · bank ref %s" % _esc(mo["neft"]["utr"])) if mo["neft"].get("utr") else ""))
    for c in mo["cheques"]:
        pays.append("cheque %s %s %s%s" % (_esc(c["no"]), _esc(_human(c["date"])) if c["date"] else "", _r(c["amount_p"]), " (void)" if c["voided"] else ""))
    if mo.get("typed_paid") is not None:
        pays.append("paid as typed on the sheet: %s" % _r(mo["typed_paid"]))
    if mo.get("settled"):                                   # S755 (F-1189)
        pays.append("settled outside the system (before the register began) · paid = payable")
    pay_h = '<div class="pay">Paid: %s</div>' % (" · ".join(pays) if pays else '<span class="mut">nothing recorded yet</span>')
    carry = (' · carried in %s' % _r(mo["carry_in_p"])) if mo["carry_in_p"] else ""
    head = ('<summary><span>%s%s <span class="mut">· %d bill%s%s</span></span><span class="n">%s</span></summary>'
            % (_esc(mo["name"]), " 🔒" if mo["final"] else "", len([b for b in mo["bills"] if b["amount_p"] > 0]), "" if len(mo["bills"]) == 1 else "s",
               (" · %d return%s" % (len([b for b in mo["bills"] if b["amount_p"] < 0]), "" if len([b for b in mo["bills"] if b["amount_p"] < 0]) == 1 else "s")) if mo["returns_p"] else "",
               _r(mo["payable_p"])))
    recon = ('<div class="pay"><b>Reconciliation:</b> purchases %s − returns %s%s = payable <b>%s</b> · paid %s · <span class="bal %s">balance %s</span></div>'
             % (_r(mo["purchases_p"]), _r(mo["returns_p"]), carry, _r(mo["payable_p"]), _r(mo["paid_p"]) if mo["paid_p"] is not None else "—",
                "ok" if not mo["balance_p"] else "bad", _r(mo["balance_p"])))
    items = ('<details class="b"%s><summary><span>Items this month · %d</span><span class="n">%s</span></summary>%s</details>'
             % (" open" if print_ else "", len(mo["items"]), _esc(_s750_fmt_q(sum(i["qty"] for i in mo["items"]))) + " units", _s750_items_table(mo["items"])))
    return '<details class="m"%s>%s%s%s%s<div style="margin:4px 0 2px"><b>Bills</b></div>%s%s</details>' % (" open" if (open_ or print_) else "", head, recon, summ, pay_h, "".join(bills_h), items)


@bp.route("/page/ledger")
def page_s750_ledgers():
    """The dealers: one line each -- this financial year's purchases, the last month's state, the way to the ledger. Read only."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    if not _s452_may_advice(con, u):
        return _refuse("The dealer ledgers are for the doctor and the senders.")
    prefix = request.script_root + _url_prefix
    today = dt.datetime.now(IST).date()
    fy_from = "%04d-04" % (today.year if today.month >= 4 else today.year - 1)
    rows = con.execute("SELECT b.supplier_norm, MAX(b.supplier), COUNT(*), SUM(CASE WHEN b.month>=? THEN b.amount_p ELSE 0 END), MAX(b.month), "
                       "SUM(CASE WHEN b.month>=? THEN 1 ELSE 0 END) FROM purchase_bill b WHERE b.supplier_norm IS NOT NULL AND %s GROUP BY b.supplier_norm ORDER BY 4 DESC" % EFF_BILL,
                       (fy_from, fy_from)).fetchall()
    h = ['<div id="s750l"><style>%s</style><h1>Dealer ledgers</h1><div class="muted">Sanjeevni Medicos · one running ledger per dealer: bills with their items, returns, the '
         'month summaries, payments, the balance; item quantities by month and by financial year. Reads Marg\'s exports and this server\'s own records. '
         '<a href="%s/page/check">The purchase check</a> · <a href="%s/page/hub">the hub</a>.</div>' % (S750_LEDGER_CSS, _esc(prefix), _esc(prefix))]
    h.append('<div class="scroll"><table class="sheet"><tr><th>Dealer</th><th class="n">%s bills</th><th class="n">%s purchases</th><th>Last month</th></tr>' % (_esc(_s750_fy(fy_from)), _esc(_s750_fy(fy_from))))
    for r in rows:
        h.append('<tr><td><a href="%s/page/ledger/%s">%s</a></td><td class="n">%d</td><td class="n">%s</td><td>%s</td></tr>'
                 % (_esc(prefix), _esc(_s750_q(str(r[0]))), _esc(str(r[1] or r[0]).title()), int(r[5] or 0), _r(int(r[3] or 0)), _esc(_month_name(str(r[4]))) if r[4] else ""))
    h.append("</table></div></div>")
    return _page("Dealer ledgers", "".join(h))


@bp.route("/page/ledger/<path:key>")
def page_s750_ledger(key):
    """One dealer's running ledger. Read only; ?print=1 opens every fold."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    if not _s452_may_advice(con, u):
        return _refuse("The dealer ledgers are for the doctor and the senders.")
    key = str(key or "")[:120]
    if not con.execute("SELECT 1 FROM purchase_bill WHERE supplier_norm=? LIMIT 1", (key,)).fetchone():
        return "no such dealer", 404
    prefix = request.script_root + _url_prefix
    print_ = str(request.args.get("print") or "") == "1"
    L = s750_ledger(con, key)
    h = ['<div id="s750l"><style>%s</style><h1>%s — dealer ledger</h1><div class="muted">%s · %d month%s · paid by %s · <a class="noprint" href="%s/page/ledger">all dealers</a> · '
         '<a class="noprint" href="%s/page/ledger/%s?print=1" target="_blank" rel="noopener">print</a></div>'
         % (S750_LEDGER_CSS, _esc(L["name"].title()), _esc(L["name"]), len(L["months"]), "" if len(L["months"]) == 1 else "s", _esc(L["route"]), _esc(prefix), _esc(prefix), _esc(_s750_q(key)))]
    for fy in sorted(L["fys"].values(), key=lambda f: f["fy"], reverse=True):
        h.append('<div class="fy"><div class="kv"><span><b>%s</b> · %d month%s%s</span><span>purchases <b>%s</b></span><span>returns <b>%s</b></span><span>payable <b>%s</b></span>'
                 '<span>paid <b>%s</b></span><span class="%s">balance <b>%s</b></span></div>'
                 '<details class="b"%s><summary><span>Items supplied in %s · %d</span><span class="n">%s units</span></summary>%s</details></div>'
                 % (_esc(fy["fy"]), fy["months"], "" if fy["months"] == 1 else "s",
                    (" (%d settled outside the system, before the register began)" % fy["settled"]) if fy.get("settled") else "",   # S755 (F-1189)
                    _r(fy["purchases_p"]), _r(fy["returns_p"]), _r(fy["payable_p"]), _r(fy["paid_p"]),
                    "ok" if not fy["balance_p"] else "bad", _r(fy["balance_p"]), " open" if print_ else "", _esc(fy["fy"]), len(fy["items"]),
                    _esc(_s750_fmt_q(sum(i["qty"] for i in fy["items"]))), _s750_items_table(fy["items"], cap=200 if print_ else 60)))
    for i, mo in enumerate(L["months"]):
        h.append(_s750_month_html(con, L, mo, prefix, i == 0, print_))
    if not L["months"]:
        h.append('<div class="muted">No bills of this dealer in Marg\'s exports.</div>')
    h.append('<div class="mut" style="margin-top:10px">Quantities add each line\'s qty and free; a Marg purchase return counts negative. Paid: the NEFT when the month\'s bank SMS '
             'came, the cheques recorded, or what was typed as paid on the sheet.</div></div>')
    if print_:
        h.append("<script>window.addEventListener('load',function(){setTimeout(function(){window.print();},300);});</script>")
    return _page("%s — dealer ledger" % L["name"].title(), "".join(h))


# ------------------------------------------------------------------ the doors (the doctor only)
@bp.route("/api/s750/answer", methods=["POST"])
def api_s750_answer():
    """The owner's answer on a dealer's line of row 7: {dealer, month, decision: ask | carry | accept | none | scan | rescan, amount_p?}."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    amt = b.get("amount_p")
    try:
        amt = int(amt) if amt not in (None, "") else None
    except (TypeError, ValueError):
        amt = None
    ok, msg = _s454_sr().s750_answer_put(con, _who(u), str(b.get("dealer") or ""), str(b.get("month") or ""), str(b.get("decision") or ""), amt, str(b.get("note") or ""))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


@bp.route("/api/s750/undo", methods=["POST"])
def api_s750_undo():
    """Undo of an answer on row 7: {act}. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s750_undo(con, _who(u), _s749_int(b, "act"))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)


@bp.route("/api/s750/dealer_of", methods=["POST"])
def api_s750_dealer_of():
    """The owner names the dealer of a summary the reader could not place: {scan, dealer}. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s750_dealer_pick(con, _who(u), _s749_int(b, "scan"), str(b.get("dealer") or ""))
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S750 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S756 (09-Nov-2026, Sanjeevni session 412, kit S756_SUMMARY_DEALER_WA; the owner's go 06:31 IST) -------------------------------------
#  THE DOOR /api/s756/pause -- the doctor only: {dealer, on: true | false} pauses or resumes the daily WhatsApp reminder to one dealer whose
#  month summary is awaited (scan_register.s756_pause_put; audited). The snapshot's Pause / Resume buttons post here.
KIT_S756 = "S756_SUMMARY_DEALER_WA"


@bp.route("/api/s756/pause", methods=["POST"])
def api_s756_pause():
    """Pause or resume a dealer's summary reminders: {dealer, on}. The doctor only."""
    u, con, err = _s749_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    on = b.get("on")
    on = on is True or str(on).strip().lower() in ("1", "true", "yes", "on")
    ok, msg = _s454_sr().s756_pause_put(con, _who(u), str(b.get("dealer") or ""), on)
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S756 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S781 (11-Nov-2026, Sanjeevni session 426, kit S781_PROVISIONAL_BILLS; D891, D892 -- the owner's mock V3 approved 04:29 IST) ------
#  The Purchase bills page (/page/scans) opens with provisional_s781.summary_html: the month in three parts (in Marg · scanned, not yet in
#  Marg · both), how reliable the scans are, the provisional list with each scan's read lines, and -- for the doctor -- where Marg's bill
#  differs from its scan, with Check here (the scan inline, the lines side by side) and his taps. NEVER into stock (D891).
#  POST /api/s781/mark {bill, action: amir|clear|return|flag|undo, flag, note} -- the doctor only. Fail-soft: an error in S781 leaves the
#  page exactly as it was before it.
KIT_S781 = "S781_PROVISIONAL_BILLS"
import sys as _sys_s781                                       # noqa: E402


def _s781():
    import provisional_s781                                   # noqa: PLC0415 -- beside this file
    return provisional_s781


_s781_register_page_before = _s454_register_page
S781_AT = '<div class="hd" id="s454heads">'


def _s454_register_page(con, u):                              # noqa: F811 -- S781: the provisional bills at the top
    out = _s781_register_page_before(con, u)
    try:
        page = out[0] if isinstance(out, tuple) else out          # _page answers (html, 200, headers)
        if isinstance(page, str) and S781_AT in page and request.args.get("legacy") != "1":
            SR = _s454_sr()
            months = SR.months_with_bills(con)
            month = str(request.args.get("month") or (months[0] if months else dt.date.today().strftime("%Y-%m")))[:7]
            if re.match(r"^\d{4}-\d{2}$", month):
                add = _s781().summary_html(con, month, request.script_root + _url_prefix, _is_doctor(u))
                page = page.replace(S781_AT, add + S781_AT, 1)
                out = ((page,) + tuple(out[1:])) if isinstance(out, tuple) else page
    except Exception as e:                                    # noqa: BLE001 -- the page as it was before S781
        print("S781 register page failed: %r" % (e,), file=_sys_s781.stderr)
    return out


@bp.route("/api/s781/mark", methods=["POST"])
def api_s781_mark():
    """The doctor's answer on a bill whose Marg entry differs from its scan: {bill, action, flag, note}."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        bid = 0
    if bid <= 0:
        return jsonify(ok=False, error="bad_request", message="Which bill?"), 400
    con = _db()
    ok, msg, code = _s781().mark(con, _who(u), bid, str(b.get("action") or ""), str(b.get("flag") or ""), str(b.get("note") or ""))
    return jsonify(ok=ok, message=msg), code
# ---- S781 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S850_MARG_IS_RIGHT (17-Nov-2026, Sanjeevni session 476; D993 b-c, D995): "Marg is right" on one line of "Scan reading against Marg" -----
@bp.route("/api/s850/line", methods=["POST"])
def api_s850_line():
    """The doctor's tap on a scan line of a bill whose totals differ: {a: scan id, k: line key, do: right | undo}."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
    b = request.get_json(silent=True) or {}
    try:
        sid = int(b.get("a") or 0)
    except (TypeError, ValueError):
        sid = 0
    if sid <= 0 or not str(b.get("k") or ""):
        return jsonify(ok=False, error="bad_request", message="Which line?"), 400
    con = _db()
    try:
        import marg_right as _s850                            # noqa: PLC0415
        ok, msg, code = _s850.tap(con, _who(u), sid, str(b.get("k")), str(b.get("do") or "right"))
    except Exception as e:                                    # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        ok, msg, code = False, "Not saved (%s)." % e.__class__.__name__, 503
    return jsonify(ok=ok, message=msg), code
# ---- S850 end ---------------------------------------------------------------------------------------------------------------------------
