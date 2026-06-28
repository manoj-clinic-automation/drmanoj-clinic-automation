"""
att_core.py  —  attendance calculation engine (standard library only).

Reads punches.csv (from the listener) and staff_master.csv (rebuilt from the
salary workbook).  Computes a per-day attendance table using each person's OWN
weekday/Sunday shift timings.  No external dependencies.
"""
import csv
import os
import datetime
import att_config as cfg


def _parse_dt(s):
    return datetime.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")


def _parse_t(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%H:%M").time()
    except ValueError:
        return None


def load_staff():
    """Return {user_id: {...all fields...}} from staff_master.csv."""
    staff = {}
    with open(cfg.STAFF_MASTER, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                uid = int(row["user_id"])
            except (KeyError, ValueError):
                continue
            staff[uid] = {
                "name": row.get("name", f"#{uid}"),
                "department": row.get("department", ""),
                "base_salary": row.get("base_salary", ""),
                "allowed_offs": row.get("allowed_offs", ""),
                "wd_start": _parse_t(row.get("wd_start")),
                "wd_end": _parse_t(row.get("wd_end")),
                "sun_start": _parse_t(row.get("sun_start")),
                "sun_end": _parse_t(row.get("sun_end")),
                "active": (row.get("active", "Y").strip().upper() != "N"),
                "timing_note": row.get("timing_note", ""),
            }
    return staff


def load_punches():
    """Return a de-duplicated list of (user_id, datetime) from punches.csv."""
    seen, rows = set(), []
    if not os.path.exists(cfg.PUNCH_CSV):
        return rows
    with open(cfg.PUNCH_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                uid = int(row["user_id"])
                dt = _parse_dt(row["datetime"])
            except (KeyError, ValueError):
                continue
            key = (uid, row["datetime"])
            if key in seen:
                continue
            seen.add(key)
            rows.append((uid, dt))
    return rows


def _shift_for(info, is_sunday):
    if is_sunday and info["sun_start"]:
        return info["sun_start"], info["sun_end"]
    return info["wd_start"], info["wd_end"]


def compute_day(target_date, staff=None, punches=None):
    """Build the attendance picture for one calendar date, shift-aware."""
    if staff is None:
        staff = load_staff()
    if punches is None:
        punches = load_punches()
    is_sunday = target_date.weekday() == 6

    byuser = {}
    for uid, dt in punches:
        if dt.date() == target_date:
            byuser.setdefault(uid, []).append(dt)

    present, absent = [], []
    for uid, info in sorted(staff.items()):
        if uid in cfg.EXCLUDE_IDS or not info["active"]:
            continue
        s_start, s_end = _shift_for(info, is_sunday)
        times = sorted(byuser.get(uid, []))
        if times:
            first, last = times[0], times[-1]
            n = len(times)
            hours = round((last - first).total_seconds() / 3600, 2) if n >= 2 else None
            # late — only when the first punch is plausibly an arrival
            late, late_min = False, 0
            if s_start and not (is_sunday and not cfg.FLAG_LATE_ON_SUNDAY):
                sched = datetime.datetime.combine(target_date, s_start) \
                        + datetime.timedelta(minutes=cfg.GRACE_MIN)
                sched_end = datetime.datetime.combine(target_date, s_end) if s_end else None
                if first > sched and (sched_end is None or first <= sched_end):
                    late = True
                    late_min = int((first - sched).total_seconds() // 60)
            # early departure (only meaningful with an out-punch)
            early = False
            if n >= 2 and s_end:
                sched_end = datetime.datetime.combine(target_date, s_end)
                if (sched_end - last).total_seconds() / 60 >= cfg.EARLY_THRESHOLD_MIN:
                    early = True
            present.append({
                "uid": uid, "name": info["name"], "department": info["department"],
                "first": first, "last": last, "n": n, "hours": hours,
                "late": late, "late_min": late_min, "early": early,
                "likely_in": (n % 2 == 1),
            })
        else:
            absent.append({"uid": uid, "name": info["name"], "department": info["department"]})

    present.sort(key=lambda r: r["first"])
    absent.sort(key=lambda r: r["name"])
    return {
        "date": target_date,
        "is_sunday": is_sunday,
        "present": present,
        "absent": absent,
        "present_count": len(present),
        "absent_count": len(absent),
        "total": len(present) + len(absent),
        "late_count": sum(1 for r in present if r["late"]),
        "early_count": sum(1 for r in present if r["early"]),
    }
