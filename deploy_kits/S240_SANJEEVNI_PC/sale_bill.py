#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sale_bill.py  —  keep the sale bill's own money row
Dr. Manoj Agarwal Clinic · Sanjeevni Medicos · Session 237 · Rung 1

WHY THIS EXISTS (F-385)
  Marg's BILL WISE SALES STATEMENT gives, for every bill:

      BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH

  The item lines under it are at GROSS. The discount appears ONCE, for the whole
  bill. Our parser reads all of it correctly -- and then `write_lines_csv()`
  emits only the NET as "amount", so GROSS, DISCOUNT, TAX, DR/CR and CASH are
  gone before anything can store them.

  The consequence is money: every figure that values a sale from its item lines
  is a GROSS figure. On a 30%-discounted appliance it overstates the takings by
  up to 43%.

  This module keeps that row. Nothing else changes.

WHAT IT DOES NOT DO
  It does not touch the parser, the ingest, the CSV format, or any existing
  table. It adds ONE table and fills it. Written beside, never over.
  It attributes nothing to item lines -- that is Rung 2, and it needs the
  ruling table (T1) live first.

WHAT IT DELIBERATELY DOES NOT STORE
  No patient name, no phone, no clinic ID. The bill's money and nothing else.
  Attribution needs the money; it does not need to know whose bill it was.

THE ROUNDING, MADE VISIBLE INSTEAD OF TOLERATED
  Marg rounds a bill's NET to the whole rupee, so `gross - discount + dr/cr`
  does not always equal `net`. Measured on 09-Sep-2026: 15 of 21 bills exact,
  6 differing by Rs 0.03 to Rs 0.45. That residual is STORED, in `round_p`,
  rather than swallowed by a tolerance -- an unexplained residual is then a
  number somebody can look at, not a silence. Anything beyond one rupee is
  refused as a parse we do not understand.

THE PARSER IS NOT ASSUMED
  Measured 10-Sep-2026: `/root/finance/marg_report.py` on the VPS matches
  NEITHER copy in the repository. So this module never assumes the shape of what
  the parser hands back: it asserts the keys it needs and refuses loudly, naming
  what is missing, rather than writing a row of NULLs from a parser it did not
  expect.

RUN
  Look, change nothing (safe anywhere, prints what it WOULD write):
    python3 sale_bill.py --scan /path/to/MargArchive/SALE_BILLWISE

  Prove the logic, no files, no database:
    python3 sale_bill.py --selftest

  Fill the table from the archive (idempotent -- run it as often as you like):
    python3 sale_bill.py --scan /path/to/MargArchive/SALE_BILLWISE --write /root/finance/finance.db
"""

import argparse
import hashlib
import os
import re
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS sale_bill (
    unit           TEXT    NOT NULL,
    business_date  TEXT    NOT NULL,          -- ISO, the DAY the bill belongs to
    bill_no        TEXT    NOT NULL,
    gross_p        INTEGER NOT NULL,          -- paise, as Marg printed it
    disc_p         INTEGER NOT NULL,          -- the whole-bill discount. THE POINT OF THIS TABLE
    tax_p          INTEGER NOT NULL,
    drcr_p         INTEGER NOT NULL,
    net_p          INTEGER NOT NULL,          -- signed: a credit note is negative
    cash_p         INTEGER NOT NULL,
    noncash_p      INTEGER NOT NULL,          -- net - cash, i.e. UPI and/or credit
    is_credit_note INTEGER NOT NULL DEFAULT 0,
    round_p        INTEGER NOT NULL,          -- net - (gross - disc + drcr). Marg's rupee rounding, kept visible
    source_name    TEXT    NOT NULL,          -- the export file this row was read from
    source_stamp   TEXT    NOT NULL,          -- its export stamp, e.g. 20260909-221733
    source_md5     TEXT    NOT NULL,
    written_at     TEXT    NOT NULL,
    PRIMARY KEY (unit, business_date, bill_no)
);
CREATE INDEX IF NOT EXISTS ix_sale_bill_date ON sale_bill (unit, business_date);
CREATE INDEX IF NOT EXISTS ix_sale_bill_disc ON sale_bill (unit, disc_p) WHERE disc_p <> 0;
"""

