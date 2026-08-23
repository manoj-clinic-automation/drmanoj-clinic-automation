"""
att_scenario.py — v2.0 (S199) — DEDUCTION & REWARD SCENARIO, read-only. Std-lib only.

THE OWNER'S FRAME (S199 ruling): the system exists to PROMOTE AND REWARD
punctuality and minimum absence — deductions are deterrents, waivable in the
initial months. This page is strictly a scenario view: it computes three
systems side by side on the same real month and APPLIES NONE OF THEM.

The three systems compared, per staff:

  OLD (as actually practiced — validated line-by-line on the owner's July 2026
      provisional sheet): Rs.1 x EVERY late minute (no grace) + a symmetric
      leave line (leaves - allowed_offs) x base/OLD_DAY_DIVISOR — symmetric
      means UNDER-use is CREDITED back (a reward that already existed). No
      other fines.
  RAMP (notice v6 as it applies to August): late bands -> marks; slab 8;
      incentive FULL<=5 / HALF<=8; Rs.50/Rs.100 absent fines (leave-adjusted);
      extra-leaves C-model at base/30 beyond allowed_offs; encashment credit.
  STRICT (notice v6 from September): same, slab 5, incentive FULL<=2 / HALF<=5.

Enforcement status is read live from the Staff Ledger's D332 setting
(`attendance_enforce_from` in /root/staff_ledger/ledger_settings.json,
fail-soft): until the notice is served, everything here is PREVIEW.

Dress / I-card: counts are shown but valued Rs.0 pending the owner's
verification with reception (S199: the August grid shows 55% of days ticked,
best-attendance staff ticked most — a possible checkbox-polarity inversion).

Optional AS-PAID overlay: if /root/salary_actuals_<ym>.csv exists (the owner's
own sheet, saved on the box, NEVER in the repo — F-31), a reconciliation table
compares it with the machine, row by row. The parser reads the owner's July
layout: rows whose first cell is a serial number, columns
NAME/ADVANCE/LEAVES/LEAVE AMT/LOAN/LATE/PAYABLE.

Computation reuses the LIVE report's own functions (att_month_report v2.6) and
the LIVE salary engine's register read (salary_engine.load_register), so the
scenario cannot drift from what the real machinery would say.

v2.0 keeps the exact v1.1 interfaces the Staff Register route calls:
  build(ym) -> (rows, note, grid_err, limits)
  render_document(ym, rows, note, grid_err, limits, back_href=None) -> str
  write_csv / write_html for the CLI.

USAGE (on the VPS)
  /root/wa/venv/bin/python3 /root/att_scenario.py 2026-07
  /root/wa/venv/bin/python3 /root/att_scenario.py --selftest

Console output never prints salary or Rs. values (F-31); money appears only in
the output files / the gated web page.
"""
import sys
import os
import csv
import html
import math
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# ---- OLD SYSTEM (validated on the July 2026 provisional sheet) --------------
OLD_RATE_PER_MIN = 1.0       # Rs.1 per late minute, every minute, no grace
OLD_DAY_DIVISOR = 30.5       # the sheet's empirical day rate: base / 30.5
                             # (owner to rule: keep 30.5 or standardise to 30)

# ---- NEW SYSTEM constants (mirror att_month_report / salary_engine) ---------
DAYS_BASIS = 30              # notice: day = base / 30
FEST_QUOTA = 2               # festival leave / financial year
DRESS_RS = 20                # per marked day — HELD AT Rs.0 pending verification
ICARD_RS = 20
DEFAULT_OFFS = 2             # fallback when staff_master allowed_offs is blank

LEDGER_SETTINGS = "/root/staff_ledger/ledger_settings.json"
STRICT_YM = "2026-09"        # any non-ramp month yields the strict limits

_TODAY_OVERRIDE = None       # selftest only


def money(x):
    v = round(float(x) + 1e-9, 2)
    if v == int(v):
        return str(int(v))
    return ("%.2f" % v).rstrip("0").rstrip(".")


