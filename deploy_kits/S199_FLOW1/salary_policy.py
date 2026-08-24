"""
salary_policy.py — v1.1 (S199) — THE NEW SALARY FLOW ENGINE. Std-lib only.

The owner's month-end flow (S199 rulings), every number a SETTING:

  Sheet 1  attendance grid (biometric punches; L approved leave · A uninformed
           absent · * non-biometric override/request day) — staff view first,
           then the owner's doored review.
  Sheet 2  advances & loans (this month's advances · long-term loans: when
           taken, instalment, this-month deduction, balance · holds).
  Owner approves both (with corrections made through the register/ledger
  screens — the sheets are checklists, the apps are the pen), THEN
  Sheet 3  detailed salary sheet (all columns) and
  Sheet 4  payment & signature page are computed.

PREVIEW IS A STANDARD FEATURE: any month renders fully with a PREVIEW banner
and NOTHING written anywhere, until the month is locked AND covered by the
enforcement date. This module writes NOTHING in preview; the settings file is
written only by the settings page; the hold ledger only at a real collection.

POLICY (owner-ruled S199, all values in salary_policy_settings.json):
  Late: <=10-min daily grace x8 days stays (the attendance layer's rule).
        Money: first FREE_LATE_MIN (90) minutes of the month free, then
        progressive pricing at the person's OWN salary minute-rate
        (base / (30 x shift minutes)): band-1 x0.5, band-2 x1.0, tail x1.5.
  Hold: only COLLECT_NOW_PCT (25%) of the late charge is collected; the rest
        is HELD, released back on measured improvement (IMPROVE_PCT fewer
        chargeable minutes next month), waivable individual -> all.
  Leaves: beyond allowed_offs -> one day salary (base/DAY_DIVISOR) each;
        under-use credited (symmetric). No ladder (owner ruling).
  Fines: Rs.50 uninformed absence; Rs.100/day beyond 3 genuine absences.
  Dress/I-card: Rs.15 per day WITHOUT each (register dropdown, post-migration).
  Incentive: marks <= 5 -> one day salary; <= 8 -> half day.
  Marks remain the tracking score only; money never comes from the slab.

Reads: att_month_report/att_core/att_scenario (attendance), salary_engine's
load_register (leaves/dress/coverage), staff_ledger read-only (advances/loans).
All fail-soft: a missing neighbour degrades the sheet with a loud note, never
a crash.

USAGE (VPS)
  /root/wa/venv/bin/python3 /root/staff_register/salary_policy.py 2026-08
      -> writes flow_<ym>_sheet1.html / _sheet2.html / _sheets34.html in /root
  /root/wa/venv/bin/python3 /root/staff_register/salary_policy.py --selftest

Console prints NO money (F-31).
"""
import os
import sys
import csv
import json
import html
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ATT_DIR = os.environ.get("ATT_DIR", "/root")
for _d in (ATT_DIR, BASE, "/root", "/root/staff_register"):
    if _d and os.path.isdir(_d) and _d not in sys.path:
        sys.path.append(_d)

SETTINGS_PATH = os.path.join(BASE, "salary_policy_settings.json")
SETTINGS_AUDIT = os.path.join(BASE, "salary_policy_settings_audit.jsonl")
HOLD_LEDGER = os.path.join(BASE, "hold_ledger.jsonl")

DEFAULTS = {
    "free_late_min": 90,        # owner S199: 90 free minutes/month over the 10-min x8 grace
    "band1_end": 180,           # cumulative minutes; 91-180 at mult1
    "band2_end": 360,           # 181-360 at mult2; beyond at mult3
    "mult1": 0.5, "mult2": 1.0, "mult3": 1.5,
    "collect_now_pct": 25,      # % of late charge collected; rest -> HOLD
    "improve_pct": 30,          # % fewer chargeable minutes releases the hold
    "hold_enabled": 1,
    "dress_rs": 15, "icard_rs": 15,
    "fine_uninformed": 50, "fine_excess": 100, "excess_free_days": 3,
    "incentive_full_marks": 5, "incentive_half_marks": 8,
    "day_divisor": 30,
    "enforce_from": "",         # '' = everything is PREVIEW (D332 pattern)
    "require_pack_approval": 1, # salary lock refuses without Sheet1+Sheet2 approval
    # S199-B: the staff month view (owner windows, all adjustable):
    "staff_view_current": 1,        # staff may watch the RUNNING month live
    "staff_view_after_lock_days": 5,# completed month disappears N days after lock
    "staff_remarks_enabled": 1,     # staff may raise day remarks for review
}

