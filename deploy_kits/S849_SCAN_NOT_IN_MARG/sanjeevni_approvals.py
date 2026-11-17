#!/usr/bin/env python3
# =============================================================================
#  sanjeevni_approvals.py  ·  v1.10  ·  kit S410_MEDICINE_ORDERING  ·  Session 283 (Sanjeevni)
#
#  S417 (F-636, 26-Sep-2026): the Yes Bank tile takes a provisional supplier NEFT off its headline -- '− ₹X provisional NEFT (awaiting
#  statement)' as its own line, the headline marked 'incl. provisional' -- until the statement confirms it (S407), then the line goes and
#  nothing is counted twice. Read-only; no table. With no such NEFT the tile's answer is byte-identical.
#
#  v1.12 (S638, D780, 24-Oct-2026): the owner's EXPIRY WATCH -- GET /finance/sanjeevni/expiry (the page, expiry_watch.owner_page) and
#  POST /finance/sanjeevni/expiry/settings (its thresholds), checker only; Needs you gains expiry_watch.needs_you_lines (what is expired or
#  stops selling next month; the month's Batch Stock not received), each line carrying href to the page. Fail-soft: without the module
#  or its tables nothing here changes. NEEDS_YOU_WITHOUT_S638=1 leaves the lines out -- set only by an older kit's frozen walk re-run.
#  v1.11 (S428, D633, 27-Sep-2026): the Month section gains the leakage line (stock_watch.month_leak, fail-soft); Needs you gains
#  the stock watch's lines -- the confirmed count Sunday, a cadence move, an unexplained trace, missed mornings, red leakage months.
#  v1.10 (S410, D626, 26-Sep-2026): Needs you gains order_rules' lines -- an order still unsent on its next order day, a supplier's
#  month running above its 90-day pace, the Kedar review (one tap), the freeze, the Sunday one-liner (fail-soft).
#  NEEDS_YOU_WITHOUT_S410=1 leaves them out -- set only by an older kit's frozen walk re-run.
#
#  v1.9 (S408, D624, 26-Sep-2026): after the 10th, Needs you gains the previous month's empty statement cells and Shavez's open
#  checklist items (read from packs, fail-soft). NEEDS_YOU_WITHOUT_S408=1 leaves them out -- set only by S400's frozen walk re-run.
#
#  v1.8 (S407, D623, 26-Sep-2026): Needs you gains 'N supplier message(s) unsent' (a queued WhatsApp older than 30 minutes)
#  and 'NEFT of <Month>: bank shows X, sheet Y -- differs by Z' (read from supplier_msg, fail-soft).
#
#  v1.7 (S406, D622, 26-Sep-2026): the Needs-you returns line counts only real items (returns_kinds.pending_count:
#  counter returns >= returns.big_p, never bought, returned more than sold); the months API gains counter_returns and
#  counter_returns_pct. NEEDS_YOU_WITHOUT_S406=1 keeps the old rule -- set only by S400's frozen walk re-run.
#
#  v1.6 (S405, D621, 26-Sep-2026): Needs you gains 'NEFT of ₹X seen on <date> -- matched to <Month>. OK?' (read from
#  bank_sms, fail-soft) with the two POST routes /api/neft-event/ok and /api/neft-event/reject (the owner's one tap).
#
#  v1.5 (S403, D618, 26-Sep-2026): Needs you gains three lines read from porders (fail-soft): 'Orthotic shortages: N items --
#  order not sent' · 'Bill scan pending on N purchase bills' · 'Buying rules for medicines await your approval'.
#
#  v1.4 (S400, D616, 25-Sep-2026): each day line carries Bhati's mark (his verdict and time, his galti list, the cash
#  he entered) read from sale_check, fail-soft; Needs you gains "Bhati found mistakes on N day(s)" for unapproved days.
#  Nothing else moves. v1.0 was kit S368_APPROVALS_TREE, Session 281.
#
#  THE APPROVALS PAGE AS ONE TREE (D591 finished; D603, the owner, 22-Sep-2026: one page,
#  the audit material a collapsed section on it, never a second page). This module is the
#  page's read door. It composes SENTENCES on the server (D349) and reads every rupee from
#  the one cash calculation (sanjeevni_cash, D600). It writes nothing.
#
#  v1.1 (S375, D604, 22-Sep-2026): the owner records a cash deposit (pool -> Yes Bank) and a transfer
#  (ICICI -> Yes Bank, or either account -> its own HUF savings) himself. A transfer is never income and
#  never touches a day, a sale or the cash calculation; money to an HUF savings account leaves the
#  pharmacy's picture. ICICI's position is computed from the settlements ICICI has credited less what has
#  been moved out of it -- never typed. Everything recorded reads "waiting for the statement" until the
#  bank's own statement covers its date.
#
#  v1.3 (S378, 23-Sep-2026): Bank opens with both accounts' balances, bold. Yes Bank is the balance its own
#  statement closes on plus every recorded movement that statement does not show; ICICI is S377's count. Each
#  says how it was made, and that a payment or a charge the bank has taken since is not in it.
#
#  v1.2 (S377, F-615, 23-Sep-2026): what ICICI holds is counted from the BANK'S OWN closing balance
#  (table `bank_anchor`, seeded from the statement he gave), not from zero at the cash anchor -- v1.1 could
#  not see the money the account already held, and refused his real 20-Sep transfer because of it. And a
#  count that is short never refuses the bank: the transfer is recorded and the shortfall is named.
#
#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target
#      GET /finance/sanjeevni/api/days           one line per filed day from the anchor
#      GET /finance/sanjeevni/api/bank?month=    the pharmacy's UPI by day; the Yes Bank statement
#      GET /finance/sanjeevni/api/months         the months, one Marg figure named for its days
#      POST /finance/sanjeevni/api/bank/deposit  record a cash deposit from the pool     (checker)
#      POST /finance/sanjeevni/api/bank/transfer record a transfer between accounts      (checker)
#      POST /finance/sanjeevni/api/bank/undo     remove one unconfirmed entry you just made (checker)
#      POST /finance/sanjeevni/api/neft-event/ok      S405: the SMS NEFT provisional is right (checker)
#      POST /finance/sanjeevni/api/neft-event/reject  S405: 'Not this' -- the event is rejected (checker)
#      GET /finance/approvals/old                the page as it was (finance_approvals_old.html)
#  checker (the owner) only.
# =============================================================================
import datetime as dt
import os

from flask import Blueprint, jsonify, request, send_from_directory

VERSION = "1.12"
bp = Blueprint("sanjeevni_approvals", __name__)
_db = _require = None
_unit = "medical"
HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.environ.get("FINANCE_UI_DIR", os.path.join(HERE, "finance_ui"))
ANCHOR_FLOOR = "2026-08-17"
DEP_KINDS = ("deposit_not_in_bank", "bank_deposit_not_booked", "deposit_unevidenced")

# S375 (D604): the four accounts money can sit in or leave to. The two HUF savings accounts are
# OUTSIDE the pharmacy's books -- money reaching them has left, and is never an expense.
ACCOUNTS = {"icici": "ICICI Sanjeevni", "yesbank": "Yes Bank Sanjeevni",
            "huf_icici": "ICICI HUF savings", "huf_yesbank": "Yes Bank HUF savings"}
INSIDE = ("icici", "yesbank")
ROUTES = {("icici", "yesbank"), ("icici", "huf_icici"), ("yesbank", "huf_yesbank")}
TRANSFER_DDL = (
    "CREATE TABLE IF NOT EXISTS bank_transfer ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, transfer_date TEXT NOT NULL,"
    " from_account TEXT NOT NULL, to_account TEXT NOT NULL, amount_p INTEGER NOT NULL,"
    " ref TEXT, note TEXT, entered_by TEXT, entered_at TEXT,"
    " UNIQUE (unit, transfer_date, from_account, to_account, amount_p))")


