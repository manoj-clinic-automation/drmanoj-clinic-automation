#!/usr/bin/env python3
"""S248_SALARY_RAISE -- the owner's salary raise, applied to the staff master.

The owner, 13-Sep-2026: "awdhesh - increase by 500 / sandeep - increase by 600",
to apply from the August 2026 salary.

base_salary lives once per person in staff_master.csv and carries no effective-from
date, so this is the whole change: two cells. August 2026 is NOT locked, so the
August pack recomputes with the new figures; July 2026 IS locked and its official
total is stored, so nothing already paid can move.

Refuses unless each person is present and still sitting at exactly the figure this
raise was worked out from. Backs up first, writes atomically, prints before and
after, and says ALREADY APPLIED on a second run without touching the file.

  usage: python3 raise_salary_s248.py --apply [path/to/staff_master.csv]
         python3 raise_salary_s248.py --dry   [path/to/staff_master.csv]
"""
import csv
import io
import os
import shutil
import sys
import datetime

DEFAULT = "/root/staff_master.csv"

# name -> (the figure it must be now, the figure it becomes)
RAISE = {
    "Awdhesh": (10000, 10500),      # +500
    "Sandip":  (7400,  8000),       # +600
}


def _num(v):
    try:
        return float(str(v).strip() or 0)
    except ValueError:
        return None


def read_master(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    rows = list(csv.DictReader(io.StringIO(text)))
    fields = csv.DictReader(io.StringIO(text)).fieldnames or []
    return text, rows, fields


def plan(rows):
    """(what changes, what is already done, what is wrong) -- nothing is written."""
    todo, done, stop = [], [], []
    seen = {}
    for r in rows:
        nm = (r.get("name") or "").strip()
        if nm in RAISE:
            seen.setdefault(nm, []).append(r)
    for nm, (was, now) in RAISE.items():
        hits = seen.get(nm, [])
        if not hits:
            stop.append("%s is not in the staff master" % nm)
            continue
        if len(hits) > 1:
            stop.append("%s appears %d times in the staff master" % (nm, len(hits)))
            continue
        cur = _num(hits[0].get("base_salary"))
        if cur is None:
            stop.append("%s has a base_salary that is not a number" % nm)
        elif cur == float(now):
            done.append("%s is already Rs %d" % (nm, now))
        elif cur != float(was):
            stop.append("%s is Rs %g, not the Rs %d this raise was worked out from "
                        "-- someone has changed it; nothing applied" % (nm, cur, was))
        else:
            todo.append((nm, int(cur), now, hits[0]))
    return todo, done, stop


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode not in ("--apply", "--dry"):
        raise SystemExit(__doc__)
    path = argv[2] if len(argv) > 2 else DEFAULT
    if not os.path.exists(path):
        raise SystemExit("REFUSED: %s does not exist" % path)
    text, rows, fields = read_master(path)
    if "name" not in fields or "base_salary" not in fields:
        raise SystemExit("REFUSED: %s has no name/base_salary column" % path)

    todo, done, stop = plan(rows)
    for line in done:
        print("   already: " + line)
    if stop:
        for line in stop:
            print("!! " + line)
        raise SystemExit(1)
    if not todo:
        print("== ALREADY APPLIED -- the staff master already carries this raise. "
              "Nothing changed.")
        return 0
    print("   before:")
    for nm, cur, now, _r in todo:
        print("     %-12s Rs %-8d ->  Rs %d" % (nm, cur, now))
    if mode == "--dry":
        print("== DRY RUN -- nothing written.")
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S248_SALARY_RAISE_%s" % (path, stamp)
    shutil.copy2(path, bak)
    for _nm, _cur, now, r in todo:
        r["base_salary"] = str(now)
    tmp = path + ".s248.tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    os.replace(tmp, path)
    try:
        shutil.copystat(bak, path)
    except OSError:
        pass

    _t2, rows2, _f2 = read_master(path)
    check = {(r.get("name") or "").strip(): _num(r.get("base_salary")) for r in rows2}
    for nm, _cur, now, _r in todo:
        if check.get(nm) != float(now):
            shutil.copy2(bak, path)
            raise SystemExit("!! REFUSED after writing: %s did not land -- the file has "
                             "been put back from %s" % (nm, bak))
    if len(rows2) != len(rows):
        shutil.copy2(bak, path)
        raise SystemExit("!! REFUSED after writing: the row count changed -- put back "
                         "from %s" % bak)
    print("   after:")
    for nm, _cur, now, _r in todo:
        print("     %-12s Rs %d" % (nm, now))
    print("   backup: " + bak)
    print("== APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
