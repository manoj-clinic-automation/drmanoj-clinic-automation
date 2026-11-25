#!/usr/bin/env python3
# make_s952.py · kit S952_RECORD_JUDGES · Sanjeevni session 519 · 25-Nov-2026
# Makes the four patched files FROM the 25-Nov bundle's bytes (each FROM pin checked, each anchor found exactly once):
#   stock_figure.py  rule 0 in carried(): an order line whose order's scanned bill is linked to a Marg bill is carried by THAT bill only
#   porders.py       detect_supplies: a missing line never takes a bill; rule 0's answer ('s') is accepted; the scan repair runs first
#   stock_watch.py   write_point / settle_provisional / _s934_settle / open_trace judge against the one record (record_judges.judge)
#   stock_check.py   the counts list shows the judgment's own words
#   python make_s952.py FROM_DIR OUT_DIR
import hashlib
import os
import sys

FROM = {"stock_figure.py": "07bca1df78b6f9d3725eda94351158d8", "porders.py": "eeaad33783725305a3712de88650260d",
        "stock_watch.py": "c7584585faf0fc786e4f09ce606989c5", "stock_check.py": "14ca39be464b14a5797f41103b8a448b"}


def once(s, old, new, name):
    n = s.count(old)
    if n != 1:
        sys.exit("!! %s: anchor found %d times: %r" % (name, n, old[:90]))
    return s.replace(old, new)


SF_HEAD_OLD = 'VERSION = "1.5"\n'
SF_HEAD_NEW = 'VERSION = "1.6"                                                 # v1.6 S952_RECORD_JUDGES (D1065): rule 0 -- the order\'s own scanned bill\n'

SF_RULE0_OLD = '''    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    lid = line.get("line_id")
'''
SF_RULE0_NEW = '''    s952 = _s952_rule0(ctx, sp, line, k, lines_of, forms, sx, same_k)   # S952 (D1065): the order's own scanned bill, before rules b-e
    if s952 is not None:
        return s952 or None
    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    lid = line.get("line_id")
'''