ANCHOR_DDL = (
    "CREATE TABLE IF NOT EXISTS bank_anchor ("
    " unit TEXT NOT NULL, account TEXT NOT NULL, as_on TEXT NOT NULL, balance_p INTEGER NOT NULL,"
    " source TEXT, entered_by TEXT, entered_at TEXT, PRIMARY KEY (unit, account))")


def ensure_schema(con):
    """The two tables this module owns. Created on first use; nothing else is touched."""
    con.execute(TRANSFER_DDL)
    con.execute(ANCHOR_DDL)


def anchor_for(con, account, unit=None):
    """The bank's own closing balance for this account, as on a date, from a statement it printed.
    None when no statement has been anchored yet -- the count then starts where it always did."""
    unit = unit or _unit
    if not _has(con, "bank_anchor"):
        return None
    r = con.execute("SELECT as_on, balance_p, source FROM bank_anchor WHERE unit=? AND account=?",
                    (unit, account)).fetchone()
    return dict(as_on=r[0], balance_p=int(r[1]), source=r[2] or "") if r else None


def _audit_row(con, who, action, detail):
    try:
        import json as _json
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) "
                    "VALUES (?,?,?,NULL,?,?,?)",
                    ("bank_entry", None, action, _json.dumps(detail, ensure_ascii=False), who,
                     dt.datetime.now().replace(microsecond=0).isoformat()))
    except Exception:  # noqa: BLE001 -- the record is the row itself; the audit is a courtesy
        pass


def transfers(con, unit=None):
    unit = unit or _unit
    if not _has(con, "bank_transfer"):
        return []
    return [dict(id=r[0], date=r[1], frm=r[2], to=r[3], amount_p=int(r[4]), ref=r[5] or "", note=r[6] or "",
                 by=r[7] or "", at=r[8] or "")
            for r in con.execute("SELECT id, transfer_date, from_account, to_account, amount_p, ref, note, "
                                 "entered_by, entered_at FROM bank_transfer WHERE unit=? "
                                 "ORDER BY transfer_date, id", (unit,))]


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    try:                                                      # S803 (12-Nov-2026): the Marg watch -- bills changed after their day (marg_billwatch.py)
        import marg_billwatch                                 # noqa: PLC0415 -- beside this file
        marg_billwatch.init(app, db_getter, require_fn)
    except Exception as _e803:                                # noqa: BLE001 -- these pages keep working without it
        import sys as _sys803                                 # noqa: PLC0415
        print("marg_billwatch NOT mounted: %s" % _e803, file=_sys803.stderr)
    try:                                                      # S845 (16-Nov-2026): the Item ledger -- read only (item_ledger.py; D992)
        import item_ledger                                    # noqa: PLC0415 -- beside this file
        item_ledger.init(app, db_getter, require_fn)
    except Exception as _e845:                                # noqa: BLE001 -- these pages keep working without it
        import sys as _sys845                                 # noqa: PLC0415
        print("item_ledger NOT mounted: %s" % _e845, file=_sys845.stderr)
    try:                                                      # S849 (17-Nov-2026): scanned bills not found in Marg (scan_ask.py; D995)
        import scan_ask                                       # noqa: PLC0415 -- beside this file
        scan_ask.init(app, db_getter, require_fn)
    except Exception as _e849:                                # noqa: BLE001 -- these pages keep working without it
        import sys as _sys849                                 # noqa: PLC0415
        print("scan_ask NOT mounted: %s" % _e849, file=_sys849.stderr)
    return bp


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def rs(p):
    """Indian grouping, whole rupees; None stays None."""
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


def dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b")
    except (TypeError, ValueError):
        return str(iso or "?")


def _today():
    return dt.date.today().isoformat()


# ------------------------------------------------------------------ the rows (one source)
def _cash_rows(con):
    import sanjeevni_cash as sc
    r = sc.days(con, ANCHOR_FLOOR, "9999-12-31", _unit)
    if not r.get("ok"):
        return [], r
    return r["rows"], r


def _marg_net(con):
    """business_date -> (net_p, bills) from Marg's latest export rows."""
    out = {}
    if _has(con, "sale_bill"):
        for d, n, s in con.execute("SELECT business_date, COUNT(*), COALESCE(SUM(net_p),0) FROM sale_bill "
                                   "WHERE unit=? GROUP BY 1", (_unit,)):
            out[d] = (int(s), int(n))
    return out


def _kal_rows(con):
    """business_date -> the doctors' log row (handed, to, received) when one exists."""
    out = {}
    if _has(con, "darpan_kal_day"):
        for r in con.execute("SELECT business_date, handed_p, handed_to, received_at, state FROM darpan_kal_day "
                             "WHERE unit=? AND handed_p IS NOT NULL", (_unit,)):
            out[r[0]] = dict(handed_p=int(r[1]), to=r[2], received=bool(r[3]), state=r[4])
    return out


