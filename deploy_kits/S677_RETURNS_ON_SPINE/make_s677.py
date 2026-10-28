"""make_s677.py -- kit S677_RETURNS_ON_SPINE (Sanjeevni session S362, 28-Oct-2026). Rung 4d, stage 1: the returns engine's LINES and credit
notes come from the spine; the PATIENT stays on sale_item. The S212 four-rung ladder retires: a return is sp_sale_bill.credit_note = 1 and
its sp_sale_line rows, found by date and bill number. Every caller of returns_for_day (the owner's approvals card and Needs-you,
returns_kinds, darpan_kal, the escalation watchdog, the daily gaps, darpan_app's cn-detail) keeps the same row shape.
  /root/finance/spine/spine_read.py        ad441b1d -> TO   credit_notes(), return_days(), sale_lines(), lines_of_bills() -- read-only doors
  /root/finance/finance_returns_audit.py   d693c0b4 -> TO   _spine(), _line_row(), return_days(); find_return_lines, audit_return's prior
                                                            purchases, _return_lines_by_bill and returns_for_range read the spine
  /root/finance/returns_kinds.py           bd45cfeb -> TO   month_notes: the days from finance_returns_audit.return_days
  /root/finance/finance_returns_escalate.py c4864500 -> TO  escalate_day: the return's lines from find_return_lines; escalate_recent: return_days
  /root/finance/sanjeevni_approvals.py     26a8dbdb -> TO   the fallback Needs-you count: the days from return_days
Usage: python make_s677.py <live root, e.g. /root> <out dir>"""
import hashlib, os, sys