REQUIRED_KEYS = ("bill_no", "gross_p", "disc_p", "tax_p", "drcr_p", "net_p", "cash_p")
MAX_ROUND_P = 100          # one rupee. Beyond this it is not rounding, it is a misread
STAMP_RE = re.compile(r"__(\d{8}-\d{6})__")


class SaleBillError(Exception):
    pass


# ---------------------------------------------------------------------------
# The pure half. No database, no files. Everything here is selftested.
# ---------------------------------------------------------------------------
def stamp_from_name(name):
    """The export stamp out of the archive's filename convention.
    Returns '' when the name does not carry one -- which is not fatal, it only
    means this file cannot win a tie against another export of the same day."""
    m = STAMP_RE.search(name or "")
    return m.group(1) if m else ""


def check_keys(bill):
    """Refuse a bill the parser did not give us in the shape we need.
    Loud, and it names what is missing -- see THE PARSER IS NOT ASSUMED."""
    missing = [k for k in REQUIRED_KEYS if k not in bill]
    if missing:
        raise SaleBillError(
            "the parser handed back a bill without %s. This module was written "
            "against a parser that provides %s. Do not guess -- read the live "
            "marg_report.py before changing anything."
            % (", ".join(missing), ", ".join(REQUIRED_KEYS)))
    return True


def round_residual(bill):
    """What Marg's rupee rounding left over: net - (gross - discount + dr/cr)."""
    return int(bill["net_p"]) - (int(bill["gross_p"]) - int(bill["disc_p"]) + int(bill.get("drcr_p") or 0))


def row_from_bill(bill, unit, business_date, source_name, source_stamp, source_md5, now_iso):
    """One bill dict -> one sale_bill row. Pure."""
    check_keys(bill)
    net = int(bill["net_p"])
    cash = int(bill["cash_p"])
    resid = round_residual(bill)
    if abs(resid) > MAX_ROUND_P:
        raise SaleBillError(
            "bill %s on %s does not add up: gross %d - discount %d + dr/cr %d = %d, "
            "but NET says %d (off by %d paise, more than the one rupee Marg rounds by). "
            "This is not rounding and it is not stored."
            % (bill["bill_no"], business_date, bill["gross_p"], bill["disc_p"],
               bill.get("drcr_p") or 0,
               int(bill["gross_p"]) - int(bill["disc_p"]) + int(bill.get("drcr_p") or 0),
               net, resid))
    return {
        "unit": unit,
        "business_date": business_date,
        "bill_no": str(bill["bill_no"]).strip(),
        "gross_p": int(bill["gross_p"]),
        "disc_p": int(bill["disc_p"]),
        "tax_p": int(bill.get("tax_p") or 0),
        "drcr_p": int(bill.get("drcr_p") or 0),
        "net_p": net,
        "cash_p": cash,
        "noncash_p": int(bill.get("noncash_p", net - cash)),
        "is_credit_note": 1 if bill.get("is_credit_note") else 0,
        "round_p": resid,
        "source_name": source_name,
        "source_stamp": source_stamp,
        "source_md5": source_md5,
        "written_at": now_iso,
    }


def rows_from_report(rep, unit, source_name, source_md5, now_iso):
    """Every bill in a parsed report, as rows. Pure -- `rep` is what
    marg_report.read_report() returns."""
    stamp = stamp_from_name(source_name)
    out = []
    for day in rep.get("days") or []:
        d = day.get("date")
        if not d:
            raise SaleBillError("a day in %s has no date" % source_name)
        for b in day.get("bills") or []:
            out.append(row_from_bill(b, unit, d, source_name, stamp, source_md5, now_iso))
    return out


def wins(new_stamp, old_stamp):
    """When two exports cover the same day, the LATER export wins -- and the
    answer must not depend on the order the files happened to be processed in."""
    return (new_stamp or "") >= (old_stamp or "")


def summarise(rows):
    """The numbers worth printing, so a run is never a silent success (F-383)."""
    s = {"bills": len(rows),
         "gross_p": sum(r["gross_p"] for r in rows),
         "disc_p": sum(r["disc_p"] for r in rows),
         "net_p": sum(r["net_p"] for r in rows),
         "cash_p": sum(r["cash_p"] for r in rows),
         "with_discount": sum(1 for r in rows if r["disc_p"] != 0),
         "credit_notes": sum(1 for r in rows if r["is_credit_note"]),
         "rounded": sum(1 for r in rows if r["round_p"] != 0),
         "days": len({(r["unit"], r["business_date"]) for r in rows})}
    s["disc_pct"] = (100.0 * s["disc_p"] / s["gross_p"]) if s["gross_p"] else 0.0
    return s


