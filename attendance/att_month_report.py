"""
att_month_report.py — monthly salary-inputs report (read-only; std-lib only).

Runs beside att_core.py / att_config.py / staff_master.csv / punches.csv on the VPS.
Computes, for one month, per active staff member:
  Present, Absent, Late marks (policy), Late minutes (raw), Extra minutes,
  >60-min-late days (owner review), Deduction half-days, Incentive tier.

POLICY (locked S151, effective Aug-2026):
  - Grace 10 min. Arrival >10 min after shift start = 1 late mark; >30 min = 2 marks.
  - >60 min late = counted separately for owner review (informed/uninformed is human judgment).
  - Every 3 marks in the month = 0.5 day salary deduction.
  - Incentive: Aug-2026 & Sep-2026 (ramp): FULL if marks <= 5, HALF if <= 8.
               From Oct-2026: FULL if marks <= 2, HALF if <= 5.
  - Sundays: never late (engine rule), extra time measured vs Sunday shift end.
  - Extra time counted only on days with a genuine out-punch (2+ punches).
Late detection itself comes from att_core.compute_day — engine and report can never disagree.

Usage:
  /root/wa/venv/bin/python3 /root/att_month_report.py 2026-08
  /root/wa/venv/bin/python3 /root/att_month_report.py --selftest

Outputs (written beside this script):
  salary_inputs_YYYY-MM.csv   — for records / Excel
  salary_inputs_YYYY-MM.html  — A4-printable (open in browser, Ctrl+P)

No file used by any other service is written. Never prints salary values.
"""
import sys
import os
import csv
import html
import datetime
import calendar

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

GRACE_POLICY_MIN = 10      # notice point 3
DOUBLE_MARK_MIN = 30       # notice point 3
REVIEW_MIN = 60            # notice point 4
MARKS_PER_HALFDAY = 3      # notice point 5
RAMP_MONTHS = {"2026-08", "2026-09"}   # notice point 6


def incentive_tier(marks, ym):
    if ym in RAMP_MONTHS:
        full, half = 5, 8
    else:
        full, half = 2, 5
    if marks <= full:
        return "FULL"
    if marks <= half:
        return "HALF"
    return "-"


