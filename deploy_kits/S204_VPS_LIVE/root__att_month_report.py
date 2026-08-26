"""
att_month_report.py — v2.6 (S196; v2 lineage S153) — monthly salary-inputs report
(read-only; std-lib only).

Runs beside att_core.py / att_config.py / staff_master.csv / punches.csv on the VPS.
Additive layer on the frozen attendance core (engine untouched; presence + punch pairs
come from att_core.compute_day; ALL policy math lives here so roster-based Sunday
shifts stay owner-policy, not engine data).

v2.6 (S196) — APPROVED PRESENT-REQUESTS FOLD AS PUNCHES:
  The Staff Register's mark-me-present flow (staff raises the SAME DAY only,
  checker verifies, the doctor approves) writes present_request rows in the
  register DB. This report reads the APPROVED ones read-only, fail-soft
  (ATT_REGISTER_DB, default /root/staff_register/staff_register.db) and merges
  each as a SYNTHETIC PUNCH at the request's server receipt time — so presence,
  the late bands, departure pairing with any real machine punch-out, and the
  review-file loop all treat the request exactly like a punch made at that
  moment. Request-backed days carry a '*' in the day grid. Pending, verified
  and rejected requests change NOTHING. If the register DB is unreachable the
  report runs exactly as v2.5 (a salary report must never go dark because a
  neighbouring database moved).

POLICY (D252/D253 as amended S153, notice v6 = the staff-facing law):
  Late bands (per episode, weekday or duty-Sunday):
    <= 10 min          : grace, free for at most GRACE_DAYS_CAP days/month;
                         from the (cap+1)th grace day, <=10 min = 1 mark.
    11-29 min          : 1 mark.
    30-59 min          : 2 marks.
    >= 60 min          : 2 marks informed / 3 marks uninformed (review file).
  Deductions (Option B slabs): half_days = floor(max(0, marks - half_limit) / 3).
    half_limit: Aug-2026 (ramp) = 8; from Sep-2026 (strict) = 5.
  Incentive: ramp (Aug-2026): FULL <=5, HALF <=8. Strict (Sep-2026 on): FULL <=2, HALF <=5.
    NOTE: S151 code ramped Aug+Sep; notice v5/v6 point 6 says strict FROM September.
    The notice wins (owner-confirmed S153).
  Early departure, three tiers (S153 punch-pattern ruling):
    ARTEFACT  last punch within 30 min of the first (accidental re-punch, no real
              punch-out) -> treated like a single punch: duty presumed done, no
              deduction, no OT. Greyed in the grid as a coaching list.
    SMALL     gap to shift end <= 120 min -> auto-deducted at 1x per-minute rate.
    EARLY_BIG gap > 120 min -> listed on the sheet with its would-be amount but
              NEVER auto-applied; owner rules on the printed sheet against the
              physical register.
  Single punch (n==1): presumed stayed till end of duty — no deduction, and no OT
    (OT always needs the out-punch, notice point 7).
  OT: out-punch beyond shift end = minutes x 2x per-minute rate — CANDIDATES ONLY,
    listed for owner approval (approval is human judgment; nothing auto-pays).
  Per-minute rate = base_salary / (30 x weekday shift minutes). Half-day = salary/60.
  Absents: uninformed = Rs.50 each (review file); > ABSENT_FREE_DAYS days = Rs.100/day
    from the next day (all absents count for the 100-line).
  Sunday roster (D253, from 2026-09; before that Sundays follow sun_start columns):
    group A: duty 1st & 3rd Sundays (WEEKDAY shift); other Sundays OFF (ignored).
    group B: duty 2nd & 4th Sundays (WEEKDAY shift); other Sundays OFF.
    group C: every Sunday, sun_start-sun_end (half-day pattern).
    group ARJ: as C for presence; minutes_exempt.
    5th Sunday: normal full working day for ALL (WEEKDAY shift).
  minutes_exempt staff (Arjun): presence/absence + absent fines only; no marks,
    no early-departure deduction, no OT.
  Habitual tracker: months in the calendar year with marks > half_limit; flag at >= 3.

Informed-flag loop:
  First run writes review_YYYY-MM.csv (ABSENT + LATE60 rows, informed=Y default).
  Owner edits informed=N against the reception register, reruns; the file is never
  overwritten once present.

Usage:
  /root/wa/venv/bin/python3 /root/att_month_report.py 2026-08
  /root/wa/venv/bin/python3 /root/att_month_report.py --selftest

Outputs (written beside this script):
  salary_inputs_YYYY-MM.csv       — summary, for records / Excel
  deductions_extras_YYYY-MM.csv   — per-line log (date, item, minutes, Rs.) for
                                    explaining any figure to staff
  salary_inputs_YYYY-MM.html      — A4-printable; summary + the log as its own sheet
  review_YYYY-MM.csv              — informed flags (created once, owner-edited)

No file used by any other service is written. Console output never prints salary
values or Rs. amounts (F-31); money appears only in the output files.
"""
import sys
import os
import csv
import html
import math
import datetime
import calendar

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

GRACE_MIN_POLICY = 10          # notice point 2/3: <=10 min band
GRACE_DAYS_CAP = 8             # notice point 2: at most 8 free grace days/month
BAND2_MIN = 30                 # notice point 3: 30-59 = 2 marks
BAND3_MIN = 60                 # notice point 4: >=60 = 2 informed / 3 uninformed
MARKS_PER_HALFDAY = 3          # notice point 5 (Option B slab)
RAMP_MONTHS = {"2026-08"}      # notice point 6: strict FROM September (notice wins)
ROSTER_FROM = os.environ.get("ATT_ROSTER_FROM", "2099-01")
# D341b (S200): the D253 Sunday roster is NOT adopted yet — groups are unassigned
# and rostering is only a thought. The era (5th-Sunday full-day rule included)
# now waits for an EXPLICIT switch: set ATT_ROSTER_FROM (e.g. "2026-10") in the
# environment/att_config when the owner actually adopts it. Was: "2026-09" —
# which would have made 29 Nov 2026 a full working Sunday for everyone, unasked.
ABSENT_FREE_DAYS = 3           # notice point 9
FINE_UNINFORMED = 50           # notice point 8
FINE_EXCESS_ABSENT = 100       # notice point 9
HABITUAL_FLAG_AT = 3           # notice point 10
DAYS_BASIS = 30                # owner ruling S153: 30-day month
ARTEFACT_WINDOW_MIN = 30       # last punch within 30 min of first = double-punch artefact
EARLY_AUTO_MAX_MIN = 120       # early departure auto-deducts only up to 2 h; bigger = EARLY_BIG (review on sheet)

_TODAY_OVERRIDE = None         # selftest only; never set in production

