#!/usr/bin/env python3
"""
rejoin_returns_s220.py -- S220: ONE return, counted ONCE.

THE DEFECT, MEASURED (02-Sep-2026, on the live db copy). Since 18-Jun-2026 --
the owner's line: "from 18th June every return must have item lines" -- 17
returns sit on the bill spine under SYNTHETIC references (`S186-F104-###`,
written by the S186 backfill when the export of that fortnight carried no
credit-note bill row), while their item lines sit under the REAL credit-note
number (`CN00105` ...) with no bill row at all. The audit's union sees each of
those returns TWICE: once as "identity needed" (the spine row, on WALK-IN) and
once as "no patient attributed" (the orphan lines). Rs 6,527 since 18-Jun,
counted double; the monthly return count inflated (Aug 47 for 43 real).

Money-wise they are the same return: on every one of the 17 the spine amount
(Marg's bill value) and the item lines valued through finance_money agree to
within rounding -- 100/101, 170/172, 1570/1574, 1340/1348 ... -- and on each
day the pairing is UNIQUE both ways. Cross-checked offline against the owner's
full Marg sale-return register (197 credit notes): every CN number and rupee
value agrees.

WHAT THIS DOES. For each synthetic spine row, find the orphan credit note on
the SAME day whose line value is within tolerance (Rs 10 or 1%, whichever is
larger), require the match to be unique in BOTH directions, and re-key the
spine row's `source_ref` to the credit-note number. Nothing else changes:
same patient_ref, same amount, same day, same batch. The lines and the bill
row now join; the audit examines the return once, values it from the bill
row ("cash actually refunded"), and shows its lines. Identity is untouched --
16 of the 17 had no clinic ID typed at Marg and stay "identity needed" until
Darpan's sheet or the mobile lookup names them (that work is already in hand).

DISCIPLINE (S218 SS3: money writes never ship blind).
  --dry-run  (default)  prints the pairing table and changes NOTHING.
  --apply               takes an sqlite backup beside the db first
                        (finance.db.bak_S220_rejoin_<stamp>), applies the
                        unique pairs only, records each in audit_log, and
                        prints before/after counts from the live audit.
  --from YYYY-MM-DD     lower bound (default 2026-06-18, the owner's line).
                        --from 2026-04-01 covers the whole history; D361 says
                        the past raises no WORK -- a record repair that stops
                        double counting is not work for a person, but it is
                        the owner's call, so it is a flag, not a default.
  FIN_DB=...            the database (default /root/finance/finance.db).

No patient name or number is ever printed.
"""
import argparse
import datetime as dt
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("FIN_DIR", HERE))
from finance_money import line_amount_p            # noqa: E402  (the S212 rule: never sum a rate)

DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
SYNTH = "S186-F104-%"


def tol(p):
    return max(1000, int(round(0.01 * p)))


def orphan_cns(con, unit, since):
    """Credit-note bills that have item lines but NO bill row: {(day, cn): value_p}."""
    out = {}
    rows = con.execute(
        "SELECT bill_no, business_date, qty_raw, pack, amount_p FROM sale_line_item l "
        "WHERE l.unit=? AND l.is_return=1 AND l.business_date>=? "
        "AND NOT EXISTS (SELECT 1 FROM sale_item s WHERE s.source_ref=l.bill_no)",
        (unit, since)).fetchall()
    for bill, day, qty, pack, rate in rows:
        try:
            v = line_amount_p(qty, pack, rate)
        except Exception:
            v = None
        if v is None:
            out[(day, bill)] = None          # a line we cannot value poisons the whole bill
        elif out.get((day, bill), 0) is not None:
            out[(day, bill)] = out.get((day, bill), 0) + v
    return out


def synthetic_spine(con, unit, since):
    return con.execute(
        "SELECT s.id, s.source_ref, d.business_date, s.amount_p, s.patient_ref_id "
        "FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
        "WHERE s.unit=? AND s.service LIKE '%return%' AND s.source_ref LIKE ? "
        "AND d.business_date>=? ORDER BY d.business_date, s.id",
        (unit, SYNTH, since)).fetchall()


