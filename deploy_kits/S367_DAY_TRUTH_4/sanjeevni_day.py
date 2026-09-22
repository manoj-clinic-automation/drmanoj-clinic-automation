#!/usr/bin/env python3
# =============================================================================
#  sanjeevni_day.py  ·  v1.1  ·  kit S367_DAY_TRUTH_4  ·  Session 281 (Sanjeevni)
#  v1.1 (S367, F-613 / D602, 22-Sep-2026): the checks say HOW the day was filed -- automatically
#  from which Marg export, at what time, or by whom -- and whether a later export, the resync or
#  a person changed it since; a day with a pool deposit says whether the Yes Bank statement
#  shows it. No login name stands in for the source any more ("entered by manoj" was the
#  autofile running under his login). v1.0: kit S365_DAY_PANEL, Session 280.
#
#  ONE COUNTER DAY, AS THE OWNER READS IT (his words, 21-Sep-2026: "simple, human
#  readable, expandable ... which sale returns were there, what were the sales").
#
#      Sale (Marg)                 bills  -> each bill -> its medicines
#       - Sale returns             credit notes -> their medicines
#       - Paid by UPI              the bank's own payments
#       - Without cash             home / procedure medicine bills
#       = Cash received            (the owner's figure: 15-Sep = 11,291)
#       + a home-medicine return put back / - paid from the drawer   (only if any)
#       = Cash for the drawer      and where it went (pool on approval)
#      Checks, in words.  Needs you, in words -- or "nothing needs you".
#
#  Every figure is READ; nothing here writes. The money arithmetic is the one
#  calculation's (sanjeevni_cash): the day's drawer cash here equals its row there,
#  and the walk proves it for every day.
#  GET /finance/sanjeevni/api/day/<YYYY-MM-DD>   -- checker (the owner) only.
# =============================================================================
import datetime as dt
import sqlite3

from flask import Blueprint, jsonify

VERSION = "1.1"
bp = Blueprint("sanjeevni_day", __name__)
_db = _require = None
_unit = "medical"
HEADS = {"home_medicine": "Home medicine", "procedure_medicine": "Procedure medicine", "other": "Other, without cash"}


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def _cols(con, t):
    return {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}


def _stamp(st):
    """Marg's export stamp 20260905-085353 -> '08:53 on 05-Sep'."""
    try:
        t = dt.datetime.strptime(str(st)[:15], "%Y%m%d-%H%M%S")
        return t.strftime("%H:%M on %d-%b")
    except (TypeError, ValueError):
        return str(st or "?")


def _at(iso):
    try:
        return dt.datetime.fromisoformat(str(iso)[:19]).strftime("%H:%M on %d-%b")
    except (TypeError, ValueError):
        return str(iso or "?")


def filing_story(con, eid, iso, unit, entered_by):
    """In words: how this day came to be, and what changed it since (S367). Returns a list of
    check dicts. Reads audit_log, sale_bill_push and sale_bill; writes nothing."""
    import json as _json
    out = []
    rows = con.execute("SELECT action, by_whom, at, before_json, after_json FROM audit_log "
                       "WHERE table_name='day_entry' AND row_id=? ORDER BY id", (eid,)).fetchall()
    auto = next((r for r in rows if r[0] == "autofile"), None)
    if auto:
        a = {}
        try:
            a = _json.loads(auto[4] or "{}")
        except ValueError:
            pass
        push = None
        if a.get("from_push") and _has(con, "sale_bill_push"):
            push = con.execute("SELECT export_stamp, days_json, bills FROM sale_bill_push WHERE md5 LIKE ?",
                               (str(a["from_push"]) + "%",)).fetchone()
        src = ("Marg's export of %s" % _stamp(push[0])) if push else "Marg's sale report"
        if push and push[1] and len(_json.loads(push[1] or "[]")) == 1:
            src += " (%d bills)" % int(push[2] or 0)
        out.append(dict(ok=True, text="filed automatically at %s from %s, net sale %s -- nobody typed it"
                                      % (_at(auto[2]), src, rs(a.get("net_p")))))
    elif rows and rows[0][0] == "create":
        out.append(dict(ok=True, text="filed on the old form by %s at %s" % (rows[0][1] or entered_by or "?", _at(rows[0][2]))))
    for act, who, at, b, af in rows:
        try:
            bj, aj = _json.loads(b or "{}"), _json.loads(af or "{}")
        except ValueError:
            bj, aj = {}, {}
        if act == "resync_marg":
            out.append(dict(ok=True, text="brought up to Marg's later export (%s, %s bills) at %s: cash %s -> %s"
                                          % (_stamp(aj.get("marg_export")), aj.get("marg_bills", "?"), _at(at),
                                             rs(bj.get("cash_p")), rs(aj.get("cash_p")))))
        elif act == "resync_upi":
            out.append(dict(ok=True, text="UPI set to the bank's statement at %s: %s -> %s"
                                          % (_at(at), rs(bj.get("upi_p")), rs(aj.get("upi_p")))))
        elif act == "correct":
            why = aj.get("ruling") or aj.get("reason") or ""
            last = out[-1] if out else None
            if not why and last is not None and last.get("_by") == who and not last.get("_why"):
                last["_n"] += 1; last["_to"] = at
                last["text"] = "corrected %d times by %s, %s to %s" % (last["_n"], who or "?", _at(last["_from"]), _at(at))
                continue
            out.append(dict(ok=True, text="corrected by %s at %s%s" % (who or "?", _at(at), (" -- " + str(why)[:160]) if why else ""),
                            _by=who, _why=why, _n=1, _from=at, _to=at))
    if _has(con, "sale_bill"):
        r = con.execute("SELECT COUNT(*), MAX(source_stamp) FROM sale_bill WHERE unit=? AND business_date=?",
                        (unit, iso)).fetchone()
        if auto and r and r[0]:
            first = None
            try:
                first = _json.loads(auto[4] or "{}").get("from_push")
            except ValueError:
                pass
            p2 = con.execute("SELECT md5 FROM sale_bill_push WHERE export_stamp=? LIMIT 1", (r[1],)).fetchone() \
                if _has(con, "sale_bill_push") else None
            if first and p2 and not str(p2[0]).startswith(str(first)):
                out.append(dict(ok=None, text="Marg's bills for this day now come from its later export of %s (%d bills)"
                                              % (_stamp(r[1]), int(r[0]))))
    for c in out:
        for k in ("_by", "_why", "_n", "_from", "_to"):
            c.pop(k, None)
    return out