def enforcement_status(ym):
    """Human line + enforced flag for ym, from the D332 ledger setting.
    Fail-soft: unreadable settings -> 'preview' with a note."""
    try:
        import json
        with open(LEDGER_SETTINGS, encoding="utf-8") as f:
            d = json.load(f).get("attendance_enforce_from")
    except Exception:
        d = None
        return ("PREVIEW ONLY — enforcement setting not readable from here; "
                "treat nothing as applied", False)
    if not d:
        return ("PREVIEW ONLY — notice not served (attendance_enforce_from is "
                "unset, D332); NOTHING on this page is applied to pay", False)
    if ym >= d:
        return ("ENFORCED from %s — this month IS covered by the served notice" % d,
                True)
    return ("PREVIEW for this month — enforcement starts %s (D332)" % d, False)


def _offs(info):
    try:
        v = int(float(info.get("allowed_offs") or DEFAULT_OFFS))
        return v if v >= 0 else DEFAULT_OFFS
    except (TypeError, ValueError):
        return DEFAULT_OFFS


def raw_late_minutes(ym, amr, att_core, pol_all):
    """{uid: total raw late minutes, EVERY late minute} — the OLD system's
    late base, using the report's own duty_shift + arrival rule (validated:
    reproduces the owner's July LATE column to the minute)."""
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
            if raw > 0:
                out[uid] = out.get(uid, 0) + raw
    return out


def register_read(ym):
    """(reg_by_name, covered, err) via the LIVE salary engine's own
    load_register + coverage rule (F-67), so leave/dress/outstation and the
    covered flag can never disagree with the salary page. Fail-soft."""
    try:
        for d in ("/root/staff_register",
                  os.path.join(BASE, "staff_register")):
            if os.path.isdir(d) and d not in sys.path:
                sys.path.append(d)
        import salary_engine as E
        out = E.load_register(ym)
        # live signature (verified S199): returns (agg, staff, covered)
        if not (isinstance(out, tuple) and len(out) >= 3):
            raise ValueError("unexpected load_register shape")
        agg, staff, covered = out[0], out[1], out[2]
        by_name = {}
        for sid, a in (agg or {}).items():
            nm = (staff.get(sid, {}).get("name") or "").strip().lower()
            if nm:
                by_name[nm] = a
        return by_name, bool(covered), ""
    except Exception as e:
        return {}, False, "%s: %s" % (type(e).__name__, e)


def load_actuals(ym):
    """The owner's AS-PAID sheet, optional, owner-copied to
    /root/salary_actuals_<ym>.csv (stays on the box; never in the repo).
    Parses rows whose FIRST cell is a bare serial number:
    serial, NAME, ADVANCE, LEAVES, LEAVE AMT, LOAN, LATE, PAYABLE, ...
    Returns ({UPPERNAME: row}, note)."""
    p = os.path.join("/root", "salary_actuals_%s.csv" % ym)
    if not os.path.exists(p):
        p2 = os.path.join(BASE, "salary_actuals_%s.csv" % ym)
        if not os.path.exists(p2):
            return {}, ""
        p = p2

    def num(x):
        x = (x or "").strip().replace(",", "")
        if not x:
            return 0.0
        try:
            return float(x)
        except ValueError:
            return 0.0

    out = {}
    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if not row or not (row[0] or "").strip().isdigit():
                    continue
                if len(row) < 8:
                    continue
                name = (row[1] or "").strip()
                if not name:
                    continue
                out[name.upper()] = {
                    "advance": num(row[2]), "leaves": num(row[3]),
                    "leave_amt": num(row[4]), "loan": num(row[5]),
                    "late": num(row[6]), "payable": num(row[7]),
                }
    except Exception as e:
        return {}, "actuals file unreadable (%s)" % e
    return out, ("AS-PAID sheet loaded: %s (%d rows)" % (p, len(out))
                 if out else "")