_TODAY_OVERRIDE = None          # selftest only


# ------------------------------------------------------------- settings -----
def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            s.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
    except Exception:
        pass
    return s


def save_settings(new, by="?"):
    """Validated merge; audit line appended. Returns (ok, err)."""
    cur = load_settings()
    clean = {}
    for k, v in (new or {}).items():
        if k not in DEFAULTS:
            continue
        if k == "enforce_from":
            v = str(v or "").strip()
            if v and not _valid_ym(v):
                return False, "enforce_from must be YYYY-MM or empty"
            clean[k] = v
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return False, "%s must be a number" % k
        if fv < 0:
            return False, "%s cannot be negative" % k
        clean[k] = int(fv) if float(fv).is_integer() else fv
    cur.update(clean)
    tmp = SETTINGS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cur, f, indent=2, sort_keys=True)
    os.replace(tmp, SETTINGS_PATH)
    try:
        with open(SETTINGS_AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now(), "by": by, "changed": clean}) + "\n")
    except Exception:
        pass
    return True, ""


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _valid_ym(ym):
    try:
        return (isinstance(ym, str) and len(ym) == 7 and ym[4] == "-"
                and 2000 <= int(ym[:4]) <= 2100 and 1 <= int(ym[5:7]) <= 12)
    except (ValueError, TypeError):
        return False


def enforced(ym, s=None):
    s = s or load_settings()
    d = s.get("enforce_from") or ""
    return bool(d) and ym >= d


def money(x):
    v = round(float(x) + 1e-9, 2)
    return str(int(v)) if v == int(v) else ("%.2f" % v).rstrip("0").rstrip(".")