# v2.6 (S196): the Staff Register DB holding approved present-requests.
# Read-only + fail-soft — see load_present_requests().
REGISTER_DB_DEFAULT = "/root/staff_register/staff_register.db"

VALID_GROUPS = {"A", "B", "C", "ARJ", ""}


def load_present_requests(ym):
    """{(uid, 'YYYY-MM-DD'): datetime} — APPROVED mark-me-present requests for
    ym from the Staff Register DB (read-only URI; the register owns the store).
    The request's server receipt time IS the punch time (S196). Empty dict on
    ANY problem — the report then behaves exactly like v2.5."""
    import sqlite3
    path = os.environ.get("ATT_REGISTER_DB", REGISTER_DB_DEFAULT)
    out = {}
    if not path or not os.path.exists(path):
        return out
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
        try:
            rows = con.execute(
                "SELECT staff_id, reg_date, req_ts FROM present_request "
                "WHERE status='approved' AND reg_date LIKE ?",
                (ym + "-%",)).fetchall()
        finally:
            con.close()
    except Exception:
        return {}
    for uid, dstr, ts in rows:
        try:
            out[(int(uid), str(dstr))] = datetime.datetime.strptime(
                str(ts).strip(), "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            continue
    return out


def limits_for(ym):
    """(full_limit, half_limit) for the incentive; half_limit doubles as the
    Option-B deduction threshold."""
    if ym in RAMP_MONTHS:
        return 5, 8
    return 2, 5


def incentive_tier(marks, ym):
    full, half = limits_for(ym)
    if marks <= full:
        return "FULL"
    if marks <= half:
        return "HALF"
    return "-"


def marks_for_late(raw_late, grace_days_used):
    """Return (marks, grace_day_consumed, is_late60) for one day's raw late minutes.
    raw_late is minutes after shift start (no engine grace applied)."""
    if raw_late <= 0:
        return 0, False, False
    if raw_late <= GRACE_MIN_POLICY:
        if grace_days_used < GRACE_DAYS_CAP:
            return 0, True, False
        return 1, False, False          # notice point 2: beyond the cap, <=10 min = 1 mark
    if raw_late < BAND2_MIN:
        return 1, False, False          # 11-29
    if raw_late < BAND3_MIN:
        return 2, False, False          # 30-59
    return 2, False, True               # >=60: 2 now; +1 later if uninformed


def sunday_index(date):
    """1..5 — which Sunday of the month this date is."""
    return (date.day - 1) // 7 + 1


def load_staff_policy():
    """Read staff_master.csv directly for the v2 columns (sunday_group,
    minutes_exempt) plus salary/shifts. Additive: unknown columns default safe."""
    import att_config as cfg
    out = {}
    with open(cfg.STAFF_MASTER, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                uid = int(row["user_id"])
            except (KeyError, ValueError):
                continue
            grp = (row.get("sunday_group") or "").strip().upper()
            if grp not in VALID_GROUPS:
                raise SystemExit(f"staff_master.csv: bad sunday_group '{grp}' for uid {uid}")
            try:
                sal = float(row.get("base_salary") or 0)
            except ValueError:
                sal = 0.0
            out[uid] = {
                "sunday_group": grp,
                "minutes_exempt": (row.get("minutes_exempt") or "").strip().upper() in ("Y", "1", "TRUE"),
                "base_salary": sal,
            }
    return out


def duty_shift(date, ym, info, pol):
    """Resolve the day's duty shift per D253 roster. Returns (start, end) times,
    or (None, None) when the person is OFF (day fully ignored)."""
    if date.weekday() != 6:
        return info["wd_start"], info["wd_end"]
    # Sunday:
    if ym < ROSTER_FROM:
        # pre-roster behaviour: sun columns as-is; empty sun_start = off
        if info["sun_start"]:
            return info["sun_start"], info["sun_end"]
        return None, None
    grp = pol["sunday_group"]
    si = sunday_index(date)
    if si == 5:
        return info["wd_start"], info["wd_end"]          # 5th Sunday: normal full day, all
    if grp == "A":
        return (info["wd_start"], info["wd_end"]) if si in (1, 3) else (None, None)
    if grp == "B":
        return (info["wd_start"], info["wd_end"]) if si in (2, 4) else (None, None)
    if grp in ("C", "ARJ"):
        return info["sun_start"], info["sun_end"]        # every-Sunday half-day pattern
    # no group assigned: pre-roster fallback
    if info["sun_start"]:
        return info["sun_start"], info["sun_end"]
    return None, None


def per_min_rate(info, pol):
    """1x per-minute rate = salary / (30 x weekday shift minutes)."""
    if not (info["wd_start"] and info["wd_end"] and pol["base_salary"] > 0):
        return 0.0
    m = (info["wd_end"].hour * 60 + info["wd_end"].minute) \
        - (info["wd_start"].hour * 60 + info["wd_start"].minute)
    if m <= 0:
        return 0.0
    return pol["base_salary"] / (DAYS_BASIS * m)


def load_review(path):
    """{(uid, 'YYYY-MM-DD', type): informed_bool} — empty dict when no file yet."""
    flags = {}
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                uid = int(row["user_id"])
            except (KeyError, ValueError):
                continue
            key = (uid, row["date"].strip(), row["type"].strip().upper())
            flags[key] = (row.get("informed", "Y").strip().upper() != "N")
    return flags


def write_review(path, events):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "date", "type", "informed"])
        for uid, name, date, typ in events:
            w.writerow([uid, name, date, typ, "Y"])


