"""
att_scenario.py — v1.1 (S199) — DEDUCTION SCENARIO, read-only. Std-lib only.

v1.1: render_document() returns the scenario HTML as a STRING (write_html now
wraps it), so the Staff Register app can serve the scenario inline behind the
manoj/bhawna salary gate (kit S199_SCEN2). CLI behaviour is byte-unchanged.

WHAT THIS IS
------------
A what-if report for the owner BEFORE any deduction policy is applied to real
pay (D332: enforcement dates are settings; July AND August were ruled
preview-only — F-150). It computes, per staff, on the SAME month of real
punch data, side by side:

  (1) NEW POLICY as August's ramp applies it   (marks slab 8 · incentive <=5/<=8)
  (2) NEW POLICY at September's STRICT slabs   (marks slab 5 · incentive <=2/<=5)
      — the identical behaviour, next month's thresholds: shows how much
      harder the strict month bites.
  (3) THE OLD FLAT SYSTEM: Rs.1 per late minute (every late minute, no grace)
      + one day's salary (base/30) per absent day beyond the allowed count.
      Constants below; change and re-run if the old practice differed.

Dress / I-card (Rs.20 per marked day each, from the Staff Register grid) are
computed IN FULL but shown in their OWN table as DISCRETIONARY — with the
month's total at waive-none / waive-half / waive-all, so the owner can decide
how much to waive with the figure in front of him. They are NOT included in
the mandatory-deduction totals.

WHAT IT DOES NOT DO
-------------------
Writes nothing any live service reads. Creates no review file (unlike the
monthly report, it never writes review_<ym>.csv — if that file already exists
its informed=N edits are honoured, else everything defaults to informed=Y,
exactly like the report's first pass). Changes no database. Console output
prints NO salary or Rs. figures (F-31); money appears only in the two output
files, which are written beside this script in /root — NOT inside any git
working tree (F-31/D320: salary data never enters the public repo).

HOW IT COMPUTES
---------------
It imports the live att_month_report (v2.6) and calls ITS collect_month(),
ITS marks_for_late bands, ITS limits_for()/incentive_tier() and ITS
per_min_rate() — so the scenario cannot drift from what the real salary
report would say. The only additions of its own:
  * a raw-late-minutes pass (the old Rs.1/min system charged every late
    minute, including <=10-min days the new policy graces) — same arrival
    rule as the report (first punch counted only if a plausible arrival);
  * a read-only look at the Staff Register DB for dress/I-card marked days
    (register staff matched to attendance staff by name, the same rule
    salary_engine.py uses; DB missing -> zeros, said out loud, never a crash).

USAGE (on the VPS)
  /root/wa/venv/bin/python3 /root/att_scenario.py 2026-08
  /root/wa/venv/bin/python3 /root/att_scenario.py --selftest

OUTPUTS (beside this script)
  scenario_YYYY-MM.csv    — per-staff, every column
  scenario_YYYY-MM.html   — browser -> print A4: comparison + discretionary tables
"""
import sys
import os
import csv
import html
import math
import datetime
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# ---- OLD-SYSTEM CONSTANTS (owner-stated S199; edit here if practice differed) --
OLD_RATE_PER_MIN = 1.0      # Rs.1 per late minute, flat
OLD_GRACE_MIN = 0           # old system had no grace band; set 10 to forgive <=10-min days
OLD_ABSENT_FREE = 3         # absents allowed before a day-salary cut
# old absent rule: max(0, absents - OLD_ABSENT_FREE) x (base_salary / 30)

DRESS_RS = 20               # per marked day (register grid) — DISCRETIONARY
ICARD_RS = 20               # per marked day (register grid) — DISCRETIONARY

STRICT_YM = "2026-09"       # any non-ramp month: yields the strict limits from the live code

_TODAY_OVERRIDE = None      # selftest only


def money(x):
    return ("%.2f" % round(x + 1e-9, 2)).rstrip("0").rstrip(".") if x else "0"