def build(ym):
    import att_core
    import att_config as cfg
    import att_month_report as amr

    if _TODAY_OVERRIDE:
        amr._TODAY_OVERRIDE = _TODAY_OVERRIDE

    pol_all = amr.load_staff_policy()
    acc, _log, _events = amr.collect_month(ym, att_core, cfg, pol_all)

    review_path = os.path.join(BASE, "review_%s.csv" % ym)
    flags = amr.load_review(review_path)
    review_note = ("review_%s.csv honoured (informed=N rows applied)" % ym
                   if flags is not None else
                   "no review_%s.csv yet — everything treated informed=Y" % ym)
    if flags is None:
        flags = {}

    raw_late = raw_late_minutes(ym, amr, att_core, pol_all)
    reg_by_name, covered, reg_err = register_read(ym)
    actuals, act_note = load_actuals(ym)
    enf_line, _enforced = enforcement_status(ym)

    _fa, half_ramp = amr.limits_for("2026-08")     # ramp limits by definition
    _fs, half_strict = amr.limits_for(STRICT_YM)   # strict limits

    grid_err = reg_err
    rows = []
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        pol, info = a["pol"], a["info"]
        base = pol["base_salary"]
        rate = amr.per_min_rate(info, pol)
        day30 = base / DAYS_BASIS if base else 0.0
        day_old = base / OLD_DAY_DIVISOR if base else 0.0
        half_day = base / 60 if base else 0.0
        exempt = pol["minutes_exempt"]
        offs = _offs(info)
        nm_l = a["name"].strip().lower()
        g = reg_by_name.get(nm_l, None)
        disc_used = (g or {}).get("disc_used", 0)
        fest_used = (g or {}).get("fest_used", 0)
        fest_prior = (g or {}).get("fest_prior_fy", 0)
        outst = (g or {}).get("outstation", 0)
        leave_dates = (g or {}).get("leave_dates", set()) or set()
        dressn = (g or {}).get("dress", 0)
        icardn = (g or {}).get("icard", 0)

        # marks incl. uninformed >=60 additions
        marks = a["marks"]
        for dstr in a["late60_dates"]:
            if not flags.get((uid, dstr, "LATE60"), True):
                marks += 1

        # genuine absence (engine rule): absents minus sanctioned-leave days
        # among them minus outstation. Uncovered month -> raw absents.
        if covered:
            leave_in_absent = len(leave_dates & set(a["absent_dates"]))
            genuine = max(0, a["absent"] - leave_in_absent - outst)
        else:
            genuine = a["absent"]

        # absent fines (leave-adjusted, engine style)
        uninf = sum(1 for dstr in a["absent_dates"]
                    if not flags.get((uid, dstr, "ABSENT"), True))
        fine_uninf = uninf * amr.FINE_UNINFORMED
        fine_excess = max(0, genuine - amr.ABSENT_FREE_DAYS) * amr.FINE_EXCESS_ABSENT

        # early departure (auto tier only)
        early_rs = 0.0 if exempt else round(a["early_min"] * rate, 2)

        # extra-leaves C-model (covered months only; per-staff allowed_offs)
        if covered:
            C = disc_used + genuine
            fest_allow = max(0, FEST_QUOTA - fest_prior)
            fest_over = max(0, fest_used - fest_allow)
            extra_days = max(0, C - offs) + fest_over
            extraleave_rs = round(extra_days * day30, 2)
            encash_days = max(0, offs - C) if extra_days == 0 else 0
            encash_rs = round(encash_days * day30, 2)
            xl_note = ""
        else:
            C = genuine
            extra_days = 0
            extraleave_rs = 0.0
            encash_days = 0
            encash_rs = 0.0
            xl_note = "no register grid this month — engine cannot separate " \
                      "sanctioned leave, so no extra-leaves cut and no encashment"

        def slab(limit):
            if exempt:
                return 0, 0.0
            hd = math.floor(max(0, marks - limit) / amr.MARKS_PER_HALFDAY)
            return hd, round(hd * half_day, 2)

        def inc(month):
            if exempt or not base:
                return "-", 0.0
            t = amr.incentive_tier(marks, month)
            if t == "FULL":
                return t, round(day30, 2)
            if t == "HALF":
                return t, round(half_day, 2)
            return "NONE", 0.0

        hd_r, slab_r = slab(half_ramp)
        hd_s, slab_s = slab(half_strict)
        tier_r, inc_r = inc("2026-08")
        tier_s, inc_s = inc(STRICT_YM)

        ded_common = early_rs + fine_uninf + fine_excess + extraleave_rs
        ramp_ded = round(slab_r + ded_common, 2)
        strict_ded = round(slab_s + ded_common, 2)
        ramp_reward = round(inc_r + encash_rs, 2)
        strict_reward = round(inc_s + encash_rs, 2)
        ramp_net = round(ramp_ded - ramp_reward, 2)      # + = staff loses
        strict_net = round(strict_ded - strict_reward, 2)

        # OLD, as practiced: Rs1/min + symmetric leave line around allowed_offs
        old_min = 0 if exempt else raw_late.get(uid, 0)
        old_late = round(old_min * OLD_RATE_PER_MIN, 2)
        old_leaves = (disc_used + fest_used + genuine) if covered else a["absent"]
        old_leave_amt = round((old_leaves - offs) * day_old, 2)   # +ded / -credit
        old_net = round(old_late + old_leave_amt, 2)

        act = actuals.get(a["name"].strip().upper())

        rows.append({
            "Name": a["name"], "Base": base, "Offs allowed": offs,
            "Present": a["present"], "Absent (machine)": a["absent"],
            "Genuine absent": genuine, "Sanctioned leave": disc_used + fest_used,
            "Late marks": marks, "<=10min free days used": a["grace_days"],
            "Raw late min": old_min, "Early-dep min": 0 if exempt else a["early_min"],
            # ramp
            "RAMP slab half-days": hd_r, "RAMP late-marks Rs": slab_r,
            "RAMP incentive": tier_r, "RAMP incentive Rs": inc_r,
            # strict
            "STRICT slab half-days": hd_s, "STRICT late-marks Rs": slab_s,
            "STRICT incentive": tier_s, "STRICT incentive Rs": inc_s,
            # common new-system parts
            "Early Rs": early_rs, "Uninformed-absent Rs": fine_uninf,
            "Excess-absent Rs": fine_excess,
            "Extra-leaves days": extra_days, "Extra-leaves Rs": extraleave_rs,
            "Encash days": encash_days, "Encash Rs": encash_rs,
            "XL note": xl_note,
            # totals (net effect: deductions minus rewards; negative = staff GAINS)
            "RAMP deductions": ramp_ded, "RAMP rewards": ramp_reward,
            "RAMP net effect": ramp_net,
            "STRICT deductions": strict_ded, "STRICT rewards": strict_reward,
            "STRICT net effect": strict_net,
            # old
            "OLD late Rs": old_late, "OLD leaves": old_leaves,
            "OLD leave amt": old_leave_amt, "OLD net effect": old_net,
            "RAMP vs OLD": round(ramp_net - old_net, 2),
            "STRICT vs OLD": round(strict_net - old_net, 2),
            # dress / i-card (held at 0)
            "Dress days": dressn, "I-card days": icardn,
            # as-paid overlay
            "SHEET late": act["late"] if act else "",
            "SHEET leaves": act["leaves"] if act else "",
            "SHEET leave amt": act["leave_amt"] if act else "",
            "SHEET payable": act["payable"] if act else "",
            "SHEET late diff": (round(act["late"] - old_late, 2) if act else ""),
            "exempt": "Y" if exempt else "",
        })

    parts = [review_note, enf_line]
    if act_note:
        parts.append(act_note)
    if not covered:
        parts.append("register grid: NOT COVERED for %s" % ym)
    note = " · ".join(parts)
    return rows, note, grid_err, (half_ramp, half_strict)