# ------------------------------------------------------- hold ledger --------
def hold_rows():
    out = []
    if not os.path.exists(HOLD_LEDGER):
        return out
    try:
        with open(HOLD_LEDGER, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
    except Exception:
        pass
    return out


def hold_state(staff=None):
    """{(staff, ym): {"held":Rs,"status","history":[...]}} folded from the
    append-only ledger. Actions RELEASE/LAPSE/WAIVE close a hold."""
    st = {}
    for r in hold_rows():
        if r.get("action"):
            key = (r.get("staff"), r.get("ym"))
            h = st.get(key)
            if h:
                h["status"] = r["action"]
                h["history"].append(r)
        elif r.get("held") is not None:
            st[(r.get("staff"), r.get("ym"))] = {
                "held": float(r.get("held") or 0), "status": "HELD",
                "history": [r]}
    if staff is not None:
        return {k: v for k, v in st.items() if k[0] == staff}
    return st


def append_hold(row):
    """The ONLY writer. Never called from a preview path."""
    with open(HOLD_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


# --------------------------------------------------------- data plumbing ----
def _att_modules():
    import att_core
    import att_config as cfg
    import att_month_report as amr
    import att_scenario as scn
    if _TODAY_OVERRIDE:
        amr._TODAY_OVERRIDE = _TODAY_OVERRIDE
        scn._TODAY_OVERRIDE = _TODAY_OVERRIDE
    return att_core, cfg, amr, scn


def _ledger():
    try:
        import staff_ledger as L
        return L, ""
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def _register(ym):
    try:
        import salary_engine as E
        agg, staff, covered = E.load_register(ym)
        by_name = {}
        for sid, a in (agg or {}).items():
            nm = (staff.get(sid, {}).get("name") or "").strip().lower()
            if nm:
                by_name[nm] = a
        return by_name, bool(covered), ""
    except Exception as e:
        return {}, False, "%s: %s" % (type(e).__name__, e)


def _shift_minutes(info):
    st, en = info.get("wd_start"), info.get("wd_end")
    if not (st and en):
        return 720
    m = (en.hour * 60 + en.minute) - (st.hour * 60 + st.minute)
    return m if m > 0 else 720


def _offs(info):
    try:
        v = int(float(info.get("allowed_offs") or 2))
        return v if v >= 0 else 2
    except (TypeError, ValueError):
        return 2


def progressive_charge(minutes, rate, s):
    f, b1, b2 = s["free_late_min"], s["band1_end"], s["band2_end"]
    m1, m2, m3 = s["mult1"], s["mult2"], s["mult3"]
    m = max(0, minutes)
    return round(rate * (m1 * max(0, min(m, b1) - f)
                         + m2 * max(0, min(m, b2) - b1)
                         + m3 * max(0, m - b2)), 2)


def prev_ym(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return "%04d-12" % (y - 1) if m == 1 else "%04d-%02d" % (y, m - 1)


# ------------------------------------------------------------ compute -------
def compute(ym, with_prev=True):
    """The whole month, per staff. Pure computation — writes nothing."""
    s = load_settings()
    att_core, cfg, amr, scn = _att_modules()
    pol_all = amr.load_staff_policy()
    acc, _log, _ev = amr.collect_month(ym, att_core, cfg, pol_all)
    raw = scn.raw_late_minutes(ym, amr, att_core, pol_all)
    raw_prev = {}
    if with_prev:
        try:
            raw_prev = scn.raw_late_minutes(prev_ym(ym), amr, att_core, pol_all)
        except Exception:
            raw_prev = {}
    flags = amr.load_review(os.path.join(ATT_DIR, "review_%s.csv" % ym)) or {}
    reg, covered, reg_err = _register(ym)
    holds = hold_state()

    L, led_err = _ledger()
    led_rows = []
    opens = []
    if L:
        try:
            led_rows = L.load_ledger()
            opens = L.open_advances()
        except Exception as e:
            led_err = "%s: %s" % (type(e).__name__, e)
            L = None

    staff_out = []
    for uid in sorted(acc, key=lambda u: acc[u]["name"].lower()):
        a = acc[uid]
        pol, info = a["pol"], a["info"]
        name = a["name"]
        base = pol["base_salary"]
        exempt = pol["minutes_exempt"]
        offs = _offs(info)
        day = base / s["day_divisor"] if base else 0.0
        shift_min = _shift_minutes(info)
        rate = base / (30.0 * shift_min) if base else 0.0
        g = reg.get(name.strip().lower(), {}) or {}
        disc = g.get("disc_used", 0)
        fest = g.get("fest_used", 0)
        outst = g.get("outstation", 0)
        leave_dates = g.get("leave_dates", set()) or set()
        dressn = g.get("dress", 0)
        icardn = g.get("icard", 0)

        marks = a["marks"]
        for dstr in a["late60_dates"]:
            if not flags.get((uid, dstr, "LATE60"), True):
                marks += 1

        if covered:
            leave_in_absent = len(leave_dates & set(a["absent_dates"]))
            genuine = max(0, a["absent"] - leave_in_absent - outst)
            leaves_total = disc + fest + genuine
        else:
            genuine = a["absent"]
            leaves_total = a["absent"]

        # late money (progressive + hold)
        mins = 0 if exempt else raw.get(uid, 0)
        charge = 0.0 if exempt else progressive_charge(mins, rate, s)
        if s["hold_enabled"]:
            collect = round(charge * s["collect_now_pct"] / 100.0, 2)
        else:
            collect = charge
        held = round(charge - collect, 2)

        # last month's hold: release preview on measured improvement
        pm = prev_ym(ym)
        ph = holds.get((name, pm))
        prev_min = 0 if exempt else raw_prev.get(uid, 0)
        release = 0.0
        release_note = ""
        if ph and ph["status"] == "HELD" and ph["held"] > 0:
            if prev_min > 0:
                improve = (prev_min - mins) / float(prev_min) * 100.0
                if improve >= s["improve_pct"]:
                    release = ph["held"]
                    release_note = "improved %d%% — hold releases" % round(improve)
                else:
                    release_note = "improvement %d%% (< %d%%) — hold stays" % (
                        round(improve), s["improve_pct"])
            else:
                release = ph["held"]
                release_note = "no prior lateness — hold releases"

        # leaves: symmetric at full day rate (owner ruling: no ladder)
        leave_amt = round((leaves_total - offs) * day, 2) if base else 0.0
        if not covered and leaves_total == 0 and a["present"] == 0:
            leave_amt = 0.0

        uninf = sum(1 for dstr in a["absent_dates"]
                    if not flags.get((uid, dstr, "ABSENT"), True))
        fine_uninf = uninf * s["fine_uninformed"]
        fine_exc = max(0, genuine - s["excess_free_days"]) * s["fine_excess"]

        dress_rs = 0.0 if exempt else dressn * s["dress_rs"]
        icard_rs = 0.0 if exempt else icardn * s["icard_rs"]

        if exempt or not base:
            inc = 0.0
            inc_tier = "-"
        elif marks <= s["incentive_full_marks"]:
            inc, inc_tier = round(day, 2), "FULL"
        elif marks <= s["incentive_half_marks"]:
            inc, inc_tier = round(day / 2, 2), "HALF"
        else:
            inc, inc_tier = 0.0, "-"

        # ledger side (advances/loans) — descriptive + a preview deduction
        advances_month, loans, adv_ded = [], [], 0.0
        open_bal = 0.0
        if L:
            for r in led_rows:
                if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                        and r.get("staff") == name
                        and str(r.get("date_from", ""))[:7] == ym
                        and float(r.get("amount") or 0) > 0):
                    advances_month.append(r)
            for o in opens:
                if o["issue"].get("staff") != name:
                    continue
                open_bal += o["balance"]
                inst = min(o["balance"], o["instalment"] or o["balance"])
                due_now = True
                am = o["issue"].get("against_month")
                if am and am > ym:
                    due_now = False           # future-attributed quota advance
                if o["interest"]:
                    loans.append({"o": o, "due": inst if due_now else 0})
                if due_now:
                    adv_ded += inst
            adv_ded = round(adv_ded, 2)

        deductions = round(collect + leave_amt + fine_uninf + fine_exc
                           + dress_rs + icard_rs, 2)
        net = round(base - deductions - adv_ded + inc + release, 2) if base else 0.0

        staff_out.append({
            "uid": uid, "name": name, "base": base, "exempt": exempt,
            "offs": offs, "shift_min": shift_min, "rate": round(rate, 4),
            "present": a["present"], "absent": a["absent"],
            "genuine": genuine, "disc": disc, "fest": fest,
            "leaves_total": leaves_total, "leave_amt": leave_amt,
            "marks": marks, "grace_days": a["grace_days"],
            "late_min": mins, "late_charge": charge,
            "collect": collect, "held": held,
            "prev_min": prev_min, "release": release, "release_note": release_note,
            "fine_uninf": fine_uninf, "fine_exc": fine_exc,
            "dress_days": dressn, "icard_days": icardn,
            "dress_rs": dress_rs, "icard_rs": icard_rs,
            "incentive": inc, "inc_tier": inc_tier,
            "advances_month": advances_month, "loans": loans,
            "open_bal": open_bal, "adv_ded": adv_ded,
            "grid": a["grid"], "absent_dates": a["absent_dates"],
            "leave_dates": leave_dates, "net": net,
        })

    notes = []
    if reg_err:
        notes.append("register: %s (grid items zero)" % reg_err)
    if led_err:
        notes.append("ledger: %s (advance/loan columns empty)" % led_err)
    if not covered:
        notes.append("register grid NOT COVERED for %s — sanctioned leave "
                     "cannot be separated" % ym)
    return {"ym": ym, "settings": s, "covered": covered, "staff": staff_out,
            "notes": notes, "enforced": enforced(ym, s),
            "preview": not enforced(ym, s)}


# ------------------------------------------------------------- rendering ----
_CSS = """
 body{font-family:Segoe UI,Arial,sans-serif;font-size:12px;margin:16px;color:#222}
 h1{font-size:16px;margin:0 0 2px} h2{font-size:13px;margin:14px 0 4px}
 .sub{color:#666;margin:0 0 8px;font-size:11px}
 .banner{padding:6px 10px;margin:8px 0;border-radius:6px;font-weight:bold}
 .prev{background:#fff8e1;border:1px solid #e0c060}
 .enf{background:#e8f4e8;border:1px solid #7ab97a}
 .tw{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0}
 th,td{border:1px solid #bbb;padding:3px 5px;text-align:left;white-space:nowrap;font-size:11px}
 th{background:#f0ede6}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 tr.tot td{font-weight:bold;background:#faf7ef}
 .L{background:#dcf0dc} .A{background:#f8d7d7} .R{background:#dbe9fa} .OFF{color:#bbb}
 a.door{color:#0a58ca;text-decoration:none}
 .note{background:#fff8e1;border:1px solid #e0c060;padding:5px 8px;margin:6px 0;font-size:11px}
 .hdr{ text-align:center }
 @media print{ body{margin:6mm} .noprint{display:none} th,td{font-size:10px} }
"""


def _banner(res):
    if res["enforced"]:
        return '<div class="banner enf">ENFORCED — this month is covered by the served notice.</div>'
    return ('<div class="banner prev">PREVIEW — nothing on this page is applied '
            'to pay. Enforcement starts only when the notice date is set in '
            'Settings.</div>')


def _head(title):
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>%s</title>"
            "<style>%s</style></head><body>" % (html.escape(title), _CSS))


def _clinic_hdr(sub):
    return ("<div class='hdr'><h1>Dr. Manoj Agarwal Clinic — Sanjeevni</h1>"
            "<div class='sub'>%s</div></div>" % html.escape(sub))


def sheet1_html(res, doors=False, prefix="/register", only_uid=None,
                back=None, print_=False):
    """The attendance grid. only_uid -> a staff member's own view (no others)."""
    ym = res["ym"]
    e = html.escape
    year, mon = int(ym[:4]), int(ym[5:7])
    import calendar
    ndays = calendar.monthrange(year, mon)[1]
    out = [_head("Attendance %s" % ym), _clinic_hdr(
        "SHEET 1 · ATTENDANCE — %s · P punch · L approved leave · "
        "A absent (uninformed unless ruled) · * non-biometric override" % ym)]
    if back:
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    out.append('<div class="tw"><table><tr><th>Staff</th>')
    for d in range(1, ndays + 1):
        out.append("<th>%d</th>" % d)
    out.append("<th>P</th><th>A</th><th>L</th><th>Marks</th>"
               "<th>Late min</th>%s</tr>" %
               ("<th>Staff remark</th>" if print_ else ""))
    for st in res["staff"]:
        if only_uid is not None and st["uid"] != only_uid:
            continue
        out.append("<tr><td>%s</td>" % e(st["name"]))
        for d in range(1, ndays + 1):
            cell = st["grid"].get(d)
            dstr = "%s-%02d" % (ym, d)
            if cell is None:
                out.append("<td></td>")
                continue
            stt = cell.get("st")
            if stt == "OFF":
                out.append('<td class="OFF">·</td>')
            elif stt == "AB":
                mark = "L" if dstr in st["leave_dates"] else "A"
                cls = "L" if mark == "L" else "A"
                inner = mark
                if doors:
                    inner = '<a class="door" href="%s/?d=%s">%s</a>' % (prefix, dstr, mark)
                out.append('<td class="%s">%s</td>' % (cls, inner))
            else:
                sym = "P" + ("*" if cell.get("req") else "")
                tip = "%s–%s" % (cell.get("in", ""), cell.get("out", "") or "…")
                if cell.get("late"):
                    tip += " · %d min late" % cell["late"]
                cls = "R" if cell.get("req") else ""
                inner = '<span title="%s">%s</span>' % (e(tip), sym)
                if doors and cell.get("req"):
                    inner = '<a class="door" href="%s/review?ym=%s" title="%s">%s</a>' % (
                        prefix, ym, e(tip), sym)
                out.append('<td class="%s">%s</td>' % (cls, inner))
        out.append('<td class="n">%d</td><td class="n">%d</td><td class="n">%d</td>'
                   '<td class="n">%d</td><td class="n">%d</td>%s</tr>'
                   % (st["present"], st["absent"], len(st["leave_dates"]),
                      st["marks"], st["late_min"],
                      "<td style='min-width:120px'></td>" if print_ else ""))
    out.append("</table></div>")
    out.append('<div class="sub">Hover a P for punch times. * = approved '
               'present-request (server time is the punch). Money appears on '
               'no staff copy.</div>')
    out.append("</body></html>")
    return "".join(out)


def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None):
    e = html.escape
    ym = res["ym"]
    out = [_head("Advances & loans %s" % ym), _clinic_hdr(
        "SHEET 2 · ADVANCES, LOANS & HOLDS — %s" % ym)]
    if back:
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    out.append("<h2>Advances taken this month</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Date</th><th>Amount</th><th>Against month</th>"
               "<th>Instalment</th><th></th></tr>")
    any_a = False
    for st in res["staff"]:
        for r in st["advances_month"]:
            any_a = True
            door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                    % (ledger_prefix, e(st["name"]))) if doors else ""
            out.append("<tr><td>%s</td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(str(r.get("against_month") or "-")),
                          money(r.get("instalment") or r.get("amount") or 0), door))
    if not any_a:
        out.append("<tr><td colspan='6'>none recorded</td></tr>")
    out.append("</table></div>")

    out.append("<h2>Long-term loans (interest-bearing)</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Taken</th><th>Instalment</th>"
               "<th>This month deduction</th><th>Balance</th><th></th></tr>")
    any_l = False
    for st in res["staff"]:
        for lo in st["loans"]:
            any_l = True
            o = lo["o"]
            door = ('<a class="door" href="%s/advances">ledger</a>' % ledger_prefix) if doors else ""
            out.append("<tr><td>%s</td><td>%s</td><td class='n'>%s</td>"
                       "<td class='n'>%s</td><td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]), e(str(o["issue"].get("date_from", ""))),
                          money(o["instalment"]), money(lo["due"]),
                          money(o["balance"]), door))
    if not any_l:
        out.append("<tr><td colspan='6'>none open</td></tr>")
    out.append("</table></div>")

    out.append("<h2>Improvement holds</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Last month held</th><th>This month</th>"
               "<th>New charge</th><th>Collect now</th><th>New hold</th></tr>")
    for st in res["staff"]:
        if not (st["held"] or st["release"] or st["release_note"] or st["late_charge"]):
            continue
        out.append("<tr><td>%s</td><td class='n'>%s</td><td>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]),
                      money(st["release"]) if st["release"] else "-",
                      e(st["release_note"] or "-"),
                      money(st["late_charge"]), money(st["collect"]),
                      money(st["held"])))
    out.append("</table></div>")

    # S199-B (owner): Sheet 2 also lists EVERY fine/deduction for review,
    # so the pack covers the whole money side before approval.
    out.append("<h2>All fines &amp; deductions this month (for review)</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Late charge</th>"
               "<th>Collect now</th><th>Hold</th><th>Leave amt (+ded/-credit)</th>"
               "<th>Uninformed</th><th>Excess-absent</th><th>Dress</th>"
               "<th>I-card</th><th>Incentive (+)</th></tr>")
    t = [0.0]*9
    for st in res["staff"]:
        vals = [st["late_charge"], st["collect"], st["held"], st["leave_amt"],
                st["fine_uninf"], st["fine_exc"], st["dress_rs"], st["icard_rs"],
                st["incentive"]]
        for i, v in enumerate(vals):
            t[i] += float(v)
        out.append("<tr><td>%s</td>%s</tr>" % (
            e(st["name"]),
            "".join("<td class='n'>%s</td>" % money(v) for v in vals)))
    out.append('<tr class="tot"><td>TOTAL</td>%s</tr></table></div>'
               % "".join("<td class='n'>%s</td>" % money(v) for v in t))

    out.append('<div class="sub">Advance/loan figures are the ledger\'s own; '
               'corrections happen in the ledger (defer / waive there), then '
               'reload this sheet.</div>')
    out.append("</body></html>")
    return "".join(out)


