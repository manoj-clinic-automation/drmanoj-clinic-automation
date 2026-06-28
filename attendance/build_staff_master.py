#!/usr/bin/env python3
"""
build_staff_master.py  —  rebuild staff_master.csv from the salary workbook.

The salary workbook (Salary_System_2026.xlsx, "Staff Master" sheet) stays the
single source of truth for names, timings, Sunday timings, base salary and
allowed offs.  Run this whenever you add or change an employee there, then copy
the new staff_master.csv up to the VPS.

Usage:
    python build_staff_master.py
    python build_staff_master.py "C:\\path\\to\\Salary_System_2026.xlsx"

Output:  staff_master.csv  (next to this script)
"""
import sys
import re
import csv
import openpyxl

SRC = sys.argv[1] if len(sys.argv) > 1 else "Salary_System_2026.xlsx"
OUT = "staff_master.csv"


def split_timing(s):
    """'08:00-16:00' or '09:30-15:30 + 18:00-21:00' -> (start, end, raw_note)."""
    if not s:
        return "", "", ""
    times = re.findall(r"\d{1,2}:\d{2}", str(s))
    if not times:
        return "", "", ""
    start = times[0]
    end = times[-1]
    note = str(s).strip() if "+" in str(s) else ""   # keep raw only for split shifts
    return start, end, note


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["Staff Master"]
    rows = []
    for r in range(3, ws.max_row + 1):
        code = ws.cell(r, 1).value
        if code in (None, ""):
            continue  # no Emp Code -> not on the biometric device (salary-only)
        name = ws.cell(r, 2).value or f"#{code}"
        dept = ws.cell(r, 3).value or ""
        base = ws.cell(r, 4).value
        offs = ws.cell(r, 5).value
        wd_start, wd_end, wd_note = split_timing(ws.cell(r, 6).value)
        sun_start, sun_end, _ = split_timing(ws.cell(r, 7).value)
        rows.append({
            "user_id": int(code),
            "name": str(name).strip(),
            "department": str(dept).strip(),
            "base_salary": "" if base in (None, "") else int(base),
            "allowed_offs": "" if offs in (None, "") else offs,
            "wd_start": wd_start,
            "wd_end": wd_end,
            "sun_start": sun_start,
            "sun_end": sun_end,
            "active": "Y",
            "timing_note": wd_note,
        })

    cols = ["user_id", "name", "department", "base_salary", "allowed_offs",
            "wd_start", "wd_end", "sun_start", "sun_end", "active", "timing_note"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"Wrote {OUT} with {len(rows)} staff.")


if __name__ == "__main__":
    main()