PARTY = {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you", "pool": "the pool", "bank": "the bank"}


def _bhati_marks(con):
    """S400: business_date -> Bhati's mark (verdict, time, galti list, cash entry); {} when the module or its
    tables are not there."""
    try:
        import sale_check  # noqa: PLC0415
        return sale_check.owner_marks(con) or {}
    except Exception:  # noqa: BLE001
        return {}


def day_lines(con):
    rows, meta = _cash_rows(con)
    if not rows:
        return dict(ok=False, error=meta.get("error", "no_rows"), message=meta.get("message", ""), days=[])
    marg = _marg_net(con)
    kal = _kal_rows(con)
    bhati = _bhati_marks(con)                                   # S400
    out = []
    for x in rows:
        d = x["date"]
        m = marg.get(d)
        filed = x["sale_p"]
        marg_ok = None if m is None else (m[0] == filed)
        handed = [h for h in x["handed"] if h.get("src") != "approval"]
        implied = [h for h in x["handed"] if h.get("src") == "approval"]
        if handed:
            went = "; ".join("%s to %s" % (rs(h["amount_p"]), PARTY.get(h["to"], h["to"])) for h in handed)
        elif implied:
            went = "to the pool (approved)"
        elif x["waiting_approval"]:
            went = "in the drawer"
        else:
            went = ""
        k = kal.get(d)
        out.append(dict(date=d, day=dmy(d), weekday=dt.date.fromisoformat(d).strftime("%a"),
                        status=x["status"], approved=(x["status"] in ("approved", "locked")),
                        sale=rs(x["sale_p"]), upi=rs(x["upi_p"]), without_cash=rs(x["without_cash_p"]),
                        cash=rs(x["into_drawer_p"]), cash_p=x["into_drawer_p"],
                        elsewhere=rs(x["received_elsewhere_p"]) if x["received_elsewhere_p"] else None,
                        marg_ok=marg_ok, marg=rs(m[0]) if m else None, marg_bills=(m[1] if m else None),
                        went=went, logged=bool(handed) or bool(k),
                        log=(dict(to=PARTY.get(k["to"], k["to"]), amount=rs(k["handed_p"]), received=k["received"]) if k else None),
                        banked=[dict(amount=rs(b["amount_p"]), bank=b.get("bank"), place=b.get("place")) for b in x.get("banked", [])],
                        waiting_approval=bool(x["waiting_approval"]), bhati=bhati.get(d)))
    close = rows[-1]["close"]
    return dict(ok=True, days=out, anchor=ANCHOR_FLOOR,
                position=dict(drawer=rs(close["drawer"]), pool=rs(close["pool"]),
                              with_doctors=rs(close["with_doctors"]), bank=rs(close["bank"])))


# ------------------------------------------------------------------ the bank
def _statement_covers(con, iso):
    """Does a loaded statement reach far enough PAST this date to prove the money never arrived? A credit can
    land up to three days late, so a statement that stops on the day itself proves nothing: the entry waits
    rather than being called missing (S377)."""
    if not _has(con, "bank_statement_period"):
        return False
    need = (dt.date.fromisoformat(iso) + dt.timedelta(days=3)).isoformat()
    return con.execute("SELECT 1 FROM bank_statement_period WHERE period_from<=? AND period_to>=?",
                       (iso, need)).fetchone() is not None


def _seen_in_yesbank(con, iso, amount_p, deposit):
    """Does the loaded Yes Bank statement show this money, within three days either way?"""
    if not _has(con, "bank_statement_line"):
        return False
    col = "deposit_p" if deposit else "withdrawal_p"
    lo = (dt.date.fromisoformat(iso) - dt.timedelta(days=0)).isoformat()
    hi = (dt.date.fromisoformat(iso) + dt.timedelta(days=3)).isoformat()
    return con.execute("SELECT 1 FROM bank_statement_line WHERE %s=? AND txn_date BETWEEN ? AND ?" % col,
                       (amount_p, lo, hi)).fetchone() is not None


def icici_position(con, unit=None):
    """What ICICI holds, computed and never typed (S377):

        the balance the BANK printed on its own statement, as on its date
      + every POS settlement credited after that date
      - every transfer recorded out of ICICI after that date

    With no anchored statement it falls back to what v1.1 did -- settlements since the 17-Aug cash anchor,
    which cannot see the money the account already held, and is therefore only ever a floor."""
    unit = unit or _unit
    anc = anchor_for(con, "icici", unit)
    since = anc["as_on"] if anc else ANCHOR_FLOOR
    base = anc["balance_p"] if anc else 0
    # a settlement dated D is credited the next working day, so a settlement dated ON the anchor's date is
    # money that arrived AFTER that closing balance -- it counts.
    credited = int(con.execute("SELECT COALESCE(SUM(parsed_total_p),0) FROM upi_statement WHERE unit=? "
                               "AND statement_date>=?", (unit, since)).fetchone()[0] or 0)
    out = sum(t["amount_p"] for t in transfers(con, unit) if t["frm"] == "icici" and t["date"] > since)
    last = con.execute("SELECT MAX(statement_date) FROM upi_statement WHERE unit=?", (unit,)).fetchone()[0]
    return dict(credited_p=credited, out_p=out, base_p=base, holds_p=base + credited - out,
                since=since, upto=last, anchored=bool(anc),
                source=(anc["source"] if anc else ""))


def yesbank_position(con, unit=None):
    """What Yes Bank holds: the balance ITS OWN statement closes on, plus every movement we have recorded
    that the statement does not show. A movement the statement shows is already inside the bank's figure and
    is never added twice. Nothing the bank has done since the statement -- a supplier payment, the POS rental
    and its GST -- can be known here; the next statement settles it."""
    unit = unit or _unit
    base_p, as_on = 0, None
    if _has(con, "bank_statement_period"):
        r = con.execute("SELECT period_to, closing_p FROM bank_statement_period ORDER BY period_to DESC "
                        "LIMIT 1").fetchone()
        if r:
            as_on, base_p = r[0], int(r[1] or 0)
    added, taken = 0, 0
    if _has(con, "cash_pool_deposit"):
        for d, amt in con.execute("SELECT deposit_date, amount_p FROM cash_pool_deposit WHERE unit=?", (unit,)):
            if not _seen_in_yesbank(con, d, int(amt), True):
                added += int(amt)
    for t in transfers(con, unit):
        if t["to"] == "yesbank" and not _seen_in_yesbank(con, t["date"], t["amount_p"], True):
            added += t["amount_p"]
        elif t["frm"] == "yesbank" and not _seen_in_yesbank(con, t["date"], t["amount_p"], False):
            taken += t["amount_p"]
    return dict(base_p=base_p, as_on=as_on, added_p=added, taken_p=taken,
                holds_p=base_p + added - taken, anchored=bool(as_on))


# ------------------------------------------------------------------ S417: a provisional NEFT on the Yes Bank tile (F-636)
def _neft_tol(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='neft.stmt_tolerance_p'").fetchone()
        return max(0, int(float(r[0]))) if (r and r[0] not in (None, "")) else 0
    except Exception:  # noqa: BLE001
        return 0


def provisional_nefts(con, yp=None):
    """S417 (F-636). The owner tapped 'NEFT done' for August and the Yes Bank tile did not move. A supplier NEFT that is PROVISIONAL --
    tapped by the owner, or seen by the bank SMS and confirmed by him (S405 / S407's purchase_neft_event) -- and that no statement has
    confirmed yet is taken off the tile as its own line. Confirmed means: S407's bank_line_id; or a NEFT debit of the same amount (within
    neft.stmt_tolerance_p) from 3 days before to 15 days after its date in the loaded statement; or a statement whose period already
    reaches its date (the debit is then inside the bank's own closing balance -- subtracting it again would count it twice).
    Read-only: nothing is written here."""
    if not _has(con, "purchase_neft_event"):
        return []
    yp = yp or yesbank_position(con)
    as_on = str(yp.get("as_on") or "")
    tol = _neft_tol(con)
    has_lines = _has(con, "bank_statement_line")
    out = []
    for r in con.execute("SELECT id, month, source, amount_p, sms_date, created_at FROM purchase_neft_event WHERE kind='provisional' "
                         "AND (source='owner' OR confirmed_by IS NOT NULL) AND bank_line_id IS NULL ORDER BY id").fetchall():
        d = str(r[4] or r[5] or "")[:10]
        try:
            d0 = dt.date.fromisoformat(d)
        except ValueError:
            continue
        amt = int(r[3] or 0)
        if amt <= 0 or (as_on and as_on >= d):
            continue
        lo, hi = (d0 - dt.timedelta(days=3)).isoformat(), (d0 + dt.timedelta(days=15)).isoformat()
        if has_lines and con.execute("SELECT 1 FROM bank_statement_line WHERE withdrawal_p BETWEEN ? AND ? AND UPPER(description) LIKE '%NEFT%' "
                                     "AND txn_date BETWEEN ? AND ? LIMIT 1", (amt - tol, amt + tol, lo, hi)).fetchone():
            continue
        try:
            mname = dt.date(int(str(r[1])[:4]), int(str(r[1])[5:7]), 1).strftime("%B %Y")
        except (TypeError, ValueError):
            mname = str(r[1] or "")
        out.append(dict(id=int(r[0]), month=r[1], amount_p=amt, amount=rs(amt), date=d, day=dmy(d),
                        text="%s purchases · NEFT %s · %s" % (mname, dmy(d), "you tapped NEFT done" if r[2] == "owner" else "the bank SMS, confirmed by you")))
    return out


def _yes_tile_s417(con, yp):
    """The Yes Bank tile's figures (S378) -- and, S417, the provisional NEFT line(s) with the headline net of them. With none, the very
    same dict as before (same keys, same order, same values)."""
    tile = dict(holds=rs(max(yp["holds_p"], 0)), base=rs(yp["base_p"]), as_on=(dmy(yp["as_on"]) if yp["as_on"] else None),
                added=rs(yp["added_p"]), taken=rs(yp["taken_p"]), anchored=yp["anchored"])
    try:
        prov = provisional_nefts(con, yp)
    except Exception:  # noqa: BLE001 -- the tile never waits for this
        prov = []
    if prov:
        p = sum(x["amount_p"] for x in prov)
        tile.update(holds=rs(max(yp["holds_p"] - p, 0)), incl_provisional=True, provisional=prov, provisional_total=rs(p),
                    before_provisional=rs(max(yp["holds_p"], 0)))
    return tile


def bank_view(con, ym):
    upi = []
    for d, tot, n, at in con.execute("SELECT statement_date, parsed_total_p, txn_count, ingested_at FROM upi_statement "
                                     "WHERE unit=? AND substr(statement_date,1,7)=? ORDER BY statement_date",
                                     (_unit, ym)):
        upi.append(dict(date=d, day=dmy(d), amount=rs(int(tot or 0)), payments=int(n or 0)))
    upi_total = sum(int(r[0] or 0) for r in con.execute(
        "SELECT parsed_total_p FROM upi_statement WHERE unit=? AND substr(statement_date,1,7)=?", (_unit, ym)))
    period = None
    if _has(con, "bank_statement_period"):
        p = con.execute("SELECT period_from, period_to, opening_p, closing_p, ingested_at FROM bank_statement_period "
                        "ORDER BY period_to DESC LIMIT 1").fetchone()
        if p:
            age = (dt.date.today() - dt.date.fromisoformat(p[1])).days
            period = dict(from_=p[0], to=p[1], from_day=dmy(p[0]), to_day=dmy(p[1]), opening=rs(int(p[2] or 0)),
                          closing=rs(int(p[3] or 0)), loaded_at=(p[4] or "")[:16].replace("T", " "), days_since=age)
    pool = []
    if _has(con, "cash_pool_deposit"):
        pool = [dict(id=r[0], date=r[1], amount_p=int(r[2]), bank=r[3], place=r[4]) for r in con.execute(
            "SELECT id, deposit_date, amount_p, bank, place FROM cash_pool_deposit WHERE unit=? ORDER BY deposit_date, id",
            (_unit,))]
    lines = []
    if _has(con, "bank_statement_line"):
        lines = [dict(id=r[0], date=r[1], amount_p=int(r[2] or 0), desc=(r[3] or "")[:60]) for r in con.execute(
            "SELECT id, txn_date, deposit_p, description FROM bank_statement_line WHERE is_cash_deposit=1 "
            "ORDER BY txn_date, id")]
    used = set()
    deposits = []
    for x in pool:
        hit = None
        for k in lines:
            if k["id"] in used or k["amount_p"] != x["amount_p"]:
                continue
            lag = (dt.date.fromisoformat(k["date"]) - dt.date.fromisoformat(x["date"])).days
            if 0 <= lag <= 3:
                hit = k
                break
        if hit:
            used.add(hit["id"])
            st, txt = "ok", "confirmed in the statement (%s)" % dmy(hit["date"])
        elif period and period["from_"] <= x["date"] <= period["to"]:
            st, txt = "bad", "NOT in the Yes Bank statement"
        else:
            st, txt = "wait", "no statement covers this date yet"
        deposits.append(dict(id=x["id"], date=x["date"], day=dmy(x["date"]), amount=rs(x["amount_p"]),
                             place=x["place"] or "", source="pool", status=st, text=txt))
    for k in lines:
        if k["id"] not in used:
            deposits.append(dict(date=k["date"], day=dmy(k["date"]), amount=rs(k["amount_p"]), place="",
                                 source="bank", status="bad", text="the bank received it; the books have no deposit for it"))
    deposits.sort(key=lambda z: z["date"])
    # ---- S375: the transfers he has recorded, each with what the statement says --------
    moves = []
    for t in transfers(con):
        if t["frm"] == "yesbank" or t["to"] == "yesbank":
            deposit = (t["to"] == "yesbank")
            if _seen_in_yesbank(con, t["date"], t["amount_p"], deposit):
                st, txt = "ok", "confirmed in the Yes Bank statement"
            elif _statement_covers(con, t["date"]):
                st, txt = "bad", "NOT in the Yes Bank statement"
            else:
                st, txt = "wait", "no Yes Bank statement covers this date yet"
        else:
            st, txt = "wait", "the ICICI statement for this date has not been read yet"
        moves.append(dict(id=t["id"], date=t["date"], day=dmy(t["date"]), amount=rs(t["amount_p"]),
                          frm=ACCOUNTS.get(t["frm"], t["frm"]), to=ACCOUNTS.get(t["to"], t["to"]),
                          frm_key=t["frm"], to_key=t["to"], ref=t["ref"],
                          leaves=(t["to"] not in INSIDE), status=st, text=txt))
    ip = icici_position(con)
    yp = yesbank_position(con)
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),
                yesbank=_yes_tile_s417(con, yp),                                                   # S417
                statement=period, deposits=deposits, transfers=moves,
                icici=dict(holds=rs(max(ip["holds_p"], 0)),
                           short=(rs(-ip["holds_p"]) if ip["holds_p"] < 0 else ""),
                           credited=rs(ip["credited_p"]), out=rs(ip["out_p"]),
                           base=(rs(ip["base_p"]) if ip["anchored"] else ""), anchored=ip["anchored"],
                           source=ip["source"], since=dmy(ip["since"]),
                           upto=(dmy(ip["upto"]) if ip["upto"] else None)),
                accounts=ACCOUNTS,
                banked_total=rs(sum(x["amount_p"] for x in pool)))