# ---------------------------------------------------------------------------
# The I/O half.
# ---------------------------------------------------------------------------
def ensure_schema(con):
    con.executescript(SCHEMA)
    con.commit()


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def upsert(con, rows):
    """Write the rows. A later export replaces an earlier one for the same bill;
    an earlier one never overwrites a later one. Returns a reconciled count."""
    ins = upd = skip = 0
    for r in rows:
        cur = con.execute(
            "SELECT source_stamp FROM sale_bill WHERE unit=? AND business_date=? AND bill_no=?",
            (r["unit"], r["business_date"], r["bill_no"])).fetchone()
        if cur is None:
            ins += 1
        elif wins(r["source_stamp"], cur[0]):
            upd += 1
        else:
            skip += 1
            continue
        con.execute(
            "INSERT INTO sale_bill (unit,business_date,bill_no,gross_p,disc_p,tax_p,drcr_p,"
            "net_p,cash_p,noncash_p,is_credit_note,round_p,source_name,source_stamp,source_md5,written_at) "
            "VALUES (:unit,:business_date,:bill_no,:gross_p,:disc_p,:tax_p,:drcr_p,:net_p,:cash_p,"
            ":noncash_p,:is_credit_note,:round_p,:source_name,:source_stamp,:source_md5,:written_at) "
            "ON CONFLICT(unit,business_date,bill_no) DO UPDATE SET "
            "gross_p=excluded.gross_p, disc_p=excluded.disc_p, tax_p=excluded.tax_p, "
            "drcr_p=excluded.drcr_p, net_p=excluded.net_p, cash_p=excluded.cash_p, "
            "noncash_p=excluded.noncash_p, is_credit_note=excluded.is_credit_note, "
            "round_p=excluded.round_p, source_name=excluded.source_name, "
            "source_stamp=excluded.source_stamp, source_md5=excluded.source_md5, "
            "written_at=excluded.written_at", r)
    con.commit()
    return {"inserted": ins, "updated": upd, "kept_newer": skip}


def find_exports(root):
    """Every sale export under a folder, oldest stamp first so a later export
    naturally lands last (though `wins()` makes the result order-independent)."""
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.upper().endswith((".XLS", ".XLSX")) and "SALE_BILLWISE" in fn.upper():
                out.append(os.path.join(dirpath, fn))
    return sorted(out, key=lambda p: (stamp_from_name(os.path.basename(p)), p))


def candidate_roots():
    """The folders worth looking in, rooted at the finance app's own directory so
    the answer follows FINANCE_DIR rather than a hard-coded path.
    (Earned by this kit's own installer walk: with FINANCE_DIR pointed elsewhere,
    a hard-coded list found nothing and reported it as 'no exports here'.)"""
    fin = os.environ.get("FINANCE_DIR", "/root/finance").rstrip("/")
    return [fin + "/scans", fin + "/marg", fin + "/marg_archive", fin + "/inbox",
            fin, "/root/margsync", "/root/MargArchive"]


def locate(roots=None, verbose=True):
    """Where do the sale exports actually live on this machine?

    The archive is kept on the clinic PC; the database is on the VPS, and the
    two are not the same folder. Rather than ask anybody, look: this counts the
    sale exports under each likely root and says so. Read-only, and a wrong
    guess costs nothing but a line of output."""
    roots = roots or candidate_roots()
    found = []
    for r in roots:
        if not os.path.isdir(r):
            if verbose:
                print("   %-28s (no such folder)" % r)
            continue
        n = len(find_exports(r))
        found.append((r, n))
        if verbose:
            print("   %-28s %d sale export(s)" % (r, n))
    best = max(found, key=lambda x: x[1]) if found else None
    if verbose:
        if best and best[1]:
            print("\n   -> use: --scan %s" % best[0])
        else:
            print("\n   -> no sale exports found under any of these. Name the folder with --scan.")
    return best