def sheets34_html(res, back=None, approved=None):
    """Sheet 3 (detail, all columns) + Sheet 4 (signature) with page break."""
    e = html.escape
    ym = res["ym"]
    s = res["settings"]
    out = [_head("Salary %s" % ym), _clinic_hdr(
        "SHEET 3 · MONTHLY SALARY — DETAILED WORKING — %s" % ym)]
    if back:
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    if approved is not None and not approved:
        out.append('<div class="note">Sheet 1 / Sheet 2 not yet approved for '
                   'this month — this is a working preview of the computation.</div>')
    cols = ["Name", "Salary", "Advance ded.", "Leaves", "Leave amt", "Late min",
            "Marks", "Late charge", "Collect now", "Hold", "Hold released",
            "Dress", "I-card", "D+I fine", "Fines", "Incentive", "NET PAYABLE"]
    out.append("<div class='tw'><table><tr>" +
               "".join("<th>%s</th>" % c for c in cols) + "</tr>")
    tot = dict.fromkeys(range(len(cols)), 0.0)
    for st in res["staff"]:
        di = st["dress_rs"] + st["icard_rs"]
        fines = st["fine_uninf"] + st["fine_exc"]
        vals = [st["name"], st["base"], st["adv_ded"], st["leaves_total"],
                st["leave_amt"], st["late_min"], st["marks"], st["late_charge"],
                st["collect"], st["held"], st["release"], st["dress_days"],
                st["icard_days"], di, fines, st["incentive"], st["net"]]
        out.append("<tr>" + "".join(
            ("<td>%s</td>" % e(str(v))) if i == 0 else
            ("<td class='n'>%s</td>" % money(v)) for i, v in enumerate(vals))
            + "</tr>")
        for i, v in enumerate(vals):
            if i:
                tot[i] += float(v)
    out.append('<tr class="tot"><td>TOTAL</td>' + "".join(
        "<td class='n'>%s</td>" % money(tot[i]) for i in range(1, len(cols)))
        + "</tr></table></div>")
    out.append('<div class="sub">Leave amt: (leaves − allowed) × salary÷%d, '
               'negative = credit. Late charge: after %d free min, progressive '
               'at own salary minute-rate. Hold: %d%% of the charge, returnable '
               'on %d%% improvement. D+I fine: Rs.%s/day each without.</div>'
               % (s["day_divisor"], s["free_late_min"],
                  100 - s["collect_now_pct"], s["improve_pct"],
                  money(s["dress_rs"])))
    out.append('<div style="page-break-before:always"></div>')
    out.append(_clinic_hdr("SHEET 4 · SALARY PAYMENT & SIGNATURE — %s" % ym))
    out.append(_banner(res))
    out.append("<div class='tw'><table><tr><th>S.No</th><th>Name</th>"
               "<th>Amount (Rs.)</th><th style='min-width:180px'>Signature / "
               "हस्ताक्षर</th><th style='min-width:90px'>Date</th></tr>")
    for i, st in enumerate(res["staff"], 1):
        out.append("<tr style='height:34px'><td>%d</td><td>%s</td>"
                   "<td class='n'>%s</td><td></td><td></td></tr>"
                   % (i, e(st["name"]), money(st["net"])))
    out.append("</table></div>")
    out.append('<div class="sub">Received the above amount in full. / '
               'उपरोक्त राशि पूरी प्राप्त की।</div>')
    out.append("</body></html>")
    return "".join(out)


