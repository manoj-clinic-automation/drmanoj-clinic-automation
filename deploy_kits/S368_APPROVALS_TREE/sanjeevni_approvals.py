#!/usr/bin/env python3
# =============================================================================
#  sanjeevni_approvals.py  ·  v1.0  ·  kit S368_APPROVALS_TREE  ·  Session 281 (Sanjeevni)
#
#  THE APPROVALS PAGE AS ONE TREE (D591 finished; D603, the owner, 22-Sep-2026: one page,
#  the audit material a collapsed section on it, never a second page). This module is the
#  page's read door. It composes SENTENCES on the server (D349) and reads every rupee from
#  the one cash calculation (sanjeevni_cash, D600). It writes nothing.
#
#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target
#      GET /finance/sanjeevni/api/days           one line per filed day from the anchor
#      GET /finance/sanjeevni/api/bank?month=    the pharmacy's UPI by day; the Yes Bank statement
#      GET /finance/sanjeevni/api/months         the months, one Marg figure named for its days
#      GET /finance/approvals/old                the page as it was (finance_approvals_old.html)
#  checker (the owner) only.
# =============================================================================
import datetime as dt
import os

from flask import Blueprint, jsonify, request, send_from_directory

VERSION = "1.0"
bp = Blueprint("sanjeevni_approvals", __name__)
_db = _require = None
_unit = "medical"
HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.environ.get("FINANCE_UI_DIR", os.path.join(HERE, "finance_ui"))
ANCHOR_FLOOR = "2026-08-17"
DEP_KINDS = ("deposit_not_in_bank", "bank_deposit_not_booked", "deposit_unevidenced")


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
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


def day_lines(con):
    rows, meta = _cash_rows(con)
    if not rows:
        return dict(ok=False, error=meta.get("error", "no_rows"), message=meta.get("message", ""), days=[])
    marg = _marg_net(con)
    kal = _kal_rows(con)
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
                        waiting_approval=bool(x["waiting_approval"])))
    close = rows[-1]["close"]
    return dict(ok=True, days=out, anchor=ANCHOR_FLOOR,
                position=dict(drawer=rs(close["drawer"]), pool=rs(close["pool"]),
                              with_doctors=rs(close["with_doctors"]), bank=rs(close["bank"])))


# ------------------------------------------------------------------ the bank
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
        deposits.append(dict(date=x["date"], day=dmy(x["date"]), amount=rs(x["amount_p"]), place=x["place"] or "",
                             source="pool", status=st, text=txt))
    for k in lines:
        if k["id"] not in used:
            deposits.append(dict(date=k["date"], day=dmy(k["date"]), amount=rs(k["amount_p"]), place="",
                                 source="bank", status="bad", text="the bank received it; the books have no deposit for it"))
    deposits.sort(key=lambda z: z["date"])
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),
                statement=period, deposits=deposits,
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
    return dict(ok=True, months=out)


# ------------------------------------------------------------------ needs you
def _returns_pending(con, ym):
    """The returns of the month that wait for the owner's OK -- the same rule as cn-detail (S220)."""
    try:
        from finance_returns_audit import returns_for_day  # noqa: PLC0415
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
    days = [r[0] for r in con.execute("SELECT DISTINCT business_date FROM sale_line_item WHERE unit=? AND is_return=1 "
                                      "AND substr(business_date,1,7)=? UNION SELECT DISTINCT e.business_date FROM sale_item s "
                                      "JOIN day_entry e ON e.id=s.day_entry_id WHERE s.unit=? AND s.service LIKE '%_return' "
                                      "AND substr(e.business_date,1,7)=?", (_unit, ym, _unit, ym))]
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
    # 3 · returns waiting for his OK, this month
    rp = _returns_pending(con, today[:7])
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


@bp.route("/finance/approvals/old")
def page_old():
    u, err = _require("checker")
    if err:
        return err
    return send_from_directory(UI_DIR, "finance_approvals_old.html")
