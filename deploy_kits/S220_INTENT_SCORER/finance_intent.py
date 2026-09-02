#!/usr/bin/env python3
"""
finance_intent.py -- S220: the intent scorer for sale returns. READ-ONLY on the
books; writes only its own table, `intent_signal`.

THE OWNER'S BRIEF (02-Sep-2026): "deep analytics to catch the intent from historic
data and from constant monitoring, because this is a sum which anyone can
exploit." And the rule that governs every line here, his, from S211: "This is
not an accusation about a patient. It catches gaps at the sales counter... The
detector proposes; a person disposes."

WHAT A SIGNAL IS. A pattern, measured against ITS OWN BASELINE -- the same
counter, the same items, the same patients, in the weeks before -- never
against a number somebody picked. Each signal says what it saw, how much money
it touches, what normal looked like, and how far from normal this is. A signal
is a row to look at. It is never a finding, never red, never a verdict.

THE SIGNALS (v1), each computable from finance.db alone:
  S1  the void shape     a return, same day and same patient as a sale, for the
                         same rupees -- the one way a cash sale is made to
                         vanish after the money was taken; also the ordinary
                         shape of a correction. Weekly count vs the 12-week median.
  S2  cash out, bank in  a return whose earlier sale (same patient, same item,
                         within the window) was paid by UPI. Refunds are cash
                         (owner's rule) -- so this is cash leaving the drawer
                         for money that arrived by bank. Weekly count and rupees.
  S3  repeat returners   a named patient with 3+ returns in 90 days; and returns
                         on a mobile shared by several patient records.
  S4  rate drift         the trailing 4-week return rate (returns / sales, rupees)
                         against the prior 12-week median. Ratio >= 1.5 = look.
  S5  item outliers      an item whose 90-day return rate is 3x the counter's
                         overall rate, with 3+ returns.
  S6  the large share    Rs 1,000+ returns' share of the month's return rupees,
                         against the prior 3-month median.
  S7  bill continuity    MARG_BILL_RANGE_GAP flags in the window (M1 writes them;
                         tracked from 02-Sep by the owner's ruling).

DELIBERATELY NOT BUILT, and why (measured 02-Sep): "return then resale of the
same batch" -- 171 of 204 returned lines are resold within 30 days, because a
pharmacy sells continuously; the test cannot tell anything apart. "Returns on
the owner's absent days" -- day_entry carries no attendance yet (manned_by is
empty on all 137 days). "Per person" -- Marg's user-wise register is not on the
router yet; until then the counter is Darpan on >90% of days (owner).

D361: the past raises no work. This tool SCORES the past anyway -- it is the
only baseline there is -- and marks every signal before returns.act_from as
historical, which the card shows greyed and never counts.

USAGE
  python3 finance_intent.py                 score as of today, write intent_signal
  python3 finance_intent.py --as-of DATE    score as of DATE
  python3 finance_intent.py --dry-run       print, write nothing
  FIN_DB=... FIN_DIR=...                    the database / the modules
No patient name or number is printed; the table carries patient_ref ids only.
"""
import argparse
import collections
import datetime as dt
import os
import sqlite3
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("FIN_DIR", HERE))
DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
UNIT = "medical"
WALK_IN = "WALK-IN"

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS intent_signal ("
    " id INTEGER PRIMARY KEY, computed_at TEXT NOT NULL, as_of TEXT NOT NULL, unit TEXT NOT NULL,"
    " signal TEXT NOT NULL, scope TEXT NOT NULL, key TEXT NOT NULL, period_from TEXT, period_to TEXT,"
    " n INTEGER, value REAL, baseline REAL, ratio REAL, worth_p INTEGER, level TEXT NOT NULL,"
    " historical INTEGER NOT NULL DEFAULT 0, detail TEXT,"
    " UNIQUE(as_of, unit, signal, scope, key))")

LOOK = "look"        # worth a person's minute
WATCH = "watch"      # on the record, below the line


def _setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r else "") or default
    except Exception:                                        # noqa: BLE001
        return default


def _d(s):
    return dt.date.fromisoformat(s)