def collect_month(ym, att_core, cfg, pol_all, upto_today=True):
    """One pass over the month. Returns (acc, log, review_events).
    acc[uid] = counters; log = list of per-line explain rows;
    review_events = [(uid,name,date,'ABSENT'|'LATE60')]."""
    year, mon = int(ym[:4]), int(ym[5:7])
    ndays = calendar.monthrange(year, mon)[1]
    today = _TODAY_OVERRIDE or datetime.date.today()
    staff = att_core.load_staff()
    punches = att_core.load_punches()
    # v2.6 (S196): approved present-requests become synthetic punches at their
    # server receipt time. load_punches() returns a fresh list — safe to extend.
    preq = load_present_requests(ym)
    for (uid, dstr), dt in preq.items():
        punches.append((uid, dt))

    acc, log, review_events = {}, [], []
    for uid, info in staff.items():
        if uid in cfg.EXCLUDE_IDS or not info["active"]:
            continue
        pol = pol_all.get(uid, {"sunday_group": "", "minutes_exempt": False, "base_salary": 0.0})
        acc[uid] = {"name": info["name"], "info": info, "pol": pol,
                    "present": 0, "absent": 0, "absent_dates": [],
                    "marks": 0, "late_min": 0, "late_days": 0,
                    "grace_days": 0, "late60_dates": [],
                    "early_min": 0, "ot_min": 0, "noout_days": 0,
                    "earlybig": [], "grid": {}}

    for d in range(1, ndays + 1):
        date = datetime.date(year, mon, d)
        if upto_today and date > today:
            break
        day = att_core.compute_day(date, staff=staff, punches=punches)
        by_present = {r["uid"]: r for r in day["present"]}
        for uid, a in acc.items():
            info, pol = a["info"], a["pol"]
            s_start, s_end = duty_shift(date, ym, info, pol)
            r = by_present.get(uid)
            if s_start is None:
                a["grid"][d] = {"st": "OFF"}
                continue                                  # OFF day: fully ignored
            if r is None:
                a["absent"] += 1
                a["absent_dates"].append(date.isoformat())
                a["grid"][d] = {"st": "AB"}
                review_events.append((uid, a["name"], date.isoformat(), "ABSENT"))
                continue
            a["present"] += 1
            cell = {"st": "OK", "late": 0, "marks": 0, "early": 0,
                    "ebig": 0, "ot": 0, "art": False,
                    "in": r["first"].strftime("%H:%M"), "out": ""}
            if (uid, date.isoformat()) in preq:       # v2.6: request-backed day
                cell["req"] = True
            a["grid"][d] = cell
            if pol["minutes_exempt"]:
                continue                                  # Arjun: presence only
            sched_start = datetime.datetime.combine(date, s_start)
            sched_end = datetime.datetime.combine(date, s_end) if s_end else None
            first, last, n = r["first"], r["last"], r["n"]
            # ---- lateness (first punch must be a plausible arrival) ----
            if sched_end is None or first <= sched_end:
                raw_late = max(0, int((first - sched_start).total_seconds() // 60))
            else:
                raw_late = 0
            m, grace_used, is60 = marks_for_late(raw_late, a["grace_days"])
            if grace_used:
                a["grace_days"] += 1
            if m:
                a["marks"] += m
                a["late_days"] += 1
                a["late_min"] += raw_late
                cell["late"], cell["marks"] = raw_late, m
                log.append((uid, date.isoformat(), "LATE", raw_late, 0.0,
                            f"{raw_late} min late -> {m} mark(s)"))
            if is60:
                a["late60_dates"].append(date.isoformat())
                review_events.append((uid, a["name"], date.isoformat(), "LATE60"))
            # ---- departure side ----
            if sched_end is None:
                continue
            gap_ff = int((last - first).total_seconds() // 60)
            if n == 1 or gap_ff <= ARTEFACT_WINDOW_MIN:
                a["noout_days"] += 1                      # no real punch-out: duty presumed done
                cell["art"] = True
                continue
            cell["out"] = last.strftime("%H:%M")
            if last < sched_end:
                em = int((sched_end - last).total_seconds() // 60)
                if em <= 0:
                    pass
                elif em <= EARLY_AUTO_MAX_MIN:
                    a["early_min"] += em
                    cell["early"] = em
                    log.append((uid, date.isoformat(), "EARLY_DEP", em, 0.0,
                                f"left {em} min before shift end"))
                else:
                    a["earlybig"].append((date.isoformat(),
                                          first.strftime("%H:%M"),
                                          last.strftime("%H:%M"), em))
                    cell["ebig"] = em
                    log.append((uid, date.isoformat(), "EARLY_BIG", em, 0.0,
                                f"last punch {last.strftime('%H:%M')}, {em} min before "
                                f"shift end — NOT applied; rule on sheet vs register"))
            elif last > sched_end:
                om = int((last - sched_end).total_seconds() // 60)
                if om > 0:
                    a["ot_min"] += om
                    cell["ot"] = om
                    log.append((uid, date.isoformat(), "OT_CANDIDATE", om, 0.0,
                                f"{om} min beyond shift end (needs owner approval)"))
    return acc, log, review_events


def habitual_months(ym, att_core, cfg, pol_all):
    """{uid: months-over-cap so far this calendar year, INCLUDING ym}."""
    year, mon = int(ym[:4]), int(ym[5:7])
    over = {}
    for m in range(1, mon + 1):
        mym = f"{year}-{m:02d}"
        acc, _, _ = collect_month(mym, att_core, cfg, pol_all)
        _, half = limits_for(mym)
        for uid, a in acc.items():
            if a["present"] + a["absent"] == 0:
                continue
            if a["marks"] > half:
                over[uid] = over.get(uid, 0) + 1
    return over


def month_report(ym, att_core, cfg):
    pol_all = load_staff_policy()
    acc, log, review_events = collect_month(ym, att_core, cfg, pol_all)

    review_path = os.path.join(BASE, f"review_{ym}.csv")
    flags = load_review(review_path)
    first_pass = flags is None
    if first_pass:
        write_review(review_path, sorted(set(review_events)))
        flags = {}

    over = habitual_months(ym, att_core, cfg, pol_all)
    _, half_limit = limits_for(ym)

    rows, money_log = [], []
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        pol, info = a["pol"], a["info"]
        rate = per_min_rate(info, pol)
        half_day_rs = pol["base_salary"] / 60 if pol["base_salary"] else 0.0

        # +1 mark per uninformed >=60-min day
        marks = a["marks"]
        for dstr in a["late60_dates"]:
            if not flags.get((uid, dstr, "LATE60"), True):
                marks += 1
                money_log.append((a["name"], dstr, "LATE60 UNINFORMED", "", 0.0,
                                  "+1 late mark (uninformed >=60 min)"))
        # Option B slab deduction
        half_days = math.floor(max(0, marks - half_limit) / MARKS_PER_HALFDAY)
        ded_marks_rs = round(half_days * half_day_rs, 2)
        if half_days:
            money_log.append((a["name"], "-", "LATE-MARKS DEDUCTION",
                              f"{marks} marks", ded_marks_rs,
                              f"floor(max(0,{marks}-{half_limit})/3)={half_days} half-day(s)"))
        # early departures (skip minutes-exempt)
        ded_early_rs = 0.0
        if not pol["minutes_exempt"] and a["early_min"]:
            ded_early_rs = round(a["early_min"] * rate, 2)
            money_log.append((a["name"], "-", "EARLY-DEPARTURE DEDUCTION",
                              f"{a['early_min']} min", ded_early_rs,
                              "missing minutes x 1x per-minute rate"))
        # absent fines
        uninf = sum(1 for dstr in a["absent_dates"]
                    if not flags.get((uid, dstr, "ABSENT"), True))
        fine_uninf = uninf * FINE_UNINFORMED
        excess = max(0, a["absent"] - ABSENT_FREE_DAYS)
        fine_excess = excess * FINE_EXCESS_ABSENT
        if fine_uninf:
            money_log.append((a["name"], "-", "UNINFORMED-ABSENT FINE",
                              f"{uninf} day(s)", float(fine_uninf),
                              f"Rs.{FINE_UNINFORMED} x {uninf} (register-checked)"))
        if fine_excess:
            money_log.append((a["name"], "-", "EXCESS-ABSENT FINE",
                              f"{excess} day(s)", float(fine_excess),
                              f"Rs.{FINE_EXCESS_ABSENT}/day beyond {ABSENT_FREE_DAYS}"))
        # OT candidates (extra payment side)
        ot_rs = 0.0
        if not pol["minutes_exempt"] and a["ot_min"]:
            ot_rs = round(a["ot_min"] * rate * 2, 2)
            money_log.append((a["name"], "-", "OT CANDIDATE (needs approval)",
                              f"{a['ot_min']} min", ot_rs,
                              "minutes x 2x rate — pay only what owner approves"))
        tier = incentive_tier(marks, ym)
        inc_rs = 0.0
        if pol["base_salary"]:
            if tier == "FULL":
                inc_rs = round(pol["base_salary"] / 30, 2)
            elif tier == "HALF":
                inc_rs = round(pol["base_salary"] / 60, 2)
        if inc_rs:
            money_log.append((a["name"], "-", f"INCENTIVE ({tier})", "-", inc_rs,
                              "1 day salary (FULL) / half day (HALF) — added to net"))
        net_rs = round(inc_rs + ot_rs - ded_marks_rs - ded_early_rs
                       - fine_uninf - fine_excess, 2)

        # per-line detail from the day log
        for luid, dstr, typ, minutes, _rs, note in log:
            if luid != uid:
                continue
            rs = 0.0
            if typ == "EARLY_DEP":
                rs = round(minutes * rate, 2)
            elif typ == "OT_CANDIDATE":
                rs = round(minutes * rate * 2, 2)
            elif typ == "EARLY_BIG":
                note = f"would be Rs.{round(minutes * rate, 2)} if confirmed — " + note
            money_log.append((a["name"], dstr, typ, f"{minutes} min", rs, note))

        rows.append({
            "Name": a["name"],
            "Group": pol["sunday_group"] or "-",
            "Present": a["present"],
            "Absent": a["absent"],
            "Late marks": marks,
            "Late days": a["late_days"],
            "Late minutes": a["late_min"],
            "Grace days used": a["grace_days"],
            ">=60min days": len(a["late60_dates"]),
            "Early-dep minutes": a["early_min"] if not pol["minutes_exempt"] else 0,
            "No-out-punch days": a["noout_days"],
            "Early-big days": len(a["earlybig"]),
            "Deduction half-days": half_days,
            "Ded: marks Rs": ded_marks_rs,
            "Ded: early-dep Rs": ded_early_rs,
            "Fine: uninformed Rs": fine_uninf,
            "Fine: excess-absent Rs": fine_excess,
            "OT cand. minutes": a["ot_min"] if not pol["minutes_exempt"] else 0,
            "OT candidate Rs": ot_rs,
            "Incentive": tier,
            "Incentive Rs": inc_rs,
            "Net Rs": net_rs,
            "Months over cap (yr)": over.get(uid, 0),
            "Habitual flag": "HABITUAL" if over.get(uid, 0) >= HABITUAL_FLAG_AT else "",
            "Absent dates": " ".join(a["absent_dates"]),
        })
    return rows, money_log, first_pass, review_path, acc


CONSOLE_COLS = ["Name", "Group", "Present", "Absent", "Late marks", "Late days",
                "Grace days used", ">=60min days", "Early-dep minutes",
                "Early-big days", "No-out-punch days", "OT cand. minutes",
                "Deduction half-days", "Incentive",
                "Habitual flag"]                      # no Rs. columns on console (F-31)


def write_outputs(ym, rows, money_log, acc):
    heads = list(rows[0].keys()) if rows else []
    csv_path = os.path.join(BASE, f"salary_inputs_{ym}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=heads)
        w.writeheader()
        w.writerows(rows)

    log_heads = ["Name", "Date", "Item", "Quantity", "Rs", "Explanation"]
    log_path = os.path.join(BASE, f"deductions_extras_{ym}.csv")
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(log_heads)
        for row in money_log:
            w.writerow(row)

    # ---------- landscape day-grid ----------
    year, mon = int(ym[:4]), int(ym[5:7])
    ndays = calendar.monthrange(year, mon)[1]
    day_hdrs = ""
    for d in range(1, ndays + 1):
        wd = datetime.date(year, mon, d).weekday()
        cls = ' class="sun"' if wd == 6 else ""
        day_hdrs += f"<th{cls}>{d}</th>"

    def cellhtml(c):
        if c is None:
            return "<td></td>"
        if c["st"] == "OFF":
            return '<td class="off"></td>'
        if c["st"] == "AB":
            return '<td class="ab">A</td>'
        l1 = c.get("in", "")
        if c.get("req"):
            l1 += "*"                     # v2.6: presence by approved request
        if c.get("late"):
            l1 += f'<br><span class="lt">L{c["late"]}</span>'
        l2 = ""
        if c.get("out"):
            l2 = f'<br>{c["out"]}'
            if c.get("early"):
                l2 += f'<br><span class="lt">E{c["early"]}</span>'
            elif c.get("ebig"):
                l2 += f'<br><span class="lt">E{c["ebig"]}!</span>'
            elif c.get("ot"):
                l2 += f'<br><b>OT{c["ot"]}</b>'
        cls = []
        if c.get("art"):
            cls.append("art")
        if c.get("ebig"):
            cls.append("ebig")
        cl = f' class="{" ".join(cls)}"' if cls else ""
        return f"<td{cl}>{l1}{l2}</td>"

    grid_rows = ""
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        cells = "".join(cellhtml(a["grid"].get(d)) for d in range(1, ndays + 1))
        grid_rows += f'<tr><td class="nm">{html.escape(a["name"])}</td>{cells}</tr>\n'

    # EARLY_BIG review table (rule-on-sheet)
    eb_rows = ""
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        rate = per_min_rate(a["info"], a["pol"])
        for dstr, tfirst, tlast, em in a["earlybig"]:
            ded = round(em * rate, 2)
            eb_rows += (f"<tr><td>{html.escape(a['name'])}</td><td>{dstr}</td>"
                        f"<td>{tfirst}</td><td>{tlast}</td><td>{em}</td>"
                        f"<td><b>{ded}</b></td>"
                        f"<td class=\"rule\"></td><td class=\"rule\"></td></tr>\n")
    if not eb_rows:
        eb_rows = '<tr><td colspan="8">none this month</td></tr>'

    def tbl(heads_, data_rows):
        hc = "".join(f"<th>{html.escape(str(h))}</th>" for h in heads_)
        cells = "\n".join(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
            for r in data_rows)
        return f"<table>{'<tr>' + hc + '</tr>'}\n{cells}</table>"

    def sumtbl():
        hs = heads[:-1]
        hc = "".join(f"<th>{html.escape(str(h))}</th>" for h in hs)
        out = [f"<tr>{hc}</tr>"]
        for r in rows:
            tds = []
            for h in hs:
                v = r[h]
                if h == "Net Rs":
                    cls = "net-pos" if float(v) >= 0 else "net-neg"
                    tds.append(f'<td><span class="{cls}">{float(v):+.2f}</span></td>')
                else:
                    tds.append(f"<td>{html.escape(str(v))}</td>")
            out.append("<tr>" + "".join(tds) + "</tr>")
        return "<table>" + "\n".join(out) + "</table>"


    by_staff = {}
    for row in money_log:
        by_staff.setdefault(row[0], []).append(row)
    log_details = ""
    for nm in sorted(by_staff, key=str.lower):
        inner = tbl(["Date", "Item", "Quantity", "Rs", "Explanation"],
                    [r[1:] for r in by_staff[nm]])
        log_details += (f"<details><summary><b>{html.escape(nm)}</b> "
                        f"({len(by_staff[nm])} lines)</summary>"
                        f"<div class='rev'>{inner}</div></details>\n")
    if not log_details:
        log_details = "<p>no money lines this month</p>"

    full_l, half_l = limits_for(ym)
    policy_box = f"""<div class="policy">
<b>Late-marks system :</b> 10 मिनट तक देर माफ़ (महीने में {GRACE_DAYS_CAP} दिन) &nbsp;|&nbsp;
11&ndash;29 मिनट = 1 mark &nbsp;|&nbsp; 30&ndash;59 = 2 marks &nbsp;|&nbsp;
60+ = 2 marks (बताकर) / 3 marks (बिना बताए)।
इनाम: &le;{full_l} marks = पूरा, &le;{half_l} = आधा।
{half_l} marks के बाद हर 3 marks = आधे दिन की कटौती (salary &divide; 60)।<br>
<b>Overtime duty :</b> ड्यूटी के बाद रुकना &mdash; डॉक्टर साहब की अनुमति और मशीन punch ज़रूरी &mdash;
भुगतान of overtime = <b>double the salary rate</b>, जल्दी जाना = सामान्य दर से कटौती।
<b>Punch out is compulsory</b>&mdash; बिना out-punch के overtime नहीं जुड़ता।<br>
<b>छुट्टी / ग़ैरहाज़िरी:</b> बिना पहले बताए ग़ैरहाज़िर = &#8377;{FINE_UNINFORMED} &nbsp;|&nbsp;
महीने में {ABSENT_FREE_DAYS} दिन से ज़्यादा = अगले दिन से &#8377;{FINE_EXCESS_ABSENT}/दिन &nbsp;|&nbsp;
छुट्टी केवल रिसेप्शन रजिस्टर में लिखकर व स्वीकृति (doctor sign) से मान्य &mdash; सिर्फ़ WhatsApp = सूचना नहीं।
इनाम राशि: पूरा = 1 दिन का वेतन, आधा = आधे दिन का। Net = incentive + OT &minus; deductions.
</div>"""

    grp_names = {}
    for uid2 in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        g = acc[uid2]["pol"]["sunday_group"] or "-"
        grp_names.setdefault(g, []).append(acc[uid2]["name"])
    def gn(g):
        return ", ".join(grp_names.get(g, [])) or "-"
    sunday_box = f"""<details class="noprint"><summary><b>रविवार व्यवस्था / Sunday system
(notice points 12&ndash;15) &mdash; click to open</b></summary><div class="policy">
Group A ({gn("A")}) &mdash; पहला व तीसरा रविवार पूरी ड्यूटी। &nbsp;
Group B ({gn("B")}) &mdash; दूसरा व चौथा रविवार पूरी ड्यूटी। बाकी रविवार पूरी छुट्टी।<br>
पाँचवाँ रविवार = सबके लिए सामान्य पूरा कार्य-दिवस। ड्यूटी वाले रविवार को सभी नियम लागू।<br>
{gn("C")} &mdash; रविवार व्यवस्था पहले जैसी (हर रविवार आधे दिन की ड्यूटी); {gn("ARJ")} भी।<br>
अदला-बदली आपसी सहमति से, पहले बताकर, रजिस्टर में लिखकर &mdash; दोनों के हस्ताक्षर व
डॉक्टर साहब के काउंटर-साइन के बाद ही मान्य।
</div></details>"""

    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Attendance {ym}</title><style>
@page {{ size: A4 landscape; margin: 8mm; }}
body {{ font-family: Arial, sans-serif; }}
h2 {{ margin: 0 0 2mm 0; font-size: 13pt; }}
p {{ margin: 0 0 2mm 0; font-size: 8pt; color: #444; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #999; text-align: center; }}
.grid th, .grid td {{ font-size: 6.5pt; padding: 1px; }}
.grid td.nm {{ text-align: left; font-weight: bold; font-size: 8pt; padding: 1px 3px; }}
.grid th.sun {{ background: #FDE9D9; color: #333; }}
th {{ background: #1F4E79; color: #fff; font-size: 7.5pt; padding: 2px; }}
td.off {{ background: #F2F2F2; }}
td.ab  {{ background: #F8CBAD; font-weight: bold; }}
td.art {{ background: #D9D9D9; }}
td.ebig {{ background: #BFBFBF; font-weight: bold; }}
.sum td, .sum th {{ font-size: 7.5pt; padding: 2px 3px; }}
.sum td:first-child {{ text-align: left; font-weight: bold; }}
.rev td, .rev th {{ font-size: 9pt; padding: 3px 6px; }}
td.rule {{ min-width: 28mm; background: #FFFDE7; }}
.pagebreak {{ page-break-before: always; }}
.grid td {{ line-height: 1.15; }}
span.lt {{ color: #C00000; font-weight: bold; }}
span.net-pos {{ color: #006100; font-weight: bold; }}
span.net-neg {{ color: #C00000; font-weight: bold; }}
.grid td {{ border-bottom: 2px solid #555; }}
.policy {{ border: 1.5px solid #1F4E79; background: #EAF1F8; padding: 3mm;
  font-size: 9pt; margin: 2mm 0 3mm 0; line-height: 1.5; }}
details {{ margin: 1mm 0; }} summary {{ cursor: pointer; font-size: 10pt; }}
@media print {{ .noprint {{ display: none; }} body {{ -webkit-print-color-adjust: exact; }} }}
</style></head><body>
<h2>Attendance Grid — {ym}</h2>
<p>L = minutes late &nbsp; E = left early (auto-deducted, &le;{EARLY_AUTO_MAX_MIN} min) &nbsp;
E..! dark grey = big early exit, review below &nbsp; <b>OT</b> bold = overtime candidate &nbsp;
&middot; = clean day &nbsp; A = absent &nbsp; light grey = no proper punch-out
(duty presumed done — coach to punch out) &nbsp; blank grey = off day &nbsp;
* = present by APPROVED register request (the request time is the punch time).</p>
<table class="grid"><tr><th>Name</th>{day_hdrs}</tr>
{grid_rows}</table>
<div class="pagebreak"></div>
<h2>Month Summary — {ym}</h2>
{policy_box}
{sunday_box}
<p>Notice v6 policy; Option-B deduction floor(max(0,marks-{limits_for(ym)[1]})/3) half-days;
{DAYS_BASIS}-day basis; OT needs approval. Subtract Darpan's outstation days from Absent
before entry. Generated {datetime.date.today().isoformat()}.</p>
<div class="sum">{sumtbl()}</div>
<h2 style="margin-top:4mm">Big Early-Exit Review — {ym} (rule on this sheet against the register)</h2>
<p>NOT applied by the machine. Tick Genuine and write the Rs you approve; file this sheet.</p>
<table class="rev"><tr><th>Name</th><th>Date</th><th>First punch</th><th>Last punch</th>
<th>Min before shift end</th><th>Deductible Rs (if genuine)</th><th>Genuine? (Y/N)</th><th>Rs applied</th></tr>
{eb_rows}</table>
<div class="noprint">
<h2 style="margin-top:6mm">Deductions &amp; Extra Payments Log — {ym} (screen only — click a name)</h2>
<p>Every rupee line-by-line. OT lines are candidates until approved; EARLY_BIG lines carry
Rs 0 until ruled above. Not printed: the grid + summary + policy note answer staff queries.</p>
{log_details}
</div>
</body></html>"""
    html_path = os.path.join(BASE, f"salary_inputs_{ym}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return csv_path, log_path, html_path


def print_table(rows):
    if not rows:
        print("No active staff / no data.")
        return
    heads = CONSOLE_COLS
    widths = [max(len(h), max(len(str(r[h])) for r in rows)) for h in heads]
    line = "  ".join(h.ljust(w) for h, w in zip(heads, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[h]).ljust(w) for h, w in zip(heads, widths)))


# ------------------------- selftest -------------------------
def selftest():
    # The fixture below deliberately EXERCISES the D253 roster logic, which
    # production now gates behind ATT_ROSTER_FROM (D341b). Pin the era ON for
    # the test so the dormant code stays proven; production stays gated.
    global ROSTER_FROM
    ROSTER_FROM = "2026-09"
    """Synthetic month proving every rule. A check that cannot fail is not a check."""
    import tempfile
    import importlib
    tmp = tempfile.mkdtemp()
    staff_csv = os.path.join(tmp, "staff_master.csv")
    punch_csv = os.path.join(tmp, "punches.csv")
    global BASE
    old_base = BASE
    BASE = tmp                                    # review/output files land in tmp
    with open(staff_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "department", "base_salary", "allowed_offs",
                    "wd_start", "wd_end", "sun_start", "sun_end", "active",
                    "timing_note", "sunday_group", "minutes_exempt"])
        # 12h weekday shift 09-21 -> 720 min; salary 9000 -> rate 9000/(30*720)=0.41666/min
        w.writerow([1, "TestA", "X", 9000, 2, "09:00", "21:00", "09:00", "21:00", "Y", "", "A", "N"])
        w.writerow([2, "TestB", "X", 9000, 2, "09:00", "21:00", "09:00", "21:00", "Y", "", "B", "N"])
        w.writerow([3, "TestC", "X", 9000, 2, "09:00", "21:00", "09:00", "14:00", "Y", "", "C", "N"])
        w.writerow([4, "TestArj", "X", 6000, 2, "09:00", "21:00", "09:00", "14:00", "Y", "", "ARJ", "Y"])
        w.writerow([5, "TestGone", "X", 9000, 2, "09:00", "21:00", "", "", "N", "", "", "N"])

    # September 2026: Sundays = 6,13,20,27 (four). Roster ACTIVE (>= 2026-09).
    # October 2026 has no 5th Sunday either... 2026-11: Sundays 1,8,15,22,29 -> FIVE. Use Nov (strict).
    P = []
    # --- TestA (group A): duty Sundays Nov 1 & 15; off 8, 22; 5th (29) normal ---
    # 9 grace days (1..10 skipping Sun 8): days 2,3,4,5,6,7,9,10,11 at 09:05 -> 8 free + 9th = 1 mark
    for d in [2, 3, 4, 5, 6, 7, 9, 10, 11]:
        P.append((1, f"2026-11-{d:02d} 09:05:00"))
    P.append((1, "2026-11-12 09:20:00"))                          # 20m -> 1 mark
    P.append((1, "2026-11-13 09:45:00"))                          # 45m -> 2 marks
    P.append((1, "2026-11-14 10:10:00"))                          # 70m -> 2 marks + LATE60
    P.append((1, "2026-11-01 09:00:00"))                          # duty Sunday (1st), on time, single punch
    P.append((1, "2026-11-08 12:00:00"))                          # OFF Sunday: ignored entirely
    P.append((1, "2026-11-16 09:00:00")); P.append((1, "2026-11-16 20:00:00"))  # early dep 60
    P.append((1, "2026-11-17 09:00:00")); P.append((1, "2026-11-17 21:45:00"))  # OT 45
    P.append((1, "2026-11-18 09:00:00"))                          # single punch: no ded, no OT
    P.append((1, "2026-11-19 09:00:00")); P.append((1, "2026-11-19 09:10:00"))  # ARTEFACT double punch
    P.append((1, "2026-11-20 09:00:00")); P.append((1, "2026-11-20 15:00:00"))  # EARLY_BIG 360 gap
    # remaining weekdays absent for TestA
    # --- TestB (group B): duty Sundays 8 & 22 ---
    P.append((2, "2026-11-08 09:30:00"))                          # duty Sunday, 30m -> 2 marks
    P.append((2, "2026-11-01 10:00:00"))                          # OFF Sunday: ignored
    for d in range(2, 8):                                          # Mon 2 .. Sat 7 on time
        P.append((2, f"2026-11-{d:02d} 09:00:00"))
    # --- TestC: every Sunday half-day 09-14; 5th Sunday (29) full day ---
    P.append((3, "2026-11-01 09:20:00")); P.append((3, "2026-11-01 14:30:00"))  # Sun: 20m late=1 mark; 30 OT cand
    P.append((3, "2026-11-29 09:00:00")); P.append((3, "2026-11-29 21:00:00"))  # 5th Sun full day, clean
    # --- TestArj: minutes exempt; late punch must yield 0 marks ---
    P.append((4, "2026-11-02 10:30:00"))
    P.append((4, "2026-11-01 09:00:00"))                          # Sunday half-day presence
    with open(punch_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "datetime"])
        for uid, dt in P:
            w.writerow([uid, dt])

    global _TODAY_OVERRIDE
    import att_config as cfg
    import att_core
    old_sm, old_pc = cfg.STAFF_MASTER, cfg.PUNCH_CSV
    _TODAY_OVERRIDE = datetime.date(2026, 12, 1)
    cfg.STAFF_MASTER, cfg.PUNCH_CSV = staff_csv, punch_csv
    importlib.reload(att_core)
    # v2.6: point the register-DB read at a THROWAWAY store for the whole test —
    # the selftest must never read live present-requests (and must not go dark
    # when none exist).
    import sqlite3 as _sq3
    reg_db = os.path.join(tmp, "reg.db")
    old_regdb = os.environ.get("ATT_REGISTER_DB")
    os.environ["ATT_REGISTER_DB"] = reg_db
    _rc = _sq3.connect(reg_db)
    _rc.execute("CREATE TABLE present_request (id INTEGER PRIMARY KEY, reg_date TEXT,"
                " staff_id INTEGER, req_user TEXT, req_ts TEXT, reason TEXT,"
                " status TEXT, verify_user TEXT, verify_ts TEXT, decide_user TEXT,"
                " decide_ts TEXT, decide_note TEXT)")
    # APPROVED for TestB on Tue 2026-12-01 at 10:10 (shift 09:00 -> 70 min late);
    # a PENDING row for TestC the same day must change nothing.
    _rc.execute("INSERT INTO present_request(reg_date,staff_id,req_user,req_ts,reason,"
                "status) VALUES('2026-12-01',2,'testb','2026-12-01 10:10:00','x','approved')")
    _rc.execute("INSERT INTO present_request(reg_date,staff_id,req_user,req_ts,reason,"
                "status) VALUES('2026-12-01',3,'testc','2026-12-01 09:05:00','x','pending')")
    _rc.commit(); _rc.close()
    try:
        ym = "2026-11"
        rows, money_log, first_pass, review_path, acc = month_report(ym, att_core, cfg)
        assert first_pass and os.path.exists(review_path), "review file not created"
        by = {r["Name"]: r for r in rows}
        assert "TestGone" not in by, "inactive staff leaked"
        a, b, c, arj = by["TestA"], by["TestB"], by["TestC"], by["TestArj"]

        # --- TestA ---
        # marks: 9th grace day 1 + 20m 1 + 45m 2 + 70m 2 = 6 (informed default)
        assert a["Late marks"] == 6, a
        assert a["Grace days used"] == 8, a
        assert a[">=60min days"] == 1, a
        # strict month: half_limit 5 -> Option B: floor(max(0,6-5)/3)=0 half-days
        assert a["Deduction half-days"] == 0, a
        assert a["Ded: marks Rs"] == 0.0, a
        # early dep 60 min @ 9000/(30*720)=0.416667 -> 25.00 (EARLY_BIG adds nothing)
        assert abs(a["Ded: early-dep Rs"] - 25.0) < 0.01, a
        # OT 45 min @ 2x -> 37.50
        assert a["OT cand. minutes"] == 45, a
        assert abs(a["OT candidate Rs"] - 37.5) < 0.01, a
        # no-out-punch: 9 grace + 3 late + Sun1 + Nov18 (single) + Nov19 (artefact pair)
        assert a["No-out-punch days"] == 15, a
        assert a["Early-big days"] == 1, a             # Nov 20 (360 min gap, NOT deducted)
        assert a["Early-dep minutes"] == 60, a         # still only Nov 16
        assert a["Incentive"] == "-", a                # 6 > 5 strict half
        # OFF Sunday Nov 8: neither absent nor late — present only on duty days
        # present days: 9 grace + 12,13,14 + Sun1 + 16,17,18,19,20 = 18
        assert a["Present"] == 18, a

        # --- TestB ---
        assert b["Late marks"] == 2, b                 # Sunday-duty 30m
        assert b["Present"] == 7, b                    # 6 weekdays + duty Sun 8
        # absent days = every other duty day in Nov (up to 30) with no punch
        assert b["Absent"] > 3, b                      # triggers excess fine
        assert b["Fine: excess-absent Rs"] == (b["Absent"] - 3) * 100, b

        # --- TestC ---
        assert c["Late marks"] == 1, c                 # Sunday 20m vs sun 09:00
        assert c["OT cand. minutes"] == 30, c          # past 14:00 sun end
        assert c["Present"] == 2, c                    # Sun 1 + 5th Sun 29

        # --- TestArj ---
        assert arj["Late marks"] == 0 and arj["Early-dep minutes"] == 0 \
            and arj["OT cand. minutes"] == 0, arj
        assert arj["Present"] == 2, arj

        # --- informed-flag loop: mark TestA's LATE60 + one absent as uninformed ---
        rowsr = list(csv.DictReader(open(review_path, encoding="utf-8")))
        target_abs = None
        for r in rowsr:
            if r["name"] == "TestA" and r["type"] == "LATE60":
                r["informed"] = "N"
            if r["name"] == "TestA" and r["type"] == "ABSENT" and target_abs is None:
                r["informed"] = "N"
                target_abs = r["date"]
        with open(review_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["user_id", "name", "date", "type", "informed"])
            w.writeheader(); w.writerows(rowsr)
        rows2, ml2, fp2, _, acc2 = month_report(ym, att_core, cfg)
        assert not fp2, "review file overwritten on second pass"
        a2 = {r["Name"]: r for r in rows2}["TestA"]
        assert a2["Late marks"] == 7, a2               # +1 uninformed LATE60
        assert a2["Fine: uninformed Rs"] == 50, a2
        # Option B strict: floor(max(0,7-5)/3)=0 still; push: three uninformed... check math fn directly
        assert math.floor(max(0, 8 - 5) / 3) == 1 and math.floor(max(0, 11 - 5) / 3) == 2

        # --- ramp vs strict (notice wins: ramp Aug only) ---
        assert limits_for("2026-08") == (5, 8)
        assert limits_for("2026-09") == (2, 5), "Sept must be STRICT (notice v6 point 6)"
        assert incentive_tier(5, "2026-08") == "FULL"
        assert incentive_tier(5, "2026-09") == "HALF"
        assert incentive_tier(6, "2026-09") == "-"

        # --- band unit checks ---
        assert marks_for_late(0, 0) == (0, False, False)
        assert marks_for_late(10, 0) == (0, True, False)
        assert marks_for_late(10, 8) == (1, False, False)      # cap crossed
        assert marks_for_late(11, 0) == (1, False, False)
        assert marks_for_late(29, 0) == (1, False, False)
        assert marks_for_late(30, 0) == (2, False, False)
        assert marks_for_late(59, 0) == (2, False, False)
        assert marks_for_late(60, 0) == (2, False, True)

        # --- Sunday index ---
        assert sunday_index(datetime.date(2026, 11, 1)) == 1
        assert sunday_index(datetime.date(2026, 11, 29)) == 5

        # --- EARLY_BIG: logged with Rs 0 and would-be note; never billed ---
        eb = [rw for rw in ml2 if rw[2] == "EARLY_BIG"]
        assert len(eb) == 1 and eb[0][4] == 0.0 and "would be Rs.150.0" in eb[0][5], eb
        # --- grid content ---
        ga = acc2[1]["grid"]
        assert ga[19]["art"] is True and ga[20]["ebig"] == 360, (ga[19], ga[20])
        assert ga[8]["st"] == "OFF" and ga[1]["st"] == "OK", (ga[8], ga[1])

        # --- money log carries an explanation for every Rs line ---
        assert all(len(rw) == 6 for rw in ml2)
        assert any("EARLY-DEPARTURE" in rw[2] for rw in ml2)
        assert any("OT CANDIDATE" in rw[2] for rw in ml2)
        assert any("UNINFORMED-ABSENT" in rw[2] for rw in ml2)

        # --- outputs write and parse back ---
        p1, p2, p3 = write_outputs(ym, rows2, ml2, acc2)
        assert os.path.getsize(p1) and os.path.getsize(p2) and os.path.getsize(p3)
        page = open(p3, encoding="utf-8").read()
        assert 'class="art"' in page and 'E360!' in page and '<b>OT45</b>' in page, "grid markers missing"
        assert "09:00" in page and "21:45" in page, "punch times missing from grid cells"
        assert page.count("<details>") >= 3 and "noprint" in page, "collapsible log missing"
        assert "policy" in page and "double the salary rate" in page and "1 mark" in page, "policy box missing"
        assert "Big Early-Exit Review" in page and "15:00" in page, "review table missing"
        assert "<b>150.0</b>" in page and "Deductible Rs" in page, "deductible column missing"
        assert "रविवार व्यवस्था" in page and 'details class="noprint"' in page, "Sunday box missing"
        # v2.5: net math, incentive Rs, adjacent OT cols, colored net, row separators
        a25 = {r["Name"]: r for r in rows2}
        assert a25["TestA"]["Incentive Rs"] == 0.0 and a25["TestA"]["Net Rs"] == -737.5, a25["TestA"]
        assert a25["TestB"]["Incentive Rs"] == 300.0 and a25["TestB"]["Net Rs"] == -1500.0, a25["TestB"]
        assert a25["TestArj"]["Incentive Rs"] == 200.0, a25["TestArj"]
        ks = list(rows2[0].keys())
        assert ks.index("OT candidate Rs") == ks.index("OT cand. minutes") + 1, ks
        assert ks.index("Net Rs") == ks.index("Incentive Rs") + 1, ks
        assert "net-neg" in page and "Late-marks system" in page and "doctor sign" in page, "v2.5 page bits"
        assert any(rw[2].startswith("INCENTIVE") for rw in ml2), "incentive not in money log"
        assert "छुट्टी / ग़ैरहाज़िरी" in page, "absents policy line missing"
        assert page.count("pagebreak") == 2, "print must flow to ~2 sheets"
        import shutil; shutil.copy(p3, os.path.join(old_base, "selftest_grid.html"))
        back = list(csv.DictReader(open(p1, encoding="utf-8")))
        assert len(back) == 4

        # ---- v2.6 (S196): approved present-request = synthetic punch ----
        # December 2026, processed up to the 2026-12-01 today-override -> ONE
        # day, Tuesday. No machine punch exists for anyone; TestB has an
        # APPROVED request at 10:10, TestC only a PENDING one.
        ym6 = "2026-12"
        rows6, ml6, fp6, revp6, acc6 = month_report(ym6, att_core, cfg)
        by6 = {r["Name"]: r for r in rows6}
        b6, c6, a6 = by6["TestB"], by6["TestC"], by6["TestA"]
        assert b6["Present"] == 1 and b6["Absent"] == 0, \
            "approved request must count as presence"
        assert b6["Late marks"] == 2 and b6[">=60min days"] == 1, \
            "the request TIME must feed the late bands (70 min -> LATE60)"
        assert c6["Present"] == 0 and c6["Absent"] == 1, \
            "a PENDING request must change nothing"
        assert a6["Absent"] == 1, "others unaffected"
        g6 = acc6[2]["grid"][1]
        assert g6["st"] == "OK" and g6.get("req") is True and g6["in"] == "10:10", g6
        assert g6["late"] == 70, g6
        q1, q2, q3 = write_outputs(ym6, rows6, ml6, acc6)
        page6 = open(q3, encoding="utf-8").read()
        assert "10:10*" in page6, "request-backed day must carry the * marker"
        assert "APPROVED register request" in page6, "the * legend line"
        rev6 = list(csv.DictReader(open(revp6, encoding="utf-8")))
        assert any(r["name"] == "TestB" and r["type"] == "LATE60" for r in rev6), \
            "a request-backed >=60 late enters the informed-flag loop like any punch"
        # fail-soft: with the register DB gone the report must still run (v2.5
        # behaviour), never crash
        os.environ["ATT_REGISTER_DB"] = os.path.join(tmp, "nope.db")
        rows7, _, _, _, acc7 = month_report(ym6, att_core, cfg)
        b7 = {r["Name"]: r for r in rows7}["TestB"]
        assert b7["Present"] == 0 and b7["Absent"] == 1, \
            "no register DB -> exactly the v2.5 picture"
        os.environ["ATT_REGISTER_DB"] = reg_db
    finally:
        cfg.STAFF_MASTER, cfg.PUNCH_CSV = old_sm, old_pc
        BASE = old_base
        if old_regdb is None:
            os.environ.pop("ATT_REGISTER_DB", None)
        else:
            os.environ["ATT_REGISTER_DB"] = old_regdb
        _TODAY_OVERRIDE = None
    print("SELFTEST PASSED — 40+ policy, roster, money and loop checks OK")


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
    rows, money_log, first_pass, review_path, acc = month_report(ym, att_core, cfg)
    print_table(rows)
    if first_pass:
        print(f"\nFIRST PASS: {review_path} created with informed=Y defaults.")
        print("Edit informed=N against the reception register, then rerun for final fines.")
    p1, p2, p3 = write_outputs(ym, rows, money_log, acc)
    print(f"\nWritten: {p1}\nWritten: {p2}  (the per-line explain log)\nWritten: {p3}  (browser -> print A4)")


if __name__ == "__main__":
    main()