# ------------------------------------------------------------------ output --
def render_document(ym, rows, review_note, grid_err, limits, back_href=None):
    half_ramp, half_strict = limits
    e = html.escape
    has_sheet = any(r["SHEET payable"] != "" for r in rows)

    def td(v, num=True):
        s = money(v) if isinstance(v, (int, float)) else str(v)
        return '<td class="%s">%s</td>' % ("n" if num else "", e(s))

    def table(cols, rws, totals=None):
        out = ["<div class='tw'><table><thead><tr>"]
        out += ["<th>%s</th>" % e(c[0]) for c in cols]
        out.append("</tr></thead><tbody>")
        for r in rws:
            out.append("<tr>")
            for label, key in cols:
                out.append(td(r[key], num=(key != "Name")))
            out.append("</tr>")
        if totals:
            out.append('<tr class="tot"><td>TOTAL</td>')
            for label, key in cols[1:]:
                if key in totals:
                    s = sum(float(r[key]) for r in rws
                            if isinstance(r[key], (int, float)))
                    out.append(td(s))
                else:
                    out.append("<td></td>")
            out.append("</tr>")
        out.append("</tbody></table></div>")
        return "".join(out)

    summary_cols = [("Staff", "Name"),
                    ("OLD net", "OLD net effect"),
                    ("RAMP ded", "RAMP deductions"), ("RAMP reward", "RAMP rewards"),
                    ("RAMP net", "RAMP net effect"),
                    ("STRICT net", "STRICT net effect"),
                    ("RAMP vs OLD", "RAMP vs OLD"), ("STRICT vs OLD", "STRICT vs OLD")]
    reward_cols = [("Staff", "Name"), ("Late marks", "Late marks"),
                   ("RAMP incentive", "RAMP incentive"), ("Rs", "RAMP incentive Rs"),
                   ("STRICT incentive", "STRICT incentive"), ("Rs ", "STRICT incentive Rs"),
                   ("Unused-leave credit days", "Encash days"), ("Encash Rs", "Encash Rs")]
    newded_cols = [("Staff", "Name"), ("Marks", "Late marks"),
                   ("RAMP slab Rs (limit %d)" % half_ramp, "RAMP late-marks Rs"),
                   ("STRICT slab Rs (limit %d)" % half_strict, "STRICT late-marks Rs"),
                   ("Early Rs", "Early Rs"),
                   ("Uninf Rs", "Uninformed-absent Rs"), ("Excess Rs", "Excess-absent Rs"),
                   ("Extra-leave days", "Extra-leaves days"), ("Extra-leaves Rs", "Extra-leaves Rs")]
    old_cols = [("Staff", "Name"), ("Late min", "Raw late min"),
                ("OLD late Rs (Rs1/min)", "OLD late Rs"),
                ("Leaves", "OLD leaves"), ("Allowed", "Offs allowed"),
                ("Leave amt (+ded/-credit)", "OLD leave amt"),
                ("OLD net", "OLD net effect")]
    dress_cols = [("Staff", "Name"), ("Dress-ticked days", "Dress days"),
                  ("I-card-ticked days", "I-card days")]
    sheet_cols = [("Staff", "Name"), ("Sheet late", "SHEET late"),
                  ("Machine late", "OLD late Rs"), ("Late diff", "SHEET late diff"),
                  ("Sheet leaves", "SHEET leaves"), ("Machine absents", "Absent (machine)"),
                  ("Sheet leave amt", "SHEET leave amt"), ("Sheet payable", "SHEET payable")]

    body = []
    body.append("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    body.append("<title>Salary scenario %s</title><style>" % e(ym))
    body.append(
        "body{font-family:Segoe UI,Arial,sans-serif;font-size:12px;margin:18px;color:#222}"
        "h1{font-size:17px;margin:0 0 2px} h2{font-size:14px;margin:16px 0 4px}"
        ".sub{color:#666;margin:0 0 8px}"
        ".tw{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0}"
        "th,td{border:1px solid #bbb;padding:3px 6px;text-align:left;white-space:nowrap}"
        "th{background:#f0ede6;font-size:11px}"
        "td.n{text-align:right;font-variant-numeric:tabular-nums}"
        "tr.tot td{font-weight:bold;background:#faf7ef}"
        ".note{background:#fff8e1;border:1px solid #e0c060;padding:6px 8px;margin:8px 0}"
        ".phil{background:#e8f4e8;border:1px solid #7ab97a;padding:6px 8px;margin:8px 0}"
        "a.back{display:inline-block;margin:0 0 8px;color:#0a5;text-decoration:none;font-weight:bold}"
        "details{margin:8px 0} summary{cursor:pointer;font-weight:bold}"
        "@media print{body{margin:8mm} a.back{display:none}}")
    body.append("</style></head><body>")
    if back_href:
        body.append('<a class="back" href="%s">&larr; Back to Salary</a>' % e(back_href))
    body.append("<h1>Salary scenario &mdash; %s</h1>" % e(ym))
    body.append('<div class="phil"><b>Purpose:</b> promote and reward punctuality '
                'and minimum absence. Deductions are deterrents — waivable in the '
                'initial months. <b>This page applies NOTHING to pay.</b></div>')
    body.append('<div class="note">%s%s</div>'
                % (e(review_note),
                   (" &middot; register read problem: %s (grid items shown as zero)"
                    % e(grid_err)) if grid_err else ""))

    body.append("<h2>1 &middot; The verdict table — three systems, same month "
                "(net effect: + = staff loses, &minus; = staff gains)</h2>")
    body.append(table(summary_cols, rows,
                      totals={"OLD net effect", "RAMP deductions", "RAMP rewards",
                              "RAMP net effect", "STRICT net effect",
                              "RAMP vs OLD", "STRICT vs OLD"}))

    body.append("<h2>2 &middot; Rewards first — what the new system GIVES</h2>")
    body.append(table(reward_cols, rows,
                      totals={"RAMP incentive Rs", "STRICT incentive Rs", "Encash Rs"}))

    body.append("<h2>3 &middot; New-system deductions, itemised</h2>")
    body.append(table(newded_cols, rows,
                      totals={"RAMP late-marks Rs", "STRICT late-marks Rs", "Early Rs",
                              "Uninformed-absent Rs", "Excess-absent Rs",
                              "Extra-leaves Rs"}))

    body.append("<h2>4 &middot; The old system, as actually practiced "
                "(validated on the July sheet)</h2>")
    body.append(table(old_cols, rows,
                      totals={"OLD late Rs", "OLD leave amt", "OLD net effect"}))

    body.append("<h2>5 &middot; Dress &amp; I-card — counts only, valued Rs.0 "
                "pending verification</h2>")
    body.append('<div class="note">August shows ticks on 55%% of days with the '
                'best-attendance staff ticked most — likely the checkbox is being '
                'ticked to mean "OK". Confirm with reception before any money is '
                'attached. Would-be value at Rs.%d/day is shown nowhere on purpose.</div>'
                % DRESS_RS)
    body.append(table(dress_cols, rows))

    if has_sheet:
        body.append("<h2>6 &middot; Reconciliation vs your AS-PAID sheet</h2>")
        body.append(table(sheet_cols, rows))
        body.append('<p class="sub">"Late diff" should read 0 everywhere — the '
                    'machine and your sheet counting the same minutes. A non-zero '
                    'row needs a look.</p>')

    body.append("<details><summary>How every number is computed (plain language)</summary>"
                "<ul>"
                "<li><b>Late bands (new):</b> &le;10 min late = free, up to 8 such days a "
                "month (the '&le;10min free days used' count); 11&ndash;29 min = 1 mark; "
                "30&ndash;59 = 2 marks; &ge;60 = 2 (3 if uninformed).</li>"
                "<li><b>Slab:</b> half-days lost = (marks &minus; limit) &divide; 3, "
                "rounded down. Limit %d on the ramp, %d strict. Half-day = salary &divide; 60.</li>"
                "<li><b>Incentive:</b> ramp FULL &le;5 marks (a full day's pay), HALF &le;8 "
                "(half day); strict FULL &le;2, HALF &le;5.</li>"
                "<li><b>Extra leaves:</b> sanctioned + genuine absence beyond each person's "
                "allowed offs &rarr; day salary (&divide;30) each; unused allowance is "
                "CREDITED (encashment) when nothing is owed.</li>"
                "<li><b>Fines:</b> Rs.50 per uninformed absence; Rs.100/day beyond 3 genuine "
                "absences.</li>"
                "<li><b>Old system:</b> Rs.1 &times; every late minute + (leaves &minus; "
                "allowed) &times; salary &divide; %s — under-use credited back, exactly as "
                "your July sheet did.</li>"
                "</ul></details>" % (half_ramp, half_strict, money(OLD_DAY_DIVISOR)))
    body.append("</body></html>")
    return "".join(body)


def write_csv(ym, rows):
    p = os.path.join(BASE, "scenario_%s.csv" % ym)
    cols = list(rows[0].keys()) if rows else ["Name"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


def write_html(ym, rows, review_note, grid_err, limits):
    p = os.path.join(BASE, "scenario_%s.html" % ym)
    with open(p, "w", encoding="utf-8") as f:
        f.write(render_document(ym, rows, review_note, grid_err, limits))
    return p


def selftest():
    print("att_scenario v2 selftest: import wiring only (numeric checks run in "
          "the build sandbox; this proves imports on the box).")
    import att_core          # noqa
    import att_config        # noqa
    import att_month_report  # noqa
    print("imports OK")
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
    rows, note, gerr, limits = build(ym)
    print("Scenario computed for %s — %d staff." % (ym, len(rows)))   # F-31: no Rs on console
    print("NOTE:", note)
    if gerr:
        print("REGISTER:", gerr, "— grid items zero in the files.")
    p1 = write_csv(ym, rows)
    p2 = write_html(ym, rows, note, gerr, limits)
    print("Written: %s\nWritten: %s  (browser -> print A4)" % (p1, p2))
    print("These files hold salary figures — keep them OUT of the git tree (F-31/D320).")


if __name__ == "__main__":
    main()