def _iso(d):
    return d.isoformat()


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _ratio(v, b):
    if b is None or b <= 0:
        return None if not v else float("inf")
    return round(v / b, 2)


def _rs(p):
    return "Rs {:,.0f}".format((p or 0) / 100.0)


# ------------------------------------------------------------------ the data
def _returns(con, lo, hi):
    """Bill-spine returns with their day and patient, lo..hi inclusive."""
    return con.execute(
        "SELECT s.id, s.source_ref bill, d.business_date day, s.patient_ref_id pid, s.amount_p amt, s.mode "
        "FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
        "WHERE s.unit=? AND s.service LIKE '%!_return' ESCAPE '!' AND d.business_date BETWEEN ? AND ?",
        (UNIT, lo, hi)).fetchall()


def _sales_p(con, lo, hi):
    r = con.execute(
        "SELECT COALESCE(SUM(s.amount_p),0) FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
        "WHERE s.unit=? AND s.service NOT LIKE '%!_return' ESCAPE '!' AND d.business_date BETWEEN ? AND ?",
        (UNIT, lo, hi)).fetchone()
    return int(r[0] or 0)


def _returns_p(con, lo, hi):
    return sum(int(r["amt"] or 0) for r in _returns(con, lo, hi))


def _walkin(con):
    r = con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (WALK_IN,)).fetchone()
    return r[0] if r else None


# ------------------------------------------------------------------ signals
def s1_void_shape(con, as_of, walk):
    """Weekly count of same-day, same-patient, same-rupee sale+return pairs vs the 12-week median."""
    out = []
    weeks = [(as_of - dt.timedelta(days=7 * k + 6), as_of - dt.timedelta(days=7 * k)) for k in range(13)]
    counts = []
    worths = []
    for lo, hi in weeks:
        n = w = 0
        for r in _returns(con, _iso(lo), _iso(hi)):
            if not r["pid"] or r["pid"] == walk:
                continue
            m = con.execute(
                "SELECT 1 FROM sale_item t JOIN day_entry e ON e.id=t.day_entry_id "
                "WHERE t.unit=? AND t.service NOT LIKE '%!_return' ESCAPE '!' AND t.patient_ref_id=? "
                "AND e.business_date=? AND ABS(t.amount_p-?)<=100 LIMIT 1",
                (UNIT, r["pid"], r["day"], r["amt"])).fetchone()
            if m:
                n += 1
                w += int(r["amt"] or 0)
        counts.append(n)
        worths.append(w)
    base = _median(counts[1:])
    cur, cw = counts[0], worths[0]
    lo, hi = weeks[0]
    ratio = _ratio(cur, base)
    level = LOOK if (cur >= 3 and ratio is not None and ratio >= 1.5) else WATCH
    out.append(dict(signal="void shape", scope="week", key=_iso(lo), period_from=_iso(lo), period_to=_iso(hi),
                    n=cur, value=float(cur), baseline=base, ratio=ratio, worth_p=cw, level=level,
                    detail="%d same-day full returns this week (%s); the 12-week median is %s. A same-day "
                           "return for a bill's exact rupees is how a correction looks -- and how a cash sale "
                           "is made to vanish after the money was taken." % (
                               cur, _rs(cw), "%.1f" % base if base is not None else "n/a")))
    return out