def scan(root, unit, marg_report, now_iso, verbose=True):
    """Read every export under `root`. Returns (rows, problems). Reads only."""
    rows, problems = [], []
    files = find_exports(root)
    if verbose:
        print("found %d sale export(s) under %s" % (len(files), root))
    for p in files:
        name = os.path.basename(p)
        try:
            rep = marg_report.read_report(p)
        except Exception as e:
            problems.append("%s: parser refused it -- %s" % (name, e))
            continue
        for err in (rep.get("errors") or []):
            problems.append("%s: %s" % (name, err))
        try:
            rs = rows_from_report(rep, unit, name, md5_of(p), now_iso)
        except SaleBillError as e:
            problems.append("%s: %s" % (name, e))
            continue
        rows.extend(rs)
        if verbose:
            days = sorted({r["business_date"] for r in rs})
            print("  %-62s %3d bills  %s" % (name[:62], len(rs),
                                             days[0] if len(days) == 1 else "%s..%s" % (days[0], days[-1])))
    return rows, problems


def dedupe(rows):
    """Collapse the same bill seen in several exports, later stamp winning.
    The same rule `upsert` uses, so --scan and --write always agree."""
    best = {}
    for r in rows:
        k = (r["unit"], r["business_date"], r["bill_no"])
        if k not in best or wins(r["source_stamp"], best[k]["source_stamp"]):
            best[k] = r
    return [best[k] for k in sorted(best)]


def rupees(p):
    return "%s%s" % ("-" if p < 0 else "", "{:,}".format(abs(p) / 100.0))


def print_summary(rows, problems):
    s = summarise(rows)
    print("\n=== what this would keep ===")
    print("  bills                %d over %d day(s)" % (s["bills"], s["days"]))
    print("  gross                Rs %s" % rupees(s["gross_p"]))
    print("  DISCOUNT             Rs %s   (%.2f%% of gross) <- the number that is thrown away today"
          % (rupees(s["disc_p"]), s["disc_pct"]))
    print("  net                  Rs %s" % rupees(s["net_p"]))
    print("  cash                 Rs %s" % rupees(s["cash_p"]))
    print("  bills with a discount %d of %d" % (s["with_discount"], s["bills"]))
    print("  credit notes          %d" % s["credit_notes"])
    print("  bills Marg rounded    %d" % s["rounded"])
    if problems:
        print("\n  %d problem(s):" % len(problems))
        for p in problems[:20]:
            print("   ! %s" % p)
        if len(problems) > 20:
            print("   ... and %d more" % (len(problems) - 20))
    else:
        print("\n  no problems")
    return s


# ---------------------------------------------------------------------------
# selftest -- no network, no files, no database.
# ---------------------------------------------------------------------------
def _bill(no="A001", gross=10000, disc=0, tax=0, drcr=0, net=None, cash=None, cn=False):
    net = (gross - disc + drcr) if net is None else net
    cash = net if cash is None else cash
    return {"bill_no": no, "gross_p": gross, "disc_p": disc, "tax_p": tax, "drcr_p": drcr,
            "net_p": net, "cash_p": cash, "noncash_p": net - cash, "is_credit_note": cn,
            "patient_name": "SOMEBODY", "phone": "PHONE-NOT-STORED", "clinic_id": "1234"}