# ------------------------------------------------------------------ the months
def month_view(con):
    import sanjeevni_cash as sc
    rows = sc.month_rows(con, _unit)
    banked = {}
    if _has(con, "cash_pool_deposit"):
        for ym, s in con.execute("SELECT substr(deposit_date,1,7), SUM(amount_p) FROM cash_pool_deposit WHERE unit=? GROUP BY 1",
                                 (_unit,)):
            banked[ym] = int(s or 0)
    out = []
    for m in rows:
        if m["ym"] < ANCHOR_FLOOR[:7]:
            continue
        wc = m["home_p"] + m["proc_p"] + m["other_p"]
        out.append(dict(ym=m["ym"], label=dt.date.fromisoformat(m["ym"] + "-01").strftime("%B %Y"), days=m["days"],
                        sale=rs(m["sale_p"]), upi=rs(m["upi_p"]), cash=rs(m["cash_p"]), without_cash=rs(wc),
                        home=rs(m["home_p"]), procedure=rs(m["proc_p"]), other=rs(m["other_p"]),
                        elsewhere=rs(m["received_elsewhere_p"]), cash_income=rs(m["cash_income_p"]),
                        income=rs(m["income_p"]), banked=rs(banked.get(m["ym"], 0)),
                        marg=rs(m["marg_sale_p"]) if m["marg_sale_p"] is not None else None,
                        marg_days=m["marg_days"],
                        marg_note=("Marg's own bills, all %d days" % m["days"]) if m["marg_days"] == m["days"] and m["marg_days"]
                        else ("Marg's own bills, %d of %d days" % (m["marg_days"], m["days"]) if m["marg_days"] else "no Marg bills on record")))
    # S406 (D622): counter returns per month -- count, rupees, % of counter sales (fail-soft: None when the engine cannot answer)
    for row in out:
        try:
            import returns_kinds  # noqa: PLC0415
            f = returns_kinds.month_fields(con, _unit, row["ym"])
        except Exception:  # noqa: BLE001
            f = {}
        row["counter_returns_n"] = f.get("counter_returns_n")
        row["counter_returns_p"] = f.get("counter_returns_p")
        row["counter_returns"] = rs(f["counter_returns_p"]) if f.get("counter_returns_p") is not None else None
        row["counter_returns_pct"] = f.get("counter_returns_pct")
    # S428 (D633): the month's leakage line -- loss points + count write-offs at cost against the month's sales (fail-soft)
    try:
        import stock_watch  # noqa: PLC0415
        for row in out:
            row["leak"] = stock_watch.month_leak(con, row["ym"])
    except Exception:  # noqa: BLE001
        for row in out:
            row["leak"] = None
    return dict(ok=True, months=out)


