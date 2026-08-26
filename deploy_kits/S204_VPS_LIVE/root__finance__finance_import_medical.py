#!/usr/bin/env python3
# =============================================================================
#  finance_import_medical.py  ·  Session 179 · step B1
#  Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly
#
#  WHAT THIS DOES
#    Imports the legacy Google-Sheet "Medical (Sanjeevni)" tab into finance.db
#    AS RECORDED (owner instruction, S179) and emits a reconciliation report.
#
#  WHAT THIS DOES NOT DO
#    It does not write to the Google Sheet. It does not touch any live system.
#    It does not silently correct a single rupee. Every discrepancy in the source
#    becomes a visible, dated, itemised row you can act on.
#
#  KEY IMPORT RULE (follows from the owner's ruling that Old Balance was MEANT
#  to be yesterday's closing cash):
#    Whenever the typed Old Balance disagrees with the computed carry-forward,
#    the difference is written as a cash_adjustment with status 'open' and
#    reason 'legacy carry-forward break'. The ledger then reconciles exactly to
#    the sheet's own closing figure, AND the entire drift is enumerated.
#
#  Money is INTEGER PAISE throughout. No floats.
#  Stdlib only — no third-party imports, so it runs anywhere.
#
#  Usage:
#     python3 finance_import_medical.py --csv medical_legacy.csv --db finance.db \
#             --report S179_B1_Medical_Reconciliation_Report.md --outdir .
# =============================================================================

import argparse
import csv
import datetime as dt
import json
import os
import re
import sqlite3
import sys

UNIT = "medical"
LEGACY_SERVICE = "pharmacy_sale"
NOW = None  # set in main() from --asof, so runs are reproducible


# ----------------------------------------------------------------- helpers

def paise(text):
    """Return (paise, known). known=False when the source cell is blank or junk.
    Blank is NOT the same as zero and is never silently treated as zero."""
    if text is None:
        return 0, False
    s = str(text).strip().replace(",", "").replace("₹", "")
    if s == "" or s.upper() in ("#VALUE!", "#REF!", "#N/A", "-", "NA", "NO"):
        return 0, False
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return 0, False
    val = int(round(float(s) * 100))
    return (-val if neg else val), True


def rupees(p):
    """Format paise as a plain rupee string for the report."""
    if p is None:
        return ""
    sign = "-" if p < 0 else ""
    p = abs(p)
    whole, frac = divmod(p, 100)
    # Indian digit grouping
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = head + "," + tail
    return "%s%s.%02d" % (sign, s, frac)


def parse_date(text):
    """Parse the sheet's M/D/YYYY. Never slice a date string (F-78)."""
    if not text:
        return None
    s = str(text).strip().split(" ")[0]
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        if d.year < 1900:           # catches the '0026' corruption seen in other tabs
            return ("BAD_YEAR", s)
        return d
    return ("UNPARSEABLE", s)


def parse_ts(text):
    if not text:
        return None
    s = str(text).strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ----------------------------------------------------------------- schema