def raw_late_minutes(ym, amr, att_core, pol_all):
    """{uid: total raw late minutes over the month, EVERY late minute} using the
    report's own duty_shift + arrival-plausibility rule. Present-request
    synthetic punches are merged exactly as the report merges them (v2.6)."""
    year, mon = int(ym[:4]), int(ym[5:7])
    import calendar as _cal
    ndays = _cal.monthrange(year, mon)[1]
    today = _TODAY_OVERRIDE or datetime.date.today()
    staff = att_core.load_staff()
    punches = att_core.load_punches()
    for (_uid, _d), dt in amr.load_present_requests(ym).items():
        punches.append((_uid, dt))
    out = {}
    for d in range(1, ndays + 1):
        date = datetime.date(year, mon, d)
        if date > today:
            break
        day = att_core.compute_day(date, staff=staff, punches=punches)
        by_present = {r["uid"]: r for r in day["present"]}
        for uid, info in staff.items():
            if not info["active"]:
                continue
            pol = pol_all.get(uid)
            if pol is None or pol["minutes_exempt"]:
                continue
            s_start, s_end = amr.duty_shift(date, ym, info, pol)
            if s_start is None:
                continue
            r = by_present.get(uid)
            if r is None:
                continue
            sched_start = datetime.datetime.combine(date, s_start)
            sched_end = datetime.datetime.combine(date, s_end) if s_end else None
            first = r["first"]
            if sched_end is None or first <= sched_end:
                raw = max(0, int((first - sched_start).total_seconds() // 60))
            else:
                raw = 0
            if raw > OLD_GRACE_MIN:
                out[uid] = out.get(uid, 0) + raw
    return out


def register_grid(ym, db_path):
    """{lowercase name: {'dress': n, 'icard': n}} read-only from the Staff
    Register DB, leave days excluded the way salary_engine excludes them.
    (None, reason) on any problem — the scenario then shows zeros LOUDLY."""
    if not db_path or not os.path.exists(db_path):
        return None, "register DB not found at %s" % db_path
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
        con.row_factory = sqlite3.Row
        try:
            staff = {r["staff_id"]: (r["name"] or "").strip().lower()
                     for r in con.execute("SELECT staff_id, name FROM staff")}
            closed = {r["fest_date"] for r in con.execute(
                "SELECT fest_date FROM festival_day WHERE clinic_closed=1")}
            agg = {}
            for r in con.execute(
                    "SELECT * FROM daily_register WHERE reg_date LIKE ?",
                    (ym + "-%",)):
                nm = staff.get(r["staff_id"])
                if not nm:
                    continue
                on_leave = bool(r["leave_kind"]) and r["reg_date"] not in closed
                if on_leave:
                    continue
                a = agg.setdefault(nm, {"dress": 0, "icard": 0})
                if r["dress_improper"]:
                    a["dress"] += 1
                if r["icard_missing"]:
                    a["icard"] += 1
        finally:
            con.close()
    except Exception as e:
        return None, "register DB unreadable (%s: %s)" % (type(e).__name__, e)
    return agg, ""


def build(ym):
    import att_core
    import att_config as cfg
    import att_month_report as amr

    if _TODAY_OVERRIDE:
        amr._TODAY_OVERRIDE = _TODAY_OVERRIDE

    pol_all = amr.load_staff_policy()
    acc, _log, _events = amr.collect_month(ym, att_core, cfg, pol_all)

    # informed flags: honour an existing review file; NEVER create one here
    review_path = os.path.join(BASE, "review_%s.csv" % ym)
    flags = amr.load_review(review_path)
    review_note = ("review_%s.csv honoured (informed=N rows applied)" % ym
                   if flags is not None else
                   "no review_%s.csv yet — everything treated informed=Y "
                   "(the report's own first-pass default)" % ym)
    if flags is None:
        flags = {}

    raw_late = raw_late_minutes(ym, amr, att_core, pol_all)

    reg_db = os.environ.get("ATT_REGISTER_DB", amr.REGISTER_DB_DEFAULT)
    grid, grid_err = register_grid(ym, reg_db)
    if grid is None:
        grid = {}

    _full_a, half_aug = amr.limits_for(ym)
    _full_s, half_strict = amr.limits_for(STRICT_YM)

    rows = []
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        pol, info = a["pol"], a["info"]
        base = pol["base_salary"]
        rate = amr.per_min_rate(info, pol)
        half_day_rs = base / 60 if base else 0.0
        day_rs = base / 30 if base else 0.0
        exempt = pol["minutes_exempt"]

        # marks incl. uninformed >=60 additions (the report's own rule)
        marks = a["marks"]
        for dstr in a["late60_dates"]:
            if not flags.get((uid, dstr, "LATE60"), True):
                marks += 1

        # absent fines (same in Aug and strict months)
        uninf = sum(1 for dstr in a["absent_dates"]
                    if not flags.get((uid, dstr, "ABSENT"), True))
        fine_uninf = uninf * amr.FINE_UNINFORMED
        excess = max(0, a["absent"] - amr.ABSENT_FREE_DAYS)
        fine_excess = excess * amr.FINE_EXCESS_ABSENT

        # early departure (same both)
        early_rs = 0.0 if exempt else round(a["early_min"] * rate, 2)

        def slab(limit):
            if exempt:
                return 0, 0.0
            hd = math.floor(max(0, marks - limit) / amr.MARKS_PER_HALFDAY)
            return hd, round(hd * half_day_rs, 2)

        def inc(month):
            if exempt or not base:
                return "-", 0.0
            tier = amr.incentive_tier(marks, month)
            if tier == "-":
                tier = "NONE"       # the live code's own '-' tier, spelt out
            if tier == "FULL":
                return tier, round(base / 30, 2)
            if tier == "HALF":
                return tier, round(base / 60, 2)
            return tier, 0.0

        hd_aug, ded_aug = slab(half_aug)
        hd_str, ded_str = slab(half_strict)
        tier_aug, inc_aug = inc(ym)
        tier_str, inc_str = inc(STRICT_YM)

        new_aug_total = round(ded_aug + early_rs + fine_uninf + fine_excess, 2)
        new_str_total = round(ded_str + early_rs + fine_uninf + fine_excess, 2)

        # old flat system
        old_min = 0 if exempt else raw_late.get(uid, 0)
        old_late_rs = round(old_min * OLD_RATE_PER_MIN, 2)
        old_abs_days = max(0, a["absent"] - OLD_ABSENT_FREE)
        old_abs_rs = round(old_abs_days * day_rs, 2)
        old_total = round(old_late_rs + old_abs_rs, 2)

        g = grid.get(a["name"].strip().lower(), {"dress": 0, "icard": 0})
        dress_rs = 0.0 if exempt else g["dress"] * DRESS_RS
        icard_rs = 0.0 if exempt else g["icard"] * ICARD_RS

        rows.append({
            "Name": a["name"], "Base salary": base,
            "Present": a["present"], "Absent": a["absent"],
            "Late marks": marks, "Grace days used": a["grace_days"],
            "Raw late min (all)": old_min,
            "Early-dep min": 0 if exempt else a["early_min"],
            "AUG half-days": hd_aug, "AUG marks Rs": ded_aug,
            "STRICT half-days": hd_str, "STRICT marks Rs": ded_str,
            "Early Rs": early_rs,
            "Uninformed-absent Rs": fine_uninf, "Excess-absent Rs": fine_excess,
            "NEW Aug total": new_aug_total,
            "NEW Strict total": new_str_total,
            "AUG incentive": "%s %s" % (tier_aug, money(inc_aug)),
            "STRICT incentive": "%s %s" % (tier_str, money(inc_str)),
            "OLD late Rs": old_late_rs,
            "OLD absent days cut": old_abs_days, "OLD absent Rs": old_abs_rs,
            "OLD total": old_total,
            "Diff Aug vs OLD": round(new_aug_total - old_total, 2),
            "Diff Strict vs OLD": round(new_str_total - old_total, 2),
            "Dress days": g["dress"], "Dress Rs (full)": dress_rs,
            "I-card days": g["icard"], "I-card Rs (full)": icard_rs,
            "exempt": "Y" if exempt else "",
        })
    return rows, review_note, grid_err, (half_aug, half_strict)


def write_csv(ym, rows):
    p = os.path.join(BASE, "scenario_%s.csv" % ym)
    cols = [c for c in rows[0].keys()] if rows else ["Name"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


def render_document(ym, rows, review_note, grid_err, limits, back_href=None):
    """Return the complete self-contained scenario HTML as a string. Used both by
    write_html (CLI, writes to file) and by the Staff Register web route (S199_SCEN2,
    returns it inline behind the salary gate). back_href, when given, adds a small
    'Back to Salary' link at the top so the register page has a way home."""
    half_aug, half_strict = limits
    e = html.escape

    def td(v, num=True):
        return '<td class="%s">%s</td>' % ("n" if num else "", e(str(v)))

    main_cols = ["Name", "Present", "Absent", "Late marks", "Grace days used",
                 "Raw late min (all)", "Early-dep min",
                 "AUG marks Rs", "Early Rs", "Uninformed-absent Rs",
                 "Excess-absent Rs", "NEW Aug total", "NEW Strict total",
                 "OLD late Rs", "OLD absent Rs", "OLD total",
                 "Diff Aug vs OLD", "Diff Strict vs OLD"]
    disc_cols = ["Name", "Dress days", "Dress Rs (full)", "I-card days",
                 "I-card Rs (full)"]

    def table(cols, rws, totals=True):
        out = ["<table><thead><tr>"]
        out += ["<th>%s</th>" % e(c) for c in cols]
        out.append("</tr></thead><tbody>")
        for r in rws:
            out.append("<tr>")
            for c in cols:
                out.append(td(r[c], num=(c != "Name")))
            out.append("</tr>")
        if totals and rws:
            out.append('<tr class="tot"><td>TOTAL</td>')
            for c in cols[1:]:
                try:
                    s = sum(float(r[c]) for r in rws)
                    out.append(td(money(s) if s == round(s, 2) else s))
                except (TypeError, ValueError):
                    out.append("<td></td>")
            out.append("</tr>")
        out.append("</tbody></table>")
        return "".join(out)

    dress_total = sum(r["Dress Rs (full)"] + r["I-card Rs (full)"] for r in rows)
    body = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Deduction scenario %s</title><style>
 body{font-family:Segoe UI,Arial,sans-serif;font-size:12px;margin:18px;color:#222}
 h1{font-size:17px;margin:0 0 2px} h2{font-size:14px;margin:18px 0 4px}
 .sub{color:#666;margin:0 0 10px}
 table{border-collapse:collapse;width:100%%;margin:6px 0}
 th,td{border:1px solid #bbb;padding:3px 6px;text-align:left}
 th{background:#f0ede6;font-size:11px}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 tr.tot td{font-weight:bold;background:#faf7ef}
 .note{background:#fff8e1;border:1px solid #e0c060;padding:6px 8px;margin:8px 0}
 a.back{display:inline-block;margin:0 0 8px;color:#0a5;text-decoration:none;font-weight:bold}
 @media print{body{margin:8mm} a.back{display:none}}
</style></head><body>
%s
<h1>Deduction scenario — %s (SCENARIO ONLY — nothing here is applied to pay)</h1>
<p class="sub">Month-to-date. New policy figures use the live report's own bands
(&le;10 grace ×8 days · 11–29 = 1 mark · 30–59 = 2 · &ge;60 = 2/3). AUG slab:
half-days = (marks − %d)÷3 · STRICT (from Sept): (marks − %d)÷3 · half-day =
salary÷60. OLD system: Rs.%s per late minute (every minute%s) + day salary
(base÷30) per absent beyond %d. D332: July AND August are preview-only —
enforcement is a setting you switch when the notice is served.</p>
<div class="note">%s%s</div>
<h2>1 · Mandatory-logic comparison (dress / I-card NOT included)</h2>
%s
<h2>2 · Dress &amp; I-card — DISCRETIONARY (computed in full; your call how much to waive)</h2>
%s
<p>Month total if waived none: <b>Rs.%s</b> · if half waived: <b>Rs.%s</b> ·
if fully waived: <b>Rs.0</b>. Rs.%d per marked day each, register-grid marked,
issuance-gated. Arjun exempt.</p>
<h2>3 · Incentive (the give-back side, per the notice)</h2>
%s
</body></html>""" % (
        e(ym),
        ('<a class="back" href="%s">&larr; Back to Salary</a>' % e(back_href))
        if back_href else "",
        e(ym), half_aug, half_strict, money(OLD_RATE_PER_MIN),
        "" if OLD_GRACE_MIN == 0 else ", after %d min" % OLD_GRACE_MIN,
        OLD_ABSENT_FREE,
        e(review_note),
        (" &middot; DRESS/I-CARD: %s — shown as ZERO" % e(grid_err)) if grid_err else "",
        table(main_cols, rows),
        table(disc_cols, rows),
        money(dress_total), money(dress_total / 2), DRESS_RS,
        table(["Name", "AUG incentive", "STRICT incentive"], rows, totals=False))
    return body


def write_html(ym, rows, review_note, grid_err, limits):
    p = os.path.join(BASE, "scenario_%s.html" % ym)
    with open(p, "w", encoding="utf-8") as f:
        f.write(render_document(ym, rows, review_note, grid_err, limits))
    return p


def selftest():
    print("att_scenario selftest: import wiring only (the numeric checks run "
          "offline in the build sandbox; on the box this proves the imports).")
    import att_core          # noqa
    import att_config        # noqa
    import att_month_report  # noqa
    print("imports OK:", "att_core", "att_config", "att_month_report v2.6"
          if "v2.6" in (att_month_report.__doc__ or "") else "att_month_report")
    print("PASS")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--selftest":
        selftest()
        return
    ym = sys.argv[1]
    try:
        datetime.datetime.strptime(ym, "%Y-%m")
    except ValueError:
        print("Month must look like 2026-08")
        sys.exit(1)
    rows, review_note, grid_err, limits = build(ym)
    # F-31: no salary/Rs values on the console
    print("Scenario computed for %s — %d staff." % (ym, len(rows)))
    print("NOTE:", review_note)
    if grid_err:
        print("DRESS/I-CARD:", grid_err, "— shown as zero in the files.")
    p1 = write_csv(ym, rows)
    p2 = write_html(ym, rows, review_note, grid_err, limits)
    print("Written: %s\nWritten: %s  (browser -> print A4)" % (p1, p2))
    print("These files hold salary figures — keep them OUT of the git tree (F-31/D320).")


if __name__ == "__main__":
    main()
