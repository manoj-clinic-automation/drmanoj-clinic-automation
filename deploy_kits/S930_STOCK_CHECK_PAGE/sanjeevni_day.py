#!/usr/bin/env python3
# =============================================================================
#  sanjeevni_day.py  ·  v1.4  ·  kit S874_HUB_SHORT_MOBILE_CALL  ·  Session 482 (Sanjeevni), 18-Nov-2026
#  v1.4 (S874, his words 13:41): the day names its OWN short (cash for the drawer less what left it) with the two
#  answers, Accept (write off) / Add an entry; every bill and return carries the patient's FULL mobile -- the
#  patient record's, else the Call Console's patient mirror by clinic ID (read-only, as his 'not in Docterz' list
#  reads it; his page only -- the checker's door); the Hub puts a Call button beside it (the portal's own
#  click-to-call). v1.3 was S869.
#  v1.3 (S869): the owner's day panel says WHO a bill was typed to and WHAT was sold -- every without-cash
#  bill carries the name EXACTLY as Darpan typed it in Marg ('PROSIJER ...', 'HOME MEDI ...') and its medicines
#  with each line's value (strips:tabs x the strip rate); every sale return carries the patient as typed, the
#  clinic ID and the mobile (his own page: the full number), its lines and their values, and the key the
#  Returns card's own verdict is read by (the Hub joins /finance/darpan/api/cn-hub by it -- one check, one
#  Approve / Reject, two places).  His own entries on the day (hub_cash: money into another account, cash
#  taken out) are listed; the drawer figure is the one calculation's, entries and accepted shorts included.
#  v1.2 was kit S400_MEDICAL_SALE_CHECK, Session 283.
#  v1.2 (S400, D616, 25-Sep-2026): the Checks also say what Bhati found when he checked the day against
#  the paper copy and Marg -- his verdict, his galti list, the cash he entered (sale_check.owner_checks,
#  fail-soft). v1.1 was kit S367_DAY_TRUTH_4, Session 281.
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
import os
import sqlite3

from flask import Blueprint, jsonify

VERSION = "1.4"
bp = Blueprint("sanjeevni_day", __name__)
_db = _require = None
_unit = "medical"
HEADS = {"home_medicine": "Home medicine", "procedure_medicine": "Procedure medicine", "other": "Other, without cash"}


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    try:                                                     # S869: the owner's entries and the drawer's reasons (hub_cash.py)
        import hub_cash
        hub_cash.init(app, db_getter, require_fn, unit)
    except Exception as ex:                                  # noqa: BLE001 -- the panel then shows no entries
        print("hub_cash not mounted: %s" % ex)
    try:                                                     # S927: the Needs-you lines' inline panels and doors (hub_panels.py)
        import hub_panels
        hub_panels.init(app, db_getter, require_fn, unit)
    except Exception as ex:                                  # noqa: BLE001 -- the lines then open their pages, as before
        print("hub_panels not mounted: %s" % ex)
    try:                                                     # S930: the owner's Stock check page (stock_check.py) -- Marg against the shelf
        import stock_check
        stock_check.init(app, db_getter, require_fn, unit)
    except Exception as ex:                                  # noqa: BLE001 -- the old stock pages then stand as before
        print("stock_check not mounted: %s" % ex)
    try:                                                     # S876: the patient's record inline (patient_events.py)
        import patient_events
        patient_events.init(app, db_getter, require_fn, unit)
    except Exception as ex:                                  # noqa: BLE001 -- the Hub then says the record could not be opened
        print("patient_events not mounted: %s" % ex)
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


def line_value_p(qty_raw, pack, rate_p):
    """S869: a Marg line's value in paise. qty_raw is 'strips:tabs' ('0:7', '1:4') or a plain count ('1.0');
    pack '1*10' names the tabs per strip; the rate is per strip. None when it cannot be read."""
    try:
        per = 1
        p = str(pack or "")
        if "*" in p:
            per = int(float(p.split("*")[-1].strip())) or 1
        q = str(qty_raw or "").strip()
        if ":" in q:
            s, t = q.split(":", 1)
            units = float(s or 0) + float(t or 0) / per
        else:
            units = float(q or 0)
        return int(round(units * int(rate_p or 0)))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