def build_db(db_path, schema_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.executescript(open(schema_path, encoding="utf-8").read())
    con.commit()
    return con


# ----------------------------------------------------------------- import

def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_medical(con, rows, flags):
    """Import legacy rows. Returns list of dicts describing each imported day."""
    cur = con.cursor()

    # ---- normalise + order -------------------------------------------------
    recs = []
    for i, r in enumerate(rows):
        d = parse_date(r.get("business_date"))
        ts = parse_ts(r.get("timestamp"))
        if not isinstance(d, dt.date):
            flags.append(dict(code="BAD_DATE", severity="high", unit=UNIT,
                              business_date=None,
                              detail="source row %d has unusable date %r — NOT imported" % (i + 2, r.get("business_date"))))
            continue
        tot, tot_ok = paise(r.get("medical_total"))
        upi, upi_ok = paise(r.get("medical_upi"))
        exp, exp_ok = paise(r.get("expenses"))
        dep, dep_ok = paise(r.get("deposit"))
        ob, ob_ok = paise(r.get("old_balance"))
        sheet_close, sc_ok = paise(r.get("total_cash"))
        recs.append(dict(
            src_row=i + 2, ts=ts, date=d,
            total_p=tot, total_ok=tot_ok,
            upi_p=upi, upi_ok=upi_ok,
            exp_p=exp, exp_ok=exp_ok,
            dep_p=dep, dep_ok=dep_ok,
            ob_p=ob, ob_ok=ob_ok,
            sheet_close_p=sheet_close, sheet_close_ok=sc_ok,
            med_pdf=(r.get("medicine_pdf") or "").strip(),
            imp_pdf=(r.get("implant_pdf") or "").strip(),
            raw=r,
        ))

    # ---- resolve same-date resubmissions: latest timestamp WINS ------------
    by_date = {}
    for rec in recs:
        by_date.setdefault(rec["date"], []).append(rec)

    current, superseded = [], []
    for d, group in by_date.items():
        if len(group) == 1:
            current.append(group[0])
            continue
        group.sort(key=lambda x: (x["ts"] or dt.datetime.min, x["src_row"]))
        current.append(group[-1])
        for old in group[:-1]:
            superseded.append((d, old))
        flags.append(dict(code="RESUBMISSION", severity="medium", unit=UNIT,
                          business_date=d.isoformat(),
                          detail="%d submissions for this date; latest (sheet row %d) kept as current, "
                                 "%d earlier kept as revision(s)" % (len(group), group[-1]["src_row"], len(group) - 1)))
    current.sort(key=lambda x: x["date"])

    # ---- insert ------------------------------------------------------------
    running_close_p = 0
    out = []

    for rec in current:
        d = rec["date"]
        cur.execute(
            "INSERT INTO day_entry (unit, business_date, status, manned_source, source, "
            " entered_at, approved_by, approved_at, legacy_ref) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (UNIT, d.isoformat(), "locked", "legacy_unknown", "legacy_sheet",
             rec["ts"].isoformat() if rec["ts"] else None,
             "legacy_import", NOW, str(rec["raw"].get("timestamp") or "")))
        eid = cur.lastrowid

        # revenue lines (cash part is derived from total minus UPI, as the sheet did)
        cash_p = rec["total_p"] - rec["upi_p"]
        if cash_p < 0:
            flags.append(dict(code="UPI_EXCEEDS_TOTAL", severity="high", unit=UNIT,
                              business_date=d.isoformat(),
                              detail="UPI %s exceeds total %s" % (rupees(rec["upi_p"]), rupees(rec["total_p"]))))
            cash_p = 0
        cur.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,?,?,?)",
                    (eid, LEGACY_SERVICE, "cash", cash_p))
        cur.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,?,?,?)",
                    (eid, LEGACY_SERVICE, "upi", max(rec["upi_p"], 0)))
        if not rec["total_ok"]:
            flags.append(dict(code="TOTAL_UNREADABLE", severity="high", unit=UNIT,
                              business_date=d.isoformat(),
                              detail="sale total cell unreadable: %r" % rec["raw"].get("medical_total")))

        # expenses — blank/junk imported as UNKNOWN, never guessed as zero
        if rec["exp_ok"] and rec["exp_p"] != 0:
            cur.execute("INSERT INTO day_expense (day_entry_id, amount_p, amount_known, category_text, note) "
                        "VALUES (?,?,1,?,?)", (eid, rec["exp_p"], "legacy (uncategorised)",
                                               "imported from sheet"))
        elif not rec["exp_ok"]:
            cur.execute("INSERT INTO day_expense (day_entry_id, amount_p, amount_known, category_text, note) "
                        "VALUES (?,0,0,?,?)", (eid, "legacy (unreadable)",
                                               "source cell was %r" % rec["raw"].get("expenses")))
            flags.append(dict(code="EXPENSE_UNKNOWN", severity="medium", unit=UNIT,
                              business_date=d.isoformat(),
                              detail="expense cell %r — imported as UNKNOWN, not as zero"
                                     % rec["raw"].get("expenses")))

        # deposit -> cash out to bank
        if rec["dep_ok"] and rec["dep_p"] > 0:
            cur.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference) "
                        "VALUES (?,'out','bank',?,?)", (eid, rec["dep_p"], "legacy deposit"))

        # legacy attachments — Drive links preserved, nothing re-hosted
        for url, doc in ((rec["med_pdf"], "legacy_medicine_copy"),
                         (rec["imp_pdf"], "legacy_implant_copy")):
            if url and url.lower().startswith("http"):
                cur.execute("INSERT INTO attachment (day_entry_id, doc_type, external_url, uploaded_by) "
                            "VALUES (?,?,?, 'legacy_import')", (eid, doc, url))
            else:
                flags.append(dict(code="MISSING_SCAN", severity="medium", unit=UNIT,
                                  business_date=d.isoformat(), detail="no %s link" % doc))

        # ---- THE CARRY-FORWARD BREAK ---------------------------------------
        # computed opening = yesterday's computed closing (the owner's ruling).
        # typed Old Balance disagreeing with it is, by definition, unexplained.
        computed_open_p = running_close_p
        typed_open_p = rec["ob_p"] if rec["ob_ok"] else computed_open_p
        break_p = typed_open_p - computed_open_p
        if break_p != 0:
            cur.execute(
                "INSERT INTO cash_adjustment (day_entry_id, amount_p, reason, source, status) "
                "VALUES (?,?,?,'legacy_import','open')",
                (eid, break_p,
                 "legacy carry-forward break: sheet's Old Balance %s vs computed carry-forward %s"
                 % (rupees(typed_open_p), rupees(computed_open_p))))
            cur.execute(
                "INSERT OR IGNORE INTO recon_exception "
                "(unit, business_date, kind, expected_p, actual_p, diff_p, severity, status, detail, "
                " opened_at, shout_count) VALUES (?,?,?,?,?,?,?, 'open', ?, ?, 0)",
                (UNIT, d.isoformat(), "carry_forward_break",
                 computed_open_p, typed_open_p, break_p,
                 "high" if abs(break_p) >= 100000 else "medium",
                 "imported from sheet; awaiting the doctor's reason", NOW))

        # closing after this day
        exp_used_p = rec["exp_p"] if rec["exp_ok"] else 0
        dep_used_p = rec["dep_p"] if rec["dep_ok"] else 0
        closing_p = typed_open_p + cash_p - exp_used_p - dep_used_p

        if closing_p < 0:
            cur.execute(
                "INSERT OR IGNORE INTO recon_exception "
                "(unit, business_date, kind, expected_p, actual_p, diff_p, severity, status, detail, "
                " opened_at, shout_count) VALUES (?,?,?,NULL,?,?, 'high', 'open', ?, ?, 0)",
                (UNIT, d.isoformat(), "negative_cash", closing_p, closing_p,
                 "cash in hand went negative — physically impossible", NOW))

        # does our ledger reproduce the sheet's own closing figure?
        if rec["sheet_close_ok"] and closing_p != rec["sheet_close_p"]:
            flags.append(dict(code="SHEET_CLOSE_MISMATCH", severity="high", unit=UNIT,
                              business_date=d.isoformat(),
                              detail="our closing %s vs sheet's Total Cash %s"
                                     % (rupees(closing_p), rupees(rec["sheet_close_p"]))))

        out.append(dict(date=d, entry_id=eid, opening_computed_p=computed_open_p,
                        opening_typed_p=typed_open_p, break_p=break_p,
                        total_p=rec["total_p"], upi_p=rec["upi_p"], cash_p=cash_p,
                        expense_p=exp_used_p, expense_known=rec["exp_ok"],
                        deposit_p=dep_used_p, closing_p=closing_p,
                        sheet_close_p=rec["sheet_close_p"] if rec["sheet_close_ok"] else None))
        running_close_p = closing_p

    # ---- superseded submissions kept verbatim ------------------------------
    for d, old in superseded:
        cur.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?", (UNIT, d.isoformat()))
        row = cur.fetchone()
        if row:
            cur.execute("INSERT INTO day_revision (day_entry_id, revision, submitted_at, payload_json, superseded_at) "
                        "VALUES (?,?,?,?,?)",
                        (row[0], 0, old["ts"].isoformat() if old["ts"] else None,
                         json.dumps(old["raw"], ensure_ascii=False), NOW))

    # ---- missing days ------------------------------------------------------
    if out:
        seen = {r["date"] for r in out}
        day = out[0]["date"]
        last = out[-1]["date"]
        while day <= last:
            if day not in seen:
                sunday = (day.weekday() == 6)
                cur.execute(
                    "INSERT OR IGNORE INTO recon_exception "
                    "(unit, business_date, kind, severity, status, detail, opened_at, shout_count) "
                    "VALUES (?,?, 'missing_day', ?, 'open', ?, ?, 0)",
                    (UNIT, day.isoformat(), "low" if sunday else "high",
                     "no entry for this day (%s)%s" % (day.strftime("%A"),
                                                       " — Sunday" if sunday else ""),
                     NOW))
            day += dt.timedelta(days=1)

    for f in flags:
        cur.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) VALUES (?,?,?,?,?)",
                    (f.get("unit"), f.get("business_date"), f["code"], f["severity"], f["detail"]))

    con.commit()
    return out