SF_FUNCS_OLD = '''def _family_bill(ctx, sp, k20, lo, od, own, forms, sib, split=None):
'''
SF_FUNCS_NEW = '''# ------------------------------------------------------------------ S952 (D1065, the owner's "YES" 25-Nov 12:25): RULE 0 -- the scanned bill
#  An order whose tied scan is LINKED to a Marg bill (purchase_scan_link -> purchase_bill) is answered by THAT bill and by no other: its line is
#  carried by the matching line of the linked bill as the spine holds it (rule b still keeps one bill line to one order line); none of the
#  linked bills carrying the medicine -> carried() is None (it did not come on its order's bill -- no other bill may take it, the slide that made
#  TYRO BR's false loss: bill 250 paired to order 90's missing line, F-1659 / F-1660). A linked bill not in the spine yet -> None too (Amir's entry
#  is on its way; no other bill takes the line meanwhile). An order with no linked scan: rules c-e exactly as before. The switch:
#  arrival.pair_by_scan ('0' turns rule 0 off). A line's own billed_bill_no (rule a) still comes first -- record_judges.scan_repair rights the
#  answers made before this rule.
def _s952_on(ctx):
    if "s952on" not in ctx.c:
        on = True
        try:
            r = ctx.con.execute("SELECT value FROM setting WHERE key='arrival.pair_by_scan'").fetchone() if ctx.con is not None else None
            on = not (r and str(r[0] or "").strip().lower() in ("0", "off", "no", "false"))
        except sqlite3.Error:
            on = True
        ctx.c["s952on"] = on
    return ctx.c["s952on"]


def _s952_scan_bills(ctx):
    """{order_id: {(supkey, bill, date)}} -- the Marg bills linked to each order's tied scans by an EXACT or CONFIRMED link (an AUTO or
    PROBABLE link is a guess and never decides; such an order keeps rules c-e), both spellings of the dealer. {} without the
    tables; None on a read failure (rule 0 then stands aside). Once per Ctx."""
    if "s952sb" not in ctx.c:
        out = {}
        try:
            con = ctx.con
            if con is not None and _has(con, "order_scan_tie") and _has(con, "purchase_scan_link") and _has(con, "purchase_bill"):
                sk = _sw().supkey
                for oid, sn, sup, bno, bdt in con.execute("SELECT t.order_id, b.supplier_norm, b.supplier, b.bill_no, b.bill_date FROM order_scan_tie t "
                                                          "JOIN purchase_scan_link k ON k.asset_bill_id=t.asset_bill_id JOIN purchase_bill b ON b.id=k.bill_id "
                                                          "WHERE t.asset_bill_id IS NOT NULL AND COALESCE(k.grade,'') IN ('EXACT','CONFIRMED')"):   # a guess (AUTO / PROBABLE) never decides
                    s = out.setdefault(int(oid), set())
                    for key in (sk(sn), sk(sup)):
                        if key:
                            s.add((key, _bill(bno), str(bdt or "")[:10]))
        except sqlite3.Error:
            out = None
        ctx.c["s952sb"] = out
    return ctx.c["s952sb"]


S952_DATE_SLACK = 7                                           # the order book's bill date and the spine's may differ (A000211: 15-10 / 13-10)


def _s952_spine_bills(ctx, sp):
    """{(supkey, bill): [date, ...]} the spine's purchase bills by dealer and number. Once per Ctx."""
    if "s952spb" not in ctx.c:
        out = {}
        try:
            for r in sp.q("SELECT supkey, bill, date FROM sp_purchase_bill"):
                out.setdefault((str(r["supkey"] or ""), _bill(r["bill"])), []).append(str(r["date"] or "")[:10])
        except Exception:                                     # noqa: BLE001
            out = {}
        ctx.c["s952spb"] = out
    return ctx.c["s952spb"]


def _s952_keyed(ctx, sp, oid):
    """The spine's bills {(supkey, bill, spine date)} that the order's linked scans name -- the same dealer and bill number, the dates within
    S952_DATE_SLACK days. None: rule 0 does not speak (no link, or unreadable); an empty set: linked, not in the spine yet."""
    SB = _s952_scan_bills(ctx)
    if not SB or not oid:
        return None
    bills = SB.get(int(oid))
    if not bills:
        return None
    idx = _s952_spine_bills(ctx, sp)
    out = set()
    for (sk, b, d) in bills:
        for sd in idx.get((sk, b), []):
            try:
                if abs((dt.date.fromisoformat(sd) - dt.date.fromisoformat(d)).days) <= S952_DATE_SLACK:
                    out.add((sk, b, sd))
            except ValueError:
                continue
    return out


def _s952_order_of(ctx, line):
    oid = line.get("order_id")
    if oid:
        return int(oid)
    if "s952lo" not in ctx.c:
        try:
            ctx.c["s952lo"] = {int(a): int(b) for a, b in ctx.con.execute("SELECT id, order_id FROM purchase_order_line")} if ctx.con is not None else {}
        except sqlite3.Error:
            ctx.c["s952lo"] = {}
    lid = line.get("line_id")
    return ctx.c["s952lo"].get(int(lid)) if lid is not None else None


def _s952_rule0(ctx, sp, line, k, lines_of, forms, sx, same_k):
    """RULE 0 (S952): None -- rule 0 does not speak (switch off, no linked scan, unreadable); False -- the order's linked bills do not carry
    the line (or are not in the spine yet): no bill carries it; a dict (how 's') -- the first linked bill's matching lines, summed."""
    if not _s952_on(ctx):
        return None
    keyed = _s952_keyed(ctx, sp, _s952_order_of(ctx, line))
    if keyed is None:
        return None
    if not keyed:
        return False
    lid = line.get("line_id")
    taken = _taken_split(sp, sx, lid, ctx) if sx is not None else _taken_lines(sp, k, lid, ctx)
    for k2 in same_k:
        taken = list(taken) + [t for t in _taken_lines(sp, k2, lid, ctx) if t not in taken]
    hit, hkey = None, None
    for p, pk, ps in lines_of(""):
        sk, d, b = str(p["supkey"] or ""), str(p["date"] or "")[:10], _bill(p["bill"])
        if (sk, b, d) not in keyed:
            continue
        if hit is not None and (sk, b, d) != hkey:
            break
        old_line = sx is not None and pk == sx["old_k"]
        if any(t[1] == sk and t[2] == b and _matches(ctx, sp, pk, t[3], t[4] or old_line, p["name27"]) for t in taken):
            continue
        if not _matches(ctx, sp, pk, forms, ps, p["name27"]):
            continue
        if hit is None:
            hit = dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0),
                       qty=float(p["qty"] or 0), free=float(p["free"] or 0), seq=p["seq"], name27=str(p["name27"] or ""), how="s",
                       packing=str(p.get("packing") or ""))
            hkey = (sk, b, d)
        else:
            hit["units"] += float(p["units"] or 0)
            hit["qty"] += float(p["qty"] or 0)
            hit["free"] += float(p["free"] or 0)
    return hit if hit is not None else False


def _family_bill(ctx, sp, k20, lo, od, own, forms, sib, split=None):
'''