# --------------------------------------------------------------- selftest ---
def selftest():
    # pure-math checks, no data files needed
    s = dict(DEFAULTS)
    assert progressive_charge(0, 0.5, s) == 0
    assert progressive_charge(90, 0.5, s) == 0                      # free
    assert progressive_charge(180, 0.5, s) == round(0.5 * 0.5 * 90, 2)
    assert progressive_charge(360, 1.0, s) == round(0.5 * 90 + 1.0 * 180, 2)
    v = progressive_charge(500, 1.0, s)
    assert v == round(0.5 * 90 + 180 + 1.5 * 140, 2), v
    ok, err = save_settings({"free_late_min": "not-a-number"})
    assert not ok and "number" in err
    ok, err = save_settings({"enforce_from": "banana"})
    assert not ok
    assert _valid_ym("2026-08") and not _valid_ym("2026-13")
    assert prev_ym("2026-01") == "2025-12" and prev_ym("2026-08") == "2026-07"
    print("salary_policy math selftest PASS")
    try:
        _att_modules()
        print("attendance modules import OK")
    except Exception as e:
        print("attendance modules NOT importable here (%s) — fine offline" % e)
    print("PASS")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--selftest":
        selftest()
        return
    ym = sys.argv[1]
    if not _valid_ym(ym):
        print("Month must look like 2026-08")
        sys.exit(1)
    res = compute(ym)
    print("Computed %s — %d staff · %s · notes: %d" %
          (ym, len(res["staff"]), "ENFORCED" if res["enforced"] else "PREVIEW",
           len(res["notes"])))                       # F-31: no money on console
    for name, doc in (("sheet1", sheet1_html(res, print_=True)),
                      ("sheet2", sheet2_html(res)),
                      ("sheets34", sheets34_html(res))):
        p = os.path.join(ATT_DIR, "flow_%s_%s.html" % (ym, name))
        with open(p, "w", encoding="utf-8") as f:
            f.write(doc)
        print("Written:", p)
    print("Salary figures live only in the files — keep them OUT of git (F-31).")


if __name__ == "__main__":
    main()