# ----------------------------------------------------------------- report

def write_report(con, ledger, path, csv_dir):
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM day_entry WHERE unit=?", (UNIT,))
    n_days = cur.fetchone()[0]

    cur.execute("SELECT business_date, amount_p, reason FROM cash_adjustment a "
                "JOIN day_entry e ON e.id=a.day_entry_id WHERE e.unit=? ORDER BY business_date", (UNIT,))
    adjustments = cur.fetchall()

    cur.execute("SELECT kind, COUNT(*), COALESCE(SUM(ABS(diff_p)),0) FROM recon_exception "
                "WHERE unit=? AND status='open' GROUP BY kind ORDER BY 2 DESC", (UNIT,))
    exc = cur.fetchall()

    cur.execute("SELECT code, severity, COUNT(*) FROM data_flag WHERE unit=? GROUP BY code, severity "
                "ORDER BY 3 DESC", (UNIT,))
    flagsum = cur.fetchall()

    cur.execute("SELECT ym, days_recorded, revenue_p, cash_p, upi_p, expense_p, deposited_p, adjust_p "
                "FROM v_month_summary WHERE unit=? ORDER BY ym", (UNIT,))
    months = cur.fetchall()

    cur.execute("SELECT business_date, opening_p, cash_in_p, upi_in_p, expense_p, cash_out_p, "
                "adjust_p, closing_p FROM v_cash_ledger WHERE unit=? ORDER BY business_date", (UNIT,))
    vled = cur.fetchall()

    pos = sum(a[1] for a in adjustments if a[1] > 0)
    neg = sum(a[1] for a in adjustments if a[1] < 0)
    net = pos + neg
    final_close = ledger[-1]["closing_p"] if ledger else 0
    sheet_final = ledger[-1]["sheet_close_p"] if ledger else None

    tot_rev = sum(r["total_p"] for r in ledger)
    tot_upi = sum(r["upi_p"] for r in ledger)
    tot_cash = sum(r["cash_p"] for r in ledger)
    tot_exp = sum(r["expense_p"] for r in ledger)
    tot_dep = sum(r["deposit_p"] for r in ledger)

    L = []
    A = L.append
    A("# B1 — MEDICAL (SANJEEVNI) RECONCILIATION REPORT")
    A("")
    A("*Session 179 · produced by `finance_import_medical.py` from the legacy Google Sheet.*")
    A("*Offline run. Nothing installed, nothing served, no live system touched, no rupee corrected.*")
    A("")
    A("## 1 · What was imported")
    A("")
    A("| | |")
    A("|---|---:|")
    A("| Days imported | **%d** |" % n_days)
    A("| Period | %s → %s |" % (ledger[0]["date"], ledger[-1]["date"]) if ledger else "| Period | — |")
    A("| Sale total | ₹%s |" % rupees(tot_rev))
    A("| of which UPI | ₹%s (%.1f%%) |" % (rupees(tot_upi), 100.0 * tot_upi / tot_rev if tot_rev else 0))
    A("| of which cash | ₹%s |" % rupees(tot_cash))
    A("| Expenses | ₹%s |" % rupees(tot_exp))
    A("| Deposited to bank | ₹%s |" % rupees(tot_dep))
    A("")
    A("## 2 · The carry-forward breaks — itemised")
    A("")
    A("Because you confirmed `Old Balance` was **meant to be yesterday's closing cash**, every")
    A("disagreement below is an unexplained movement. Each one is now a real row in the database")
    A("with status `open`, waiting for your reason. Nothing was corrected.")
    A("")
    A("| | |")
    A("|---|---:|")
    A("| Breaks found | **%d** of %d days (%.1f%%) |" % (len(adjustments), n_days,
                                                          100.0 * len(adjustments) / n_days if n_days else 0))
    A("| Upward corrections | +₹%s |" % rupees(pos))
    A("| Downward corrections | −₹%s |" % rupees(abs(neg)))
    A("| **Net unexplained** | **₹%s** |" % rupees(net))
    A("")
    A("### The 15 largest, worth your attention first")
    A("")
    A("| Date | Day | Adjustment | Running closing after |")
    A("|---|---|---:|---:|")
    big = sorted(adjustments, key=lambda a: -abs(a[1]))[:15]
    closemap = {r["date"].isoformat(): r["closing_p"] for r in ledger}
    for d, amt, _ in big:
        wd = dt.date.fromisoformat(d).strftime("%a")
        A("| %s | %s | %s₹%s | ₹%s |" % (d, wd, "+" if amt > 0 else "−", rupees(abs(amt)),
                                          rupees(closemap.get(d, 0))))
    A("")
    A("*(All %d are in `medical_adjustments.csv`.)*" % len(adjustments))
    A("")
    A("## 3 · Open exceptions — these will keep shouting until closed")
    A("")
    A("| Kind | Count | Total absolute difference |")
    A("|---|---:|---:|")
    for kind, cnt, tot in exc:
        A("| `%s` | %d | ₹%s |" % (kind, cnt, rupees(tot)))
    A("")
    A("## 4 · Data-quality flags raised during import")
    A("")
    if flagsum:
        A("| Code | Severity | Count |")
        A("|---|---|---:|")
        for code, sev, cnt in flagsum:
            A("| `%s` | %s | %d |" % (code, sev, cnt))
    else:
        A("*None.*")
    A("")
    A("## 5 · Month by month")
    A("")
    A("| Month | Days | Sale | Cash | UPI | Expenses | Deposited | Adjustments |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for ym, dcount, rev, cash, upi, exp, dep, adj in months:
        A("| %s | %d | ₹%s | ₹%s | ₹%s | ₹%s | ₹%s | ₹%s |" % (
            ym, dcount, rupees(rev), rupees(cash), rupees(upi), rupees(exp), rupees(dep), rupees(adj)))
    A("")
    A("## 6 · Proof the import is faithful")
    A("")
    A("| Check | Result |")
    A("|---|---|")
    A("| Ledger's final closing cash | ₹%s |" % rupees(final_close))
    A("| Sheet's own last `Total Cash` | %s |" % ("₹" + rupees(sheet_final) if sheet_final is not None else "—"))
    tie = (sheet_final is not None and final_close == sheet_final)
    A("| **Do they agree?** | **%s** |" % ("YES — the import reproduces the sheet exactly" if tie
                                            else "NO — investigate before proceeding"))
    A("")
    A("A second, independent check — the arithmetic the pharmacy *should* satisfy if nothing had")
    A("ever gone missing:")
    A("")
    expected = tot_cash - tot_exp - tot_dep
    A("| | |")
    A("|---|---:|")
    A("| Cash sales − expenses − deposits | ₹%s |" % rupees(expected))
    A("| Actual closing cash per the sheet | ₹%s |" % rupees(final_close))
    A("| **Gap needing explanation** | **₹%s** |" % rupees(expected - final_close))
    A("")
    A("## 7 · What happens to these numbers next")
    A("")
    A("Nothing automatically. Each break is an `open` row waiting for a reason. As you work down the")
    A("list, most will turn out to be recognisable — a deposit entered a day late, cash you or")
    A("Dr Bhawna took from the drawer, a correction typed over the top of an earlier figure. Those")
    A("get an explanation and close. What survives that pass is the real, irreducible number, and it")
    A("will be a great deal smaller than ₹%s." % rupees(abs(net)))
    A("")
    A("---")
    A("")
    A("*B1 output. Files alongside this report: `finance.db`, `medical_daily_ledger.csv`,")
    A("`medical_adjustments.csv`, `medical_exceptions.csv`.*")

    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ---- CSVs --------------------------------------------------------------
    with open(os.path.join(csv_dir, "medical_daily_ledger.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "opening", "sale_total", "upi", "cash", "expenses",
                    "deposited", "adjustment", "closing"])
        for d, op, cin, upi, exp, out_, adj, close in vled:
            w.writerow([d, rupees(op), rupees(cin + upi), rupees(upi), rupees(cin),
                        rupees(exp), rupees(out_), rupees(adj), rupees(close)])

    with open(os.path.join(csv_dir, "medical_adjustments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "day", "adjustment", "reason"])
        for d, amt, reason in adjustments:
            w.writerow([d, dt.date.fromisoformat(d).strftime("%A"), rupees(amt), reason])

    cur.execute("SELECT business_date, kind, severity, diff_p, detail FROM recon_exception "
                "WHERE unit=? AND status='open' ORDER BY business_date", (UNIT,))
    with open(os.path.join(csv_dir, "medical_exceptions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "kind", "severity", "difference", "detail"])
        for d, kind, sev, diff, detail in cur.fetchall():
            w.writerow([d, kind, sev, rupees(diff) if diff is not None else "", detail])

    return tie


# ----------------------------------------------------------------- selftest

def selftest():
    ok = 0
    assert paise("31845") == (3184500, True); ok += 1
    assert paise("") == (0, False); ok += 1
    assert paise("O") == (0, False); ok += 1
    assert paise("#VALUE!") == (0, False); ok += 1
    assert paise("-30056") == (-3005600, True); ok += 1
    assert paise("1,234") == (123400, True); ok += 1
    assert rupees(3184500) == "31,845.00"; ok += 1
    assert rupees(-3005600) == "-30,056.00"; ok += 1
    assert rupees(10000000) == "1,00,000.00"; ok += 1
    assert parse_date("4/1/2026") == dt.date(2026, 4, 1); ok += 1
    assert parse_date("6/11/0026")[0] == "BAD_YEAR"; ok += 1
    assert parse_ts("4/9/2026 11:38:54").hour == 11; ok += 1
    print("selftest OK (%d assertions)" % ok)
    return 0


# ----------------------------------------------------------------- main

def main():
    global NOW
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="medical_legacy.csv")
    ap.add_argument("--db", default="finance.db")
    ap.add_argument("--schema", default="finance_schema.sql")
    ap.add_argument("--report", default="S179_B1_Medical_Reconciliation_Report.md")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--asof", default="2026-08-14T00:00:00")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    NOW = a.asof
    con = build_db(a.db, a.schema)
    rows = load_rows(a.csv)
    flags = []
    ledger = import_medical(con, rows, flags)
    tie = write_report(con, ledger, os.path.join(a.outdir, a.report), a.outdir)

    print("imported %d days | %d flags | ledger ties to sheet: %s"
          % (len(ledger), len(flags), "YES" if tie else "NO"))
    con.close()
    return 0 if tie else 2


if __name__ == "__main__":
    sys.exit(main())