PO_HEAD_OLD = 'VERSION = "1.2"   #'
PO_HEAD_NEW = 'VERSION = "1.3"   # S952 (D1065): detect_supplies -- the order\'s own scanned bill (rule 0), a missing line never takes a bill, the scan repair first;'

PO_REPAIR_OLD = '''    n = 0
    _s628_cols(con)
    try:                                                      # S628 (0): the one name list first -- never blocks the pass
'''
PO_REPAIR_NEW = '''    n = 0
    _s628_cols(con)
    try:                                                      # S952 (D1065): the answers made before rule 0 righted by each order's scanned bill
        import record_judges                                  # noqa: PLC0415
        if record_judges.pair_on(con) and record_judges.repair_due(con):   # only when a link, a tie, an answer or the spine moved
            n += int(record_judges.scan_repair(con).get("done") or 0)
    except Exception as _ex_rj:                               # noqa: BLE001 -- never blocks the pass
        print("porders.detect_supplies: the S952 scan repair failed (%s) -- the pass runs on" % _ex_rj, file=sys.stderr)
    try:                                                      # S628 (0): the one name list first -- never blocks the pass
'''

PO_RULE_OLD = '''            hit = SF.carried(con, sw, line, ctx)
            if not hit or hit.get("how") not in ("c", "d"):
                continue
'''
PO_RULE_NEW = '''            if missing:
                continue                                      # S952: reception marked it missing -- it never came; it never takes a bill
            hit = SF.carried(con, sw, line, ctx)
            if not hit or hit.get("how") not in ("c", "d", "s"):   # S952: 's' -- the order's own scanned bill (rule 0)
                continue
'''

SW_HEAD_OLD = 'VERSION = "1.11"\n'
SW_HEAD_NEW = 'VERSION = "1.12"                                                    # v1.12 S952_RECORD_JUDGES (D1065): every count judged against the one record\n'

SW_WP_OLD = '''    if expected is _UNSET:
        E = _s454_expected(con, sp, item)                      # S577: stock_figure.expect_for_point -- basis shelf | marg | approx
'''
SW_WP_NEW = '''    if expected is _UNSET:
        E = _s952_judge(con, sp, item, now_iso(), qty_units, live=True) or _s454_expected(con, sp, item)   # S952: the one record; else S577's
'''

SW_WP2_OLD = '''    pid = int(cur.lastrowid)
'''
SW_WP2_NEW = '''    pid = int(cur.lastrowid)
    if E.get("words"):                                         # S952: the judgment's own words, for the owner's Stock check page
        _s952_words(con, pid, E["words"])
'''