def month_report(ym, att_core, cfg):
    year, mon = int(ym[:4]), int(ym[5:7])
    ndays = calendar.monthrange(year, mon)[1]
    today = datetime.date.today()
    staff = att_core.load_staff()
    punches = att_core.load_punches()

    acc = {}
    for uid, info in staff.items():
        if uid in cfg.EXCLUDE_IDS or not info["active"]:
            continue
        acc[uid] = {"name": info["name"], "present": 0, "absent": 0,
                    "marks": 0, "late_min": 0, "late_days": 0,
                    "extra_min": 0, "review60": 0}

    for d in range(1, ndays + 1):
        date = datetime.date(year, mon, d)
        if date > today:
            break
        day = att_core.compute_day(date, staff=staff, punches=punches)
        present_uids = set()
        for r in day["present"]:
            uid = r["uid"]
            if uid not in acc:
                continue
            present_uids.add(uid)
            a = acc[uid]
            a["present"] += 1
            # ---- policy marks from engine's raw late minutes ----
            lm = r["late_min"] if r["late"] else 0
            if lm > GRACE_POLICY_MIN:
                a["late_days"] += 1
                a["late_min"] += lm
                a["marks"] += 2 if lm > DOUBLE_MARK_MIN else 1
                if lm > REVIEW_MIN:
                    a["review60"] += 1
            # ---- extra time: genuine out-punch beyond shift end ----
            info = staff[uid]
            if day["is_sunday"] and info["sun_start"]:
                s_end = info["sun_end"]
            else:
                s_end = info["wd_end"]
            if r["n"] >= 2 and s_end:
                sched_end = datetime.datetime.combine(date, s_end)
                if r["last"] > sched_end:
                    a["extra_min"] += int((r["last"] - sched_end).total_seconds() // 60)
        if not day["is_sunday"]:
            for uid in acc:
                if uid not in present_uids:
                    acc[uid]["absent"] += 1

    rows = []
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        rows.append({
            "Name": a["name"],
            "Present": a["present"],
            "Absent": a["absent"],
            "Late marks": a["marks"],
            "Late days": a["late_days"],
            "Late minutes": a["late_min"],
            "Extra minutes": a["extra_min"],
            ">60min days (review)": a["review60"],
            "Deduction (half-days)": (a["marks"] // MARKS_PER_HALFDAY) * 0.5,
            "Incentive": incentive_tier(a["marks"], ym),
        })
    return rows


def write_outputs(ym, rows):
    heads = list(rows[0].keys()) if rows else []
    csv_path = os.path.join(BASE, f"salary_inputs_{ym}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=heads)
        w.writeheader()
        w.writerows(rows)

    cells = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(r[h]))}</td>" for h in heads) + "</tr>"
        for r in rows)
    head_cells = "".join(f"<th>{html.escape(h)}</th>" for h in heads)
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Salary inputs {ym}</title><style>
@page {{ size: A4 landscape; margin: 12mm; }}
body {{ font-family: Arial, sans-serif; }}
h2 {{ margin: 0 0 2mm 0; }} p {{ margin: 0 0 4mm 0; font-size: 10pt; color: #444; }}
table {{ border-collapse: collapse; width: 100%; font-size: 10pt; }}
th, td {{ border: 1px solid #999; padding: 3px 6px; text-align: center; }}
th {{ background: #1F4E79; color: #fff; }}
td:first-child {{ text-align: left; font-weight: bold; }}
</style></head><body>
<h2>Salary Inputs — {ym}</h2>
<p>Policy: grace 10 min; &gt;30 min = 2 marks; 3 marks = &frac12;-day deduction;
incentive {"ramp (FULL &le;5, HALF &le;8)" if ym in RAMP_MONTHS else "strict (FULL &le;2, HALF &le;5)"};
Sundays never late. Subtract Darpan's outstation days from his Absent before entry.
Generated {datetime.date.today().isoformat()}.</p>
<table><tr>{head_cells}</tr>
{cells}
</table></body></html>"""
    html_path = os.path.join(BASE, f"salary_inputs_{ym}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return csv_path, html_path


def print_table(rows):
    if not rows:
        print("No active staff / no data.")
        return
    heads = list(rows[0].keys())
    widths = [max(len(h), max(len(str(r[h])) for r in rows)) for h in heads]
    line = "  ".join(h.ljust(w) for h, w in zip(heads, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[h]).ljust(w) for h, w in zip(heads, widths)))


# ------------------------- selftest -------------------------
def selftest():
    """Synthetic month proving every rule. A check that cannot fail is not a check."""
    import tempfile
    import importlib
    tmp = tempfile.mkdtemp()
    staff_csv = os.path.join(tmp, "staff_master.csv")
    punch_csv = os.path.join(tmp, "punches.csv")
    with open(staff_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "department", "base_salary", "allowed_offs",
                    "wd_start", "wd_end", "sun_start", "sun_end", "active", "timing_note"])
        w.writerow([1, "TestA", "X", "", 2, "09:00", "21:00", "09:00", "15:00", "Y", ""])
        w.writerow([2, "TestB", "X", "", 2, "11:00", "21:00", "11:00", "15:00", "Y", ""])
        w.writerow([3, "TestGone", "X", "", 2, "09:00", "21:00", "", "", "N", ""])
    # June 2026: 1st = Monday; Sunday = 7th. Use days 1..7.
    P = [
        (1, "2026-06-01 09:05:00"),                      # 5 min late -> within grace, 0 marks
        (1, "2026-06-02 09:20:00"), (1, "2026-06-02 21:30:00"),  # 20m -> 1 mark; extra 30
        (1, "2026-06-03 09:45:00"),                      # 45m -> 2 marks
        (1, "2026-06-04 10:15:00"),                      # 75m -> 2 marks + review60
        (1, "2026-06-05 21:29:00"),                      # after shift end: NOT late (arrival implausible)
        (1, "2026-06-07 09:30:00"),                      # SUNDAY: never late
        # day 6 (Sat): absent for TestA
        (2, "2026-06-01 11:00:00"),                      # on time
        (2, "2026-06-07 14:00:00"), (2, "2026-06-07 15:40:00"),  # Sunday extra 40
        (3, "2026-06-01 09:00:00"),                      # inactive: ignored
    ]
    with open(punch_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "datetime"])
        for uid, dt in P:
            w.writerow([uid, dt])

    import att_config as cfg
    import att_core
    old_sm, old_pc = cfg.STAFF_MASTER, cfg.PUNCH_CSV
    cfg.STAFF_MASTER, cfg.PUNCH_CSV = staff_csv, punch_csv
    importlib.reload(att_core)  # att_core reads cfg at call time; reload for safety
    try:
        # freeze "today" past June so all 30 days count
        rows = month_report("2026-06", att_core, cfg)
        by = {r["Name"]: r for r in rows}
        assert "TestGone" not in by, "inactive staff leaked into report"
        a, b = by["TestA"], by["TestB"]
        # TestA: present 6 (d1-5,7); working days Jun = 30-4 Sundays... absents = workdays with no punch
        assert a["Present"] == 6, a
        assert a["Late marks"] == 1 + 2 + 2, a          # d2=1, d3=2, d4=2; d1 grace; d5 not late; d7 Sunday
        assert a["Late days"] == 3, a
        assert a["Late minutes"] == 20 + 45 + 75, a
        assert a[">60min days (review)"] == 1, a
        assert a["Extra minutes"] == 30, a              # only d2 has out-punch
        assert a["Deduction (half-days)"] == 0.5, a     # 5 marks // 3 = 1 -> 0.5
        assert incentive_tier(a["Late marks"], "2026-08") == "FULL"   # ramp: 5 <= 5
        assert incentive_tier(a["Late marks"], "2026-10") == "HALF"   # strict: 5 <= 5 half
        assert b["Late marks"] == 0 and b["Extra minutes"] == 40, b   # Sunday extra vs 15:00
        assert incentive_tier(0, "2026-10") == "FULL"
        assert incentive_tier(9, "2026-08") == "-"
    finally:
        cfg.STAFF_MASTER, cfg.PUNCH_CSV = old_sm, old_pc
    print("SELFTEST PASSED — all policy and engine-reuse checks OK")


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
    import att_core
    import att_config as cfg
    rows = month_report(ym, att_core, cfg)
    print_table(rows)
    csv_path, html_path = write_outputs(ym, rows)
    print(f"\nWritten: {csv_path}\nWritten: {html_path}  (open in browser -> print A4)")


if __name__ == "__main__":
    main()