def pair(con, unit, since):
    """Return (pairs, unpaired, ambiguous). A pair is unique in both directions."""
    cns = orphan_cns(con, unit, since)
    spine = synthetic_spine(con, unit, since)
    by_day = {}
    for (day, cn), v in cns.items():
        by_day.setdefault(day, []).append((cn, v))
    pairs, unpaired, ambiguous = [], [], []
    claimed = {}
    for sid, ref, day, amt, pid in spine:
        cands = [(cn, v) for cn, v in by_day.get(day, []) if v is not None and abs(v - amt) <= tol(amt)]
        if len(cands) != 1:
            (ambiguous if cands else unpaired).append((day, ref, amt, [c for c, _ in cands]))
            continue
        cn, v = cands[0]
        # the reverse direction: this CN must fit exactly one synthetic row that day
        rev = [s for s in spine if s[2] == day and abs(v - s[3]) <= tol(s[3])]
        if len(rev) != 1 or cn in claimed:
            ambiguous.append((day, ref, amt, [cn]))
            continue
        claimed[cn] = sid
        pairs.append(dict(sid=sid, ref=ref, day=day, amt=amt, cn=cn, lines_p=v, pid=pid))
    return pairs, unpaired, ambiguous


def audit_counts(con, unit, days):
    """(rows, value) the live audit reports for these days -- the number the card shows."""
    try:
        sys.path.insert(0, os.path.dirname(DB))
        import finance_returns_audit as fra
    except Exception as ex:                       # pragma: no cover
        return "audit unavailable (%s)" % ex
    n = 0
    v = 0
    for d in sorted(set(days)):
        rows, _ = fra.returns_for_day(con, d, unit)
        n += len(rows)
        v += sum(r["amount_p"] for r in rows)
    return "%d rows, Rs %s" % (n, "{:,.0f}".format(v / 100.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--from", dest="since", default="2026-06-18")
    ap.add_argument("--unit", default="medical")
    a = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    pairs, unpaired, ambiguous = pair(con, a.unit, a.since)
    print("REJOIN RETURNS -- %s -- from %s -- %s" % (DB, a.since, "APPLY" if a.apply else "DRY RUN"))
    print("%-11s %-15s %-9s %9s %9s %6s  %s" % ("day", "synthetic ref", "credit", "bill Rs", "lines Rs", "delta", "patient"))
    for p in pairs:
        print("%-11s %-15s %-9s %9.2f %9.2f %6.2f  ref#%s" % (
            p["day"], p["ref"], p["cn"], p["amt"] / 100, p["lines_p"] / 100,
            (p["lines_p"] - p["amt"]) / 100, p["pid"]))
    print("pairs: %d unique   unpaired: %d   ambiguous: %d" % (len(pairs), len(unpaired), len(ambiguous)))
    for day, ref, amt, c in unpaired:
        print("  UNPAIRED  %s %s Rs %.2f -- no orphan credit note of that value that day" % (day, ref, amt / 100))
    for day, ref, amt, c in ambiguous:
        print("  AMBIGUOUS %s %s Rs %.2f -- candidates %s (left alone)" % (day, ref, amt / 100, c))
    days = [p["day"] for p in pairs]
    if pairs:
        print("audit before: " + audit_counts(con, a.unit, days))
    if not a.apply:
        print("DRY RUN -- nothing changed. Re-run with --apply to re-key the %d unique pair(s)." % len(pairs))
        return 0
    if not pairs:
        print("nothing to apply")
        return 0
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = DB + ".bak_S220_rejoin_" + stamp
    b = sqlite3.connect(bak)
    con.backup(b)
    b.close()
    print("backup   " + bak)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for p in pairs:
        con.execute("UPDATE sale_item SET source_ref=? WHERE id=? AND source_ref=?", (p["cn"], p["sid"], p["ref"]))
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) "
                        "VALUES ('sale_item', ?, 'rekey_return_S220', ?, ?, 'rejoin_returns_s220', ?)",
                        (p["sid"], '{"source_ref": "%s"}' % p["ref"], '{"source_ref": "%s"}' % p["cn"], now))
        except Exception:
            pass                                   # the record is wanted, never load-bearing
    con.commit()
    print("applied  %d pair(s) re-keyed; amounts, patients, days untouched" % len(pairs))
    print("audit after:  " + audit_counts(con, a.unit, days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