SW_EVE_OLD = '''    elif gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
'''
SW_EVE_NEW = '''    elif gap is None and E.get("awaits"):                      # S952: an evening count is judged to its day's end, when that day's sale report is in
        con.execute("UPDATE stock_point SET status='awaits_sales', settled_at=NULL, expected_units=NULL, gap_units=NULL WHERE id=?", (pid,))
        P.update(status="awaits_sales", verdict="counted in the evening -- judged to the day's end when that day's sale report is in",
                 verdict_hi="Shaam ki ginti -- kal ki sale report aane par milaan hoga.")
    elif gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
'''
SW_HWORDS_OLD = '''            _s936_hold_row(con, pid, H, note)
            P.update(status="recount", hold=H)
'''
SW_HWORDS_NEW = '''            _s936_hold_row(con, pid, H, note)
            P.update(status="recount", hold=H)
            _s952_words(con, pid, "short by about a fresh delivery (%s) -- held for a recount, not a loss" % H.get("what", ""))   # S952: the words agree
'''
SW_934C_OLD = '''                elif abs(gap) > allow:
                    mrp = sp.mrp_p(item) if sp.ok else None
'''
SW_934C_NEW = '''                elif abs(gap) > allow and not (E952 is not None and E952.get("near_delivery")):   # S952: a delivery's worth short is never booked
                    mrp = sp.mrp_p(item) if sp.ok else None
'''

SW_HOLD_OLD = '''        H = _s936_match(con, sp, item, ts, -gap, info["pack"], pid) if (hold and basis in ("shelf", "marg")) else None   # S936 (D1046)
'''
SW_HOLD_NEW = '''        H = _s936_match(con, sp, item, ts, -gap, info["pack"], pid) if (hold and basis in ("shelf", "marg", "record")) else None   # S936 (D1046); S952 'record'
'''

SW_ALW_OLD = '''        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if H is not None and abs(gap) > allow:'''
SW_ALW_NEW = '''        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if E.get("allowance") is not None:                      # S952: the judgment's own allowance -- its words and its verdict agree
            allow = E["allowance"]
        if H is not None and abs(gap) > allow:'''
SW_ALW2_OLD = '''                allow, _sold = allowance_units(con, item, info["pack"], since, sp)
'''
SW_ALW2_NEW = '''                allow, _sold = allowance_units(con, item, info["pack"], since, sp)
                if E952 is not None and E952.get("allowance") is not None:   # S952: the judgment's own allowance
                    allow = E952["allowance"]
'''

SW_NEVER_OLD = '''        elif abs(gap) <= allow:
            P["verdict"], P["verdict_hi"] = "%s short -- within the allowance, written as a small loss" % P["gap_text"], "%s kam -- thoda hai, likh liya" % P["gap_hi"]
'''
SW_NEVER_NEW = '''        elif E.get("never_loss") and abs(gap) > allow:         # S952: the figure cannot be told exactly here (the words say why) -- shown, never a loss
            P["verdict"], P["verdict_hi"] = "%s short -- noted, not a loss (the records are checked)" % P["gap_text"], "%s kam -- likh liya" % P["gap_hi"]
        elif abs(gap) <= allow:
            P["verdict"], P["verdict_hi"] = "%s short -- within the allowance, written as a small loss" % P["gap_text"], "%s kam -- thoda hai, likh liya" % P["gap_hi"]
'''

SW_SP_OLD = '''    for r in con.execute("SELECT id, item, qty_units, basis FROM stock_point WHERE status='provisional'").fetchall():
        b = str(r[3] or "marg")
        if b == "approx":
            continue
        E = _sf().expect_for_point(con, sp, r[1], ctx=ctx, basis=b, exclude_id=r[0])   # judged against the base BEFORE the point itself
'''
SW_SP_NEW = '''    for r in con.execute("SELECT id, item, qty_units, basis, at FROM stock_point WHERE status='provisional'").fetchall():
        b = str(r[3] or "marg")
        if b == "approx":
            continue
        E = _s952_judge(con, sp, r[1], r[4], r[2], exclude_id=r[0], ctx=ctx)      # S952: the one record at the point's own moment
        if E is not None and not E.get("awaits"):
            b = E.get("basis") or b
            if E.get("words"):
                _s952_words(con, r[0], E["words"])
        else:
            E = _sf().expect_for_point(con, sp, r[1], ctx=ctx, basis=b, exclude_id=r[0])   # judged against the base BEFORE the point itself
'''