# ------------------------------------------------------------------ needs you
def _returns_pending(con, ym):
    """The returns of the month that wait for the owner's OK -- the same rule as cn-detail (S220).
    S406 (D622): the rule is returns_kinds' -- counter returns only, real items only. NEEDS_YOU_WITHOUT_S406=1 is set
    ONLY by S400's frozen walk re-run (it asserts Needs you unchanged); the service never sets it."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S406") != "1":
        try:
            import returns_kinds  # noqa: PLC0415
            return returns_kinds.pending_count(con, _unit, ym)
        except Exception:  # noqa: BLE001
            pass
    try:
        from finance_returns_audit import returns_for_day, return_days  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
    def setting(k, d):
        r = con.execute("SELECT value FROM setting WHERE key=?", (k,)).fetchone()
        return r[0] if r and r[0] not in (None, "") else d
    act_from = setting("returns.act_from", "2026-09-02")
    try:
        large_p = int(setting("returns.large_p", "100000"))
    except (TypeError, ValueError):
        large_p = 100000
    days = return_days(con, _unit, ym + "-01", ym + "-31")        # S677: one place
    n, amt = 0, 0
    for d in sorted(days):
        if d < act_from:
            continue
        rows, _s = returns_for_day(con, d, _unit)
        for r in rows:
            large = int(r["amount_p"] or 0) >= large_p
            if not ((r["verdict"] != "ok") or large):
                continue
            a = con.execute("SELECT status FROM darpan_return_approval WHERE unit=? AND cn_bill=?", (_unit, r["bill"])).fetchone()
            if a is None or a[0] == "pending":
                n += 1
                amt += int(r["amount_p"] or 0)
    return n, amt


def needs_you(con):
    lines = []
    today = _today()
    # 1 · days to approve
    pend = [r[0] for r in con.execute("SELECT business_date FROM day_entry WHERE unit=? AND status IN ('submitted','draft') "
                                      "ORDER BY business_date", (_unit,))]
    if pend:
        span = dmy(pend[0]) if len(pend) == 1 else "%s to %s" % (dmy(pend[0]), dmy(pend[-1]))
        lines.append(dict(cls="bad", target="days", text="%d day%s to approve (%s)" % (len(pend), "" if len(pend) == 1 else "s", span),
                          dates=pend))
    # 2 · an approved day that is not Marg's (F-613)
    marg = _marg_net(con)
    for eid, d, st in con.execute("SELECT e.id, e.business_date, e.status FROM day_entry e WHERE e.unit=? AND e.business_date>=? "
                                  "AND e.status NOT IN ('submitted','draft','closed_holiday') ORDER BY e.business_date",
                                  (_unit, ANCHOR_FLOOR)):
        m = marg.get(d)
        if not m:
            continue
        f = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM day_line WHERE day_entry_id=? AND service='pharmacy_sale'",
                        (eid,)).fetchone()[0]
        if int(f) != m[0]:
            lines.append(dict(cls="bad", target="days", dates=[d],
                              text="%s is filed at %s; Marg's %d bills come to %s -- it is approved, so a person corrects it"
                              % (dmy(d), rs(int(f)), m[1], rs(m[0]))))
    # 3 · returns waiting for his OK -- S446 (F-680): every open month, the oldest named (the old line, this month only, stays
    #     exactly as it was only when NEEDS_YOU_WITHOUT_S406=1, an older kit's frozen walk)
    rl = _s760_returns_line(con, today)                     # S760: one source with the hub's Returns card; S446's line its fail-soft
    if rl:
        lines.append(rl)
    rp = _returns_pending(con, today[:7]) if rl is None else None
    if rp and rp[0]:
        lines.append(dict(cls="warn", target="returns", text="%d return%s of %s need%s your OK"
                          % (rp[0], "" if rp[0] == 1 else "s", rs(rp[1]), "s" if rp[0] == 1 else "")))
    # 4 · the bank
    for d, kind, exp, act in con.execute("SELECT business_date, kind, expected_p, actual_p FROM recon_exception "
                                         "WHERE unit=? AND status='open' AND kind IN (?,?,?) ORDER BY business_date",
                                         (_unit,) + DEP_KINDS):
        if kind == "bank_deposit_not_booked":
            t = "Yes Bank received %s in cash on %s that is not in the books" % (rs(int(act or 0)), dmy(d))
        elif kind == "deposit_not_in_bank":
            t = "%s booked as deposited on %s is NOT in the Yes Bank statement" % (rs(int(exp or 0)), dmy(d))
        else:
            t = "%s deposited on %s -- no Yes Bank statement covers that date yet" % (rs(int(exp or 0)), dmy(d))
        lines.append(dict(cls="bad" if kind != "deposit_unevidenced" else "warn", target="bank", text=t))
    # 5 · Marg reports pushed and not in the books
    if _has(con, "marg_push_staging"):
        n = con.execute("SELECT COUNT(*) FROM marg_push_staging WHERE status='pending'").fetchone()[0]
        if n:
            lines.append(dict(cls="warn", target="checks-marg", text="%d Marg report%s pushed from the counter, not yet in the books"
                              % (n, "" if n == 1 else "s")))
    # 6 · Darpan's word vs the data (darpan_kal's own owner card, read in-process)
    try:
        import darpan_kal  # noqa: PLC0415
        resp = darpan_kal.api_owner()
        j = resp.get_json() if not isinstance(resp, tuple) else None
        if j and j.get("ok"):
            n = int(j.get("count") or 0)
            if n:
                lines.append(dict(cls="warn", target="checks-kal", text="Darpan: %d item%s where his word and the data differ"
                                  % (n, "" if n == 1 else "s")))
            if j.get("owed_p"):
                lines.append(dict(cls="warn", target="checks-kal", text="%s owed back to Darpan" % rs(int(j["owed_p"]))))
    except Exception:  # noqa: BLE001
        pass
    # 8 · S400: Bhati's check of the pharmacy days -- mistakes he marked on days still to approve
    try:
        import sale_check  # noqa: PLC0415
        nb = int(sale_check.days_with_mistakes(con) or 0)
        if nb:
            lines.append(dict(cls="warn", target="days", text="Bhati found mistakes on %d day%s" % (nb, "" if nb == 1 else "s")))
    except Exception:  # noqa: BLE001
        pass
    # 9 · S403 (D618): orthotic shortages with no order sent, bills awaiting a scan, the medicine buying rules.
    #     NEEDS_YOU_WITHOUT_S403=1 is set ONLY by an older kit's walk (S400's asserts 'unchanged except its own line');
    #     the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S403") != "1":
        try:
            import porders  # noqa: PLC0415
            lines.extend(porders.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 10 · S405 (D621): a Yes Bank NEFT debit matched to a finalised pay month, awaiting his OK / Not this (fail-soft)
    try:
        import bank_sms  # noqa: PLC0415
        lines.extend(bank_sms.needs_you_lines(con))
    except Exception:  # noqa: BLE001
        pass
    # 11 · S407 (D623): supplier messages unsent for 30 minutes; a NEFT the bank statement contradicts (fail-soft)
    try:
        import supplier_msg  # noqa: PLC0415
        lines.extend(supplier_msg.needs_you_lines(con))
    except Exception:  # noqa: BLE001
        pass
    # 12 · S408 (D624): the statement shelf's empty cells and the month-end checklist's open items, after the 10th (fail-soft).
    #      NEEDS_YOU_WITHOUT_S408=1 is set ONLY by S400's frozen walk re-run (it asserts Needs you unchanged); the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S408") != "1":
        try:
            import packs  # noqa: PLC0415
            lines.extend(packs.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 13 · S410 (D626): the medicine ordering day -- a stuck order, a month above pace, the Kedar review, the freeze (fail-soft).
    #      NEEDS_YOU_WITHOUT_S410=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S410") != "1":
        try:
            import order_rules  # noqa: PLC0415
            lines.extend(order_rules.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 14 · S428 (D633): the stock watch -- the confirmed count Sunday, a cadence move, an unexplained trace, missed mornings,
    #      red leakage months running (fail-soft). NEEDS_YOU_WITHOUT_S428=1 is set ONLY by an older kit's frozen walk re-run.
    if os.environ.get("NEEDS_YOU_WITHOUT_S428") != "1":
        try:
            import stock_watch  # noqa: PLC0415
            lines.extend(stock_watch.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 15 · S444 (D647): Amir's slips as the owner's lines -- the salt list owed, his own correction unseen in Marg, Darpan's claims
    #      open, the count vouchers untouched, the duty map's orphan duties, a report refused today (fail-soft).
    #      NEEDS_YOU_WITHOUT_S444=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S444") != "1":
        try:
            import amir_day  # noqa: PLC0415
            lines.extend(amir_day.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 16 · S638 (D780): the expiry watch -- expired batches, batches Marg stops selling next month, the month's Batch Stock (fail-soft)
    if os.environ.get("NEEDS_YOU_WITHOUT_S638") != "1":
        try:
            import expiry_watch  # noqa: PLC0415
            lines.extend(expiry_watch.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)
    info = []
    if _has(con, "bank_statement_period"):
        p = con.execute("SELECT period_to FROM bank_statement_period ORDER BY period_to DESC LIMIT 1").fetchone()
        if p:
            age = (dt.date.today() - dt.date.fromisoformat(p[0])).days
            if age > 14:
                info.append(dict(cls="info", target="bank", text="the Yes Bank statement runs to %s (%d days ago) -- deposits since then are unproven"
                                 % (dmy(p[0]), age)))
        else:
            info.append(dict(cls="info", target="bank", text="no Yes Bank statement loaded yet"))
    return dict(ok=True, lines=lines + info, count=len(lines), as_of=dt.datetime.now().replace(microsecond=0).isoformat())


# ------------------------------------------------------------------ routes
@bp.route("/finance/sanjeevni/api/needs-you")
def api_needs_you():
    u, err = _require("checker")
    if err:
        return err
    return jsonify(needs_you(_db()))


def _neft_event(how):
    """S405 (D621): the owner's one tap on the SMS NEFT provisional. bank_sms owns the table and the rule."""
    u, err = _require("checker")
    if err:
        return err
    js = request.get_json(silent=True) or {}
    try:
        eid = int(js.get("id") or 0)
    except (TypeError, ValueError):
        eid = 0
    if not eid:
        return jsonify(ok=False, error="bad_id", message="Which NEFT event?"), 400
    import bank_sms  # noqa: PLC0415
    body, code = bank_sms.neft_event_decide(_db(), eid, how, u.get("user") or "owner")
    return jsonify(**body), code