CONSOLE_DB = os.environ.get("NID_CONSOLE_DB", "/root/wa/console.db")


def _m10(s):
    import re
    d = re.sub(r"\D", "", str(s or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d[0] in "6789" else ""


def mobiles_by_cid(cids, path=None):
    """S874: {clinic_id: [10-digit mobiles]} from the Call Console's patient mirror, read-only; {} when it cannot be read.
    The same read as not_in_docterz.mobiles (the parent's; his page only)."""
    import re
    want = {str(c).strip() for c in cids if c}
    out = {}
    p = path or CONSOLE_DB
    if not want or not os.path.exists(p):
        return out
    try:
        c2 = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=5)
        try:
            for ph, cid in c2.execute("SELECT phone10, clinic_id FROM patients"):
                c = str(cid if cid is not None else "").strip()
                if re.match(r"^\d+\.0$", c):
                    c = c[:-2]
                m = _m10(ph)
                if m and c in want and m not in out.setdefault(c, []):
                    out[c].append(m)
        finally:
            c2.close()
    except sqlite3.Error:
        return {}
    return out


def typed_names(con, eid, iso, unit="medical"):
    """S869: {bill_no: the customer text EXACTLY as Darpan typed it in Marg} -- from the review queue (a bill with no
    ID and no phone), the ingest's own bill text for a laddered bill (identity_resolution) and for a name that
    disagreed with its ID (identity_dispute). Writes nothing."""
    import json as _json
    out = {}
    if _has(con, "sale_item_review"):
        for raw, guess in con.execute("SELECT raw_text, guess_name FROM sale_item_review WHERE day_entry_id=? ORDER BY id", (eid,)):
            try:
                r = _json.loads(raw or "{}")
            except ValueError:
                r = {}
            b = str(r.get("bill_no") or "").strip()
            t = (r.get("patient_name") or guess or "").strip()
            if b and t and b not in out:
                out[b] = t
    for tbl in ("identity_resolution", "identity_dispute"):
        if not _has(con, tbl):
            continue
        for b, t in con.execute("SELECT bill_no, bill_name FROM %s WHERE unit=? AND business_date=? ORDER BY id" % tbl, (unit, iso)):
            b, t = str(b or "").strip(), (t or "").strip()
            if b and t and b not in out:
                out[b] = t
    return out


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
        vp = line_value_p(qty, pack, amt)                    # S869: the line's value (the amount is the strip rate)
        items.setdefault(str(b or "?"), []).append(dict(item=name, pack=pack, qty=qty, amount=rs(int(amt or 0)),
                                                        value=rs(vp) if vp is not None else None, value_p=vp,
                                                        batch=batch, expiry=exp))
    names, who = {}, {}
    pcols = _cols(con, "patient_ref")
    mob_sql = ("p.mobile" if "mobile" in pcols else "NULL") + ", " + ("p.phone_last4" if "phone_last4" in pcols else "NULL")
    for b, nm, cid, mob, l4 in con.execute("SELECT s.source_ref, p.name, p.clinic_id, %s FROM sale_item s "
                                           "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id WHERE s.day_entry_id=?" % mob_sql, (eid,)):
        if b and (nm or cid):
            names[str(b)] = (nm or "") + ((" · #%s" % cid) if cid else "")
            who[str(b)] = dict(name=nm or "", clinic_id=cid or "", mobile=(mob or (("..." + str(l4)) if l4 else "")))
    typed = {}
    try:                                                     # S869: the text as Darpan typed it
        typed = typed_names(con, eid, iso, unit)
    except Exception:                                         # noqa: BLE001 -- words only
        typed = {}
    mob = {}
    try:                                                     # S874: the full mobile by clinic ID (the Call Console's mirror)
        mob = mobiles_by_cid({w.get("clinic_id") for w in who.values() if w.get("clinic_id")})
    except Exception:                                         # noqa: BLE001
        mob = {}
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
        x["typed"] = typed.get(k) or ""                      # S869
        x["key"] = "%s|%s" % (iso, k)
        w = who.get(k) or {}
        x["clinic_id"] = w.get("clinic_id") or ""            # S874: on every bill
        full = _m10(w.get("mobile") or "") or ((mob.get(x["clinic_id"]) or [""])[0] if x["clinic_id"] else "")
        x["mobile"] = full or (w.get("mobile") or "")        # the full number when known, else the last four as before
        x["mobiles"] = mob.get(x["clinic_id"]) or ([full] if full else [])
        if x["is_return"]:                                   # S869: the patient as typed, the ID, the mobile (his own page)
            x["patient"] = typed.get(k) or w.get("name") or ""
            x["items_value"] = rs(sum(i["value_p"] for i in x["items"] if i.get("value_p") is not None)) if x["items"] else None
        if not x["name"] and x["is_return"] and any(k and k in r for r in adj_reasons):
            x["name"] = "Home-medicine return -- goods back, no cash refunded"
        if not x["name"] and x["typed"]:                     # S869: the text as typed stands in for a name
            x["name"] = x["typed"]
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
    without = [dict(bill=b, head=HEADS.get(h, h), note=t or "", amount=rs(a), typed=typed.get(b) or "",
                    items=items.get(b, []),
                    items_value=(rs(sum(i["value_p"] for i in items.get(b, []) if i.get("value_p") is not None)) if items.get(b) else None))
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
    entries, written_off_p, other_account_p = [], 0, 0
    short_p, accepted, has_kal = 0, False, False
    try:
        import sanjeevni_cash as sc
        r = sc.days(con, iso, iso, unit)
        if r.get("ok") and r["rows"]:
            row = r["rows"][0]
            drawer_p = row["into_drawer_p"]
            entries = list(row.get("entries") or [])         # S869
            written_off_p = int(row.get("written_off_p") or 0)
            other_account_p = int(row.get("other_account_p") or 0)
            try:                                             # S874: the day's own short, beyond Darpan's page's tolerance
                import hub_cash
                tol = hub_cash.tolerance_p(con)
            except Exception:                                 # noqa: BLE001
                tol = 5000
            left = sum(h["amount_p"] for h in row["handed"])
            if _has(con, "darpan_kal_day"):
                kr = con.execute("SELECT owner_decision, handed_p FROM darpan_kal_day WHERE unit=? AND business_date=?", (unit, iso)).fetchone()
                has_kal = bool(kr and kr[1] is not None)
                accepted = bool(kr and kr[0] == "accept")
            if (row["into_drawer_p"] - left) > tol and (has_kal or status in ("approved", "locked")):
                short_p = row["into_drawer_p"] - left
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
                for h in row["handed"]:                      # S869: an entry or a write-off beside the cover
                    if h.get("src") in ("entry", "accepted"):
                        went += "; %s %s" % (rs(h["amount_p"]), {"written_off": "written off (you accepted the short)"}.get(
                            h["to"], "to " + {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you", "pool": "the pool"}.get(h["to"], h["to"])))
            elif row["handed"]:
                went = "; ".join("%s to %s" % (rs(h["amount_p"]), {"pool": "the pool (you approved this day)",
                                                                  "dr_bhawna": "Dr Bhawna", "dr_manoj": "you",
                                                                  "bank": "the bank", "written_off": "written off (you accepted the short)"}.get(h["to"], h["to"]))
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
    try:                                                     # S400: Bhati's check of this day, in words
        import sale_check
        checks.extend(sale_check.owner_checks(con, iso))
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
                entries=[dict(e, amount=rs(e["amount_p"]), words=_entry_words(e)) for e in entries],   # S869
                other_account=rs(other_account_p) if other_account_p else None,
                written_off=rs(written_off_p) if written_off_p else None,
                short=rs(short_p) if short_p else None, short_p=short_p, can_accept=bool(short_p and has_kal and not accepted),   # S874
                checks=checks, needs_you=needs)


def _entry_words(e):
    try:
        import hub_cash
        return hub_cash.entry_words(e)
    except Exception:                                         # noqa: BLE001
        return "%s %s" % (rs(e.get("amount_p")), e.get("kind", ""))


@bp.route("/finance/sanjeevni/api/day/<iso>")
def api_day(iso):
    u, err = _require("checker")
    if err:
        return err
    return jsonify(day_view(_db(), iso, _unit))