SW_TR_OLD = '''    if basis in ("shelf", "marg") and basis_day and basis_day > w_from:
        w_from = basis_day                                    # S577: the window starts at the base the point was judged on
        anchor_text += "; judged on the %s of %s" % ("shelf figure" if basis == "shelf" else "Marg figure", dmy(basis_day))
'''
SW_TR_NEW = '''    if basis in ("shelf", "marg", "record") and basis_day and basis_day > w_from:   # S952: 'record' -- Marg's figure at the count's moment
        w_from = basis_day                                    # S577: the window starts at the base the point was judged on
        anchor_text += "; judged on the %s of %s" % ("shelf figure" if basis == "shelf" else "Marg figure", dmy(basis_day))
'''

SW_934A_OLD = '''            Sh = SF.shelf(con, sp, item, D, ctx, exclude_id=pid)
            M = SF.marg(con, sp, item, D, ctx)
'''
SW_934A_NEW = '''            E952 = _s952_judge(con, sp, item, at, q, last_bill=lb, exclude_id=pid, ctx=ctx)   # S952 (D1065): the one record, to the bill
            if E952 is not None and E952.get("awaits"):
                continue
            Sh = SF.shelf(con, sp, item, D, ctx, exclude_id=pid)
            M = SF.marg(con, sp, item, D, ctx)
'''

SW_934B_OLD = '''            gap = None if exp is None else round(float(q) - exp, 3)
            note_add = " · a purchase is dated that day (its time is not known) -- the gap is shown, never a loss" if pr_d else ""
'''
SW_934B_NEW = '''            if E952 is not None:                              # S952: the record's judgment replaces the shelf / Marg branch above
                basis, exp = E952.get("basis"), E952.get("expected")
                pr_d = bool(E952.get("never_loss")) and not E952.get("near_delivery")   # about a delivery: the recount rule (S936) still asks
                if E952.get("words"):
                    _s952_words(con, pid, E952["words"])
            gap = None if exp is None else round(float(q) - exp, 3)
            note_add = " · a purchase is dated that day (its time is not known) -- the gap is shown, never a loss" if (pr_d and E952 is None) else ""
'''

SW_FUNCS_OLD = '''# ------------------------------------------------------------------ the job (cron 06:30 IST)
def job(db_path, who="cron"):
'''
SW_FUNCS_NEW = '''def _s952_judge(con, sp, item, at, qty, last_bill=None, exclude_id=None, ctx=None, live=False):
    """S952 (D1065): record_judges.expect -- the count against THE ONE RECORD (Marg's figure at its moment + the deliveries truly on the
    shelf and not in Marg; an older loss not yet written off never booked twice) -- or None (the switch count.judge_by_record off, or a
    failure: the caller's own path, as before)."""
    try:
        import record_judges                                  # noqa: PLC0415 -- beside this file
        return record_judges.expect(con, sp, item, at, qty, last_bill, exclude_id, ctx, live)
    except Exception as ex:                                   # noqa: BLE001 -- a count is never refused for it
        print("stock_watch: the S952 judgment failed for %s (%s) -- the old figure is used" % (item, ex), file=sys.stderr)
        return None


def _s952_words(con, pid, words):
    """The judgment's words on the point (stock_point.judge_words, added by record_judges.ensure). Fail-soft."""
    try:
        con.execute("UPDATE stock_point SET judge_words=? WHERE id=?", (str(words)[:600], int(pid)))
    except sqlite3.Error:
        pass


# ------------------------------------------------------------------ the job (cron 06:30 IST)
def job(db_path, who="cron"):
'''

SW_NY_OLD = '''            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count", "count_day") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():'''
SW_NY_NEW = '''            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count", "count_day", "s952_check") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():   # S952: the daily self-check'''
SW_NY2_OLD = '''                                href=("/finance/stockcheck/" if n["kind"] in ("count_day", "asked_count") else None)))'''
SW_NY2_NEW = '''                                href=("/finance/stockcheck/" if n["kind"] in ("count_day", "asked_count", "s952_check") else None)))'''