def selftest():
    checks = []

    def ck(name, got, want):
        checks.append((got == want, name, got, want))

    NOW = "2026-09-10T09:00:00"
    SRC = "SALE_BILLWISE_DETAIL__2026-09-09__20260909-221733__7ca8f379.XLS"

    ck("stamp read from the archive name", stamp_from_name(SRC), "20260909-221733")
    ck("a name with no stamp is not fatal", stamp_from_name("something.xls"), "")
    ck("a multi-day export name still yields its stamp",
       stamp_from_name("SALE_BILLWISE_DETAIL__2026-09-04_to_2026-09-05__20260906-090352__7399f81a.XLS"),
       "20260906-090352")

    # --- the money identity and the rounding -------------------------------
    ck("an exact bill has no residual", round_residual(_bill(gross=10172, disc=172, net=10000)), 0)
    ck("a rounded-down bill keeps its residual",
       round_residual(_bill(gross=83682, disc=0, net=83700)), 18)
    ck("a rounded-up bill keeps its residual",
       round_residual(_bill(gross=261645, disc=0, net=261600)), -45)
    ck("dr/cr counts in the identity",
       round_residual(_bill(gross=172434, disc=17243, drcr=-200, net=155000)), 9)

    r = row_from_bill(_bill(gross=317000, disc=87000, net=230000), "medical", "2026-09-09", SRC,
                      stamp_from_name(SRC), "abc", NOW)
    ck("the four-appliance bill's discount is kept", r["disc_p"], 87000)
    ck("and its net", r["net_p"], 230000)
    ck("and it is exact", r["round_p"], 0)
    ck("noncash is derived when absent",
       row_from_bill({"bill_no": "A1", "gross_p": 1000, "disc_p": 0, "tax_p": 0, "drcr_p": 0,
                      "net_p": 1000, "cash_p": 400}, "medical", "2026-09-09", SRC, "", "abc", NOW)["noncash_p"],
       600)

    # --- what must NOT be stored (F-185 in spirit: money, not people) -------
    ck("no patient name is stored", "patient_name" in r, False)
    ck("no phone is stored", "phone" in r, False)
    ck("no clinic id is stored", "clinic_id" in r, False)

    # --- a credit note stays signed ----------------------------------------
    cnr = row_from_bill(_bill(no="CN0001", gross=-17000, disc=0, net=-17000, cash=-17000, cn=True),
                        "medical", "2026-09-09", SRC, "", "abc", NOW)
    ck("a credit note keeps its sign", cnr["net_p"], -17000)
    ck("and is flagged", cnr["is_credit_note"], 1)

    # --- refusals -----------------------------------------------------------
    try:
        row_from_bill({"bill_no": "A1", "gross_p": 100}, "medical", "2026-09-09", SRC, "", "a", NOW)
        ck("a short bill dict is refused", "no exception", "SaleBillError")
    except SaleBillError as e:
        ck("a short bill dict is refused", "SaleBillError", "SaleBillError")
        ck("and it names a missing key", "disc_p" in str(e), True)
        ck("and it says do not guess", "Do not guess" in str(e), True)
    try:
        row_from_bill(_bill(gross=100000, disc=0, net=98000), "medical", "2026-09-09", SRC, "", "a", NOW)
        ck("a bill that does not add up is refused", "no exception", "SaleBillError")
    except SaleBillError as e:
        ck("a bill that does not add up is refused", "SaleBillError", "SaleBillError")
        ck("and it is not called rounding", "not rounding" in str(e), True)
    ck("one rupee is still rounding",
       row_from_bill(_bill(gross=100000, disc=0, net=100100), "medical", "2026-09-09", SRC, "", "a", NOW)["round_p"],
       100)

    # --- which export wins --------------------------------------------------
    ck("a later export wins", wins("20260909-221733", "20260909-221435"), True)
    ck("an earlier export does not", wins("20260909-221435", "20260909-221733"), False)
    ck("the same export is idempotent", wins("20260909-221733", "20260909-221733"), True)
    ck("a stamped export beats an unstamped one", wins("20260909-221733", ""), True)

    early = row_from_bill(_bill(no="A9", gross=10000, net=10000), "medical", "2026-09-09",
                          "x__20260909-221435__a.XLS", "20260909-221435", "a", NOW)
    late = row_from_bill(_bill(no="A9", gross=20000, net=20000), "medical", "2026-09-09",
                         "x__20260909-221733__b.XLS", "20260909-221733", "b", NOW)
    ck("dedupe keeps the later one, given late first", dedupe([late, early])[0]["net_p"], 20000)
    ck("dedupe keeps the later one, given early first", dedupe([early, late])[0]["net_p"], 20000)
    ck("dedupe collapses to one row", len(dedupe([early, late])), 1)
    ck("two different bills both survive",
       len(dedupe([early, row_from_bill(_bill(no="A8"), "medical", "2026-09-09", "x", "", "a", NOW)])), 2)

    # --- the summary --------------------------------------------------------
    s = summarise([r, cnr])
    ck("summary counts the bills", s["bills"], 2)
    ck("summary sums the discount", s["disc_p"], 87000)
    ck("summary counts discounted bills", s["with_discount"], 1)
    ck("summary counts credit notes", s["credit_notes"], 1)
    ck("summary counts one day", s["days"], 1)
    ck("discount percentage is of gross", round(summarise([r])["disc_pct"], 2), 27.44)
    ck("an empty set does not divide by zero", summarise([])["disc_pct"], 0.0)

    # --- rows_from_report ---------------------------------------------------
    rep = {"days": [{"date": "2026-09-09", "bills": [_bill(no="A1"), _bill(no="A2", disc=500)]},
                    {"date": "2026-09-10", "bills": [_bill(no="A3")]}]}
    rr = rows_from_report(rep, "medical", SRC, "abc", NOW)
    ck("every bill of every day is taken", len(rr), 3)
    ck("each row carries its own day", sorted({x["business_date"] for x in rr}),
       ["2026-09-09", "2026-09-10"])
    ck("each row carries the source md5", rr[0]["source_md5"], "abc")
    try:
        rows_from_report({"days": [{"bills": [_bill()]}]}, "medical", SRC, "a", NOW)
        ck("a day with no date is refused", "no exception", "SaleBillError")
    except SaleBillError:
        ck("a day with no date is refused", "SaleBillError", "SaleBillError")
    ck("an empty report yields nothing", rows_from_report({"days": []}, "medical", SRC, "a", NOW), [])

    ck("locate has candidate roots to try", len(candidate_roots()) >= 3, True)
    _old = os.environ.get("FINANCE_DIR")
    os.environ["FINANCE_DIR"] = "/tmp/somewhere_else"
    ck("candidate roots follow FINANCE_DIR", candidate_roots()[0], "/tmp/somewhere_else/scans")
    if _old is None: del os.environ["FINANCE_DIR"]
    else: os.environ["FINANCE_DIR"] = _old
    ck("and fall back to /root/finance", candidate_roots()[0].endswith("/scans"), True)
    ck("locate reports nothing when no folder exists",
       locate(["/definitely/not/here", "/nor/here"], verbose=False), None)

    fails = [c for c in checks if not c[0]]
    for ok, name, got, want in checks:
        if not ok:
            print("  FAIL  %-52s got %r want %r" % (name, got, want))
    print("selftest: %d checks, %d failures" % (len(checks), len(fails)))
    return 1 if fails else 0