FROM = {"finance/spine/spine_read.py": "ad441b1dabf489e1bd54bb5aa62310a4",
        "finance/finance_returns_audit.py": "d693c0b4064acae8edc7876ef6dffe11",
        "finance/returns_kinds.py": "bd45cfebbaad8ab4f909d025f8b6f948",
        "finance/finance_returns_escalate.py": "c4864500d2efbd03c9c6a1e350eaf1b5",
        "finance/sanjeevni_approvals.py": "26a8dbdb56f17e2bf3d24f460530e319"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s (it is %s)" % (r, h[:8], hashlib.md5(b).hexdigest()[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:90])
    T[r] = T[r].replace(old, new, 1)


def span(r, start, end, new):
    """Replace from the unique `start` anchor up to (not including) the unique `end` anchor that follows it."""
    t = T[r]
    assert t.count(start) == 1, "%s: start anchor not once: %s" % (r, start[:90])
    i = t.index(start)
    j = t.index(end, i)
    assert t.count(end) == 1, "%s: end anchor not once: %s" % (r, end[:90])
    T[r] = t[:i] + new + t[j:]


# ----------------------------------------------------------------------------------------------------------------- spine_read.py
SR = "finance/spine/spine_read.py"
rep(SR, '''    # ---------------------------------------------------------------- health
''', '''    # ---------------------------------------------------------------- S677 (rung 4d): what the returns engine reads
    def credit_notes(self, date_from, date_to):
        """[{date, bill, gross_p, disc_p, net_p, cash_p}] -- every credit note (sp_sale_bill.credit_note = 1) in the range; by date, bill."""
        return self.q("SELECT date, bill, gross_p, disc_p, net_p, cash_p FROM sp_sale_bill WHERE credit_note=1 AND date BETWEEN ? AND ? "
                      "ORDER BY date, bill", date_from, date_to)

    def return_days(self, date_from, date_to):
        """The ISO days in the range that hold a credit note, ascending."""
        return [r["date"] for r in self.q("SELECT DISTINCT date FROM sp_sale_bill WHERE credit_note=1 AND date BETWEEN ? AND ? ORDER BY date",
                                          date_from, date_to)]

    def sale_lines(self, bill, date=None):
        """A bill's lines, by seq: [{date, bill, seq, name, k20, pack, qty_raw, units, rate_p, batch, expiry, credit_note}]. By bill number
        and date when the date is given; by bill number alone otherwise (the newest date first when a number repeats)."""
        if date:
            return self.q("SELECT l.date, l.bill, l.seq, l.name20 AS name, l.k20, l.pack, l.qty_raw, l.units, l.rate_p, l.batch, l.expiry, "
                          "COALESCE(b.credit_note,0) AS credit_note FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                          "WHERE l.bill=? AND l.date=? ORDER BY l.seq", bill, date)
        return self.q("SELECT l.date, l.bill, l.seq, l.name20 AS name, l.k20, l.pack, l.qty_raw, l.units, l.rate_p, l.batch, l.expiry, "
                      "COALESCE(b.credit_note,0) AS credit_note FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                      "WHERE l.bill=? ORDER BY l.date DESC, l.seq", bill)

    def lines_of_bills(self, bills, k20=None, returns=False, date_from=None, date_to=None):
        """The lines of the given bill numbers (a patient's bills, say), sales only (credit notes excluded) or returns only; one item key
        when given; newest first. The list is read in chunks, so a long history is fine."""
        bills = [str(b) for b in bills if b]
        out = []
        for i in range(0, len(bills), 300):
            part = bills[i:i + 300]
            w = ["l.bill IN (%s)" % ",".join("?" * len(part)), "COALESCE(b.credit_note,0)=?"]
            a = list(part) + [1 if returns else 0]
            if k20 is not None:
                w.append("l.k20=?"); a.append(k20)
            if date_from is not None:
                w.append("l.date>=?"); a.append(date_from)
            if date_to is not None:
                w.append("l.date<=?"); a.append(date_to)
            out += self.q("SELECT l.date, l.bill, l.seq, l.name20 AS name, l.k20, l.pack, l.qty_raw, l.units, l.rate_p, l.batch, l.expiry, "
                          "COALESCE(b.credit_note,0) AS credit_note FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                          "WHERE " + " AND ".join(w), *a)
        out.sort(key=lambda r: (r["date"], r["bill"], r["seq"]), reverse=True)
        return out

    # ---------------------------------------------------------------- health
''')

# ------------------------------------------------------------------------------------------------------- finance_returns_audit.py
FA = "finance/finance_returns_audit.py"
rep(FA, '''v2 · S213: ladder rung 4 reworked through finance_money (it compared a sum of
RATES against a bill's MONEY -- the confusion behind the withdrawn Rs 38,157).
Everything else is byte-identical to the S212 version.
"""
''', '''v2 · S213: ladder rung 4 reworked through finance_money (it compared a sum of
RATES against a bill's MONEY -- the confusion behind the withdrawn Rs 38,157).
Everything else is byte-identical to the S212 version.

v3 · S677 (28-Oct-2026, rung 4d stage 1): THE LINES COME FROM THE SPINE. Source A
is no longer sale_line_item but the spine's credit notes (sp_sale_bill.credit_note
= 1) and their lines (sp_sale_line), read through spine_read -- one read door, the
same store the stock figure and the order engine read. The four-rung ladder of
find_return_lines retires: a return is found by its date and bill number, or by
its bill number alone; nothing is guessed from digits or from a same-day amount.
A patient's earlier purchases are the lines of THAT PATIENT'S bills (sale_item,
by patient_ref_id -- the one place the patient column lands) read from the spine
by the item's spine key. Source B (the bill row with the patient) is unchanged.
Every row keeps its shape: item_key stays norm_item(name) for the desk and the
spot-check table; the spine's own key rides beside it as `k20`. The money is
still finance_money's. Unit: the spine is the pharmacy's; any other unit reads
no lines (as it never had any).
"""
''')
rep(FA, '''import collections
import os
import re
''', '''import collections
import datetime as _dt
import os
import re
import sys
''')
rep(FA, '''LINE_COLS = ("seq, item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym, "
             "bill_no, business_date")
''', '''LINE_COLS = ("seq, item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym, "
             "bill_no, business_date")                    # the row shape every caller reads (kept at S677)

HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_UNIT = "medical"                                     # the spine is the pharmacy's; no other unit has lines


def _spine():
    """The spine's read door, opened fresh on every call (spine.db is rebuilt whole every ten minutes -- a held connection would keep
    reading the old file). SPINE_DB names another file (the walks). Never raises here: a missing spine answers None and the engine
    reports 'not in the spine yet' for every return, which is the truth."""
    try:
        d = os.path.join(HERE, "spine")
        if d not in sys.path:
            sys.path.insert(0, d)
        from spine_read import Spine                       # noqa: PLC0415
        return Spine(os.environ.get("SPINE_DB") or os.path.join(d, "spine.db"))
    except Exception:                                      # noqa: BLE001
        return None


def _norm_item(name):
    """finance_returns.norm_item, verbatim -- the desk's and the spot-check table's key shape."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\\s+", " ", s).strip()


def _expiry_ym(printed):
    """The spine keeps the expiry as the sale report prints it (m/yy or mm/yy); the engine's rows carry 'YYYY-MM' as before, or None."""
    m = re.fullmatch(r"\\s*(\\d{1,2})\\s*/\\s*(\\d{2,4})\\s*", str(printed or ""))
    if not m:
        return None
    mm, yy = int(m.group(1)), int(m.group(2))
    if not 1 <= mm <= 12:
        return None
    return "%04d-%02d" % (yy if yy > 99 else 2000 + yy, mm)


def _line_row(l):
    """A spine line in the engine's row shape (LINE_COLS), plus k20. amount_p is the RATE PER PACK, as it always was here."""
    return dict(seq=l["seq"], item_name=l["name"], item_key=_norm_item(l["name"]), pack=l["pack"], qty_raw=l["qty_raw"],
                amount_p=l["rate_p"], batch=l["batch"], expiry_ym=_expiry_ym(l["expiry"]), bill_no=l["bill"],
                business_date=l["date"], k20=l["k20"])


def return_days(con, unit, date_from, date_to, newest_first=False):
    """The days in the range that hold a return: the spine's credit-note days UNION the days of sale_item's return rows (a return
    attributed to a patient on a day the spine has not ingested yet is still a return). ONE place for every caller (S677)."""
    days = set()
    sp = _spine() if unit == SPINE_UNIT else None
    if sp is not None:
        try:
            days.update(sp.return_days(date_from, date_to))
        except Exception:                                  # noqa: BLE001
            pass
    for (d,) in con.execute(
            "SELECT DISTINCT e.business_date FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
            "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' AND e.business_date BETWEEN ? AND ?",
            (unit, date_from, date_to)):
        days.add(d)
    return sorted(days, reverse=bool(newest_first))
''')
span(FA, '''def find_return_lines(con, bill_no, business_date, amount_p=None):''', '''def audit_return(con, bill_no, patient_ref_id, business_date, amount_p=None):''',
     '''def find_return_lines(con, bill_no, business_date, amount_p=None, sp=None):
    """A return's item lines from the spine, and where they were found.

    S677: one rung -- the bill number on its date; a second only when the date given is not the spine's (the bill number alone, newest
    date first). Nothing is inferred from digits or from a same-day amount any more: the spine holds every credit note the sale export
    printed, under the number Marg printed. `amount_p` is kept in the signature for the callers; it decides nothing.
    """
    b = str(bill_no or "").strip()
    if sp is None:
        sp = _spine()
    if not b or sp is None:
        return [], ""
    try:
        r = sp.sale_lines(b, business_date) if business_date else []
        if r:
            return [_line_row(x) for x in r], "the spine, by date and bill number"
        r = sp.sale_lines(b)
        if r:
            d0 = r[0]["date"]
            r = [x for x in r if x["date"] == d0]
            return [_line_row(x) for x in r], "the spine, by bill number (dated %s there)" % d0
    except Exception:                                      # noqa: BLE001
        return [], ""
    return [], ""


''')
rep(FA, '''    for ln in lines:
        prior = con.execute(
            "SELECT l.bill_no, l.qty_raw, l.amount_p, l.business_date "
            "FROM sale_line_item l JOIN sale_item s ON s.source_ref = l.bill_no "
            "WHERE l.item_key=? AND l.is_return=0 AND s.patient_ref_id=? "
            "AND l.business_date <= ? AND l.business_date >= date(?, ?) "
            "ORDER BY l.business_date DESC LIMIT 5",
            (ln["item_key"], patient_ref_id, business_date, business_date,
             "-%d days" % WINDOW_DAYS)).fetchall() if patient_ref_id else []
''', '''    # S677: the patient's bills from sale_item (the one place the patient lands), their lines from the spine by the item's spine key
    pbills = [r[0] for r in con.execute(
        "SELECT s.source_ref FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE s.patient_ref_id=? AND s.source_ref IS NOT NULL AND s.service NOT LIKE '%!_return' ESCAPE '!' "
        "AND e.business_date <= ? AND e.business_date >= date(?, ?)",
        (patient_ref_id, business_date, business_date, "-%d days" % WINDOW_DAYS))] if patient_ref_id else []
    if sp is None:                                         # the spine could not be read NOW: a question, never an accusation
        return [], dict(no_item_detail=1), ("the spine could not be read at this moment, so this return is not checked "
                                            "against the patient's purchases -- it will be, on the next read")
    try:
        _since = (_dt.date.fromisoformat(str(business_date)[:10]) - _dt.timedelta(days=WINDOW_DAYS)).isoformat()
    except Exception:                                      # noqa: BLE001
        _since = None
    for ln in lines:
        prior = []
        if pbills:
            try:
                # newest first; two sales on ONE day: the larger first (the old read's order within a day was SQLite's, undefined --
                # a return judged against the smaller of two same-day sales would cry 'more than sold' at a quantity the patient did buy).
                # The same PACK first: the spine's key is the name's first 20 letters, so two packs of one product share it.
                px = sorted(sp.lines_of_bills(pbills, k20=ln["k20"], returns=False, date_from=_since, date_to=business_date),
                            key=lambda x: (x["date"], float(x["units"] or 0), x["bill"]), reverse=True)
                same_pack = [x for x in px if (x["pack"] or "").strip() == (ln["pack"] or "").strip()]
                prior = [dict(bill_no=x["bill"], qty_raw=x["qty_raw"], amount_p=x["rate_p"], business_date=x["date"])
                         for x in (same_pack or px)][:5]
            except Exception:                              # noqa: BLE001
                return out, dict(flags, no_item_detail=1), ("the spine could not be read while checking this return against the "
                                                            "patient's purchases -- not examined now, never a verdict")
''')
span(FA, '''def _return_lines_by_bill(con, unit, business_date):''', '''def _has_col(con, table, col):''',
     '''def _return_lines_by_bill(con, unit, business_date, sp=None):
    """Every return LINE of the day, grouped by bill. Source A -- the spine (S677): the day's credit notes and their lines."""
    by = collections.OrderedDict()
    if unit != SPINE_UNIT:
        return by
    if sp is None:
        sp = _spine()
    if sp is None:
        return by
    try:
        for cn in sp.credit_notes(business_date, business_date):
            rows = [_line_row(x) for x in sp.sale_lines(cn["bill"], business_date)]
            by[cn["bill"]] = rows            # a credit note with no lines is still a credit note (an empty list)
    except Exception:                                      # noqa: BLE001
        return collections.OrderedDict()
    return by


''')
rep(FA, '''    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item "
        "WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION "
        "SELECT DISTINCT e.business_date FROM sale_item s "
        "JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
        "AND e.business_date BETWEEN ? AND ? ORDER BY 1",
        (unit, date_from, date_to, unit, date_from, date_to)).fetchall()]
    all_rows, total_p, per_day = [], 0, []''', '''    days = return_days(con, unit, date_from, date_to)      # S677: one place
    all_rows, total_p, per_day = [], 0, []''')
# the three populations' words: a bill row with no spine lines is 'not in the spine yet' rather than the S211 count
rep(FA, '''        if b is not None and lines:
            population = "audited"
        elif b is None:
            population = "orphan"          # lines, no bill row -- the 123
        else:
            population = "no item detail"  # bill row, no lines -- the 116
''', '''        if b is not None and lines:
            population = "audited"
        elif b is None:
            population = "orphan"          # a credit note in the spine with no bill row (no patient attributed)
        else:
            population = "no item detail"  # a bill row the spine holds no lines for -- a day not ingested yet, or a CN of no lines
''')

# ------------------------------------------------------------------------------------------------------------------- returns_kinds.py
RK = "finance/returns_kinds.py"
rep(RK, '''    from finance_returns_audit import returns_for_day    # noqa: PLC0415
    lo, hi = month + "-01", month + "-31"
    act_from = settings(con)["act_from"]
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION SELECT DISTINCT e.business_date FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' AND e.business_date BETWEEN ? AND ? ORDER BY 1 DESC",
        (unit, lo, hi, unit, lo, hi))]
''', '''    from finance_returns_audit import returns_for_day, return_days    # noqa: PLC0415
    lo, hi = month + "-01", month + "-31"
    act_from = settings(con)["act_from"]
    days = return_days(con, unit, lo, hi, newest_first=True)         # S677: the spine's credit-note days, one place
''')

# ------------------------------------------------------------------------------------------------------- finance_returns_escalate.py
FE = "finance/finance_returns_escalate.py"
rep(FE, '''from finance_returns_audit import returns_for_day
''', '''from finance_returns_audit import returns_for_day, return_days, find_return_lines
''')
rep(FE, '''            for ln in con.execute(
                    "SELECT item_key, item_name, batch FROM sale_line_item "
                    "WHERE unit=? AND bill_no=? AND is_return=1 ORDER BY seq",
                    (unit, bill)).fetchall():
                cur = con.execute(
                    "INSERT OR IGNORE INTO stock_spot_check (unit, business_date, bill_no, "
                    "item_key, item_name, batch, reason, requested_at, status) "
                    "VALUES (?,?,?,?,?,?,?,?, 'due')",
                    (unit, iso, bill, ln[0], ln[1], ln[2], reason, now))
''', '''            lines_, _src = find_return_lines(con, bill, iso)       # S677: the return's lines from the spine
            for ln in lines_:
                cur = con.execute(
                    "INSERT OR IGNORE INTO stock_spot_check (unit, business_date, bill_no, "
                    "item_key, item_name, batch, reason, requested_at, status) "
                    "VALUES (?,?,?,?,?,?,?,?, 'due')",
                    (unit, iso, bill, ln["item_key"], ln["item_name"], ln["batch"], reason, now))
''')
rep(FE, '''        iso_days = [r[0] for r in con.execute(
            "SELECT DISTINCT business_date FROM sale_line_item "
            "WHERE unit=? AND is_return=1 AND business_date >= date('now', ?) "
            "UNION "
            "SELECT DISTINCT e.business_date FROM sale_item s "
            "JOIN day_entry e ON e.id=s.day_entry_id "
            "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
            "AND e.business_date >= date('now', ?) ORDER BY 1",
            (unit, "-%d days" % days, unit, "-%d days" % days)).fetchall()]
''', '''        _since = (dt.date.today() - dt.timedelta(days=int(days))).isoformat()
        iso_days = return_days(con, unit, _since, "9999-12-31")      # S677: one place
''')

# ----------------------------------------------------------------------------------------------------------- sanjeevni_approvals.py
SA = "finance/sanjeevni_approvals.py"
rep(SA, '''    try:
        from finance_returns_audit import returns_for_day  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
''', '''    try:
        from finance_returns_audit import returns_for_day, return_days  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
''')
rep(SA, '''    days = [r[0] for r in con.execute("SELECT DISTINCT business_date FROM sale_line_item WHERE unit=? AND is_return=1 "
                                      "AND substr(business_date,1,7)=? UNION SELECT DISTINCT e.business_date FROM sale_item s "
                                      "JOIN day_entry e ON e.id=s.day_entry_id WHERE s.unit=? AND s.service LIKE '%_return' "
                                      "AND substr(e.business_date,1,7)=?", (_unit, ym, _unit, ym))]
''', '''    days = return_days(con, _unit, ym + "-01", ym + "-31")        # S677: one place
''')

rep(FA, '''def audit_return(con, bill_no, patient_ref_id, business_date, amount_p=None):
    """One return bill, line by line. Never raises on data."""
    lines, line_source = find_return_lines(con, bill_no, business_date, amount_p)
    out = []
    flags = collections.Counter()
    if not lines:
        return [], dict(no_item_detail=1), ("no item lines could be found for this "
                                            "return, by bill number, by digits, or "
                                            "by same-day amount -- so it cannot be "
                                            "examined, which is NOT the same thing "
                                            "as a clean return")
''', '''def audit_return(con, bill_no, patient_ref_id, business_date, amount_p=None, sp=None):
    """One return bill, line by line. Never raises on data. sp: an open spine door (returns_for_day passes its own); opened when none."""
    if sp is None:
        sp = _spine()
    lines, line_source = find_return_lines(con, bill_no, business_date, amount_p, sp=sp)
    out = []
    flags = collections.Counter()
    if not lines:
        return [], dict(no_item_detail=1), ("the spine holds no lines for this return under its bill number -- a day not "
                                            "ingested yet, or a credit note of no lines -- so it cannot be examined, which "
                                            "is NOT the same thing as a clean return")
''')
rep(FA, '''    lines_by_bill = _return_lines_by_bill(con, unit, business_date)
''', '''    sp = _spine() if unit == SPINE_UNIT else None               # S677: one door per day, passed down
    lines_by_bill = _return_lines_by_bill(con, unit, business_date, sp=sp)
''')
rep(FA, '''            rows, flags, note = audit_return(con, bill, patient_ref_id,
                                             business_date,
                                             b["amount_p"] if b else None)
''', '''            rows, flags, note = audit_return(con, bill, patient_ref_id,
                                             business_date,
                                             b["amount_p"] if b else None, sp=sp)
''')
# the escalation: the pharmacy unit only (find_return_lines has no unit of its own)
rep(FE, '''            lines_, _src = find_return_lines(con, bill, iso)       # S677: the return's lines from the spine
''', '''            lines_, _src = find_return_lines(con, bill, iso) if unit == "medical" else ([], "")   # S677: the spine (the pharmacy's)
''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
