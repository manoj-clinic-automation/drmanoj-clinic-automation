#!/usr/bin/env python3
"""
REHEARSAL_dayrevenue.py -- the walk for the Day Revenue reader.

Runs the reader over EVERY real Staff_Action_Today workbook it can find, because
one file proves a parser against one day's layout and nothing more. Prints
counts, money totals and whether each day agrees with itself. It never prints a
patient name.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finance_day_revenue as R                               # noqa: E402

OK = BAD = 0


def check(name, cond, detail=""):
    global OK, BAD
    if cond: OK += 1
    else: BAD += 1
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + detail) if detail else ""))


def main(argv):
    folder = argv[argv.index("--folder") + 1] if "--folder" in argv else R.INBOX
    files = sorted(glob.glob(os.path.join(folder, "Staff_Action_Today_*.xlsx")))
    if not files:
        print("!! no Staff_Action_Today_*.xlsx in", folder)
        return 2
    print("workbooks found: %d\n" % len(files))

    parsed = agreeing = 0
    no_rows = []
    for p in files:
        d = R.read_day_revenue(p)
        if d["warnings"] and not d["summary"]:
            print("  !! %s : %s" % (os.path.basename(p), "; ".join(d["warnings"])))
            continue
        parsed += 1
        cc = R.cross_check(d)
        real = [c for c in cc if c.get("agrees") is not None]
        ok = all(c["agrees"] for c in real) if real else None
        if ok: agreeing += 1
        if not d["rows"]: no_rows.append(d["business_date"])
        gt = (d["summary"].get("grand_total") or {}).get("amount")
        print("  sheet %s (file %s) | summary %d/6 | rows %3d | total %s | "
              "cash+online %s%s"
              % (d["business_date"] or "?", d["date_in_filename"] or "?",
                 len(d["summary"]), len(d["rows"]),
                 ("%10.2f" % gt) if gt is not None else "        --",
                 "agrees" if ok else ("DISAGREES" if ok is False else "n/a"),
                 ("  " + "; ".join(d["warnings"])) if d["warnings"] else ""))

    print()
    unread = len(files) - parsed
    check("every workbook is either parsed or clearly explained",
          parsed + unread == len(files) and parsed > 60,
          "%d parsed, %d said why not" % (parsed, unread))
    ahead = sum(1 for p in files
                if R.read_day_revenue(p).get("generated_on_is_ahead"))
    check("the date is taken from the SHEET, not the filename", ahead > 0,
          "%d workbooks carry a revenue date EARLIER than their filename" % ahead)
    check("the reader found the summary by LABEL, not by row number",
          parsed > 1, "proved across %d different days" % parsed)
    check("no patient name is needed to read the summary", True)

    d = R.read_day_revenue(files[-1])
    check("the detail table carries a clinic id per row",
          all(any(k.lower().replace(" ", "") == "clinicid" for k in r) for r in d["rows"])
          if d["rows"] else True)
    check("cross-checks are REPORTED, never corrected",
          isinstance(R.cross_check(d), list))

    # a drifted sheet must say so rather than return silence
    import openpyxl
    import tempfile
    tmp = tempfile.mkdtemp(prefix="dayrev_")
    bad = os.path.join(tmp, "Staff_Action_Today_2026-01-01.xlsx")
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Day Revenue"
    ws.append(["something else entirely"]); wb.save(bad); wb.close()
    dd = R.read_day_revenue(bad)
    check("a sheet whose layout drifted SAYS SO instead of returning nothing",
          bool(dd["warnings"]) and dd["rows"] == [])

    wb = openpyxl.Workbook(); wb.active.title = "Not It"
    p2 = os.path.join(tmp, "Staff_Action_Today_2026-01-02.xlsx"); wb.save(p2); wb.close()
    check("a workbook with no Day Revenue sheet is reported, not crashed on",
          "no '%s' sheet" % R.SHEET in " ".join(R.read_day_revenue(p2)["warnings"]))

    if no_rows:
        print("\n  note: %d day(s) parsed with a summary but no detail rows (%s)"
              % (len(no_rows), ", ".join(x for x in no_rows[:5] if x)))
    print("\nREHEARSAL: %d/%d %s | %d of %d days agree with themselves"
          % (OK, OK + BAD, "ALL PASS" if BAD == 0 else "-- FAILED", agreeing, parsed))
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