def s2_cash_out_bank_in(con, as_of, walk):
    """Returns whose earlier sale of the same item, same patient, was paid by UPI -- last 4 weeks."""
    window = int(_setting(con, "returns.window_days", "30") or 30)
    lo, hi = as_of - dt.timedelta(days=27), as_of
    n = w = 0
    bills = []
    for r in _returns(con, _iso(lo), _iso(hi)):
        if not r["pid"] or r["pid"] == walk or not r["bill"]:
            continue
        items = [x[0] for x in con.execute(
            "SELECT DISTINCT item_key FROM sale_line_item WHERE unit=? AND bill_no=? AND is_return=1",
            (UNIT, r["bill"]))]
        if not items:
            continue
        q = ",".join("?" * len(items))
        m = con.execute(
            "SELECT 1 FROM sale_line_item l JOIN sale_item s ON s.source_ref=l.bill_no "
            "WHERE s.unit=? AND s.patient_ref_id=? AND s.mode='upi' AND l.is_return=0 "
            "AND l.item_key IN (%s) AND l.business_date BETWEEN date(?, ?) AND ? LIMIT 1" % q,
            [UNIT, r["pid"]] + items + [r["day"], "-%d days" % window, r["day"]]).fetchone()
        if m:
            n += 1
            w += int(r["amt"] or 0)
            bills.append(r["bill"])
    level = LOOK if n >= 2 else WATCH
    return [dict(signal="cash out, bank in", scope="4 weeks", key=_iso(lo), period_from=_iso(lo), period_to=_iso(hi),
                 n=n, value=float(n), baseline=None, ratio=None, worth_p=w, level=level,
                 detail="%d return(s) in 4 weeks (%s) whose earlier sale of the same item, by the same patient, "
                        "was paid by UPI. Refunds are cash, so this is cash leaving the drawer for money that "
                        "arrived by bank. Bills: %s" % (n, _rs(w), ", ".join(bills[:6]) or "none"))]


def s3_repeat_returners(con, as_of, walk):
    out = []
    lo, hi = as_of - dt.timedelta(days=89), as_of
    per = collections.defaultdict(lambda: [0, 0, set()])
    for r in _returns(con, _iso(lo), _iso(hi)):
        if not r["pid"] or r["pid"] == walk:
            continue
        per[r["pid"]][0] += 1
        per[r["pid"]][1] += int(r["amt"] or 0)
        per[r["pid"]][2].add(r["day"])
    for pid, (n, w, days) in per.items():
        if n >= 3:
            out.append(dict(signal="repeat returner", scope="patient", key="ref#%d" % pid,
                            period_from=_iso(lo), period_to=_iso(hi), n=n, value=float(n), baseline=None,
                            ratio=None, worth_p=w, level=LOOK if n >= 4 else WATCH,
                            detail="patient ref#%d returned %d times on %d day(s) in 90 days, %s in all." % (
                                pid, n, len(days), _rs(w))))
    # shared mobiles
    for r in con.execute(
            "SELECT p.id pid, p.mobile_dup_count dup, COUNT(*) n, SUM(s.amount_p) w "
            "FROM patient_ref p JOIN sale_item s ON s.patient_ref_id=p.id "
            "JOIN day_entry d ON d.id=s.day_entry_id "
            "WHERE s.unit=? AND s.service LIKE '%!_return' ESCAPE '!' AND p.mobile_dup_count>1 "
            "AND d.business_date BETWEEN ? AND ? GROUP BY p.id", (UNIT, _iso(lo), _iso(hi))):
        out.append(dict(signal="shared mobile", scope="patient", key="ref#%d" % r["pid"],
                        period_from=_iso(lo), period_to=_iso(hi), n=r["n"], value=float(r["n"]),
                        baseline=None, ratio=None, worth_p=int(r["w"] or 0), level=WATCH,
                        detail="patient ref#%d shares its mobile with %d other record(s) and returned %d time(s) "
                               "in 90 days (%s). Two names on one phone is how a family looks -- and how one "
                               "person looks as several." % (r["pid"], (r["dup"] or 1) - 1, r["n"], _rs(int(r["w"] or 0)))))
    return out


def s4_rate_drift(con, as_of):
    cur_lo = as_of - dt.timedelta(days=27)
    cur = _ratio(_returns_p(con, _iso(cur_lo), _iso(as_of)), _sales_p(con, _iso(cur_lo), _iso(as_of)))
    prior = []
    for k in range(12):
        hi = cur_lo - dt.timedelta(days=1 + 7 * k)
        lo = hi - dt.timedelta(days=6)
        prior.append(_ratio(_returns_p(con, _iso(lo), _iso(hi)), _sales_p(con, _iso(lo), _iso(hi))))
    base = _median([p for p in prior if p is not None and p != float("inf")])
    ratio = _ratio(cur or 0, base) if cur is not None else None
    level = LOOK if (ratio is not None and ratio >= 1.5) else WATCH
    return [dict(signal="rate drift", scope="4 weeks", key=_iso(cur_lo), period_from=_iso(cur_lo), period_to=_iso(as_of),
                 n=None, value=(round(100 * cur, 2) if cur is not None else None),
                 baseline=(round(100 * base, 2) if base is not None else None), ratio=ratio,
                 worth_p=_returns_p(con, _iso(cur_lo), _iso(as_of)), level=level,
                 detail="returns are %s%% of sales over the last 4 weeks; the prior 12 weeks' median is %s%%." % (
                     "%.1f" % (100 * cur) if cur is not None else "n/a",
                     "%.1f" % (100 * base) if base is not None else "n/a"))]