def deposit_story(con, iso, unit):
    """A pool deposit on this day, and whether the Yes Bank statement shows it (S367)."""
    out = []
    if not _has(con, "cash_pool_deposit"):
        return out
    for amt, bank, place in con.execute("SELECT amount_p, bank, place FROM cash_pool_deposit WHERE unit=? "
                                        "AND deposit_date=?", (unit, iso)):
        seen = _has(con, "bank_statement_line") and con.execute(
            "SELECT 1 FROM bank_statement_line WHERE is_cash_deposit=1 AND deposit_p=? AND txn_date BETWEEN ? AND ?",
            (amt, iso, (dt.date.fromisoformat(iso) + dt.timedelta(days=3)).isoformat())).fetchone()
        covered = _has(con, "bank_statement_period") and con.execute(
            "SELECT 1 FROM bank_statement_period WHERE period_from<=? AND period_to>=?", (iso, iso)).fetchone()
        where = " at %s" % place if place else ""
        if seen:
            out.append(dict(ok=True, text="%s deposited from the pool%s -- confirmed in the %s statement"
                                          % (rs(int(amt)), where, bank or "bank")))
        elif covered:
            out.append(dict(ok=False, text="%s deposited from the pool%s -- the %s statement for this date does NOT show it"
                                           % (rs(int(amt)), where, bank or "bank")))
        else:
            out.append(dict(ok=None, text="%s deposited from the pool%s -- no %s statement covers this date yet"
                                          % (rs(int(amt)), where, bank or "bank")))
    return out


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
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