def main():
    p = argparse.ArgumentParser(description="Keep the sale bill's own money row (F-385, Rung 1).")
    p.add_argument("--scan", metavar="DIR", help="read every sale export under this folder")
    p.add_argument("--write", metavar="DB", help="write what --scan found into this database")
    p.add_argument("--unit", default="medical")
    p.add_argument("--marg-dir", default="/root/finance",
                   help="where the LIVE marg_report.py lives (default /root/finance)")
    p.add_argument("--locate", action="store_true",
                   help="find where the sale exports are on this machine, and stop")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.locate:
        print("looking for sale exports on this machine:")
        best = locate()
        return 0 if (best and best[1]) else 1
    if not a.scan:
        p.print_help()
        return 2

    import datetime as dt
    now_iso = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sys.path.insert(0, a.marg_dir)
    try:
        import marg_report
    except Exception as e:
        print("!! cannot import marg_report from %s: %s" % (a.marg_dir, e))
        return 1
    print("using the parser at %s" % (getattr(marg_report, "__file__", "?")))

    rows, problems = scan(a.scan, a.unit, marg_report, now_iso)
    rows = dedupe(rows)
    print_summary(rows, problems)

    if not a.write:
        print("\n  -> read only. Nothing was written. Add --write <db> to keep it.")
        return 0
    con = sqlite3.connect(a.write)
    ensure_schema(con)
    res = upsert(con, rows)
    got = con.execute("SELECT COUNT(*) FROM sale_bill WHERE unit=?", (a.unit,)).fetchone()[0]
    con.close()
    # F-383: reconcile what was intended against what happened, and say so.
    print("\n  written: %d inserted, %d updated, %d kept (already newer)"
          % (res["inserted"], res["updated"], res["kept_newer"]))
    print("  sale_bill now holds %d row(s) for unit %s" % (got, a.unit))
    if res["inserted"] + res["updated"] + res["kept_newer"] != len(rows):
        print("  !! MISMATCH: %d rows offered, %d accounted for" %
              (len(rows), res["inserted"] + res["updated"] + res["kept_newer"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