def s5_item_outliers(con, as_of):
    out = []
    lo, hi = as_of - dt.timedelta(days=89), as_of
    tot_r = _returns_p(con, _iso(lo), _iso(hi))
    tot_s = _sales_p(con, _iso(lo), _iso(hi))
    overall = _ratio(tot_r, tot_s) or 0
    rows = con.execute(
        "SELECT item_key, MAX(item_name) name, "
        " SUM(CASE WHEN is_return=1 THEN 1 ELSE 0 END) nr, "
        " SUM(CASE WHEN is_return=0 THEN 1 ELSE 0 END) ns "
        "FROM sale_line_item WHERE unit=? AND business_date BETWEEN ? AND ? GROUP BY item_key HAVING nr>=3",
        (UNIT, _iso(lo), _iso(hi))).fetchall()
    for r in rows:
        rate = r["nr"] / float(r["nr"] + r["ns"]) if (r["nr"] + r["ns"]) else 0
        ov = (overall if overall else 0.02)
        ratio = _ratio(rate, ov)
        if ratio is not None and ratio >= 3:
            out.append(dict(signal="item outlier", scope="item", key=r["item_key"], period_from=_iso(lo), period_to=_iso(hi),
                            n=r["nr"], value=round(100 * rate, 1), baseline=round(100 * ov, 1), ratio=ratio, worth_p=None,
                            level=LOOK if ratio >= 5 else WATCH,
                            detail="%s: %d of %d lines in 90 days were returns (%.1f%%), against %.1f%% for the counter "
                                   "as a whole." % (r["name"], r["nr"], r["nr"] + r["ns"], 100 * rate, 100 * ov)))
    return out


def s6_large_share(con, as_of):
    big = int(_setting(con, "returns.large_p", "100000") or 100000)
    y, m = as_of.year, as_of.month
    months = []
    for k in range(4):
        mm = m - k
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        lo = dt.date(yy, mm, 1)
        hi = (dt.date(yy + (mm == 12), (mm % 12) + 1, 1) - dt.timedelta(days=1))
        rows = _returns(con, _iso(lo), _iso(min(hi, as_of)))
        tot = sum(int(r["amt"] or 0) for r in rows)
        lg = sum(int(r["amt"] or 0) for r in rows if int(r["amt"] or 0) >= big)
        months.append((lo, tot, lg, sum(1 for r in rows if int(r["amt"] or 0) >= big)))
    lo, tot, lg, n = months[0]
    share = _ratio(lg, tot)
    base = _median([_ratio(x[2], x[1]) for x in months[1:] if x[1]])
    ratio = _ratio(share or 0, base) if share is not None else None
    level = LOOK if (n >= 3 and ratio is not None and ratio >= 1.5) else WATCH
    return [dict(signal="large share", scope="month", key=_iso(lo)[:7], period_from=_iso(lo), period_to=_iso(as_of),
                 n=n, value=(round(100 * share, 1) if share is not None else None),
                 baseline=(round(100 * base, 1) if base is not None else None), ratio=ratio, worth_p=lg, level=level,
                 detail="%d return(s) of %s or more this month, %s -- %s%% of the month's return rupees; the prior "
                        "3 months' median share is %s%%." % (n, _rs(big), _rs(lg),
                                                              "%.0f" % (100 * share) if share is not None else "n/a",
                                                              "%.0f" % (100 * base) if base is not None else "n/a"))]