SC_HEAD_OLD = 'VERSION = "1.3"   '
SC_HEAD_NEW = 'VERSION = "1.4"   '

SC_SEL_OLD = '''        for pid, item, at, q, e, g, basis, by, note, status in con.execute(
                "SELECT id, item, at, qty_units, expected_units, gap_units, basis, by, note, status FROM stock_point WHERE source IN ('spot','darpan') "
                "AND COALESCE(status,'')<>'superseded' ORDER BY at DESC, id DESC"):
'''
SC_SEL_NEW = '''        jw_col = "judge_words" if "judge_words" in {r[1] for r in con.execute("PRAGMA table_info(stock_point)")} else "NULL"   # S952: the judgment's words
        for pid, item, at, q, e, g, basis, by, note, status, jw in con.execute(
                "SELECT id, item, at, qty_units, expected_units, gap_units, basis, by, note, status, %s FROM stock_point WHERE source IN ('spot','darpan') "
                "AND COALESCE(status,'')<>'superseded' ORDER BY at DESC, id DESC" % jw_col):
'''
SC_NOTE_OLD = "reason=reason, note=_note_word(note), provisional=(status == \"provisional\"),"
SC_NOTE_NEW = "reason=reason, note=(\" · \".join(x for x in (str(jw or \"\").strip(), _note_word(note)) if x)[:400]), provisional=(status == \"provisional\"),   # S952"


def main(argv):
    src, out = argv[1], argv[2]
    os.makedirs(out, exist_ok=True)
    plan = {
        "stock_figure.py": [(SF_HEAD_OLD, SF_HEAD_NEW), (SF_RULE0_OLD, SF_RULE0_NEW), (SF_FUNCS_OLD, SF_FUNCS_NEW)],
        "porders.py": [(PO_HEAD_OLD, PO_HEAD_NEW), (PO_REPAIR_OLD, PO_REPAIR_NEW), (PO_RULE_OLD, PO_RULE_NEW)],
        "stock_watch.py": [(SW_HEAD_OLD, SW_HEAD_NEW), (SW_WP_OLD, SW_WP_NEW), (SW_WP2_OLD, SW_WP2_NEW), (SW_HOLD_OLD, SW_HOLD_NEW), (SW_NEVER_OLD, SW_NEVER_NEW),
                           (SW_SP_OLD, SW_SP_NEW), (SW_TR_OLD, SW_TR_NEW), (SW_934A_OLD, SW_934A_NEW), (SW_934B_OLD, SW_934B_NEW), (SW_FUNCS_OLD, SW_FUNCS_NEW),
                           (SW_NY_OLD, SW_NY_NEW), (SW_NY2_OLD, SW_NY2_NEW), (SW_ALW_OLD, SW_ALW_NEW), (SW_ALW2_OLD, SW_ALW2_NEW),
                           (SW_EVE_OLD, SW_EVE_NEW), (SW_HWORDS_OLD, SW_HWORDS_NEW), (SW_934C_OLD, SW_934C_NEW)],
        "stock_check.py": [(SC_HEAD_OLD, SC_HEAD_NEW), (SC_SEL_OLD, SC_SEL_NEW), (SC_NOTE_OLD, SC_NOTE_NEW)],
    }
    for name, reps in plan.items():
        b = open(os.path.join(src, name), "rb").read()
        h = hashlib.md5(b).hexdigest()
        if h != FROM[name]:
            sys.exit("!! %s is %s, not the FROM pin %s" % (name, h[:8], FROM[name][:8]))
        s = b.decode("utf-8")
        for old, new in reps:
            s = once(s, old, new, name)
        with open(os.path.join(out, name), "wb") as f:
            f.write(s.encode("utf-8"))
        print("%-16s %s -> %s" % (name, h[:8], hashlib.md5(s.encode("utf-8")).hexdigest()[:8]))


if __name__ == "__main__":
    main(sys.argv)