def day_view(con, iso, unit="medical"):
    e = con.execute("SELECT id, status, approved_by, approved_at, entered_by FROM day_entry "
                    "WHERE unit=? AND business_date=?", (unit, iso)).fetchone()
    try:
        wd = dt.date.fromisoformat(iso).strftime("%A")
    except ValueError:
        return dict(ok=False, error="bad_date")
    if not e:
        return dict(ok=True, date=iso, weekday=wd, filed=False,
                    needs_you=["This day has not been filed from Marg yet."])
    eid, status = e[0], e[1]
    v = con.execute("SELECT revenue_p, upi_in_p, cash_in_p, noncash_p, cash_back_p, adjust_p FROM v_day_cash "
                    "WHERE day_entry_id=?", (eid,)).fetchone()
    revenue, upi_books, cash_in, noncash_p, back_p, adjust_p = (int(x or 0) for x in v)

    # ---- the bills, as Marg printed them -----------------------------------
    items = {}
    for b, ret, name, pack, qty, amt, exp, batch in con.execute(
            "SELECT bill_no, is_return, item_name, pack, qty_raw, amount_p, expiry_ym, batch FROM sale_line_item "
            "WHERE day_entry_id=? ORDER BY bill_no, seq", (eid,)):
        items.setdefault(str(b or "?"), []).append(dict(item=name, pack=pack, qty=qty, amount=rs(int(amt or 0)),
                                                        batch=batch, expiry=exp))
    names = {}
    for b, nm, cid in con.execute("SELECT s.source_ref, p.name, p.clinic_id FROM sale_item s "
                                  "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id WHERE s.day_entry_id=?", (eid,)):
        if b and (nm or cid):
            names[str(b)] = (nm or "") + ((" · #%s" % cid) if cid else "")
    nc_by_bill = {}
    for b, head, text, amt in con.execute("SELECT bill_no, head, head_text, amount_p FROM day_noncash_bill "
                                          "WHERE day_entry_id=?", (eid,)):
        nc_by_bill[str(b or "")] = (head, text, int(amt or 0))
    source = "marg"
    bills = []
    if _has(con, "sale_bill") and con.execute("SELECT 1 FROM sale_bill WHERE unit=? AND business_date=? LIMIT 1",
                                              (unit, iso)).fetchone():
        for b, net, cn in con.execute("SELECT bill_no, net_p, is_credit_note FROM sale_bill WHERE unit=? AND "
                                      "business_date=? ORDER BY bill_no", (unit, iso)):
            bills.append(dict(bill=b, amount_p=int(net or 0), is_return=bool(cn)))
    else:                                              # before 17-Aug: the books' own bill rows
        source = "books"
        for b, amt, svc in con.execute("SELECT source_ref, amount_p, service FROM sale_item WHERE day_entry_id=? "
                                       "ORDER BY source_ref", (eid,)):
            r = "return" in (svc or "")
            bills.append(dict(bill=b, amount_p=-int(amt or 0) if r else int(amt or 0), is_return=r))
    adj_reasons = [str(r or "") for (r,) in con.execute("SELECT reason FROM cash_adjustment WHERE day_entry_id=?", (eid,))]
    unnamed = []
    for x in bills:
        k = str(x["bill"] or "")
        nc = nc_by_bill.get(k)
        x["name"] = names.get(k) or (HEADS.get(nc[0], "") + ((" -- " + nc[1]) if nc and nc[1] else "") if nc else "")
        x["amount"] = rs(x["amount_p"])
        x["items"] = items.get(k, [])
        if not x["name"] and x["is_return"] and any(k and k in r for r in adj_reasons):
            x["name"] = "Home-medicine return -- goods back, no cash refunded"
        if not x["name"]:
            unnamed.append(x)
    sales = [x for x in bills if not x["is_return"]]
    rets = [x for x in bills if x["is_return"]]
    sale_p = sum(x["amount_p"] for x in sales)
    ret_p = -sum(x["amount_p"] for x in rets)
    marg_net = sale_p - ret_p

    # ---- the bank's UPI ---------------------------------------------------
    st = con.execute("SELECT parsed_total_p, txn_count FROM upi_statement WHERE unit=? AND statement_date=?",
                     (unit, iso)).fetchone()
    pays = [dict(time=(t or "")[:5], amount=rs(int(a or 0)), ref=("..." + str(r)[-4:]) if r else "")
            for t, a, r in con.execute("SELECT txn_time, amount_p, rrn FROM upi_txn WHERE unit=? AND txn_date=? "
                                       "ORDER BY txn_time", (unit, iso))]

    # ---- without cash, rulings, adjustments, expenses ----------------------
    rul = {}
    if _has(con, "cash_bill_ruling"):
        for b, amt, place in con.execute("SELECT bill_no, amount_p, received_at_place FROM cash_bill_ruling "
                                         "WHERE unit=? AND business_date=?", (unit, iso)):
            rul[str(b)] = (int(amt), place)
    without = [dict(bill=b, head=HEADS.get(h, h), note=t or "", amount=rs(a))
               for b, (h, t, a) in nc_by_bill.items() if b not in rul]
    without_p = sum(a for b, (h, t, a) in nc_by_bill.items() if b not in rul)
    elsewhere = [dict(bill=b, amount=rs(a), place=(p or "").replace("_", " ")) for b, (a, p) in rul.items()]
    elsewhere_p = sum(a for a, _ in rul.values())
    adjs = [dict(amount=rs(int(a or 0)), why=((r or "").split(" (")[0].replace("home medicine credit note", "home-medicine return")
                                               .replace(": goods returned, no cash moved", " -- goods back, no cash refunded"))[:140])
            for a, r in con.execute("SELECT amount_p, reason FROM cash_adjustment WHERE day_entry_id=?", (eid,))]
    exps = [dict(amount=rs(int(a or 0)), what=(t or c or "expense"))
            for a, c, t in con.execute("SELECT amount_p, category_fixed, category_text FROM day_expense "
                                       "WHERE day_entry_id=? AND amount_known=1", (eid,))]

    cash_received_p = revenue - upi_books - without_p          # the owner's figure (15-Sep: 11,291)
    # ---- the one calculation's own row: the drawer and where the cash went --
    drawer_p, went = None, None
    try:
        import sanjeevni_cash as sc
        r = sc.days(con, iso, iso, unit)
        if r.get("ok") and r["rows"]:
            row = r["rows"][0]
            drawer_p = row["into_drawer_p"]
            cov = []
            if _has(con, "cash_handover_cover"):
                for src, hid, amt in con.execute("SELECT handover_src, handover_id, amount_p FROM cash_handover_cover "
                                                 "WHERE unit=? AND covers_date=?", (unit, iso)):
                    if src == "movement":
                        t = con.execute("SELECT m.party, e.business_date FROM cash_movement m JOIN day_entry e "
                                        "ON e.id=m.day_entry_id WHERE m.id=?", (hid,)).fetchone()
                    else:
                        t = con.execute("SELECT to_party, event_date FROM cash_custody_event WHERE id=?", (hid,)).fetchone()
                    if t:
                        cov.append("%s handed to %s on %s" % (rs(int(amt)), {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you",
                                                                             "pool": "the pool", "bank": "the bank"}.get(t[0], t[0]),
                                                              dt.date.fromisoformat(t[1]).strftime("%d-%b")))
            if cov:
                went = "; ".join(cov)
            elif row["handed"]:
                went = "; ".join("%s to %s" % (rs(h["amount_p"]), {"pool": "the pool (you approved this day)",
                                                                  "dr_bhawna": "Dr Bhawna", "dr_manoj": "you",
                                                                  "bank": "the bank"}.get(h["to"], h["to"]))
                                 for h in row["handed"])
            elif row.get("waiting_approval"):
                went = "in Darpan's drawer -- approve the day and it goes to the pool"
    except Exception:                                         # noqa: BLE001
        pass

    # ---- checks and needs-you, in words ------------------------------------
    checks, needs = [], []
    if source == "marg":
        if marg_net == revenue:
            checks.append(dict(ok=True, text="Marg's bills add up to the day's sale"))
        else:
            checks.append(dict(ok=False, text="Marg's bills come to %s; the day was filed at %s -- %s apart"
                               % (rs(marg_net), rs(revenue), rs(abs(marg_net - revenue)))))
            needs.append("The day's sale (%s) is not what Marg's bills add up to (%s)." % (rs(revenue), rs(marg_net)))
    if st:
        bank_p = int(st[0] or 0)
        if bank_p == upi_books:
            checks.append(dict(ok=True, text="the bank confirms the UPI (%d payments)" % int(st[1] or 0)))
        else:
            checks.append(dict(ok=False, text="the bank settled %s by UPI; the day shows %s" % (rs(bank_p), rs(upi_books))))
            needs.append("UPI differs from the bank by %s." % rs(abs(bank_p - upi_books)))
    elif upi_books:
        checks.append(dict(ok=None, text="the bank's UPI statement for this day has not arrived yet"))
    if unnamed:
        checks.append(dict(ok=None, text="%d bill(s) carry no patient name (%s) -- the money is counted in full"
                                         % (len(unnamed), rs(sum(x["amount_p"] for x in unnamed)))))
    for kind, detail in con.execute("SELECT kind, detail FROM recon_exception WHERE unit=? AND business_date=? "
                                    "AND status='open' AND kind NOT IN ('line_sum_vs_day_total','upi_vs_statement',"
                                    "'missing_day','clinic_holiday')", (unit, iso)):
        if kind == "return_flagged":
            continue                                       # the returns card owns these
        needs.append((detail or kind)[:200])
    try:                                                     # S367: how the day was filed, and deposits
        for c in deposit_story(con, iso, unit):
            checks.append(c)
            if c["ok"] is False:
                needs.append(c["text"][:200])
        checks[0:0] = filing_story(con, eid, iso, unit, e[4])
    except Exception:                                         # noqa: BLE001 -- words only; never breaks the panel
        pass
    return dict(ok=True, date=iso, weekday=wd, filed=True, status=status, approved_by=e[2],
                source=source,
                sale=dict(total=rs(sale_p), bills=len(sales), list=sales),
                returns=dict(total=rs(ret_p), count=len(rets), list=rets),
                upi=dict(total=rs(upi_books), payments=pays, bank_total=(rs(int(st[0] or 0)) if st else None)),
                without_cash=dict(total=rs(without_p), list=without),
                paid_elsewhere=dict(total=rs(elsewhere_p), list=elsewhere),
                cash_received=rs(cash_received_p), cash_received_p=cash_received_p,
                adjustments=adjs, adjust_total=rs(adjust_p + back_p) if (adjust_p or back_p) else None,
                expenses=exps,
                drawer=rs(drawer_p) if drawer_p is not None else None, drawer_p=drawer_p, went=went,
                checks=checks, needs_you=needs)


@bp.route("/finance/sanjeevni/api/day/<iso>")
def api_day(iso):
    u, err = _require("checker")
    if err:
        return err
    return jsonify(day_view(_db(), iso, _unit))