def s7_bill_continuity(con, as_of):
    lo = as_of - dt.timedelta(days=27)
    try:
        n = con.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND code='MARG_BILL_RANGE_GAP' "
                        "AND business_date BETWEEN ? AND ?", (UNIT, _iso(lo), _iso(as_of))).fetchone()[0]
    except Exception:                                        # noqa: BLE001
        n = 0
    return [dict(signal="bill continuity", scope="4 weeks", key=_iso(lo), period_from=_iso(lo), period_to=_iso(as_of),
                 n=n, value=float(n), baseline=0.0, ratio=None, worth_p=None, level=LOOK if n else WATCH,
                 detail="%d bill-numbering gap(s) flagged by the router in 4 weeks. Every user is entry-only; only the "
                        "owner's login can void a bill -- so a gap is his own action, or a missing export." % n)]


# ------------------------------------------------------------------ run
def compute(con, as_of):
    walk = _walkin(con)
    act = _setting(con, "returns.act_from", "2026-09-02")
    sigs = []
    for fn in (lambda: s1_void_shape(con, as_of, walk), lambda: s2_cash_out_bank_in(con, as_of, walk),
               lambda: s3_repeat_returners(con, as_of, walk), lambda: s4_rate_drift(con, as_of),
               lambda: s5_item_outliers(con, as_of), lambda: s6_large_share(con, as_of),
               lambda: s7_bill_continuity(con, as_of)):
        try:
            sigs.extend(fn())
        except Exception as ex:                              # noqa: BLE001
            sigs.append(dict(signal="engine", scope="error", key=str(fn), n=None, value=None, baseline=None,
                             ratio=None, worth_p=None, level=WATCH, period_from=None, period_to=None,
                             detail="a signal could not be computed: %s" % ex))
    for s in sigs:
        s["historical"] = 1 if (s.get("period_to") or _iso(as_of)) < act else 0
    return sigs


def write(con, as_of, sigs):
    con.execute(SCHEMA)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("DELETE FROM intent_signal WHERE as_of=? AND unit=?", (_iso(as_of), UNIT))
    for s in sigs:
        con.execute(
            "INSERT OR REPLACE INTO intent_signal (computed_at, as_of, unit, signal, scope, key, period_from, period_to,"
            " n, value, baseline, ratio, worth_p, level, historical, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (now, _iso(as_of), UNIT, s["signal"], s["scope"], s["key"], s.get("period_from"), s.get("period_to"),
             s.get("n"), s.get("value"), s.get("baseline"),
             (None if s.get("ratio") in (None, float("inf")) else s.get("ratio")), s.get("worth_p"), s["level"],
             s.get("historical", 0), s.get("detail")))
    con.commit()


def latest(con, unit=UNIT):
    """The newest run's signals, for the card. Fail-soft: [] without the table."""
    try:
        r = con.execute("SELECT MAX(as_of) FROM intent_signal WHERE unit=?", (unit,)).fetchone()
        if not r or not r[0]:
            return None, []
        rows = con.execute("SELECT * FROM intent_signal WHERE unit=? AND as_of=? ORDER BY level='look' DESC, "
                           "historical, signal, key", (unit, r[0])).fetchall()
        return r[0], [dict(x) for x in rows]
    except Exception:                                        # noqa: BLE001
        return None, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=_iso(dt.date.today()))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    as_of = _d(a.as_of)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sigs = compute(con, as_of)
    print("INTENT SIGNALS as of %s -- %d signal(s), %d to look at%s" % (
        _iso(as_of), len(sigs), sum(1 for s in sigs if s["level"] == LOOK and not s["historical"]),
        " (DRY RUN)" if a.dry_run else ""))
    for s in sigs:
        print("  %-5s %-18s %-9s %-12s n=%-4s ratio=%-6s %s" % (
            s["level"].upper(), s["signal"], s["scope"], s["key"], s.get("n"),
            s.get("ratio") if s.get("ratio") not in (None, float("inf")) else "-", ("(historical) " if s["historical"] else "") + (s.get("detail") or "")[:110]))
    if not a.dry_run:
        write(con, as_of, sigs)
        print("written  intent_signal as_of %s" % _iso(as_of))
    return 0


if __name__ == "__main__":
    sys.exit(main())