@bp.route("/finance/sanjeevni/api/neft-event/ok", methods=["POST"])
def api_neft_event_ok():
    return _neft_event("ok")


@bp.route("/finance/sanjeevni/api/neft-event/reject", methods=["POST"])
def api_neft_event_reject():
    return _neft_event("reject")


@bp.route("/finance/sanjeevni/api/days")
def api_days():
    u, err = _require("checker")
    if err:
        return err
    return jsonify(day_lines(_db()))


@bp.route("/finance/sanjeevni/api/bank")
def api_bank():
    u, err = _require("checker")
    if err:
        return err
    ym = (request.args.get("month") or _today()[:7])[:7]
    return jsonify(bank_view(_db(), ym))


@bp.route("/finance/sanjeevni/api/months")
def api_months():
    u, err = _require("checker")
    if err:
        return err
    return jsonify(month_view(_db()))


def _amount_p(v):
    """Rupees from the page -> paise. Refuses anything that is not a positive amount."""
    try:
        p = int(round(float(str(v).replace(",", "").replace("\u20b9", "").strip()) * 100))
    except (TypeError, ValueError):
        return None
    return p if p > 0 else None


def _good_date(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
    except (TypeError, ValueError):
        return None
    if d > dt.date.today() or d.isoformat() < ANCHOR_FLOOR:
        return None
    return d.isoformat()


@bp.route("/finance/sanjeevni/api/bank/deposit", methods=["POST"])
def api_deposit():
    """The doctors' pool -> Yes Bank, in his own hand. It leaves the pool at once (the one calculation
    reads cash_pool_deposit); the Yes Bank statement proves it later."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso, amt = _good_date(b.get("date")), _amount_p(b.get("amount"))
    if not iso or not amt:
        return jsonify(ok=False, error="bad_entry",
                       message="a date on or after 17-Aug-2026 and not in the future, and an amount"), 400
    con = _db()
    if not _has(con, "cash_pool_deposit"):
        return jsonify(ok=False, error="no_table", message="the cash tables are not installed on this box"), 503
    if con.execute("SELECT 1 FROM cash_pool_deposit WHERE unit=? AND deposit_date=? AND amount_p=?",
                   (_unit, iso, amt)).fetchone():
        return jsonify(ok=False, error="already",
                       message="a deposit of this amount on this date is already recorded"), 409
    who = u.get("user") or "owner"
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT INTO cash_pool_deposit (unit, deposit_date, amount_p, bank, place, evidence, note, "
                "entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (_unit, iso, amt, str(b.get("bank") or "Yes Bank")[:40], str(b.get("place") or "")[:60],
                 "recorded by the owner on the approvals page (S375)", str(b.get("note") or "")[:200], who, now))
    _audit_row(con, who, "pool_deposit", dict(date=iso, amount_p=amt, bank=str(b.get("bank") or "Yes Bank")))
    con.commit()
    return jsonify(ok=True, date=iso, amount=rs(amt))


@bp.route("/finance/sanjeevni/api/bank/transfer", methods=["POST"])
def api_transfer():
    """ICICI -> Yes Bank, or either account -> its own HUF savings. NEVER income, never a day, never the
    cash calculation: this money was counted when it was collected."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso, amt = _good_date(b.get("date")), _amount_p(b.get("amount"))
    frm, to = str(b.get("from") or "").strip(), str(b.get("to") or "").strip()
    if not iso or not amt:
        return jsonify(ok=False, error="bad_entry",
                       message="a date on or after 17-Aug-2026 and not in the future, and an amount"), 400
    if (frm, to) not in ROUTES:
        return jsonify(ok=False, error="bad_route",
                       message="a transfer goes ICICI to Yes Bank, or either account to its own HUF savings"), 400
    con = _db()
    ensure_schema(con)
    if con.execute("SELECT 1 FROM bank_transfer WHERE unit=? AND transfer_date=? AND from_account=? "
                   "AND to_account=? AND amount_p=?", (_unit, iso, frm, to, amt)).fetchone():
        return jsonify(ok=False, error="already",
                       message="this transfer is already recorded"), 409
    short_p = 0
    if frm == "icici":                        # S377 (F-615): our count may be short; the bank is not
        ip = icici_position(con)
        if amt > ip["holds_p"]:
            short_p = amt - max(ip["holds_p"], 0)
    who = u.get("user") or "owner"
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT INTO bank_transfer (unit, transfer_date, from_account, to_account, amount_p, ref, "
                "note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (_unit, iso, frm, to, amt, str(b.get("ref") or "")[:60], str(b.get("note") or "")[:200], who, now))
    _audit_row(con, who, "bank_transfer", dict(date=iso, amount_p=amt, frm=frm, to=to))
    con.commit()
    return jsonify(ok=True, date=iso, amount=rs(amt), frm=ACCOUNTS.get(frm, frm), to=ACCOUNTS.get(to, to),
                   leaves=(to not in INSIDE), short=(rs(short_p) if short_p else ""),
                   message=("Recorded. Our count of ICICI was %s short of this — the account holds money the "
                            "count cannot see until the ICICI statement is read." % rs(short_p)) if short_p else "")


@bp.route("/finance/sanjeevni/api/bank/undo", methods=["POST"])
def api_undo():
    """Remove one entry he made by mistake -- only while no loaded statement shows it."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    kind, rid = str(b.get("kind") or ""), b.get("id")
    con = _db()
    who = u.get("user") or "owner"
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_id"), 400
    if kind == "deposit":
        r = con.execute("SELECT deposit_date, amount_p FROM cash_pool_deposit WHERE id=? AND unit=?",
                        (rid, _unit)).fetchone()
        if not r:
            return jsonify(ok=False, error="not_found"), 404
        if _seen_in_yesbank(con, r[0], int(r[1]), True):
            return jsonify(ok=False, error="confirmed",
                           message="the bank's statement shows this deposit, so it cannot be removed"), 409
        con.execute("DELETE FROM cash_pool_deposit WHERE id=?", (rid,))
        _audit_row(con, who, "pool_deposit_undo", dict(id=rid, date=r[0], amount_p=int(r[1])))
    elif kind == "transfer":
        ensure_schema(con)
        r = con.execute("SELECT transfer_date, amount_p, from_account, to_account FROM bank_transfer "
                        "WHERE id=? AND unit=?", (rid, _unit)).fetchone()
        if not r:
            return jsonify(ok=False, error="not_found"), 404
        if (r[2] == "yesbank" or r[3] == "yesbank") and _seen_in_yesbank(con, r[0], int(r[1]), r[3] == "yesbank"):
            return jsonify(ok=False, error="confirmed",
                           message="the bank's statement shows this transfer, so it cannot be removed"), 409
        con.execute("DELETE FROM bank_transfer WHERE id=?", (rid,))
        _audit_row(con, who, "bank_transfer_undo", dict(id=rid, date=r[0], amount_p=int(r[1])))
    else:
        return jsonify(ok=False, error="bad_kind"), 400
    con.commit()
    return jsonify(ok=True)


@bp.route("/finance/sanjeevni/expiry", methods=["GET"])
def page_expiry():
    """S638 (D780): the owner's Expiry watch -- expired, near expiry, dump (orthotics and medicines), wrong batch, new products,
    out of stock. Read-only; the list is made every night by expiry_watch.run (spine/near_expiry.py)."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    return expiry_watch.owner_page(_db())


@bp.route("/finance/sanjeevni/expiry/settings", methods=["POST"])
def page_expiry_settings():
    """S638: the page's thresholds (the owner's rule of 26-Sep: every threshold a setting he alters on the screen). Audited."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    con = _db()
    saved = expiry_watch.save_settings(con, request.form, u.get("user") or "owner")
    return expiry_watch.owner_page(con, saved=saved)


@bp.route("/finance/sanjeevni/expiry/api/count", methods=["GET"])
def api_expiry_count():
    """S657 (the owner, 26-Oct-2026): the number on his home's Expiry watch box -- the two counts of his Needs-you line
    (expiry_watch.needs_you_lines, the same rule): expired batches still in stock, and batches Marg stops selling on the next 1st.
    Read only; the page itself is unchanged."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    today = expiry_watch.now_ist().date()
    run_, sec = expiry_watch.newest(_db())
    nxt = expiry_watch.ym_add(today.strftime("%Y-%m"), 1)
    on = "1-%s" % expiry_watch.MON[int(nxt[5:7])]
    if not run_:
        resp = jsonify(ok=True, n=0, expired=0, stops=0, stops_on=on, made="", title="No list yet")
    else:
        sec = expiry_watch.now_view(sec, today)
        ex = [x for x in sec.get("expired", []) if (x.get("units") or 0) > 0]
        soon = [x for x in sec.get("near", []) if x.get("expiry") and x["expiry"] <= nxt]
        resp = jsonify(ok=True, n=len(ex) + len(soon), expired=len(ex), stops=len(soon), stops_on=on,
                       made=str(run_.get("at") or "")[:16],
                       title="%d expired \u00b7 %d stop%s selling on %s" % (len(ex), len(soon), "" if len(soon) == 1 else "", on))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.route("/finance/approvals/old")
def page_old():
    u, err = _require("checker")
    if err:
        return err
    return send_from_directory(UI_DIR, "finance_approvals_old.html")


# ---- S446_AMIR_STAGES_BILLS (02-Oct-2026, F-680): lists chosen by STATE, not by the current month -------------------------------------
def _s446_returns_line(con, today):
    """Counter returns waiting for the owner's OK in EVERY open month (the last six), by returns_kinds' own rule (S406: counter
    returns, real items, from returns.act_from -- earlier ones are accepted, S219); the oldest named. None = keep the old path
    (NEEDS_YOU_WITHOUT_S406=1, an older kit's frozen walk) or nothing could be read."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S406") == "1":
        return None
    try:
        import returns_kinds  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
    y, m = int(today[:4]), int(today[5:7])
    months = []
    for _i in range(6):
        months.append("%04d-%02d" % (y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    n, p, dates = 0, 0, []
    try:
        for ym in reversed(months):
            notes = returns_kinds.month_notes(con, _unit, ym)
            s = returns_kinds.enrich(con, _unit, ym, notes, with_prev=False)
            n += int(s.get("pending_ok") or 0)
            p += int(s.get("pending_ok_p") or 0)
            dates += [str(x.get("date"))[:10] for x in notes if x.get("pending_ok") and x.get("date")]
    except Exception:  # noqa: BLE001
        return None
    if not n:
        return {}                                   # read, and nothing waits: no line (and not the old path)
    return dict(cls="warn", target="returns", text="Counter returns waiting for your OK: %d, %s (oldest %s)"
                % (n, rs(p), dmy(min(dates)) if dates else "?"))
# ---- S446_AMIR_STAGES_BILLS end ----


# ---- KIT_S760 (Sanjeevni session 414, 09-Nov-2026, D873): the Needs-you returns line from the CARD'S OWN READ ----------------------------
def _s760_returns_line(con, today):
    """Returns waiting for the owner's OK -- the very read the hub's Returns card makes (returns_kinds.hub, light: the same months,
    the same rule, the same count), so the line and the card never show two different numbers. Fail-soft: if that read fails,
    the S446 line as it was. None = keep the old path (NEEDS_YOU_WITHOUT_S406=1, an older kit's frozen walk)."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S406") == "1":
        return None
    try:
        import returns_kinds  # noqa: PLC0415
        h = returns_kinds.hub(con, _unit, today=today, light=True)
        n, p, old = int(h.get("pending_ok") or 0), int(h.get("pending_ok_p") or 0), h.get("pending_oldest")
    except Exception:  # noqa: BLE001
        return _s446_returns_line(con, today)
    if not n:
        return {}                                   # read, and nothing waits: no line (and not the old path)
    return dict(cls="warn", target="returns", n=n,
                text="Returns waiting for your OK — %d · ₹%s · oldest %s" % (n, rs(p), dmy(old) if old else "?"))
# ---- KIT_S760 end ----


# ---- KIT_S761 (09-Nov-2026, Sanjeevni session 414, kit S761_HUB_NEEDS_GOTO; D873, F-1199): Needs you GROUPED --------------------------
#  The owner's approved hub mock: one line per kind of work, red first, the information folded. The grouping is made HERE so the page,
#  the header count and every walk read one source. needs_you() keeps 'lines' and 'count' exactly as they were (owner_console and older
#  walks read them); it only GAINS 'groups', 'n_items', 'n_groups'. Every line lands in exactly one group -- nothing is dropped, nothing is
#  doubled (the walk proves it). If the grouping fails the answer is the old one, without 'groups', and the page draws the old flat list.
import re as _re761

S761_TITLES = (("days", "Days to approve"), ("returns", "Returns"), ("orders", "Orders"),
               ("arrived", "Arrived but not in Marg's purchases"), ("papers", "Bills & papers"), ("stock", "Stock count"),
               ("marg", "Marg & bank details"), ("bank", "Bank & statements"), ("darpan", "Darpan"), ("expiry", "Expiry watch"),
               ("other", "Other"), ("info", "For your information"))
_S761_ARR = _re761.compile(r"^(?P<item>.+?): counted as arrived when (?:the (?P<v1>.+?) bill was scanned|.+? tapped it [^(]*\((?P<v2>[^)]*)\))")
_S761_NOTE = _re761.compile(r"\((its bill [^)]*)\)\s*$")
# A grey line is information ONLY when it asks nothing of him: no action of its own (a one-tap id, a button, a link) and no words that ask
# for a decision. order_rules' Kedar review (its 'Move to weekly' button) and the freeze, porders' 'Buying rules ... await your approval',
# scan_register's 'Paper not found ... your tap accepts it', order_sheet's 'add it in the phone book' -- all grey at their source, all work.
_S761_PLAIN = ("cls", "target", "text")
_S761_ASKS = _re761.compile(r"(?i)your tap|\btap (?:to|here)\b|\bapprov|\baccept|\bfrozen\b|\bfreeze|\badd it\b|\btype\b|\bconfirm\b|\bdecide|\bpick\b|\bpress\b|\bOK\?")
_S761_BY_TARGET = {"porders": "orders", "weekly": "orders", "scans": "papers", "stock": "stock", "checks-marg": "marg", "bank": "bank",
                   "checks-kal": "darpan", "expiry": "expiry", "days": "days", "returns": "returns"}


def s761_is_info(l):
    """Grey and asking nothing: the only lines the information fold may hold."""
    if l.get("cls") != "info":
        return False
    if any(k not in _S761_PLAIN and l.get(k) not in (None, "", False) for k in l):
        return False                                     # an action of its own (review_supplier, neft_event, href, a button ...)
    return not _S761_ASKS.search(str(l.get("text") or ""))


def _s761_key(l):
    """The one group a line belongs to -- the first rule that fits wins."""
    t = str(l.get("text") or "")
    tg = str(l.get("target") or "")
    if "counted as arrived when" in t:
        return "arrived"
    if tg == "returns":
        return "returns"
    if tg == "days":
        return "days"
    if s761_is_info(l):
        return "info"
    if l.get("cls") == "info":                           # grey but it asks him something: the work group of its source
        return _S761_BY_TARGET.get(tg, "other")
    if tg == "checks-kal" or t.startswith("Claim for Darpan") or "owed back to Darpan" in t:
        return "darpan"
    if tg == "expiry":
        return "expiry"
    if tg == "stock":
        return "stock"
    if tg == "scans":
        return "papers"
    if tg in ("porders", "weekly") or "supplier message" in t:
        return "orders"
    if tg == "checks-marg":
        return "marg"
    if tg == "bank":
        return "bank"
    return "other"


def _s761_arrived(lines):
    """'Yuvika 8 · Kedar 3' -- the dealers, most items first; each item's own line kept whole for the fold."""
    by, order = {}, []
    for l in lines:
        m = _S761_ARR.match(str(l.get("text") or ""))
        item = (m.group("item") if m else str(l.get("text") or "")).strip()
        v = ((m.group("v1") or m.group("v2")) if m else "") or "the supplier's"
        v = v.strip() or "-"
        if v not in by:
            by[v] = []
            order.append(v)
        nm = _S761_NOTE.search(str(l.get("text") or ""))
        by[v].append(dict(item=item, text=str(l.get("text") or ""), size=bool(nm), note=(nm.group(1) if nm else "")))
    vend = sorted(order, key=lambda k: (-len(by[k]), order.index(k)))
    return [dict(vendor=k, n=len(by[k]), items=by[k]) for k in vend]


def s761_groups(lines):
    """The lines, in groups: red groups first, then amber, information last; inside a colour the fixed order above."""
    keyed = {}
    for i, l in enumerate(lines):
        keyed.setdefault(_s761_key(l), []).append((i, l))
    rank = {k: n for n, (k, _t) in enumerate(S761_TITLES)}
    out = []
    for k, title in S761_TITLES:
        got = keyed.get(k)
        if not got:
            continue
        ls = [l for _i, l in got]
        cls = "info" if k == "info" else ("bad" if any(l.get("cls") == "bad" for l in ls) else "warn")
        g = dict(key=k, title=title, cls=cls, n=len(ls), idx=[i for i, _l in got], lines=ls)
        if k == "arrived":
            g["vendors"] = _s761_arrived(ls)
            g["summary"] = " · ".join("%s %d" % (v["vendor"], v["n"]) for v in g["vendors"])
        else:
            g["summary"] = " · ".join(str(l.get("text") or "") for l in ls[:3]) + (" · and %d more" % (len(ls) - 3) if len(ls) > 3 else "")
        out.append(g)
    out.sort(key=lambda g: (0 if g["cls"] == "bad" else (2 if g["cls"] == "info" else 1), rank[g["key"]]))
    return out


_needs_you_before_s761 = needs_you


def needs_you(con):                                      # noqa: F811 -- S761: the same answer, plus its groups
    r = _needs_you_before_s761(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S761") == "1":     # set ONLY by an older kit's frozen walk re-run; the service never sets it
        return r
    try:
        g = s761_groups(r.get("lines") or [])
        if sum(x["n"] for x in g) != len(r.get("lines") or []):
            raise ValueError("a line was lost or doubled")
        work = [x for x in g if x["key"] != "info"]
        r.update(groups=g, n_items=sum(x["n"] for x in work), n_groups=len(work),
                 n_info=sum(x["n"] for x in g if x["key"] == "info"))   # the header counts what needs him; the information is counted in its own fold
    except Exception as e:                               # noqa: BLE001 -- the old answer stands; the page draws the flat list
        r["groups_error"] = str(e)[:120]
    return r
# ---- KIT_S761 end ---------------------------------------------------------------------------------------------------------------------


# ---- S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463): one Needs-you line while a Stock Register asked by the owner is not in --
#  its href opens his list (/finance/sanjeevni/marg-watch/take). Added to the lines BEFORE S761 groups them (group 'Marg & bank details').
#  NEEDS_YOU_WITHOUT_S837=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it. Fail-soft.
_needs_you_before_s837 = _needs_you_before_s761


def _needs_you_before_s761(con):                         # noqa: F811 -- S837: S761's grouping reads this name at call time
    r = _needs_you_before_s837(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S837") == "1":
        return r
    try:
        import marg_billwatch as _bw837                      # noqa: PLC0415
        add = _bw837.reg_needs_lines(con)
        if add:
            r["lines"] = list(r.get("lines") or []) + add
            r["count"] = int(r.get("count") or 0) + len(add)
    except Exception:                                    # noqa: BLE001
        pass
    return r
# ---- S837 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995): one Needs-you line while a pharmacy scan is not found in Marg past the days
#  (scan_ask.needs_lines; target 'scans' -> S761's group 'Bills & papers'); its href opens /finance/sanjeevni/not-in-marg. Added BEFORE S761 groups.
#  NEEDS_YOU_WITHOUT_S849=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it. Fail-soft.
_needs_you_before_s849 = _needs_you_before_s761


def _needs_you_before_s761(con):                         # noqa: F811 -- S849: S761's grouping reads this name at call time
    r = _needs_you_before_s849(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S849") == "1":
        return r
    try:
        import scan_ask as _sa849                            # noqa: PLC0415
        add = _sa849.needs_lines(con)
        if add:
            r["lines"] = list(r.get("lines") or []) + add
            r["count"] = int(r.get("count") or 0) + len(add)
    except Exception:                                    # noqa: BLE001
        pass
    return r
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------
