"""
salary_policy.py — v1.17 (S489, the owner, 06-Oct-2026; D681, D682) — ADVANCES AND LOANS, RE-LAID.
Sheet 2 shows advances in two tables that never mix: this month's advances (cut in full from
this salary) and instalment loans, ONE LINE PER PERSON PER LOAN however many parts it was handed
over in, with a month strip, and one closing line per person. A salary slip is printed only for
a person with a running instalment loan. A person with a PRIVATE long-term loan (Darpan) is back
on the common sheets at base LESS the loan's standing instalment;
late, absence, overtime and incentive are still worked on the full base. The long-term loan and
its instalment live only on his own page -- one loan-ledger table from April 2026 -- and a month
the instalment is not taken shows only there: the amount kept aside is paid to him on that page.
NO RUPEE MOVES: every figure is still the staff ledger's own. full net = common net + paid to him.
Nobody is paid on a sheet of their own any more (S240's SHEET 5 is retired).
v1.16 (S239, the owner, 11-Sep-2026) — PART-TIME staff pay NO leave charge:
for dates_only_staff the leave amount and the two absence fines are zero (the days they are not
rostered are not absences). Nobody else changes.
v1.15 (S239, the owner, 11-Sep-2026) — PART-TIME staff (dates_only_staff: Amir
Sohail, usually Sunday and Thursday) leave the leave/fine/credit table on Sheet 2 and the
days-not-punched table on Sheet 1; Sheet 2 gains "Part-time staff — days punched" (date, day,
in, out). Display only: the salary computation is unchanged.
v1.14 (S239, the owner) — Cover duty is ONE column: the rupees with the cover
days in brackets, e.g. 600 (3). Display only.
v1.13 (S239, the owner, 11-Sep-2026) — the "All fines, leaves & credits"
table on Sheet 2 loses the "Leave days counted" column (it only restated the days-not-punched
columns) and gains LATE MINUTES, OVERTIME (minutes, rupees) and COVER DUTY (days, rupees) for every staff,
so each person's overtime and Shivani's cover duty are on the review table. Display only:
no figure, no net and no rule changes.
v1.12 (S238, the owner, 11-Sep-2026) — the COVER DAY is verified by the
out-punch: for cover-eligible staff (Shivani) a punch-out at or after cover_auto_from
(17:00) makes the day a cover day -- extra-duty credit for that day, and overtime only
beyond cover_end (21:00). No register marking is needed; a marked day still counts.
v1.11 (S238, the owner, 11-Sep-2026) — OVERTIME IS PAID (ot_pay = 1:
"the incentive for staff not to rush back home"); an optional daily threshold
(ot_threshold_on, default OFF; ot_daily_min 15) ignores punch-out drift; on an extra-duty (cover) day
the cover hours are the extra duty, already credited; overtime counts only AFTER the
cover ends (setting cover_end, 21:00). Staff named in dates_only_staff (Amir Sohail)
leave the attendance grid: Sheet 1 lists only the dates they punched.
v1.10 (S238, the owner's third review) — last month's hold is shown
where it bites: 'deducted now' and 'written off' columns in the fines table and on the
salary sheet; Sheet 1's month summary carries the days not punched (with their dates,
Sundays marked) for the physical-register check, the late fine in total (no hold split),
and overtime minutes with OT payable (2 x own minute-rate, real out-punch only, D256);
OT enters the net only when the setting ot_pay = 1.
v1.9 (S238, the owner's second Sheet-2 review) — the advances
table flags any advance booked against a LATER month than it was given (most are
against the running month, so a later month is usually a keying slip); the second
table says, per advance, whether it is recovered IN ONE GO (how much, from which
salary) or ON INSTALMENTS (how much a month, and till which month); the fines table
spells out the days (not punched = sanctioned leave + outstation + absent without
leave) instead of an ambiguous "Leaves / Absent" pair; Sheet 2 prints on A4
LANDSCAPE; the ENFORCED/PREVIEW line is for the owner's screen only, never printed.
v1.8 (S238) — THE ADVANCE LINE IS THE LEDGER'S OWN (D349/D442):
the Advance column deducts exactly the recoveries the staff ledger recorded for the
month (instalment + interest rows stamped to it), never a second calculation from
today's open balances (which for August 2026 would have taken Darpan Rs 29,000
against the owner's Rs 20,000, and Surendra 0 against Rs 7,000). compute() reports
ledger_closed; the Lock refuses until the ledger month is closed.
Sheet 2 (the owner, 10-Sep-2026): advances taken this month exclude reversed
entries and say HOW each recovers; the open position is AS AT THE MONTH'S END (so it
reads the same on lock day as on any later day) -- open at start, taken, recovered,
interest, open at end; the improvement holds say what happened to last month's hold
in words; every section prints on one A4 sheet, never split, several to a sheet.
Sheet 1 PRINTS AS TWO A4 PAGES: page 1 the
machine-data grid with every day of the month (it was cut off at 100%: the grid
sat in a scrolling box, which a printer clips), page 2 the month summary with the
staff-remark column (the owner, 10-Sep-2026). Screen view unchanged.
v1.7 (S200/R10) — the owner-record manual advances
(manual_advances_<ym>.json) now DEDUCT in compute like ledger advances, so
Sheet 3/4 and the lock total equal the money actually left to hand over.
v1.6 (S200/R8) — back links are BUTTONS; sheet cells 16px
semi-bold for quick reading; the nav carries the Lock desk and prev/next month.
v1.5 (S200/R7) — flow UX: bigger sheet fonts; approve strips on
Sheet 1/2 (caller-supplied); FIX-ABSENTS as a standout button; owner's manual
advances table on Sheet 2 (manual_advances_<ym>.json, display-only); ALL open
advances listed (interest-only filter had hidden Darpan's tranches); staff money
page carries statement/advances/perks doors.
v1.4 (S200/D346) — GO-LIVE: Sunday absence at derived shift
weight for PAY (whole for the deterrent, D342c); the D345 ramp replaces the flat
Rs/day fine; minutes-exempt staff outside fines AND incentive (D342b/D345b); the
hold is a SUSPENDED charge — cancelled on improvement, else collected next month
(D342a); day_divisor 30.5 (D343).  Was: v1.3 (S199) — THE NEW SALARY FLOW ENGINE. Std-lib only.

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
  Incentive: marks <= 5 -> one day; <= 8 -> half day — ACCRUES TO THE ANNUAL
        POT paid at Diwali (owner ruling S199-D; NOT added to the month's net).
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
    "improve_pct": 20,          # % fewer chargeable minutes CANCELS last month's hold (owner 10-Sep-2026: 30 was too high)
    "hold_enabled": 1,
    "ot_pay": 1,                # S238 (owner 11-Sep-2026): overtime IS paid -- the incentive to stay when the clinic runs late
    "ot_threshold_on": 0,       # S238: 1 = a day's OT below ot_daily_min is ignored (punch-out drift); owner: default OFF
    "ot_daily_min": 15,         # S238: the daily OT threshold in minutes, used only when ot_threshold_on = 1
    "cover_end": "21:00",
    "cover_auto_from": "17:00",  # S238 (owner 11-Sep): cover staff leaving at/after this = a cover day (extra-duty paid); before it, OT for the up-to-1-hour overstay       # S238: extra-duty (cover) ends; OT on a cover day counts after this
    "dates_only_staff": "Amir Sohail",  # S238: comma-separated; out of the grid, punch dates only
    "dress_rs": 15, "icard_rs": 15,
    "fine_uninformed": 50,
    "fine_ramp_step": 10,       # D345: k-th excess day beyond OWN allowance = k x step
    "sunday_weight_override": -1,  # D341: -1 = derive from the Sunday shift; 0..1 forces
    "incentive_full_marks": 5, "incentive_half_marks": 8,
    "day_divisor": 30.5,   # D343: what July was actually paid on
    "enforce_from": "",         # '' = everything is PREVIEW (D332 pattern)
    "require_pack_approval": 1, # salary lock refuses without Sheet1+Sheet2 approval
    # S199-B: the staff month view (owner windows, all adjustable):
    "staff_view_current": 1,        # staff may watch the RUNNING month live
    "staff_view_after_lock_days": 5,# completed month disappears N days after lock
    "staff_remarks_enabled": 1,     # staff may raise day remarks for review
    # S199-C (owner review of the first previews):
    "min_charge_rs": 10,            # late charges below this become 0 (kills paisa noise)
    "extra_duty_rs": 200,           # per extra-duty day (register grid credit)
    "outstation_rs": 250,           # per outstation night (register grid credit)
}

_TODAY_OVERRIDE = None          # selftest only
SEPARATE_PAGES = []             # S489 (D682): nobody is kept off the main money page; the private LOAN page is private_loan_names()
VERSION = "1.17-S489"

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def month_words(ym):
    return "%s %s" % (MONTHS[int(ym[5:7])], ym[:4])


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
        if k == "dates_only_staff":
            clean[k] = ", ".join(x.strip() for x in str(v or "").split(",") if x.strip())
            continue
        if k == "cover_auto_from":
            v = str(v or "").strip()
            if _hhmm(v) is None:
                return False, "cover_auto_from must be a time like 17:00"
            clean[k] = v
            continue
        if k == "cover_end":
            v = str(v or "").strip()
            if _hhmm(v) is None:
                return False, "cover_end must be a time like 21:00"
            clean[k] = v
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
        if k == "sunday_weight_override":
            # D341 sentinel: -1 = derive from the shift; else clamp to 0..1
            if fv != -1 and not (0 <= fv <= 1):
                return False, "sunday_weight_override must be -1 (derive) or 0..1"
        elif fv < 0:
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


def manual_advances(ym, base=None):
    """S200/R10: {staff-name-lower: total Rs} from manual_advances_<ym>.json —
    the OWNER'S record of advances settled outside the ledger for months before
    the ledger carried them (July 2026). These DEDUCT in compute() exactly like
    ledger advances, so Sheet 3/4 and the lock total match the money actually
    left to hand over. Missing/unreadable file -> {} (months with no file are
    untouched). Future months should use the ledger instead."""
    p = os.path.join(base or BASE, "manual_advances_%s.json" % ym)
    out = {}
    try:
        with open(p, encoding="utf-8") as f:
            for r in json.load(f):
                nm = str(r.get("staff", "")).strip().lower()
                amt = float(r.get("amount") or 0)
                if nm and amt > 0:
                    out[nm] = out.get(nm, 0.0) + amt
    except Exception:
        return {}
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


def _reversed_ids(rows):
    """Advances genuinely reversed -- the same test staff_ledger.open_advances() uses."""
    by = {r.get("id"): r for r in rows}
    out = set()
    for r in rows:
        if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                and r.get("contra_of")):
            o = by.get(r["contra_of"])
            if o and float(r.get("amount") or 0) == -float(o.get("amount") or 0):
                out.add(o["id"])
    return out


def _brought_forward(r):
    """D258 migration rows: opening balances brought from the workbook."""
    return str(r.get("narration", "")).startswith("opening balance migrated")


def _rmonth(x):
    return (x.get("closed_month") or str(x.get("date_from", ""))[:7])


def ledger_money(rows, name, ym, rev=None):
    """S238 (D349): the staff ledger's OWN figures for one person and one month,
    AS AT THE MONTH'S END -- open at the start, taken in the month, recovered and
    interest charged at the month's close, open at the end. Later months' rows are
    ignored, so a locked month reads the same on any later day. deducted = what
    the ledger took from this month's salary (principal + interest)."""
    rev = _reversed_ids(rows) if rev is None else rev
    lines = []
    cleared = []
    for r in rows:
        if (r.get("category") != "ADVANCE_ISSUE" or r.get("status") != "APPROVED"
                or r.get("staff") != name or float(r.get("amount") or 0) <= 0
                or r.get("id") in rev):
            continue
        d = str(r.get("date_from", ""))[:7]
        bf = _brought_forward(r)
        if bf:      # a migrated opening balance exists from its first recovery month
            d = min([d] + [_rmonth(x) for x in rows if x.get("contra_of") == r["id"]
                           and x.get("status") == "APPROVED" and _rmonth(x)])
        if d > ym:
            continue
        amt = float(r["amount"])
        rec = intr = cap_before = cap_now = rec_before = 0.0
        for x in rows:
            if x.get("contra_of") != r["id"] or x.get("status") != "APPROVED":
                continue
            m = _rmonth(x)
            a = float(x.get("amount") or 0)
            c = x.get("category")
            if c == "ADVANCE_INSTALMENT":
                if m < ym: rec_before += -a
                elif m == ym: rec += -a
            elif c == "LOAN_INTEREST" and m == ym:
                intr += -a
            elif c == "LOAN_CAPITALISE":
                if m < ym: cap_before += a
                elif m == ym: cap_now += a
        # brought forward = taken before this month, OR an opening balance migrated
        # from the workbook (D258: DATED on its entry day, but years of history)
        if d < ym or bf or rec_before or cap_before:
            start, taken = round(amt - rec_before + cap_before, 2), 0.0
        else:
            start, taken = 0.0, amt
        end = round(start + taken - rec + cap_now, 2)
        # S489 (D681): what the ledger has taken month by month, what it added, and the months
        # an instalment was skipped, deferred or held -- for the one-line-per-loan view.
        _hist, _caps, _marks = {}, [], {}
        for x in rows:
            if x.get("contra_of") != r["id"] or x.get("status") != "APPROVED":
                continue
            c = x.get("category")
            a = float(x.get("amount") or 0)
            if c in ("ADVANCE_INSTALMENT", "LOAN_INTEREST"):
                m = _rmonth(x)
                if m and m <= ym:
                    _h = _hist.setdefault(m, [0.0, 0.0])
                    _h[0 if c == "ADVANCE_INSTALMENT" else 1] += -a
            elif c == "LOAN_CAPITALISE":
                m = str(x.get("date_from", ""))[:7] or _rmonth(x)   # the month it BELONGS to (a close stamps both alike)
                if m and m <= ym:
                    _caps.append((m, a))
            elif c in ("LOAN_SKIP", "ADVANCE_DEFER", "CAPACITY_HOLD"):
                m = str(x.get("date_from", ""))[:7]
                if m and m <= ym:
                    _marks[m] = {"LOAN_SKIP": "skip", "ADVANCE_DEFER": "defer", "CAPACITY_HOLD": "hold"}[c]
        _line = {"id": r["id"], "date": str(r.get("date_from", "")),
                 "amount": amt, "interest_loan": bool(r.get("interest")),
                 "start": start, "taken": taken, "recovered": round(rec, 2),
                 "interest": round(intr, 2), "end": end, "bf": bf,
                 "plan": recovery_plan(r),
                 "inst": float(r.get("instalment") or amt), "lane": _adv_lane(r),
                 "against": str(r.get("against_month") or ""),
                 "private": bool(r.get("interest")) or bool(bf),
                 "hist": sorted((m, round(v[0], 2), round(v[1], 2)) for m, v in _hist.items()),
                 "caps": sorted(_caps), "marks": _marks, "proj": []}
        if start > 0 or taken > 0 or rec > 0 or intr > 0 or end > 0:
            lines.append(_line)
        else:
            cleared.append(_line)         # finished in an earlier month: kept for a loan's own history
    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    # S238 v1.9: how each advance is recovered from here on (the close's own lanes)
    closed = any(x.get("closed_month") == ym for x in rows)
    proj = project_recovery(rows, lines, _ym_add(ym, 1) if closed else ym)
    for t in lines:
        t["terms"] = recovery_terms(proj.get(t["id"], []), t["end"])
        t["proj"] = list(proj.get(t["id"], []))
    tot = lambda k: round(sum(t[k] for t in lines), 2)
    return {"lines": lines, "cleared": cleared, "start": tot("start"), "taken": tot("taken"),
            "recovered": tot("recovered"), "interest": tot("interest"), "end": tot("end"),
            "deducted": round(tot("recovered") + tot("interest"), 2)}


def _ym_add(ym, n):
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + int(n)
    return "%04d-%02d" % (t // 12, t % 12 + 1)


def _adv_lane(r):
    """The same four lanes as staff_ledger.advance_lane (D349), read from the row."""
    amt = float(r.get("amount") or 0)
    inst = float(r.get("instalment") or amt)
    if [e for e in (r.get("schedule") or []) if float(e.get("amount") or 0) > 0]:
        return "schedule"
    if r.get("against_month") and not r.get("interest") and inst == amt:
        return "quota"
    return "loan" if r.get("interest") else "waterfall"


def project_recovery(rows, lines, start):
    """S238 v1.9: month by month, how the ledger's close will recover what is still
    open -- the SAME lanes and order as staff_ledger.close_month(): schedule steps,
    quota advances in full at their month, and ONE waterfall budget (the head
    tranche's instalment; Rs 1,000 interest out of it while a loan is open; the rest
    tranche to tranche, loans first, then oldest). Nothing waits before its
    against-month. S489: a DEFER or a SKIP already recorded in the ledger moves the plan
    exactly as close_month() will -- a deferred month collects nothing for that advance and
    its schedule runs one month longer; a skipped month pauses the person's whole waterfall
    and adds the flat interest to the skipped loan. Salary-capacity holds, and defers or
    skips not yet recorded, are still NOT foreseen.
    Returns {advance id: [(month, principal, interest), ...]}."""
    _def, _skp, _pen = {}, {}, set()
    for x in rows:
        if x.get("status") != "APPROVED" or not x.get("contra_of"):
            continue
        _m = str(x.get("date_from", ""))[:7]
        if x.get("category") == "ADVANCE_DEFER":
            _def.setdefault(x["contra_of"], set()).add(_m)
            if x.get("defer_penalty") and not x.get("penalty_waived"):
                _pen.add((x["contra_of"], _m))
        elif x.get("category") == "LOAN_SKIP":
            _skp.setdefault(x["contra_of"], set()).add(_m)
    by_id = {r.get("id"): r for r in rows}
    items = []
    for t in lines:
        r = by_id.get(t["id"])
        if not r or t["end"] <= 0:
            continue
        amt = float(r.get("amount") or 0)
        items.append({"id": t["id"], "r": r, "bal": float(t["end"]), "lane": _adv_lane(r),
                      "inst": float(r.get("instalment") or amt), "interest": bool(r.get("interest")),
                      "am": r.get("against_month") or str(r.get("date_from", ""))[:7],
                      "done": max(0.0, amt - float(t["end"]))})
    out = {i["id"]: [] for i in items}
    m = start
    for _ in range(480):
        live = [i for i in items if i["bal"] > 0.005]
        if not live:
            break
        elig = [i for i in live if i["am"] <= m]
        for i in elig:                                  # S489: deferred this month -- nothing is collected for it
            if m in _def.get(i["id"], ()) and (i["id"], m) in _pen:
                i["bal"] += 1000.0                      # the 3rd+ defer of the year adds the flat interest
        elig = [i for i in elig if m not in _def.get(i["id"], ())]
        for i in [x for x in elig if x["lane"] == "schedule"]:
            sch = sorted(((str(e["month"]), float(e["amount"])) for e in i["r"]["schedule"]
                          if float(e.get("amount") or 0) > 0))
            k = max(0, min(len(sch), (int(m[:4]) * 12 + int(m[5:7])) -
                           (int(sch[0][0][:4]) * 12 + int(sch[0][0][5:7])) + 1
                           - len([_d for _d in _def.get(i["id"], ()) if _d <= m])))
            want = min(i["bal"], max(0.0, sum(a for _, a in sch[:k]) - i["done"]))
            if want > 0:
                i["bal"] -= want; i["done"] += want; out[i["id"]].append((m, want, 0.0))
        for i in [x for x in elig if x["lane"] == "quota"]:
            out[i["id"]].append((m, i["bal"], 0.0)); i["done"] += i["bal"]; i["bal"] = 0.0
        wf = sorted([x for x in elig if x["lane"] in ("loan", "waterfall") and x["bal"] > 0.005],
                    key=lambda x: (not x["interest"], str(x["r"].get("date_from", "")),
                                   str(x["r"].get("ts_entry", ""))))
        if wf and any(x["interest"] and m in _skp.get(x["id"], ()) for x in wf):
            for x in wf:                                # S489: a skipped month -- the whole waterfall waits
                if x["interest"] and m in _skp.get(x["id"], ()):
                    x["bal"] += 1000.0
            wf = []
        if wf:
            intr_due = 1000.0 * sum(1 for x in wf if x["interest"])
            budget = min(wf[0]["inst"], intr_due + sum(x["bal"] for x in wf))
            paid_i = {}
            for x in wf:
                if x["interest"] and budget > 0:
                    pi = min(1000.0, budget); budget -= pi; paid_i[x["id"]] = pi
            for x in wf:
                p = min(budget, x["bal"]) if budget > 0 else 0.0
                budget -= p
                if p > 0 or paid_i.get(x["id"]):
                    x["bal"] -= p; x["done"] += p
                    out[x["id"]].append((m, p, paid_i.get(x["id"], 0.0)))
        m = _ym_add(m, 1)
    return out


def recovery_terms(pays, end):
    """The owner's two columns for ONE advance, from its projected recoveries."""
    t = {"kind": "", "one_go_amt": 0.0, "one_go_month": "", "per": 0.0,
         "per_note": "", "from": "", "until": "", "open_after": False}
    pays = [(m, p + i, i) for m, p, i in pays if p + i > 0.005]
    if end <= 0:
        t["kind"] = "cleared"
        return t
    if not pays:
        t["kind"] = "unplanned"
        return t
    if len(pays) == 1:
        t.update(kind="one_go", one_go_amt=round(pays[0][1], 2), one_go_month=pays[0][0])
        return t
    amts = [round(a, 2) for _, a, _ in pays]
    per = max(set(amts), key=lambda v: (amts.count(v), v))
    notes = []
    if any(i for _, _, i in pays):
        notes.append("Rs 1,000 of it interest")
    if len(pays) <= 4 and len(set(amts)) > 1:
        per = 0.0
        notes = [" · ".join("%s %s" % (month_words(m)[:3], money(a)) for m, a, _ in pays)] + notes
    else:
        if amts[0] != per:
            notes.append("first month Rs %s" % money(amts[0]))
        if amts[-1] != per:
            notes.append("last month Rs %s" % money(amts[-1]))
    t.update(kind="instalments", per=per, per_note="; ".join(notes),
             **{"from": pays[0][0], "until": pays[-1][0]})
    return t


def terms_words(t, ym):
    """One advance's recovery in plain words -- what it gave this month, then what is
    ahead (from the close's own lanes, see project_recovery)."""
    tt = t.get("terms") or {}
    got = float(t.get("recovered") or 0) + float(t.get("interest") or 0)
    pre = ("Rs %s from the %s salary" % (money(got), month_words(ym))) if got > 0 else ""
    k = tt.get("kind")
    if k == "one_go":
        nxt = "Rs %s from the %s salary" % (money(tt["one_go_amt"]), month_words(tt["one_go_month"]))
    elif k == "instalments":
        nxt = (("Rs %s a month, " % money(tt["per"])) if tt.get("per") else "") + \
            "%s to %s" % (month_words(tt["from"]), month_words(tt["until"]))
        if tt.get("per_note"):
            nxt += " (%s)" % tt["per_note"]
    elif k == "unplanned":
        nxt = "no recovery terms on the ledger"
    else:
        return (pre + " — cleared") if pre else "cleared"
    return (pre + "; then " + nxt) if pre else nxt


def recovery_plan(r):
    """How an advance recovers, in words (the owner: the old 'Instalment' header
    was wrong -- it printed the whole amount for a recover-in-full advance)."""
    amt = float(r.get("amount") or 0)
    sched = r.get("schedule") or []
    if sched:
        return " · ".join("%s %s" % (month_words(str(e.get("month", "")))[:3] + " "
                                     + str(e.get("month", ""))[2:4],
                                     money(e.get("amount") or 0)) for e in sched)
    inst = float(r.get("instalment") or amt)
    if r.get("interest"):
        return "loan · %s a month (Rs 1,000 of it interest)" % money(inst)
    if inst >= amt:
        am = r.get("against_month") or str(r.get("date_from", ""))[:7]
        return "in full from the %s salary" % month_words(am)
    return "%s a month, in line behind any open interest loan" % money(inst)


# =============================================================================
#  S489 (D681 / D682 -- the owner, 06-Oct-2026): HOW ADVANCES AND LOANS ARE SHOWN.
#
#  D681. On the month's money sheet advances are TWO tables that never mix:
#        "this month's advances" (taken and cut in full inside one salary) and
#        "instalment loans" -- ONE LINE PER PERSON PER LOAN, however many parts it was
#        handed over in: instalment, paid n of N, cut this month, balance, end month and
#        a month strip. One closing line per person: advances + instalment = cut this month.
#        A salary slip is printed only for a person with a running instalment loan.
#  D682. A person with a PRIVATE long-term loan (private_loan_staff -- Darpan) sits on the
#        common sheets at base LESS the loan's standing instalment; everything attendance
#        is still worked on the full base. The long-term loan and its instalment live only
#        on his own page, which is one loan-ledger table. A month the instalment is not
#        taken (skipped, deferred, held) changes ONLY that page: the common sheets still
#        read base-less-instalment and the amount kept aside is paid to him there.
#
#  NOTHING HERE MOVES MONEY. Every rupee is still the staff ledger's own (D349/D442):
#  these functions only sort the ledger's lines into what each sheet shows. The one
#  identity that must always hold, and that the walk proves on the box:
#        full net  ==  common-sheet net  +  paid to him on the private page
# =============================================================================
PRIVATE_LOAN_DEFAULT = "darpan"
LOAN_PAGES_PATH = os.path.join(BASE, "loan_pages.json")
INTEREST_FLAT = 1000.0          # D250's flat monthly interest; the ledger's own figure is used wherever it exists

_MON3 = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def private_loan_names(s=None):
    """Staff whose long-term loan is kept on a private page (D682). Lower-case names."""
    raw = str((s or {}).get("private_loan_staff", "") or "").strip()
    return {x.strip().lower() for x in (raw or PRIVATE_LOAN_DEFAULT).split(",") if x.strip()}


def _is_ym(x):
    return isinstance(x, str) and len(x) == 7 and x[4] == "-" and x[:4].isdigit() and x[5:].isdigit() \
        and 1 <= int(x[5:]) <= 12


def _num(x):
    """A plain number out of a record, or None (a bool, a text or a list is not a number)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return float(x)


def loan_pages(path=None):
    """The two small records Sheet 2 cannot read out of the ledger, kept in loan_pages.json
    beside this engine (written by the S489 kit, owner-ruled):
      groups  -- advances that are ONE loan handed over in parts:
                 [{"staff": name, "ids": [advance ids], "given": "14-17 Aug 2026"}]
      history -- a private loan's months BEFORE the ledger began:
                 {name: {"loan_id", "opening_date",
                         "pre": [{"ym", "kind": "skip" | "paid"}, ...],
                         "ledger_adjust": net of the ledger's own adjustment rows dated in those months}}
                 A 'paid' month is at the loan's standing terms unless it carries its own
                 "instalment" / "interest"; a 'skip' month adds "added" (default nothing). The
                 opening balance is worked back from the ledger unless the record states "opening".
    The record is CLEANED on the way in, and this never raises: history is keyed by the lower-case
    name; a group keeps only text ids, and an id belongs to the FIRST group that names it (so no
    advance can be counted twice); a month is listed once; anything malformed is dropped.
    Missing or unreadable -> both empty: every advance is then its own loan and the private page
    starts where the ledger starts, and says so."""
    out = {"groups": [], "history": {}}
    try:
        with open(path or LOAN_PAGES_PATH, encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        return out
    if not isinstance(j, dict):
        return out
    seen = set()
    for g in (j.get("groups") if isinstance(j.get("groups"), list) else []):
        if not isinstance(g, dict) or not isinstance(g.get("ids"), list) or not isinstance(g.get("staff"), str):
            continue
        ids = []
        for i in g["ids"]:
            if isinstance(i, str) and i and i not in seen:
                seen.add(i)
                ids.append(i)
        if ids:
            out["groups"].append({"staff": g["staff"], "ids": ids,
                                  "given": g["given"] if isinstance(g.get("given"), str) else ""})
    h = j.get("history")
    for k, v in (h.items() if isinstance(h, dict) else []):
        if not isinstance(k, str) or not k.strip() or not isinstance(v, dict):
            continue
        pre, months = [], set()
        for p in (v.get("pre") if isinstance(v.get("pre"), list) else []):
            if not isinstance(p, dict) or not _is_ym(p.get("ym")) or p.get("kind") not in ("skip", "paid") \
                    or p["ym"] in months:
                continue
            months.add(p["ym"])
            q = {"ym": p["ym"], "kind": p["kind"]}
            for f in ("added", "instalment", "interest"):
                if _num(p.get(f)) is not None:
                    q[f] = _num(p[f])
            pre.append(q)
        pre.sort(key=lambda p: p["ym"])
        rec = {"loan_id": v["loan_id"] if isinstance(v.get("loan_id"), str) else "",
               "opening_date": v["opening_date"] if isinstance(v.get("opening_date"), str) else "",
               "pre": pre}
        for f in ("opening", "ledger_adjust"):
            if _num(v.get(f)) is not None:
                rec[f] = _num(v[f])
        out["history"][k.strip().lower()] = rec
    return out


def loan_history(name, lp=None):
    """The history record of one person's private loan ({} when there is none), whatever the case of the name."""
    return dict(((lp or loan_pages()).get("history") or {}).get(str(name).strip().lower()) or {})


def inr(x):
    """1234567 -> '12,34,567' (Indian grouping). Paise, always two digits, only when there are any."""
    v = round(float(x or 0) + 1e-9, 2)
    neg = v < 0
    v = abs(v)
    whole = int(v)
    frac = round(v - whole, 2)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    if frac:
        s += ("%.2f" % frac)[1:]
    return ("-" if neg and (whole or frac) else "") + s


def _d_short(iso):
    """'2026-09-03' -> '3 Sep'."""
    try:
        return "%d %s" % (int(iso[8:10]), _MON3[int(iso[5:7])])
    except (ValueError, TypeError, IndexError):
        return str(iso or "")


def _m_short(ym):
    """'2026-09' -> 'Sep'."""
    try:
        return _MON3[int(ym[5:7])]
    except (ValueError, TypeError, IndexError):
        return str(ym or "")


def _given_words(parts):
    """When a loan was handed over: '17 Aug 2026', or '14-17 Aug 2026' for several parts."""
    ds = sorted(str(t.get("date", "")) for t in parts if t.get("date"))
    if not ds:
        return ""
    a, b = ds[0], ds[-1]
    if a == b:
        return "%s %s" % (_d_short(a), a[:4])
    if a[:7] == b[:7]:
        return "%d–%s %s" % (int(a[8:10]), _d_short(b), b[:4])
    return "%s – %s %s" % (_d_short(a), _d_short(b), b[:4])


def _inst_words(amounts):
    """How a loan is paid back, from its monthly amounts in order."""
    am = [round(a, 2) for a in amounts if a > 0.005]
    if not am:
        return "no instalment set"
    if len(set(am)) == 1:
        return "%s a month" % inr(am[0]) if len(am) > 1 else "%s in one go" % inr(am[0])
    if len(am) == 2:
        return "%s, then %s" % (inr(am[0]), inr(am[1]))
    if len(set(am[1:])) == 1:
        return "%s, then %s a month" % (inr(am[0]), inr(am[1]))
    if len(set(am[:-1])) == 1:
        return "%s a month, last %s" % (inr(am[0]), inr(am[-1]))
    return " · ".join(inr(a) for a in am)


def _loan_entry(members, ym, closed, label=None):
    """ONE loan, from the ledger lines that make it up (one line, or the parts of a group)."""
    members = sorted(members, key=lambda t: (str(t.get("date", "")), str(t.get("id", ""))))
    past, fut, marks = {}, {}, {}
    this = 0.0
    for t in members:
        for m, p, i in t.get("hist", []):
            if m < ym and p + i > 0.005:
                past[m] = round(past.get(m, 0.0) + p + i, 2)
        if closed:
            this += t["recovered"] + t["interest"]
        for m, p, i in t.get("proj", []):
            if p + i <= 0.005:
                continue
            if m == ym and not closed:
                this += p + i
            elif m > ym:
                fut[m] = round(fut.get(m, 0.0) + p + i, 2)
        for m, kind in (t.get("marks") or {}).items():
            if m <= ym:
                marks[m] = kind
    this = round(this, 2)
    strip = [(m, past[m], "paid") for m in sorted(past)]
    if this > 0.005:
        strip.append((ym, this, "paid" if closed else "now"))
    for m in sorted(marks):
        if m not in past and not (m == ym and this > 0.005):
            strip.append((m, 0.0, marks[m]))
    strip += [(m, fut[m], "due") for m in sorted(fut)]
    strip.sort(key=lambda x: x[0])
    n_paid = sum(1 for _m, _a, k in strip if k == "paid")
    n_all = sum(1 for _m, _a, k in strip if k in ("paid", "now", "due"))
    balance = round(sum(t["end"] for t in members), 2)
    if not closed:
        balance_after = round(balance - this, 2)
    else:
        balance_after = balance
    return {
        "ids": [t["id"] for t in members], "parts": members,
        "amount": round(sum(t["amount"] for t in members), 2),
        "given": label or _given_words(members),
        "first_date": str(members[0].get("date", "")) if members else "",
        "inst": _inst_words([a for _m, a, k in strip if k in ("paid", "now", "due")]),
        "paid": round(sum(past.values()) + (this if closed else 0.0), 2),
        "n_paid": n_paid, "n_all": n_all, "cut": this,
        "balance": balance, "balance_after": balance_after,
        "ends": (sorted(fut)[-1] if fut else (ym if balance_after <= 0.005 else "")),
        "next": fut.get(_ym_add(ym, 1), 0.0), "strip": strip,
        "unplanned": bool(balance_after > 0.005 and not fut),
        "late_month": any((t.get("against") or "") > str(t.get("date", ""))[:7]
                          and t.get("lane") == "quota" for t in members),
    }


def advance_views(lm, name, ym, closed, groups=None, private=False):
    """Sort ONE person's ledger lines (ledger_money) into what Sheet 2 shows.
      month_adv  -- taken and cut in full inside this one salary: [{id, date, amount, cut, bf}]
      loans      -- everything paid back over more than one salary, ONE entry per loan
      priv_lines -- the long-term loan's own lines (private staff only; never in the two above)
    Pure: reads only what ledger_money put on each line. Before the ledger close the 'cut'
    figures are what the close WILL take (the ledger's own projection), and say so."""
    out = {"month_adv": [], "loans": [], "priv_lines": []}
    if not lm:
        return out
    lines = list(lm.get("lines") or [])
    cleared = list(lm.get("cleared") or [])
    by_id = {t["id"]: t for t in cleared}
    by_id.update({t["id"]: t for t in lines})
    gmap = {}
    for gi, g in enumerate(groups or []):
        if str(g.get("staff", "")).strip().lower() != str(name).strip().lower():
            continue
        for i in (g.get("ids") or []):
            if i in by_id:
                gmap[i] = gi
    seen_groups = set()
    for t in lines:
        if private and t.get("private"):
            out["priv_lines"].append(t)
            continue
        gi = gmap.get(t["id"])
        if gi is not None:
            if gi in seen_groups:
                continue
            seen_groups.add(gi)
            g = groups[gi]
            members = [by_id[i] for i in (g.get("ids") or [])
                       if i in by_id and not (private and by_id[i].get("private"))]
            out["loans"].append(_loan_entry(members, ym, closed, label=g.get("given") or None))
            continue
        hist_before = [1 for m, p, i in t.get("hist", []) if m < ym and p + i > 0.005]
        proj_after = [1 for m, p, i in t.get("proj", []) if m > ym and p + i > 0.005]
        if closed:
            th = round(t["recovered"] + t["interest"], 2)
            left = t["end"]
        else:
            th = round(sum(p + i for m, p, i in t.get("proj", []) if m == ym), 2)
            left = round(t["end"] - th, 2)
        if not hist_before and not proj_after and th > 0.005 and left <= 0.005:
            out["month_adv"].append({"id": t["id"], "date": t.get("date", ""), "amount": t["amount"],
                                     "cut": th, "bf": bool(t.get("bf"))})
        elif t["start"] > 0 or t["taken"] > 0 or th > 0.005 or t["end"] > 0:
            out["loans"].append(_loan_entry([t], ym, closed))
    out["loans"].sort(key=lambda L: (L["first_date"], L["ids"]))
    out["month_adv"].sort(key=lambda a: (str(a["date"]), a["id"]))
    return out


def private_split(priv_lines, ym, closed):
    """D682: what the private page keeps aside from the month's salary, and what became of it.
    kept      -- the long-term loan's standing instalment (never more than is still owed)
    cut       -- what the ledger actually took for the long-term loan this month (principal + interest)
    paid      -- kept less cut: paid to him on the private page (0 in an ordinary month; the whole
                 instalment in a month it was skipped). None until the ledger month is closed.
    None when the person has no long-term loan open or moving this month."""
    live = [t for t in (priv_lines or [])
            if t["start"] > 0 or t["taken"] > 0 or t["end"] > 0 or t["recovered"] > 0 or t["interest"] > 0]
    if not live:
        return None
    head = live[0]                                   # interest loan first, then oldest (ledger_money's order)
    principal = round(sum(t["recovered"] for t in live), 2)
    interest = round(sum(t["interest"] for t in live), 2)
    cut = round(principal + interest, 2)
    owed = round(sum(t["start"] + t["taken"] for t in live), 2)
    int_due = interest if closed else (INTEREST_FLAT if any(t.get("interest_loan") and t["start"] > 0 for t in live) else 0.0)
    kept = round(min(float(head.get("inst") or 0.0), owed + int_due), 2)
    cut_shown = round(min(cut, kept), 2)
    mark = ""
    for t in live:
        mark = (t.get("marks") or {}).get(ym) or mark
    if not closed:
        status = "pending"
    elif cut_shown >= kept - 0.005:
        status = "paid"
    elif mark:
        status = mark
    elif cut_shown > 0.005:
        status = "part"
    else:
        status = "none"
    return {"kept": kept, "cut": cut, "cut_shown": cut_shown, "extra": round(cut - cut_shown, 2),
            "paid": (round(kept - cut_shown, 2) if closed else None),
            "reserve": round(kept - cut_shown, 2) if closed else kept,
            "principal": principal, "interest": interest, "status": status,
            "owed_after": round(sum(t["end"] for t in live), 2), "lines": live}


def fy_of_ym(ym):
    """'2026-09' -> 2026 (the Indian financial year April-March it falls in, by its first year)."""
    y, m = int(ym[:4]), int(ym[5:7])
    return y if m >= 4 else y - 1


def loan_ledger(t, hist, ym, closed):
    """The private page's one table for ONE loan line: a row per salary month.
    Months before the ledger began come from loan_pages.json (history); every later month is
    the ledger's own rows. Returns (rows, opening, note). A row:
      {ym, start, inst, interest, principal, added, end, status, src}
      status: paid | part | skip | defer | hold | pending | none | next
    The opening balance is the record's own when it states one; otherwise it is worked BACK from
    the ledger: the ledger's balance where the history ends, plus what the history's months paid
    off. note is non-empty when the history and the ledger do not meet at the join, when the
    ledger's own adjustment for the history's months is not the one the record was written for,
    or when the table's last balance is not the ledger's -- the page then SAYS so; it never
    papers over."""
    rows, note = [], ""
    hist = hist or {}
    caps = list(t.get("caps") or [])
    hh = list(t.get("hist") or [])
    marks = dict(t.get("marks") or {})
    inst_std = float(t.get("inst") or 0.0)
    int_std = INTEREST_FLAT if t.get("interest_loan") else 0.0
    pre, months = [], set()
    for p in sorted((p for p in (hist.get("pre") or []) if isinstance(p, dict) and _is_ym(p.get("ym"))),
                    key=lambda p: p["ym"]):
        if p["ym"] in months:
            continue
        months.add(p["ym"])
        if p.get("kind") == "skip":
            pre.append((p["ym"], "skip", 0.0, 0.0, float(_num(p.get("added")) or 0.0)))
        else:
            inst = _num(p.get("instalment"))
            intr = _num(p.get("interest"))
            inst = inst_std if inst is None else inst
            intr = min(int_std, inst) if intr is None else intr
            pre.append((p["ym"], "paid", inst, intr, 0.0))
    last_pre = pre[-1][0] if pre else ""
    coll = sorted(m for m, p, i in hh if p + i > 0.005)
    opening = None
    if pre:
        adj = round(sum(a for m, a in caps if m <= last_pre), 2)
        led_start = round(float(t["amount"]) + adj - sum(p for m, p, _i in hh if m <= last_pre), 2)
        back = round(sum(inst - intr for _m, k, inst, intr, _a in pre if k == "paid")
                     - sum(a for _m, k, _i, _n, a in pre if k == "skip"), 2)
        stated = _num(hist.get("opening"))
        opening = stated if stated is not None else round(led_start + back, 2)
        if abs((opening - back) - led_start) > 0.5:
            note = ("The months before the ledger end at Rs %s, but the ledger starts this loan at Rs %s "
                    "— a difference of Rs %s. The balances from %s on are the ledger's."
                    % (inr(opening - back), inr(led_start), inr(abs(opening - back - led_start)),
                       month_words(_ym_add(last_pre, 1))))
        want_adj = _num(hist.get("ledger_adjust"))
        if not note and want_adj is not None and abs(adj - want_adj) > 0.5:
            note = ("For the months before the ledger began, the ledger's own adjustment on this loan is Rs %s; "
                    "this page was written for Rs %s. The opening balance may be out by the difference — read "
                    "the ledger statement." % (inr(adj), inr(want_adj)))
        bal = opening
        for m, k, inst, intr, added in pre:
            if m > ym:
                break
            start = bal
            if k == "skip":
                bal = round(start + added, 2)
                rows.append({"ym": m, "start": start, "inst": 0.0, "interest": 0.0, "principal": 0.0,
                             "added": added, "end": bal, "status": "skip", "src": "history"})
            else:
                bal = round(start - (inst - intr), 2)
                rows.append({"ym": m, "start": start, "inst": inst, "interest": intr,
                             "principal": round(inst - intr, 2), "added": 0.0, "end": bal,
                             "status": "paid", "src": "history"})
        first = _ym_add(last_pre, 1)
        bal = led_start
    else:
        # no history record: the table starts where the LEDGER starts this loan. Anything the ledger
        # dates before that (a migrated loan's earlier skip mark or adjustment) is inside the opening.
        d0 = str(t.get("date", ""))[:7]
        first = min([m for m in ([d0] if _is_ym(d0) else []) + coll] or [ym])
        opening = round(float(t["amount"]) + sum(a for m, a in caps if m < first), 2)
        bal = opening
    m = first
    guard = 0
    while m <= ym and guard < 600:
        guard += 1
        p = round(sum(pp for mm, pp, _i in hh if mm == m), 2)
        i = round(sum(ii for mm, _p, ii in hh if mm == m), 2)
        c = round(sum(a for mm, a in caps if mm == m), 2)
        start = bal
        bal = round(start - p + c, 2)
        if p + i > 0.005:
            status = "paid" if (p + i) >= inst_std - 0.005 or bal <= 0.005 else "part"
        elif marks.get(m):
            status = marks[m]
        elif m == ym and not closed:
            status = "pending"
        else:
            status = "none"
        rows.append({"ym": m, "start": start, "inst": round(p + i, 2), "interest": i, "principal": p,
                     "added": c, "end": bal, "status": status, "src": "ledger"})
        m = _ym_add(m, 1)
    if ym >= first and abs(bal - float(t["end"])) > 0.5 and not note:
        note = ("This table ends at Rs %s but the ledger's balance for the month is Rs %s — read the "
                "ledger statement; one of its rows is not on this table." % (inr(bal), inr(t["end"])))
    nxt = [(mm, p, i) for mm, p, i in (t.get("proj") or []) if mm > ym and p + i > 0.005]
    if closed and nxt and float(t["end"]) > 0.005:     # before the close the month itself is still to come
        mm, p, i = nxt[0]
        rows.append({"ym": mm, "start": float(t["end"]), "inst": round(p + i, 2), "interest": i, "principal": p,
                     "added": 0.0, "end": round(float(t["end"]) - p, 2), "status": "next", "src": "plan"})
    return rows, opening, note


def skips_in_fy(rows, ym):
    """Months of the financial year of `ym`, up to `ym`, in which the instalment was skipped or deferred."""
    fy = fy_of_ym(ym)
    return [r["ym"] for r in rows if r["status"] in ("skip", "defer") and r["ym"] <= ym and fy_of_ym(r["ym"]) == fy]


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


def _hhmm(t):
    """'21:00' -> 1260 minutes after midnight; None when it is not a time."""
    try:
        h, m = str(t).strip().split(":")[:2]
        h, m = int(h), int(m)
        return h * 60 + m if 0 <= h < 24 and 0 <= m < 60 else None
    except (ValueError, TypeError):
        return None


OWN_SHEET_DEFAULT = ""          # S489 (D682): nobody is paid on a sheet of their own any more


def own_sheet_names(s):
    """Staff kept OFF the main salary sheet and paid on a sheet of their own.

    The owner, 12-Sep-2026: Darpan's advance history is long enough that one line on a shared
    sheet cannot tell the truth about it. Set `own_sheet_staff` in the settings to change who is
    on this list; it defaults to the name the owner gave."""
    raw = str(s.get("own_sheet_staff", "") or "").strip()
    return {x.strip().lower() for x in (raw or OWN_SHEET_DEFAULT).split(",") if x.strip()}


def dates_only_names(s):
    return {x.strip().lower() for x in str(s.get("dates_only_staff", "") or "").split(",") if x.strip()}


def _cover_eligible():
    """Names (lower) the register marks cover_eligible -- only they get automatic cover days."""
    try:
        import sqlite3
        import salary_engine as E
        con = sqlite3.connect(E.DB_PATH)
        out = {(r[0] or "").strip().lower() for r in
               con.execute("SELECT name FROM staff WHERE cover_eligible = 1")}
        con.close()
        return out, ""
    except Exception as e:
        return set(), "%s: %s" % (type(e).__name__, e)


def _cover_dates(ym):
    """{staff name (lower): set of 'YYYY-MM-DD'} -- the days the register marks EXTRA
    DUTY (cover). Read-only, from the register's own database. Returns (dates, error)."""
    try:
        import sqlite3
        import salary_engine as E
        con = sqlite3.connect(E.DB_PATH)
        out = {}
        for d, nm in con.execute(
                "SELECT r.reg_date, s.name FROM daily_register r JOIN staff s "
                "ON s.staff_id = r.staff_id WHERE r.extra_duty > 0 AND r.reg_date LIKE ?",
                (ym + "-%",)):
            out.setdefault((nm or "").strip().lower(), set()).add(d)
        con.close()
        return out, ""
    except Exception as e:
        return {}, "%s: %s" % (type(e).__name__, e)


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


def ramp_fine(excess_days, step):
    """D345: the k-th excess absent day costs k x step; cumulative for n days
    = step * n(n+1)/2. Gentle at first, growing only with repetition."""
    n = max(0, int(excess_days))
    return round(step * n * (n + 1) / 2.0, 2)


def sunday_weight(info, s):
    """D341: an absence's weight on a Sunday = that day's rostered minutes over
    the weekday minutes — derived, never typed. sunday_weight_override (0..1)
    forces a value; -1 derives. No sun shift recorded -> weight 1 (fail-safe:
    never silently cheapen an absence on bad data)."""
    ov = s.get("sunday_weight_override", -1)
    try:
        ov = float(ov)
    except (TypeError, ValueError):
        ov = -1
    if 0 <= ov <= 1:
        return ov
    st, en = info.get("sun_start"), info.get("sun_end")
    if not (st and en):
        return 1.0
    sun_m = (en.hour * 60 + en.minute) - (st.hour * 60 + st.minute)
    wd_m = _shift_minutes(info)
    if sun_m <= 0 or wd_m <= 0:
        return 1.0
    return min(1.0, round(sun_m / float(wd_m), 4))


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
    # S199-C: the RUNNING day is excluded — a 6 AM view must not read today as
    # absent. Cutoff = yesterday (past months unaffected).
    _cut = (_TODAY_OVERRIDE or datetime.date.today()) - datetime.timedelta(days=1)
    amr._TODAY_OVERRIDE = _cut
    scn._TODAY_OVERRIDE = _cut
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
    cover_dates, cover_err = _cover_dates(ym)
    cover_elig, _ce_err = _cover_eligible()
    cover_err = cover_err or _ce_err

    man_adv = manual_advances(ym)
    _lp = loan_pages()                 # S489: loan groups + a private loan's pre-ledger months
    _privn = private_loan_names(s)
    _view_err = []
    L, led_err = _ledger()
    led_rows = []
    opens = []
    led_rev = set()
    if L:
        try:
            led_rows = L.load_ledger()
            opens = L.open_advances()
            led_rev = _reversed_ids(led_rows)
        except Exception as e:
            led_err = "%s: %s" % (type(e).__name__, e)
            L = None
    ledger_closed = bool(L) and any(r.get("closed_month") == ym for r in led_rows)

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
        if 0 < charge < s.get("min_charge_rs", 0):
            charge = 0.0                       # below the noise threshold
        if s["hold_enabled"]:
            collect = round(charge * s["collect_now_pct"] / 100.0, 2)
        else:
            collect = charge
        held = round(charge - collect, 2)

        # last month's hold: release preview on measured improvement
        pm = prev_ym(ym)
        ph = holds.get((name, pm))
        prev_min = 0 if exempt else raw_prev.get(uid, 0)
        # D342a: the hold is a SUSPENDED charge — never deducted when charged.
        # Improvement >= threshold -> CANCELLED (release = amount cancelled,
        # display only, NOT added to net: the money never left the packet).
        # No improvement -> COLLECTED with THIS month (prior_collect deducts).
        release = 0.0
        prior_collect = 0.0
        release_note = ""
        if ph and ph["status"] == "HELD" and ph["held"] > 0:
            if prev_min > 0:
                improve = (prev_min - mins) / float(prev_min) * 100.0
                if improve >= s["improve_pct"]:
                    release = ph["held"]
                    release_note = "improved %d%% — suspended charge CANCELLED" % round(improve)
                else:
                    prior_collect = ph["held"]
                    release_note = ("improvement %d%% (< %d%%) — last month's "
                                    "suspended charge collected" % (
                                        round(improve), s["improve_pct"]))
            else:
                release = ph["held"]
                release_note = "no prior lateness — suspended charge CANCELLED"

        # leaves: symmetric at full day rate (owner ruling: no ladder).
        # D340/D341: PAY counts a Sunday absence at its shift-derived weight
        # (half for a half shift); the DETERRENT below stays whole-day (D342c).
        sun_w = sunday_weight(info, s)
        sun_reduction = 0.0
        for dstr in a["absent_dates"]:
            try:
                if datetime.date.fromisoformat(dstr).weekday() == 6:
                    sun_reduction += (1.0 - sun_w)
            except (ValueError, TypeError):
                pass
        leaves_weighted = round(leaves_total - sun_reduction, 2)
        leave_amt = round((leaves_weighted - offs) * day, 2) if base else 0.0
        if not covered and leaves_total == 0 and a["present"] == 0:
            leave_amt = 0.0

        uninf = sum(1 for dstr in a["absent_dates"]
                    if not flags.get((uid, dstr, "ABSENT"), True))
        # D342b/D345b: minutes-exempt staff (Arjun) sit OUTSIDE the whole
        # deterrent-and-reward loop — no fines, exactly as no incentive.
        fine_uninf = 0 if exempt else uninf * s["fine_uninformed"]
        # D345: the flat Rs/day excess fine is DEAD. A ramp beyond the person's
        # OWN allowance, on WHOLE days (D342c: Sunday counts whole here).
        fine_exc = 0 if exempt else ramp_fine(leaves_total - offs,
                                              s.get("fine_ramp_step", 10))
        # S239 (the owner, 11-Sep-2026, "1"): PART-TIME staff (setting dates_only_staff --
        # Amir Sohail, usually Sunday and Thursday) pay NO leave charge: the days he is not
        # rostered are not absences, so neither the leave amount nor the absence fines apply.
        if name.strip().lower() in dates_only_names(s):
            leave_amt, fine_uninf, fine_exc = 0.0, 0, 0

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

        # register duty credits + ledger night duty (S199-C)
        # S238 v1.12: a cover-eligible person's cover days = the register's marked days PLUS
        # every day her out-punch is at/after cover_auto_from (verified by the punch).
        _cov = set(cover_dates.get(name.strip().lower(), set()))
        _is_cover_staff = name.strip().lower() in cover_elig
        if _is_cover_staff and not exempt:
            _auto = _hhmm(s.get("cover_auto_from", "17:00")) or 1020
            for _d, _c in (a.get("grid") or {}).items():
                if isinstance(_c, dict) and _c.get("out"):
                    _o = _hhmm(_c.get("out"))
                    if _o is not None and _o >= _auto:
                        try:
                            _cov.add("%s-%02d" % (ym, int(_d)))
                        except (TypeError, ValueError):
                            pass
        extra_days = len(_cov) if _is_cover_staff else g.get("extra", 0)
        extra_rs = 0.0 if exempt else extra_days * s.get("extra_duty_rs", 200)
        outst_rs = 0.0 if exempt else outst * s.get("outstation_rs", 250)
        night_rs = 0.0

        # ledger side (advances/loans) — S238: the ledger's OWN figures (D349)
        advances_month, loans, adv_ded = [], [], 0.0
        open_bal = 0.0
        lm = None
        if L:
            for r in led_rows:
                if (r.get("category") in ("NIGHT_DUTY", "COVER_DUTY")
                        and r.get("status") == "APPROVED"
                        and r.get("staff") == name):
                    cm = r.get("closed_month")
                    if cm == ym or (not cm and str(r.get("date_from", ""))[:7] == ym):
                        night_rs += float(r.get("amount") or 0)
        if L:
            for r in led_rows:
                if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                        and r.get("staff") == name
                        and str(r.get("date_from", ""))[:7] == ym
                        and float(r.get("amount") or 0) > 0
                        and r.get("id") not in led_rev
                        and not _brought_forward(r)):
                    advances_month.append(r)
            lm = ledger_money(led_rows, name, ym, led_rev)
            loans = lm["lines"]
            open_bal = lm["end"]
            # S238 (D349/D442): deduct EXACTLY what the ledger recovered for this
            # month — its instalment and interest rows stamped to the month. Before
            # the ledger close runs there are none, so the Lock refuses (below).
            adv_ded = lm["deducted"]
        m_adv = man_adv.get(name.strip().lower(), 0.0)
        if m_adv:
            adv_ded = round(adv_ded + m_adv, 2)   # owner-record advance deducts

        leave_in_absent_cnt = (len(leave_dates & set(a["absent_dates"]))
                               if covered else 0)
        absent_excl = max(0, a["absent"] - leave_in_absent_cnt)
        duty_credits = round(night_rs + extra_rs + outst_rs, 2)
        # S238 v1.10: overtime -- the attendance report's minutes beyond shift end on days
        # with a REAL out-punch (F-47), paid at 2 x the person's own minute-rate (D256).
        ot_min = 0 if exempt else int(a.get("ot_min", 0) or 0)
        # S238 v1.11 (the owner): on a COVER day the cover hours are the extra duty,
        # credited separately -- overtime is only what she stayed beyond the cover end.
        # A day's OT below the daily threshold is ignored when the owner switches it on.
        try:
            _thr = int(float(s.get("ot_daily_min", 15) or 0)) if s.get("ot_threshold_on") else 0
        except (TypeError, ValueError):
            _thr = 0
        if (_cov or _thr) and not exempt:
            _ce = _hhmm(s.get("cover_end", "21:00")) or 1260
            ot_min = 0
            for _d, _c in (a.get("grid") or {}).items():
                if not isinstance(_c, dict) or not _c.get("ot"):
                    continue
                try:
                    _ds = "%s-%02d" % (ym, int(_d))
                except (TypeError, ValueError):
                    continue
                if _ds in _cov:
                    _o = _hhmm(_c.get("out", ""))
                    _day = max(0, _o - _ce) if _o is not None else 0
                else:
                    _day = int(_c.get("ot") or 0)
                if _day > 0 and _day >= _thr:
                    ot_min += _day
        ot_rs = round(ot_min * rate * 2, 2) if (base and ot_min) else 0.0
        ot_paid = ot_rs if s.get("ot_pay") else 0.0
        deductions = round(collect + leave_amt + fine_uninf + fine_exc
                           + dress_rs + icard_rs + prior_collect, 2)
        # S199-D: incentive accrues to the Diwali pot — NOT in the month's net.
        # D342a: release is a CANCELLATION note only, never money added back.
        net_exact = round(base - deductions - adv_ded + duty_credits + ot_paid, 2) \
            if base else 0.0
        # D477 (the owner, 12-Sep-2026): "round off net payable to last 10 rupees". Money is
        # handed over in notes, so the paise and the last digit are not paid. The cut is always
        # TOWARDS ZERO -- a payable of 8,651.33 is paid 8,650, and a month that ends negative
        # carries 1,940 forward, not 1,950 -- so the rounding never runs against the person.
        net = float(int(abs(net_exact) / 10) * 10) * (-1.0 if net_exact < 0 else 1.0)
        net_round_off = round(net_exact - net, 2)

        # S489 (D681): the ledger's lines sorted into what Sheet 2 shows.
        # S489 (D682): a person with a PRIVATE long-term loan sits on the common sheets at base
        # LESS the loan's standing instalment. Everything above -- day rate, minute rate, leave,
        # late, overtime, incentive -- was worked on the FULL base and is not touched. Only three
        # shown figures change: the salary, the advance column (the long-term instalment leaves
        # it) and the net (it loses what the private page pays him: nothing in an ordinary month,
        # the whole instalment in a month it was not taken).  full net == net + priv["reserve"].
        _is_priv = name.strip().lower() in _privn
        try:
            views = (advance_views(lm, name, ym, ledger_closed, _lp["groups"], private=_is_priv)
                     if lm else {"month_adv": [], "loans": [], "priv_lines": []})
            priv = private_split(views["priv_lines"], ym, ledger_closed) if _is_priv else None
        except Exception as _e:        # sorting the lines for display must never take the salary sheet down
            views, priv = {"month_adv": [], "loans": [], "priv_lines": []}, None
            _view_err.append("%s (%s)" % (name, type(_e).__name__))
        base_shown, adv_shown, adv_full, net_full = base, adv_ded, adv_ded, net
        if priv and base:
            base_shown = round(base - priv["kept"], 2)
            adv_shown = round(adv_ded - priv["cut_shown"], 2)
            net = round(net - priv["reserve"], 2)
            net_exact = round(net_exact - priv["reserve"], 2)

        staff_out.append({
            "uid": uid, "name": name, "base": base_shown, "base_full": base, "exempt": exempt,
            "offs": offs, "shift_min": shift_min, "rate": round(rate, 4),
            "present": a["present"], "absent": a["absent"],
            "absent_excl": absent_excl, "leave_in_absent": leave_in_absent_cnt,
            "night_rs": night_rs, "extra_rs": extra_rs, "extra_days": extra_days, "outst_rs": outst_rs,
            "outst_days": outst, "ot_min": ot_min, "ot_rs": ot_rs, "ot_paid": ot_paid,
            "duty_credits": duty_credits,
            "genuine": genuine, "disc": disc, "fest": fest,
            "leaves_total": leaves_total, "leave_amt": leave_amt,
            "marks": marks, "grace_days": a["grace_days"],
            "late_min": mins, "late_charge": charge,
            "collect": collect, "held": held,
            "prev_min": prev_min, "release": release, "release_note": release_note,
            "prior_collect": prior_collect,
            "leaves_weighted": leaves_weighted,
            "fine_uninf": fine_uninf, "fine_exc": fine_exc,
            "dress_days": dressn, "icard_days": icardn,
            "dress_rs": dress_rs, "icard_rs": icard_rs,
            "incentive": inc, "inc_tier": inc_tier,
            "advances_month": advances_month, "loans": loans,
            "open_bal": open_bal, "adv_ded": adv_shown, "adv_ded_full": adv_full, "manual_adv": m_adv,
            "views": views, "priv": priv, "net_full": net_full,
            "ledger_money": lm,
            "grid": a["grid"], "absent_dates": a["absent_dates"],
            "leave_dates": leave_dates, "net": net,
            "net_exact": net_exact, "net_round_off": net_round_off,
        })

    notes = []
    if _view_err:
        notes.append("The advance tables could not be laid out for %s — the salary figures are still the "
                     "ledger's own, but read the ledger statement and do NOT approve or print these sheets."
                     % ", ".join(_view_err))
    if reg_err:
        notes.append("register: %s (grid items zero)" % reg_err)
    if led_err:
        notes.append("ledger: %s (advance/loan columns empty)" % led_err)
    elif not ledger_closed:
        notes.append("The staff ledger has NOT been closed for %s yet, so the Advance column "
                     "is 0 — recoveries enter only at the ledger close (it opens on the 1st of "
                     "the next month). The Lock refuses until it has run." % month_words(ym))
    if cover_err:
        notes.append("extra-duty (cover) days could not be read (%s) — overtime on cover "
                     "days is NOT reduced to the time after %s" % (cover_err, s.get("cover_end")))
    if not covered:
        notes.append("register grid NOT COVERED for %s — sanctioned leave "
                     "cannot be separated" % ym)
    return {"ym": ym, "settings": s, "covered": covered, "staff": staff_out,
            "ledger_closed": ledger_closed,
            "notes": notes, "enforced": enforced(ym, s),
            "preview": not enforced(ym, s)}


# ------------------------------------------------------------- rendering ----
_CSS = """
 body{font-family:Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.5;margin:16px;color:#222;background:#faf8f4}
 h1{font-size:22px;margin:0 0 2px} h2{font-size:17px;margin:16px 0 6px}
 .sub{color:#555;margin:0 0 8px;font-size:14.5px}
 .cap{display:inline-block;background:#eee7d8;border:1px solid #cbbfa4;border-radius:6px;
      padding:2px 10px;font-weight:bold;font-size:13px;letter-spacing:.5px}
 .banner{padding:8px 12px;margin:10px 0;border-radius:8px;font-weight:bold}
 .prev{background:#fff8e1;border:1px solid #e0c060}
 .enf{background:#e8f4e8;border:1px solid #7ab97a}
 .nav{position:sticky;top:0;background:#13233b;padding:8px 12px;margin:-16px -16px 12px;
      display:flex;gap:14px;flex-wrap:wrap;z-index:5}
 .nav a{color:#bfe3ff;text-decoration:none;font-size:15px;font-weight:bold}
 .nav a.here{color:#ffd868}
 .tw{overflow-x:auto} table{border-collapse:collapse;margin:8px 0}
 th,td{border:1px solid #b9b0a0;padding:7px 10px;text-align:left;white-space:nowrap;font-size:16px}
 td{font-weight:600;color:#111} th{font-weight:700}
 th{background:#f0ede6}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 tr.tot td{font-weight:bold;background:#faf7ef}
 td.gL{background:#dcf0dc} td.gA{background:#f8d7d7} td.gR{background:#dbe9fa}
 td.t0{} td.t1{background:#fff3d6} td.t2{background:#ffd9d9}
 td.gOFF{color:#c8c0b2;text-align:center}
 th.sun{background:#e6e0f7;color:#4c1d95}
 th.sun small{display:block;font-size:9px;letter-spacing:.06em}
 td.sun,th.sun{border-left:3px solid #7c5cff}
 td.sun.t0{background:#f5f2ff}
 .gcell{font-size:14px;text-align:center}
 a.door{color:#0a58ca;text-decoration:none}
 .note{background:#fff8e1;border:1px solid #e0c060;padding:8px 12px;margin:8px 0;font-size:14.5px}
 a.doorbtn{display:inline-block;background:#1e4f8a;color:#fff;font-weight:bold;
   padding:10px 16px;border-radius:10px;text-decoration:none;font-size:15px;margin:6px 0}
 a.doorbtn.warn{background:#b45f06}
 a.doorbtn.back{background:#455a70}
 .apvbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:#eef4ff;
   border:1.5px solid #1e4f8a;border-radius:10px;padding:10px 14px;margin:10px 0;font-size:15px}
 .apvbar form{margin:0} .apvbar button{background:#16794a;color:#fff;border:0;border-radius:9px;
   padding:10px 18px;font-size:15px;font-weight:bold;cursor:pointer}
 .apvbar .done{color:#166534;font-weight:bold}
 .hdr{text-align:center;margin-bottom:4px}
 tr.flag td{background:#fff3d6}
 @media print{ body{margin:6mm;background:#fff} .noprint,.nav{display:none} th,td{font-size:10.5px;padding:3px 5px} }
"""


def _banner(res):
    if res["enforced"]:
        return '<div class="banner enf noprint">ENFORCED — this month is covered by the served notice.</div>'
    return ('<div class="banner prev noprint">PREVIEW — nothing on this page is applied '
            'to pay. Enforcement starts only when the notice date is set in '
            'Settings.</div>')


def _head(title):
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body>"
            % (html.escape(title), _CSS))


def _clinic_hdr(sheet_line, cap="MACHINE DATA — for review"):
    return ("<div class='hdr'><h1>Dr. Manoj Agarwal Clinic</h1>"
            "<div class='sub'>%s</div>%s</div>"
            % (html.escape(sheet_line),
               ("<span class='cap'>%s</span>" % html.escape(cap)) if cap else ""))


def _nav(prefix, ym, here=""):
    pm, nm = prev_ym(ym), _next_ym(ym)
    page = {"s1": "sheet1", "s2": "sheet2", "prev": "preview"}.get(here, "")
    sfx = ("/" + page) if page else ""
    items = [("flow", "Month-end flow", "%s/salary/flow?ym=%s" % (prefix, ym)),
             ("s1", "Sheet 1 · Attendance", "%s/salary/flow/sheet1?ym=%s" % (prefix, ym)),
             ("s2", "Sheet 2 · Money", "%s/salary/flow/sheet2?ym=%s" % (prefix, ym)),
             ("darpan", "Darpan · loan (private)", "%s/salary/flow/sheet2?ym=%s&staff=Darpan" % (prefix, ym)),
             ("prev", "Salary sheets", "%s/salary/flow/preview?ym=%s" % (prefix, ym)),
             ("desk", "Lock desk", "%s/salary?ym=%s" % (prefix, ym)),
             ("set", "Settings", "%s/salary/policy-settings" % prefix),
             ("ledger", "Ledger", "/ledger/")]
    bar = "".join('<a class="%s" href="%s">%s</a>'
                  % ("here" if k == here else "", html.escape(u), html.escape(t))
                  for k, t, u in items)
    bar += ('<span style="margin-left:auto;white-space:nowrap">'
            '<a href="%s/salary/flow%s?ym=%s" title="previous month">&#9198; %s</a>'
            '&nbsp;&nbsp;<a href="%s/salary/flow%s?ym=%s" title="next month">%s &#9197;</a></span>'
            % (prefix, sfx, pm, pm, prefix, sfx, nm, nm))
    return '<div class="nav noprint">' + bar + "</div>"


def _next_ym(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m > 12:
        m = 1; y += 1
    return "%04d-%02d" % (y, m)


def sheet1_html(res, doors=False, prefix="/register", only_uid=None,
                back=None, print_=False, approve_html=""):
    """Attendance grid — two stacked half-month blocks, in-times visible in the
    cells (S199-C). only_uid -> a staff member's own view."""
    ym = res["ym"]
    e = html.escape
    year, mon = int(ym[:4]), int(ym[5:7])
    import calendar
    ndays = calendar.monthrange(year, mon)[1]
    halves = [range(1, 17), range(17, ndays + 1)]
    rows = [st for st in res["staff"]
            if only_uid is None or st["uid"] == only_uid]

    out = [_head("Attendance %s" % ym)]
    if only_uid is None:
        out.append(_nav(prefix, ym, "s1"))
    out.append(_clinic_hdr("SHEET 1 · ATTENDANCE — %s" % month_words(ym)))
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    if approve_html and only_uid is None and not print_:
        out.append('<div class="noprint">%s</div>' % approve_html)
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    if doors and only_uid is None:
        out.append('<div class="noprint"><a class="doorbtn warn" href="%s/fixabsents'
                   '?ym=%s">&#128295; FIX ABSENTS — the whole month on one page</a></div>'
                   % (e(prefix), e(ym)))

    def cell(st, d):
        c = st["grid"].get(d)
        dstr = "%s-%02d" % (ym, d)
        if c is None:
            return "<td></td>"
        stt = c.get("st")
        if stt == "OFF":
            return '<td class="gOFF">&middot;</td>'
        if stt == "AB":
            mark = "L" if dstr in st["leave_dates"] else "A"
            cls = "gL" if mark == "L" else "gA"
            inner = ('<a class="door" href="%s/?d=%s">%s</a>' % (prefix, dstr, mark)
                     if doors else mark)
            return '<td class="%s gcell">%s</td>' % (cls, inner)
        late = c.get("late", 0)
        tcls = "t2" if late >= 60 else ("t1" if late else "t0")
        tip = "%s–%s" % (c.get("in", ""), c.get("out", "") or "…")
        if late:
            tip += " · %d min late" % late
        body = e(c.get("in", "P")) + ("&#42;" if c.get("req") else "")
        if doors and c.get("req"):
            body = '<a class="door" href="%s/review?ym=%s">%s</a>' % (prefix, ym, body)
        return ('<td class="%s gcell%s"><span title="%s">%s</span></td>'
                % (tcls, " gR" if c.get("req") else "", e(tip), body))

    def _sunmark(td):
        """Add the sun class to a rendered <td>, whatever classes it has."""
        if td.startswith('<td class="'):
            return '<td class="sun ' + td[len('<td class="'):]
        if td.startswith("<td>"):
            return '<td class="sun">' + td[4:]
        return td

    _donly = dates_only_names(res.get("settings") or {}) if only_uid is None else set()
    _grid_rows = [st for st in rows if st["name"].strip().lower() not in _donly]

    def _punch_days(st):
        ds = []
        for d in sorted(k for k, c in (st.get("grid") or {}).items()
                        if isinstance(c, dict) and c.get("st") == "P"):
            t = "%d" % d
            ds.append("<span class='sunk'>%s</span>" % t
                      if datetime.date(year, mon, d).weekday() == 6 else t)
        return ds

    out.append('<div class="s1grid">')
    for half in halves:
        days = [d for d in half]
        out.append('<div class="tw"><table><tr><th>Staff</th>')
        for d in days:
            _wd = datetime.date(year, mon, d).weekday()
            out.append('<th class="sun">%d<small>SUN</small></th>' % d
                       if _wd == 6 else "<th>%d</th>" % d)
        out.append("</tr>")
        for st in _grid_rows:
            out.append("<tr><td><b>%s</b></td>" % e(st["name"]))
            for d in days:
                _td = cell(st, d)
                out.append(_sunmark(_td)
                           if datetime.date(year, mon, d).weekday() == 6 else _td)
            out.append("</tr>")
        out.append("</table></div>")
    for st in rows:
        if st["name"].strip().lower() in _donly:
            _pd = _punch_days(st)
            out.append('<div class="sub" style="font-size:13px;margin:4px 0"><b>%s</b> — punched on '
                       '%d day(s): %s</div>' % (e(st["name"]), len(_pd), ", ".join(_pd) or "none"))
    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red '
               '&ge;60).<span class="noprint"> Hover for the out-punch.</span> L sanctioned leave · A absent · '
               '&#42; approved present-request. Sundays carry the purple SUN column. '
               'The running day is excluded until '
               'it ends. Money appears on no staff copy.</div>')
    out.append('</div><div class="s1sum">')
    out.append('<div class="printonly">%s</div>'
               % _clinic_hdr("SHEET 1 · MONTH SUMMARY — %s" % month_words(ym)))
    money_ok = only_uid is None            # money never appears on a staff copy
    out.append("<h2>Month summary</h2><div class='tw'><table class='s1t'>"
               "<tr><th rowspan='2'>Staff</th><th rowspan='2'>Present</th>"
               "<th colspan='4'>DAYS NOT PUNCHED on the machine</th>"
               "<th rowspan='2' class='dcol'>Dates not punched<br><small>(check against the "
               "physical register · <span class='sunk'>Sun</span> · L = sanctioned leave)</small></th>"
               "<th rowspan='2'>Late marks</th><th rowspan='2'>Late min</th>"
               + ("<th rowspan='2'>Late fine<br><small>(total)</small></th>" if money_ok else "")
               + "<th rowspan='2'>OT min</th>"
               + ("<th rowspan='2'>OT payable<br><small>%s</small></th>"
                  % ("in the net" if res["settings"].get("ot_pay") else "shown, not paid")
                  if money_ok else "")
               + ("<th rowspan='2' class='rcol'>Remark</th>" if print_ else "")
               + "</tr><tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
               "<th>absent, no leave</th></tr>")
    for st in rows:
        if st["name"].strip().lower() in _donly:
            continue          # S239: part-time -- his days are listed above, not counted as absences
        lv = st.get("leave_dates") or set()
        ds = []
        for d in sorted(st.get("absent_dates") or []):
            try:
                dd = datetime.date.fromisoformat(d)
            except (ValueError, TypeError):
                continue
            t = "%d" % dd.day + ("L" if d in lv else "")
            ds.append("<span class='sunk'>%s</span>" % t if dd.weekday() == 6 else t)
        absent = st.get("absent", 0)
        lia = st.get("leave_in_absent", 0)
        outst = min(st.get("outst_days", 0), max(0, absent - lia))
        if st["name"].strip().lower() in _donly:
            _pd = _punch_days(st)
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>—</td>"
                       "<td class='n'>—</td><td class='n'>—</td><td class='n'>—</td>"
                       "<td class='dcol'>punched on: %s</td><td class='n'>%d</td><td class='n'>%d</td>%s"
                       "<td class='n'>%d</td>%s%s</tr>"
                       % (e(st["name"]), st["present"], ", ".join(_pd) or "none",
                          st["marks"], st["late_min"],
                          ("<td class='n'>%s</td>" % money(st["late_charge"])) if money_ok else "",
                          st.get("ot_min", 0),
                          ("<td class='n'>%s</td>" % money(st.get("ot_rs", 0))) if money_ok else "",
                          "<td class='rcol'></td>" if print_ else ""))
            continue
        out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                   "<td class='n'>%d</td><td class='n'>%d</td><td class='n'>%d</td>"
                   "<td class='dcol'>%s</td><td class='n'>%d</td><td class='n'>%d</td>%s"
                   "<td class='n'>%d</td>%s%s</tr>"
                   % (e(st["name"]), st["present"], absent, lia, outst,
                      max(0, absent - lia - outst), ", ".join(ds) or "—",
                      st["marks"], st["late_min"],
                      ("<td class='n'>%s</td>" % money(st["late_charge"])) if money_ok else "",
                      st.get("ot_min", 0),
                      ("<td class='n'>%s</td>" % money(st.get("ot_rs", 0))) if money_ok else "",
                      "<td class='rcol'></td>" if print_ else ""))
    out.append("</table></div>")
    out.append('<div class="sub">Days not punched = sanctioned leave + outstation + absent '
               'without leave (one set of days). OT = minutes beyond shift end on days with a '
               'real out-punch; on a cover day (marked extra duty, or for cover staff a punch-out '
               'at/after %s) only the minutes after %s.%s%s%s</div>'
               % (e(str(res["settings"].get("cover_auto_from", "17:00"))),
                  e(str(res["settings"].get("cover_end", "21:00"))),
                  (' A day under %s min of OT is not counted.' % res["settings"].get("ot_daily_min", 15))
                  if res["settings"].get("ot_threshold_on") else '',
                  ' Late fine = the whole month\'s late charge before any hold; OT payable at '
                  '2 &times; own minute-rate.' if money_ok else '',
                  ' The blank last column is the staff-remark space.' if print_ else ''))
    out.append("</div>")
    out.append(_S1_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


# S238 v1.10: Sheet 3 on A4 LANDSCAPE with every column inside the page (it had
# grown past portrait width); Sheet 4, the signature sheet, stays portrait.
_SLIP_CSS = ("<style>.ownt tr.new td{background:#f3faf3}"
             ".ownt tr.newtot td{background:#dcf0dc;font-weight:700}"
             ".ownt tr.new td:first-child{padding-left:22px}"
             ".ownt tr.new td.n{font-weight:400;color:#444}"
             ".slip table.ownt{min-width:440px}"
             "@media print{.slip table.ownt{width:calc(100% - 2px)}}"
             ".loanfoot{border:1px solid #c79a2a;background:#fffbeb;padding:8px 12px;margin:8px 0;"
             "font-size:14px;max-width:520px;line-height:1.45}"
             ".loanfoot .wk{color:#666;font-size:12px}</style>")

_OWN_SHEET_CSS = ("<style>.ownt td,.ownt th{padding:6px 9px}"
                  ".ownt .wk{color:#666;font-size:11px}"
                  ".ownt tr.sec td{background:#f2f2f2;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.06em}"
                  ".ownt tr.net td{border-top:2px solid #222;font-size:15px}"
                  ".ownwarn{border:1px solid #a33;background:#fdecea;color:#a33;padding:9px 12px;margin:10px 0;font-size:13px;max-width:520px}</style>")

_S34_PRINT_CSS = """<style>
 @page{size:A4 landscape;margin:7mm}
 @page s4{size:A4 portrait;margin:10mm}
 @media print{
  body{margin:0;font-size:10px;line-height:1.25}
  .tw{overflow:visible}
  .hdr h1{font-size:16px} .hdr .sub{font-size:11.5px;margin:0 0 3px}
  table.s3t{width:100%;table-layout:auto}
  table.s3t th{font-size:9px;padding:3px 2px;white-space:normal;line-height:1.15;vertical-align:bottom}
  table.s3t td{font-size:10px;padding:4px 2px}
  .s4pg{page:s4}
  .s4pg table{width:100%}
  .s4pg th,.s4pg td{font-size:12px;padding:6px 8px}
  .sub{font-size:9.5px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


# S238: Sheet 2 on A4 — every section whole on one sheet, never split; several
# sections share a sheet when they fit. Screen view unchanged.
_S2_PRINT_CSS = """<style>
 @page{size:A4 landscape;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  tr.flag td{background:#fff3d6}
  .s2sec{break-inside:avoid;page-break-inside:avoid;margin:0 0 10px}
  .s2sec h2{font-size:13px;margin:8px 0 4px;break-after:avoid;page-break-after:avoid}
  .s2sec table{width:100%;margin:2px 0}
  .s2sec th,.s2sec td{font-size:11px;padding:4px 5px;white-space:normal}
  .s2sec table.wide th,.s2sec table.wide td{font-size:11.5px;padding:6px 3px}
  .s2sec table.wide small{font-size:10.5px}
  .s2sec td small{font-size:10px}
  .sub{font-size:10px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


# S238: A4, two pages. Page 1 = the grid (every day, never clipped), page 2 = the
# summary. The screen view is untouched; these rules act only when printing.
_S1_PRINT_CSS = """<style>
 .printonly{display:none}
 @page{size:A4 portrait;margin:8mm}
 @page s1sum{size:A4 landscape;margin:8mm}
 .sunk{color:#3b0f8a;font-weight:800;text-decoration:underline}
 .s1t td.dcol{white-space:normal;min-width:180px;max-width:320px;font-size:13px}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .printonly{display:block}
  .s1sum{page:s1sum}
  .s1t td.dcol{font-size:10.5px;max-width:none}
  .s1t .rcol{width:26mm}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .hdr .cap{font-size:10px;margin-top:2px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  .sub{font-size:10.5px}
  .s1grid table{width:100%;table-layout:fixed;margin:4px 0}
  .s1grid th,.s1grid td{font-size:11.5px;padding:6px 0;line-height:1.25;text-align:center;white-space:nowrap;overflow:hidden}
  .s1grid th:first-child,.s1grid td:first-child{width:22mm;text-align:left;padding-left:3px;font-size:12px}
  .s1grid .gcell{font-size:11.5px}
  .s1grid .sub{font-size:12px;color:#333}
  .s1grid th.sun small{font-size:6px;letter-spacing:0}
  .s1grid td.sun,.s1grid th.sun{border-left:2px solid #7c5cff}
  .s1grid{break-after:page;page-break-after:always}
  .s1grid .tw{break-inside:avoid;page-break-inside:avoid}
  .s1sum table{width:100%}
  .s1sum th,.s1sum td{font-size:11px;padding:4px 6px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


def _part_time_html(res):
    """S239 (the owner, 11-Sep-2026): part-time staff (setting dates_only_staff -- Amir Sohail,
    usually Sunday and Thursday, days can change) have no leave, fine or credit columns; the
    owner sees the days they punched, with in and out times."""
    e = html.escape
    pt = dates_only_names(res.get("settings") or {})
    ym = res["ym"]
    y, m = int(ym[:4]), int(ym[5:7])
    blocks = []
    for st in res["staff"]:
        if st["name"].strip().lower() not in pt:
            continue
        rows = []
        for d in sorted(k for k, c in (st.get("grid") or {}).items()
                        if isinstance(c, dict) and c.get("st") == "P"):
            c = st["grid"][d]
            dd = datetime.date(y, m, d)
            rows.append("<tr><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                        % (dd.strftime("%d-%b"), dd.strftime("%a"),
                           e(str(c.get("in", "") or "-")), e(str(c.get("out", "") or "-"))))
        blocks.append("<h3 style='margin:8px 0 4px'>%s — punched on %d day(s)</h3>"
                      "<div class='tw'><table><tr><th>Date</th><th>Day</th><th>In</th><th>Out</th></tr>%s"
                      "</table></div>"
                      % (e(st["name"]), len(rows),
                         "".join(rows) or "<tr><td colspan='4'>no punch this month</td></tr>"))
    if not blocks:
        return ""
    return ("<section class='s2sec'><h2>Part-time staff — days punched</h2>%s"
            "<div class='sub'>Part-time: no leave, fine or credit columns. Days worked are "
            "the days punched on the machine.</div></section>" % "".join(blocks))


_S489_CSS = ("<style>"
             ".chip{display:inline-block;border:1px solid #9aa5b4;border-radius:4px;padding:1px 8px;"
             "font-size:13.5px;margin:2px 5px 2px 0;white-space:nowrap;font-weight:600;background:#fff}"
             ".chip.paid{background:#dcf0dc;border-color:#3d8b3d;color:#14532d}"
             ".chip.now{background:#fff3d6;border-color:#c79a2a;color:#6b4a00}"
             ".chip.due{border-style:dashed;color:#333}"
             ".chip.skip,.chip.defer,.chip.hold{background:#fde8e8;border-color:#b55;color:#7a1f1f}"
             "tr.strip td{background:#fbfaf6;white-space:normal}"
             "th.n{text-align:right}"
             "tr.pfirst td{border-top:2px solid #6b6252}"
             "@media print{.s2sec table,table.lled{width:calc(100% - 2px) !important} .lfacts{padding-right:2px}"
             " .chip{font-size:10.5px;padding:0 5px}}"
             "tr.bear td{background:#13233b;color:#fff;border-color:#13233b}"
             ".lfacts{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0}"
             ".lfacts div.f{flex:1;min-width:150px;border:1px solid #b9b0a0;border-radius:8px;padding:8px 12px;background:#fff}"
             ".lfacts .l{font-size:12px;color:#555;text-transform:uppercase;letter-spacing:.05em}"
             ".lfacts .v{font-size:21px;font-weight:700}"
             ".lfacts .s{font-size:13px;color:#555}"
             "table.lled td,table.lled th{padding:8px 12px}"
             "table.lled tr.open td{background:#f0ede6;font-weight:700}"
             "table.lled tr.skip td{background:#fff8e1}"
             "table.lled tr.next td{color:#777;font-style:italic;font-weight:400}"
             "table.lled tr.tot td{background:#13233b;color:#fff;border-color:#13233b}"
             ".tag{display:inline-block;border:1px solid;border-radius:4px;padding:0 8px;font-size:13px;font-weight:700}"
             ".tag.pd{background:#dcf0dc;border-color:#3d8b3d;color:#14532d}"
             ".tag.sk{background:#fff3d6;border-color:#c79a2a;color:#6b4a00}"
             ".tag.du{background:#fff;border-color:#9aa5b4;border-style:dashed;color:#555;font-style:normal}"
             ".tag.no{background:#fde8e8;border-color:#b55;color:#7a1f1f}"
             ".signline{margin-top:26px;font-size:13px;color:#444}"
             ".signline span{display:inline-block;min-width:260px;border-bottom:1px solid #444;height:34px}"
             "</style>")

_STRIP_WORD = {"skip": "skipped", "defer": "deferred", "hold": "held"}


def _strip_html(loan):
    """The month strip of one loan: a chip per month, paid months ticked."""
    bits = []
    due = [m for m, _a, k in loan["strip"] if k == "due"]
    for m, a, k in loan["strip"]:
        if k == "paid":
            bits.append("<span class='chip paid'>%s %s &#10004;</span>" % (_m_short(m), inr(a)))
        elif k == "now":
            bits.append("<span class='chip now'>%s %s · this salary</span>" % (_m_short(m), inr(a)))
        elif k == "due":
            last = " · last" if (due and m == due[-1] and len(due) > 1) else ""
            bits.append("<span class='chip due'>%s %s%s</span>" % (_m_short(m), inr(a), last))
        else:
            bits.append("<span class='chip %s'>%s · %s</span>" % (k, _m_short(m), _STRIP_WORD.get(k, k)))
    return " ".join(bits)


def _views_of(st, res):
    v = st.get("views")
    if v is None:                                   # a result made by an older compute (never on the box)
        v = advance_views(st.get("ledger_money"), st["name"], res["ym"], bool(res.get("ledger_closed")),
                          loan_pages()["groups"],
                          private=str(st["name"]).strip().lower() in private_loan_names(res.get("settings")))
    return v


def advances_sections_html(res, pick, doors=False, ledger_prefix="/ledger"):
    """D681: the three advance tables of Sheet 2, for the staff in `pick`."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    mw = month_words(ym)
    msal = MONTHS[int(ym[5:7])]
    out = []

    def door(st):
        return ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                % (ledger_prefix, e(st["name"]))) if doors else ""

    # ---- 1 · this month's advances -------------------------------------------------
    out.append("<section class='s2sec'><h2>1 · This month's advances — cut in full from this salary</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Date given</th><th class='n'>Amount</th>"
               "<th>Cut from</th><th class='noprint'></th></tr>")
    any_a = False
    for st in pick:
        v = _views_of(st, res)
        for i, a in enumerate(v["month_adv"]):
            any_a = True
            out.append("<tr%s><td>%s</td><td>%s</td><td class='n'>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='pfirst'" if i == 0 else "", ("<b>%s</b>" % e(st["name"])) if i == 0 else "",
                          "brought forward" if a.get("bf") else e("%s %s" % (_d_short(a["date"]), str(a["date"])[:4])),
                          inr(a["amount"]),
                          ("%s salary" % msal) if closed else ("%s salary — at the ledger close" % msal),
                          door(st) if i == 0 else ""))
    if not any_a:
        out.append("<tr><td colspan='5'>none this month</td></tr>")
    out.append("</table></div><div class='sub'>Each of these is cut in full from this one salary."
               "</div></section>")

    # ---- 2 · instalment loans -------------------------------------------------------
    out.append("<section class='s2sec'><h2>2 · Instalment loans — one line per person, per loan</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Loan</th><th>Instalment</th>"
               "<th class='n'>Paid so far</th><th class='n'>Cut this month</th><th class='n'>Balance</th><th>Ends</th>"
               "<th class='noprint'></th></tr>")
    any_l = False
    n_late = 0
    for st in pick:
        v = _views_of(st, res)
        for i, L in enumerate(v["loans"]):
            any_l = True
            if L["balance_after"] <= 0.005 and not [1 for _m, _a, k in L["strip"] if k == "due"]:
                ends = "finished this month" if L["cut"] > 0.005 else "finished"
            elif L["ends"]:
                ends = e(month_words(L["ends"]))
            else:
                ends = "no recovery set — see the ledger"
            if L.get("late_month"):
                n_late += 1
                ends += " <small>· booked against a later month — check</small>"
            paid = ("%s<br><small>%d of %d</small>" % (inr(L["paid"]), L["n_paid"], L["n_all"])
                    if L["n_all"] else inr(L["paid"]))
            out.append("<tr%s><td>%s</td><td>Rs %s<br><small>given %s</small></td><td>%s</td>"
                       "<td class='n'>%s</td><td class='n'><b>%s</b></td><td class='n'><b>%s</b></td>"
                       "<td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='pfirst'" if i == 0 else "", "<b>%s</b>" % e(st["name"]), inr(L["amount"]),
                          e(L["given"]), e(L["inst"]), paid,
                          inr(L["cut"]) if L["cut"] > 0.005 else "—",
                          inr(L["balance_after"] if not closed else L["balance"]), ends,
                          door(st) if i == 0 else ""))
            parts = ""
            if len(L["parts"]) > 1:
                parts = ("<div class='sub' style='margin:3px 0 0'>Handed over in %d parts: %s.</div>"
                         % (len(L["parts"]),
                            " · ".join("%s %s" % (_d_short(t["date"]), inr(t["amount"])) for t in L["parts"])))
            out.append("<tr class='strip'><td></td><td colspan='7'>%s%s</td></tr>" % (_strip_html(L), parts))
    if not any_l:
        out.append("<tr><td colspan='8'>no instalment loan is running</td></tr>")
    out.append("</table></div><div class='sub'>Money paid back over more than one salary. One line for the "
               "whole loan, however many parts it was handed over in. A ticked month is what the ledger took; "
               "the months ahead follow the ledger's own recovery rules, and a month skipped, deferred or held "
               "moves them later.</div></section>")

    # ---- 3 · what each salary bears -------------------------------------------------
    out.append("<section class='s2sec'><h2>3 · What each salary bears this month</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th class='n'>This month's advances</th><th class='n'>Loan instalment</th>"
               "<th class='n'>Cut from %s salary</th><th class='n'>Loan balance after</th><th class='n'>Next month's instalment</th></tr>" % e(msal))
    any_b = False
    odd = []
    for st in pick:
        v = _views_of(st, res)
        adv = round(sum(a["cut"] for a in v["month_adv"]), 2)
        loan = round(sum(L["cut"] for L in v["loans"]), 2)
        priv = st.get("priv") or {}
        extra = float(priv.get("extra") or 0.0)             # a second long-term instalment in one month
        man = float(st.get("manual_adv") or 0.0)
        total = round(adv + loan + extra + man, 2)
        bal = round(sum(L["balance_after"] for L in v["loans"]), 2)
        nxt = round(sum(L["next"] for L in v["loans"]), 2)
        if not (adv or loan or extra or man or bal):
            continue
        any_b = True
        if closed and abs(total - float(st.get("adv_ded") or 0.0)) > 0.5:
            odd.append(st["name"])
        dash = "—"
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td class='n'>%s</td>"
                   "<td class='n'><b>%s</b></td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]), inr(adv + man) if (adv or man) else dash,
                      inr(loan + extra) if (loan or extra) else dash, inr(total),
                      inr(bal) if bal > 0.005 else dash, inr(nxt) if nxt > 0.005 else dash))
    if not any_b:
        out.append("<tr><td colspan='6'>nothing is cut for advances this month</td></tr>")
    out.append("</table></div>")
    if odd:
        out.append("<div class='note'><b>Does not add up for %s:</b> the two columns do not make the Advance "
                   "figure on the salary sheet. Do not approve this sheet — read the ledger statement first.</div>"
                   % e(", ".join(odd)))
    if not closed:
        out.append("<div class='note'>The staff ledger is not closed for %s yet. The 'cut' figures above are what "
                   "the ledger close WILL take; they enter the salary only when it has run.</div>" % mw)
    if n_late:
        out.append("<div class='note'>%d advance%s above %s booked against a LATER month than the month it was "
                   "given and set to come back in one go. If that is a slip, correct it in the ledger (reverse it "
                   "and enter it again), then reload this sheet.</div>"
                   % (n_late, "" if n_late == 1 else "s", "is" if n_late == 1 else "are"))
    out.append("<div class='sub'>The first money column is table 1, the second is table 2; together they are "
               "the Advance figure on the salary sheet.</div></section>")
    return "".join(out)


def loan_page_html(res, staff, doors=False, ledger_prefix="/ledger", back=None, prefix="/register"):
    """D682: the PRIVATE page of a person with a long-term loan -- one loan-ledger table."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    st = next((x for x in res["staff"] if str(x["name"]).strip().lower() == staff.strip().lower()), None)
    out = [_head("Loan %s" % ym), _nav(prefix, ym, "darpan"), _S489_CSS]
    nm = (st["name"] if st else staff)
    out.append(_clinic_hdr("%s — LOAN LEDGER — %s" % (nm.upper(), month_words(ym)), "PRIVATE"))
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    out.append('<div class="noprint"><a class="doorbtn" href="javascript:window.print()">&#128424; Print / save as PDF</a></div>')
    v = _views_of(st, res) if st else {"priv_lines": []}
    priv = (st or {}).get("priv")
    lines = [t for t in v.get("priv_lines", [])
             if t["start"] > 0 or t["taken"] > 0 or t["end"] > 0 or t["recovered"] > 0 or t["interest"] > 0]
    if not st or not lines:
        if st and st.get("ledger_money") is None:
            out.append("<div class='note'>The staff ledger could not be read just now, so this page cannot be shown. "
                       "Reload it in a minute.</div>")
        else:
            out.append("<div class='note'>%s has no long-term loan open in %s.</div>" % (e(nm), month_words(ym)))
        out.append(_LOAN_PRINT_CSS + "</body></html>")
        return "".join(out)
    hist_all = loan_history(st["name"])
    main = next((t for t in lines if t["id"] == hist_all.get("loan_id")), lines[0])
    hist = hist_all if main["id"] == hist_all.get("loan_id") else {}
    rows, opening, note = loan_ledger(main, hist, ym, closed)
    done_ids = {t["id"] for t in ((st.get("ledger_money") or {}).get("cleared") or [])}
    if not note and not hist.get("pre") and main.get("bf") and hist_all.get("loan_id") not in done_ids:
        # (a record that belongs to a loan since paid off is not missing -- this is simply his next loan)
        note = ("The record of this loan's months before the ledger began (loan_pages.json) was not found, "
                "so this table starts where the ledger starts.")
    others = [t for t in lines if t["id"] != main["id"]]
    sib = {}                                        # what the ledger took, month by month, for his OTHER long-term lines
    for t in others:
        for m_, p_, i_ in t.get("hist", []):
            if p_ + i_ > 0.005:
                sib[m_] = round(sib.get(m_, 0.0) + p_ + i_, 2)
    # before the close, where this month's instalment WILL go is the ledger's own plan
    sib_plan = 0.0 if closed else round(sum(p_ + i_ for t in others for m_, p_, i_ in t.get("proj", []) if m_ == ym), 2)
    side = "interest-free part" if main.get("interest_loan") else "other loan"
    kind = "loan with interest" if main.get("interest_loan") else "interest-free loan"
    inst = float(main.get("inst") or 0.0)
    int_part = INTEREST_FLAT if main.get("interest_loan") else 0.0
    past_rows = [r for r in rows if r["status"] != "next"]
    first_ym = past_rows[0]["ym"] if past_rows else ym
    out.append("<div class='lfacts'>"
               "<div class='f'><div class='l'>Opening balance</div><div class='v'>%s</div><div class='s'>%s</div></div>"
               "<div class='f'><div class='l'>Instalment</div><div class='v'>%s a month</div><div class='s'>%s</div></div>"
               "<div class='f'><div class='l'>Balance now · this loan</div><div class='v'>%s</div><div class='s'>after the %s salary</div></div>"
               "</div>"
               % (inr(opening if opening is not None else main["amount"]),
                  e("as at %s" % _date_words(hist.get("opening_date")) if (hist.get("pre") and hist.get("opening_date"))
                    else "when it entered the ledger"),
                  inr(inst),
                  ("%s off the loan + %s interest" % (inr(inst - int_part), inr(int_part))) if int_part else "no interest",
                  inr(main["end"]), month_words(ym)))
    if note:
        out.append("<div class='note'><b>Check:</b> %s</div>" % e(note))
    out.append("<div class='tw'><table class='lled'><tr><th>Salary month</th><th class='n'>Balance at start</th>"
               "<th class='n'>Instalment cut</th><th class='n'>Interest</th><th class='n'>Off the loan</th>"
               "<th class='n'>Balance at end</th><th>Status</th></tr>")
    out.append("<tr class='open'><td colspan='5'>Opening balance — %s (%s)</td><td class='n'>%s</td><td></td></tr>"
               % (e(_date_words(hist.get("opening_date")) if (hist.get("pre") and hist.get("opening_date"))
                    else "the ledger's first entry"),
                  e(kind), inr(opening if opening is not None else main["amount"])))
    t_inst = t_int = t_pr = t_add = 0.0
    n_skip = 0
    # a month counts as skipped only when NOTHING was taken for his long-term loan in it: an instalment
    # the ledger moved onto his other long-term line (a defer on this loan alone) was still taken.
    fy_sk = [m_ for m_ in skips_in_fy(past_rows, ym)
             if sib.get(m_, 0.0) <= 0.005 and not (m_ == ym and sib_plan > 0.005)]
    next_html = ""
    for r in rows:
        dash = "—"
        if r["status"] == "next":
            next_html = ("<tr class='next'><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                         "<td class='n'>%s</td><td class='n'>%s</td><td><span class='tag du'>Next</span></td></tr>"
                         % (e("%s %s" % (_m_short(r["ym"]), r["ym"][:4])), inr(r["start"]), inr(r["inst"]),
                            inr(r["interest"]) if r["interest"] else dash, inr(r["principal"]), inr(r["end"])))
            continue
        t_inst += r["inst"]; t_int += r["interest"]; t_pr += r["principal"]; t_add += r["added"]
        if r["status"] in ("paid", "part"):
            tag = "<span class='tag pd'>%s</span>" % ("Paid" if r["status"] == "paid" else "Part paid")
            cls = ""
        elif r["status"] in ("skip", "defer", "hold", "none") and sib.get(r["ym"], 0.0) > 0.005:
            tag = ("<span class='tag du'>Not on this loan</span> <small>· Rs %s taken for the %s</small>"
                   % (inr(sib[r["ym"]]), side))
            cls = ""
        elif r["status"] in ("skip", "defer", "hold") and r["ym"] == ym and sib_plan > 0.005:
            tag = ("<span class='tag du'>Not on this loan</span> <small>· Rs %s will be taken for the %s "
                   "at the ledger close</small>" % (inr(sib_plan), side))
            cls = ""
        elif r["status"] in ("skip", "defer", "hold"):
            n_skip += 1
            word = {"skip": "Skipped", "defer": "Skipped", "hold": "Held"}[r["status"]]
            k = (fy_sk.index(r["ym"]) + 1) if r["ym"] in fy_sk else 0
            tag = "<span class='tag sk'>%s</span>%s" % (word, (" <small>%s</small>" % _nth_of_two(k)) if k else "")
            if r["ym"] == ym and priv and priv.get("paid"):
                tag += " <small>· Rs %s paid to him</small>" % inr(priv["paid"])
            cls = " class='skip'"
        elif r["status"] == "pending":
            tag = "<span class='tag du'>Waits for the ledger close</span>"
            cls = ""
        else:
            tag = "<span class='tag no'>Nothing collected</span>"
            if r["ym"] == ym and priv and priv.get("paid"):
                tag += " <small>· Rs %s paid to him</small>" % inr(priv["paid"])
            cls = " class='skip'"
        intr = inr(r["interest"]) if r["interest"] else dash
        if r["added"] > 0.005:
            intr = "%s <small>added to loan</small>" % inr(r["added"])
        elif r["added"] < -0.005:
            intr = "%s <small>taken off the loan</small>" % inr(-r["added"])
        out.append("<tr%s><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                   "<td class='n'>%s</td><td class='n'><b>%s</b></td><td style='white-space:nowrap'>%s</td></tr>"
                   % (cls, e("%s %s" % (_m_short(r["ym"]), r["ym"][:4])), inr(r["start"]),
                      inr(r["inst"]) if r["inst"] else dash, intr,
                      inr(r["principal"]) if r["principal"] else dash, inr(r["end"]), tag))
    out.append("<tr class='tot'><td>%s to %s</td><td></td><td class='n'>%s</td><td class='n'>%s</td>"
               "<td class='n'>%s</td><td class='n'>%s</td><td></td></tr>"
               % (e(_m_short(first_ym)), e(_m_short(ym)), inr(t_inst),
                  inr(t_int) + ((" <small>+ %s added</small>" % inr(t_add)) if t_add > 0.005 else ""),
                  inr(t_pr), inr(past_rows[-1]["end"] if past_rows else main["end"])))
    out.append(next_html)
    out.append("</table></div>")
    foot = []
    if priv:
        if priv.get("paid") is None:
            foot.append("%s: Rs %s is kept aside from the salary for this instalment; the ledger close has not run yet."
                        % (month_words(ym), inr(priv["kept"])))
        else:
            foot.append("%s: Rs %s kept aside from salary · Rs %s instalment taken · %s."
                        % (month_words(ym), inr(priv["kept"]), inr(priv["cut_shown"]),
                           ("Rs %s paid to him" % inr(priv["paid"])) if priv["paid"] > 0.005 else "nothing left to pay him"))
            if priv.get("extra"):
                foot.append("A further Rs %s was collected for this loan through the salary sheet this month."
                            % inr(priv["extra"]))
    for t in others:
        foot.append("%s of Rs %s: balance Rs %s — %s."
                    % ("Interest-free part" if not t.get("interest_loan") else "Second loan", inr(t["amount"]), inr(t["end"]),
                       "starts when this loan is finished" if (t["end"] >= t["amount"] - 0.005 and main["end"] > 0.005)
                       else "being paid back"))
    foot.append("Skipped this year (April to March): %s." % _nth_of_two(len(fy_sk)))
    out.append("<div class='sub' style='margin-top:8px'>%s</div>" % "<br>".join(e(x) for x in foot))
    if doors:
        out.append('<div class="note noprint"><b>Full picture doors:</b> '
                   '<a class="doorbtn" href="%s/statement?staff=%s">&#128220; Complete ledger statement</a> '
                   '<a class="doorbtn" href="%s/advances">&#128181; Advances page</a> '
                   '<a class="doorbtn" href="%s/perks">&#127873; Perks</a></div>'
                   % (e(ledger_prefix), e(st["name"]), e(ledger_prefix), e(ledger_prefix)))
    out.append("<div class='signline'>Dekha / Seen — hastakshar &nbsp; <span></span> &nbsp;&nbsp; Date &nbsp; "
               "<span style='min-width:120px'></span></div>")
    out.append(_LOAN_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


_LOAN_PRINT_CSS = """<style>
 @page{size:A4 portrait;margin:12mm}
 @media print{
  body{margin:0;font-size:12px;line-height:1.35;background:#fff}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:13px;margin:0 0 4px}
  table.lled{width:100%} table.lled th,table.lled td{font-size:12px;padding:6px 8px}
  .lfacts .v{font-size:17px} .lfacts .s,.lfacts .l{font-size:10.5px}
  .sub{font-size:10.5px} .note{font-size:11px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


def _nth_of_two(k):
    """'1 of 2', '2 of 2' -- and past two, just the count (the page does not pretend a third is 'of 2')."""
    return ("%d of 2" % k) if k <= 2 else ("%d this year" % k)


def _date_words(iso):
    """'2026-03-31' -> '31 March 2026'."""
    try:
        return "%d %s %s" % (int(iso[8:10]), MONTHS[int(iso[5:7])], iso[:4])
    except (ValueError, TypeError, IndexError):
        return str(iso or "")


def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None,
                staff=None, prefix="/register", approve_html=""):
    """Sheet 2 — money review. S489 (D681/D682): the main page carries EVERYONE's advances in two
    tables that never mix (this month's advances; instalment loans, one line per loan) and one closing
    line per person. staff=<a private-loan name> renders that person's private LOAN LEDGER page;
    staff=<anyone else> the same tables for that one person. No bottom totals (owner ruling)."""
    e = html.escape
    ym = res["ym"]
    if staff is not None and staff.strip().lower() in private_loan_names(res.get("settings")):
        return loan_page_html(res, staff, doors=doors, ledger_prefix=ledger_prefix, back=back, prefix=prefix)
    sep = set()                                     # S489: nobody is kept off the main money page any more

    def _has(st):
        v = _views_of(st, res)
        return bool(v["month_adv"] or v["loans"] or st.get("manual_adv") or (st.get("priv") or {}).get("extra"))
    pick = [st for st in res["staff"]
            if (staff is None and _has(st))
            or (staff is not None and st["name"].lower() == staff.lower())]
    title = ("SHEET 2 · %s — MONEY PAGE — %s" % (staff.upper(), month_words(ym))
             if staff else "SHEET 2 · ADVANCES, LOANS & HOLDS — %s" % month_words(ym))

    out = [_head("Money %s" % ym), _nav(prefix, ym, "s2"), _S489_CSS,
           _clinic_hdr(title)]
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    if approve_html and staff is None:
        out.append('<div class="noprint">%s</div>' % approve_html)
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))

    out.append(advances_sections_html(res, pick, doors=doors, ledger_prefix=ledger_prefix))

    # S200/R7: the owner's own advance record for months settled OUTSIDE the
    # ledger (July 2026 and earlier). Display-only — already deducted when paid;
    # never touches NET. File: manual_advances_<ym>.json beside this engine.
    _madv = os.path.join(BASE, "manual_advances_%s.json" % ym)
    if staff is None and os.path.exists(_madv):
        try:
            with open(_madv, encoding="utf-8") as _f:
                _rows = json.load(_f)
        except Exception:
            _rows = []
        if _rows:
            out.append("<h2>Advances settled OUTSIDE the ledger (owner's record)</h2>"
                       "<div class='note'>These DEDUCT in this month's Advance column "
                       "(already handed over when the month was paid) — so the NET on "
                       "Sheets 3/4 is what remains to hand over.</div>"
                       "<div class='tw'><table><tr><th>Staff</th><th>Amount</th>"
                       "<th>Note</th></tr>")
            for _r in _rows:
                out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td></tr>"
                           % (e(str(_r.get("staff", ""))), money(_r.get("amount") or 0),
                              e(str(_r.get("note", "")))))
            out.append("</table></div>")

    if staff:
        st = pick[0] if pick else None
        if st:
            out.append('<div class="note noprint"><b>Full picture doors:</b> '
                       '<a class="doorbtn" href="%s/statement?staff=%s">&#128220; Complete ledger statement</a> '
                       '<a class="doorbtn" href="%s/advances">&#128181; Advances page</a> '
                       '<a class="doorbtn" href="%s/perks">&#127873; Perks</a>'
                       '<br><small>The tables above show OPEN money only. PENDING advances '
                       '(e.g. one awaiting a signed application) appear on the Advances page, '
                       'and every perk/benefit ever paid is on the Perks page.</small></div>'
                       % (e(ledger_prefix), e(st["name"]), e(ledger_prefix), e(ledger_prefix)))
            out.append("<section class='s2sec'><h2>Duty credits this month</h2><div class='tw'><table>"
                       "<tr><th>Outstation nights</th><th>Outstation Rs</th>"
                       "<th>Extra duty Rs</th><th>Night duty Rs (ledger)</th></tr>"
                       "<tr><td class='n'>%d</td><td class='n'>%s</td>"
                       "<td class='n'>%s</td><td class='n'>%s</td></tr></table></div>"
                       % (int(st.get("outst_days", 0)),
                          money(st["outst_rs"]), money(st["extra_rs"]), money(st["night_rs"])))
            out.append("</section>")

    # S238: say, in words, what happened to LAST month's hold (the owner, 10-Sep-2026).
    pm = prev_ym(ym)
    s_now = load_settings()
    _hs = hold_state()
    _pm_recorded = any(k[1] == pm for k in _hs)
    out.append("<section class='s2sec'><h2>Improvement holds</h2>")
    if not _pm_recorded:
        out.append("<div class='note'>No hold was carried from %s: holds are written only "
                   "when a month is LOCKED, and %s has no locked hold on record.</div>"
                   % (month_words(pm), month_words(pm)))
    out.append("<div class='tw'><table>"
               "<tr><th>Staff</th><th>%s hold</th><th>What happened to it</th>"
               "<th>Late charge this month</th><th>Deducted now</th>"
               "<th>Hold marked (paid now, not deducted)</th></tr>" % month_words(pm))
    _any_h = False
    for st in pick if staff else [x for x in res["staff"] if x["name"] not in sep]:
        ph = _hs.get((st["name"], pm))
        if not (st["held"] or st["release"] or st.get("prior_collect")
                or st["release_note"] or st["late_charge"] or ph):
            continue
        _any_h = True
        if ph and ph.get("status") == "HELD":
            if st["release"]:
                what = "CANCELLED — %s" % (st["release_note"] or "improved")
            elif st.get("prior_collect"):
                what = "DEDUCTED this month — %s" % (st["release_note"] or "no improvement")
            else:
                what = "still held"
            last = money(ph["held"])
        elif ph:
            what = "already closed (%s)" % ph.get("status", "").lower()
            last = money(ph.get("held", 0))
        else:
            what, last = "no hold", "-"
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]), last, e(what), money(st["late_charge"]),
                      money(st["collect"]), money(st["held"])))
    if not _any_h:
        out.append("<tr><td colspan='6'>no late charge and no hold this month</td></tr>")
    out.append("</table></div><div class='sub'>A hold is only MARKED — it is paid with this "
               "month's salary, not withheld. If next month's chargeable late minutes fall by "
               "%d%% or more, it is cancelled; if not, it is deducted from next month's salary."
               "</div></section>" % s_now["improve_pct"])

    if staff is None:
        out.append("<section class='s2sec'><h2>All fines, leaves &amp; credits (every staff — for review)</h2>"
                   "<div class='tw'><table class='wide'><tr><th rowspan='2'>Staff</th>"
                   "<th colspan='4'>DAYS NOT PUNCHED on the machine</th>"
                   "<th rowspan='2'>Days off allowed</th>"
                   "<th rowspan='2'>Late minutes</th><th rowspan='2'>Late charge</th><th rowspan='2'>Collect now</th><th rowspan='2'>Hold</th>"
                   "<th colspan='2'>%s hold</th>"
                   "<th rowspan='2'>Leave amt<br><small>(+ded / −credit)</small></th>"
                   "<th rowspan='2'>Uninformed</th><th rowspan='2'>Excess-absent</th>"
                   "<th rowspan='2'>Dress</th><th rowspan='2'>I-card</th><th rowspan='2'>Night duty (+)</th>"
                   "<th rowspan='2'>Incentive (+)</th>"
                   "<th colspan='2'>Overtime (+)</th><th rowspan='2'>Cover duty (+)<br><small>&#8377; (days)</small></th></tr>"
                   "<tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
                   "<th>absent, no leave</th><th>deducted now</th><th>written off</th>"
                   "<th>minutes</th><th>&#8377;</th></tr>"
                   % month_words(prev_ym(ym))[:3])
        _pt = dates_only_names(res.get("settings") or {})
        for st in res["staff"]:
            if st["name"].strip().lower() in _pt:
                continue      # S239: part-time staff are not in the leave/fine table (see below)
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                       "<td class='n'>%d</td><td class='n'>%d</td><td class='n'>%s</td>"
                       % (e(st["name"]), st.get("absent", 0), st.get("leave_in_absent", 0),
                          min(st.get("outst_days", 0), max(0, st.get("absent", 0) - st.get("leave_in_absent", 0))),
                          st.get("genuine", 0), money(st.get("offs", 0)))
                       + "<td class='n'>%d</td>" % int(st.get("late_min", 0) or 0)
                       + "".join("<td class='n'>%s</td>" % money(v) for v in (
                           st["late_charge"], st["collect"], st["held"],
                           st.get("prior_collect", 0), st.get("release", 0), st["leave_amt"],
                           st["fine_uninf"], st["fine_exc"], st["dress_rs"],
                           st["icard_rs"], st["night_rs"], st["incentive"]))
                       + "<td class='n'>%d</td><td class='n'>%s</td>"
                       % (st.get("ot_min", 0), money(st.get("ot_rs", 0)))
                       + ("<td class='n'>%s (%d)</td>"
                          % (money(st.get("extra_rs", 0)), st.get("extra_days", 0))
                          if (st.get("extra_days") or st.get("extra_rs"))
                          else "<td class='n'>-</td>")
                       + "</tr>")
        out.append("</table></div>"
                   "<div class='sub'>Days not punched = sanctioned leave + outstation + absent "
                   "without leave — one set of days, not two to be added. The leave amount is worked on "
                   "leave used (discretionary + festival) + absent without leave, less the days off "
                   "allowed (a Sunday counts at its lower weight). Overtime: minutes past shift end "
                   "on a real out-punch, at 2 x the person's own minute-rate (%s). Late minutes: the month's "
                   "chargeable late minutes the late charge is worked on. Cover duty: the "
                   "cover-eligible person's extra-duty credit, with the cover days in brackets. "
                   "Outstation days are duty, not leave. Last month's hold: 'deducted now' "
                   "comes off this salary (improvement under the bar); 'written off' is never "
                   "recovered (improvement at or over the bar).</div></section>"
                   % ("in the net" if res["settings"].get("ot_pay") else "shown, not paid"))
        out.append(_part_time_html(res))

    out.append('<div class="sub">Advance/loan figures are the ledger\'s own, for the month '
               'shown; corrections happen in the ledger, then reload this sheet.</div>')
    out.append(_S2_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


def has_slip(st, res):
    """D681: a salary slip is printed only for a person with a running instalment loan on the
    common sheet (a loan line that was cut this month, or still has a balance). Money that comes
    back in ONE salary -- an advance booked against next month -- is not an instalment loan."""
    v = _views_of(st, res)
    return any((L["cut"] > 0.005 or L["balance_after"] > 0.005) and L["n_all"] != 1 for L in v["loans"])


def slip_html(st, res, cap):
    """One printed page for one person: the salary slip, in the wording staff read (Roman Hindi),
    with the advance shown as it is made up -- this month's advances, each loan's instalment and
    what is still owed. Reads only what the month already computed; decides nothing.
    For a private-loan person these are the COMMON-sheet figures (D682): the long-term loan is
    not on this page."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    nm = str(st["name"])
    v = _views_of(st, res)
    di = round(float(st.get("dress_rs", 0)) + float(st.get("icard_rs", 0)), 2)
    fines = round(float(st.get("fine_uninf", 0)) + float(st.get("fine_exc", 0)), 2)
    leaves = st.get("leaves_total", 0)
    wtd = st.get("leaves_weighted", leaves)
    offs = st.get("offs", 0)
    charged = round(float(wtd) - float(offs), 2)

    def row(label, work, amount, cls=""):
        return ("<tr%s><td>%s%s</td><td class='n'>%s</td></tr>"
                % ((" class='%s'" % cls) if cls else "", e(label),
                   ("<br><span class='wk'>%s</span>" % e(work)) if work else "",
                   inr(amount)))

    o = ['<div class="s4pg slip" style="page-break-before:always">',
         _clinic_hdr("SALARY SLIP — %s — %s" % (nm.upper(), month_words(ym)), cap),
         "<div class='tw'><table class='ownt'>",
         "<tr><th>Vivran</th><th>Rs.</th></tr>",
         row("Salary", "", st["base"]),
         "<tr class='sec'><td colspan='2'>Kaate gaye</td></tr>"]
    if leaves or st.get("leave_amt"):
        # a short-shift day (a Sunday) counts as less than a full day: say what the days were counted as
        gine = ("%s din gine gaye · " % money(wtd)) if abs(float(wtd) - float(leaves)) > 0.005 else ""
        if charged >= 0:
            o.append(row("Chhutti — %s din" % money(leaves),
                         "%s%s din free · %s din ka paisa kata" % (gine, money(offs), money(charged)),
                         st["leave_amt"]))
        else:
            o.append(row("Chhutti — %s din" % money(leaves),
                         "%s%s din free · %s din bache, paisa joda" % (gine, money(offs), money(-charged)),
                         st["leave_amt"]))
    if st.get("late_min") or st.get("collect"):
        o.append(row("Late — %s minute, %s mark" % (money(st["late_min"]), money(st["marks"])),
                     "is mahine ka", st["collect"]))
    if st.get("prior_collect"):
        o.append(row("Pichhle mahine ka late", "jo roka gaya tha", st["prior_collect"]))
    if di:
        o.append(row("Dress aur I-card — %s + %s din"
                     % (money(st.get("dress_days", 0)), money(st.get("icard_days", 0))), "", di))
    if fines:
        o.append(row("Anya jurmana", "", fines))
    adv = round(sum(a["cut"] for a in v["month_adv"]), 2)
    if v["month_adv"]:
        o.append(row("Is mahine ka advance",
                     " + ".join("%s %s" % (_d_short(a["date"]), inr(a["cut"])) for a in v["month_adv"]),
                     adv, "new"))
    for L in v["loans"]:
        if L["cut"] <= 0.005:
            continue
        o.append(row("Loan ki kist",
                     "kist %d / %d · loan Rs %s (%s)" % (L["n_paid"] + (0 if closed else 1), L["n_all"],
                                                         inr(L["amount"]), L["given"]),
                     L["cut"], "new"))
    priv = st.get("priv") or {}
    if priv.get("extra"):
        o.append(row("Purana loan — ek aur kist", "", priv["extra"], "new"))
    if st.get("manual_adv"):
        o.append(row("Pehle diya advance", "", st["manual_adv"], "new"))
    o.append(row("Advance kata — kul", "upar ki advance wali lines ka jod · " + ("is mahine" if closed else "ledger band hone par katega"),
                 st.get("adv_ded", 0) if closed else adv + sum(L["cut"] for L in v["loans"]), "newtot"))
    if st.get("net_round_off"):                         # with the cuts, in every case: what is not paid in notes
        o.append(row("Round off — poore 10 rupaye", "", st["net_round_off"]))
    if st.get("duty_credits") or st.get("ot_paid"):
        o.append("<tr class='sec'><td colspan='2'>Joda gaya</td></tr>")
        if st.get("duty_credits"):
            o.append(row("Duty credit", "", st["duty_credits"]))
        if st.get("ot_paid"):
            o.append(row("Overtime", "", st["ot_paid"]))
    o.append("<tr class='net'><td><b>%s</b></td><td class='n'><b>%s</b></td></tr>"
             % ("Is mahine mila" if closed else "Is mahine mila — advance katne se PEHLE", inr(st["net"])))
    o.append("</table></div>")
    if not closed:
        o.append('<div class="ownwarn">Yeh slip abhi FINAL NAHI hai: is mahine ka ledger band nahi hua, '
                 'isliye advance aur kist abhi salary se nahi kate. Ledger band hone ke baad dobara nikalein.</div>')
    for L in v["loans"]:
        ahead = [(m, a) for m, a, k in L["strip"] if k == "due"]
        if L["balance_after"] <= 0.005 and not ahead:
            o.append('<div class="loanfoot"><b>Loan Rs %s (%s): poora ho gaya.</b></div>'
                     % (inr(L["amount"]), e(L["given"])))
        elif ahead:
            o.append('<div class="loanfoot"><b>Loan baaki: Rs %s</b> <span class="wk">(loan Rs %s, %s)</span><br>%s · %s mein khatam</div>'
                     % (inr(L["balance_after"]), inr(L["amount"]), e(L["given"]),
                        " · ".join("%s %s" % (MONTHS[int(m[5:7])], inr(a)) for m, a in ahead[:6])
                        + (" …" if len(ahead) > 6 else ""),
                        MONTHS[int(ahead[-1][0][5:7])] + (" " + ahead[-1][0][:4] if ahead[-1][0][:4] != ym[:4] else "")))
        else:
            o.append('<div class="loanfoot"><b>Loan baaki: Rs %s</b> <span class="wk">(loan Rs %s, %s)</span></div>'
                     % (inr(L["balance_after"]), inr(L["amount"]), e(L["given"])))
    if float(st["net"]) < 0:
        o.append('<div class="ownwarn">Is mahine advance, salary se Rs. %s zyada kata hai. '
                 'Matlab is mahine kuch nahi milega, aur Rs. %s agle mahine se adjust hoga.</div>'
                 % (inr(abs(float(st["net"]))), inr(abs(float(st["net"])))))
    o.append('<div class="sub">Mila / Received — hastakshar</div>'
             '<div style="height:44px;border-bottom:1px solid #444;max-width:320px"></div>')
    o.append("</div>")
    return "".join(o)


def sheets34_html(res, back=None, approved=None, prefix="/register", status_html=""):
    """Sheet 3 (detail) + Sheet 4 (signature). FINAL heading once the pack is
    approved; WORKING PREVIEW before that (S199-C)."""
    e = html.escape
    ym = res["ym"]
    s = res["settings"]
    final = bool(approved)
    cap = "FINAL — computed on the approved pack" if final else "WORKING PREVIEW — pack not yet approved"
    out = [_head("Salary %s" % ym), _nav(prefix, ym, "prev"),
           _clinic_hdr("SHEET 3 · MONTHLY SALARY — DETAILED WORKING — %s" % month_words(ym), cap)]
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    if status_html:
        out.append('<div class="noprint">%s</div>' % status_html)
    out.append('<div class="noprint"><a class="doorbtn" href="javascript:window.print()">'
               '&#128424; Print / save as PDF</a></div>')
    out.append(_banner(res))
    _own = own_sheet_names(res.get("settings") or {})   # S240: off the common sheet
    _own_staff = []
    if _own:
        res = dict(res)
        _own_staff = [_s for _s in res["staff"]
                      if str(_s["name"]).strip().lower() in _own]
        res["staff"] = [_s for _s in res["staff"]
                        if str(_s["name"]).strip().lower() not in _own]
    cols = ["Name", "Salary", "Advance ded.", "Leaves", "Leave amt", "Late min",
            "Marks", "Late charge", "Collect now", "Hold",
            "Prev hold deducted", "Prev hold written off",
            "Dress", "I-card", "D+I fine", "Fines", "Duty credits", "OT paid",
            "Incentive (to pot)", "NET PAYABLE"]
    out.append("<div class='tw'><table class='s3t'><tr>" +
               "".join("<th>%s</th>" % c for c in cols) + "</tr>")
    tot = dict.fromkeys(range(len(cols)), 0.0)
    for st in res["staff"]:
        di = st["dress_rs"] + st["icard_rs"]
        fines = st["fine_uninf"] + st["fine_exc"]
        if str(st["name"]).strip().lower() in dates_only_names(res.get("settings") or {}):
            st = dict(st); st["leaves_total"] = 0   # S240: flat pay shows no working
        vals = [st["name"], st["base"], st["adv_ded"], st["leaves_total"],
                st["leave_amt"], st["late_min"], st["marks"], st["late_charge"],
                st["collect"], st["held"], st.get("prior_collect", 0), st["release"],
                st["dress_days"], st["icard_days"], di, fines, st["duty_credits"],
                st.get("ot_paid", 0), st["incentive"], st["net"]]
        out.append("<tr>" + "".join(
            ("<td><b>%s</b></td>" % e(str(v))) if i == 0 else
            ("<td class='n'>%s</td>" % money(v)) for i, v in enumerate(vals))
            + "</tr>")
        for i, v in enumerate(vals):
            if i:
                tot[i] += float(v)
    out.append('<tr class="tot"><td>TOTAL</td>' + "".join(
        "<td class='n'>%s</td>" % money(tot[i]) for i in range(1, len(cols)))
        + "</tr></table></div>")
    out.append('<div class="sub">Leave amt: (leaves − allowed) × salary÷%s, '
               'negative = credit. Late charge: after %d free min, progressive '
               'at own salary minute-rate (charges under Rs.%s ignored). Hold: '
               '%d%% of the charge is marked, not deducted; cancelled on %d%% improvement next month, '
               'otherwise deducted next month. Duty '
               'credits: night + extra duty + outstation. Incentive accrues to '
               'the annual pot (paid at Diwali) — not in this month&#39;s net. D+I fine: Rs.%s/day '
               'each without. NET PAYABLE is cut to the last Rs.10 — the paise and the last digit are not paid out.</div>'
               % ("%g" % s["day_divisor"], s["free_late_min"], money(s.get("min_charge_rs", 0)),
                  100 - s["collect_now_pct"], s["improve_pct"], money(s["dress_rs"])))
    out.append('<div class="s4pg" style="page-break-before:always">')
    out.append(_clinic_hdr("SHEET 4 · SALARY PAYMENT & SIGNATURE — %s" % month_words(ym), cap))
    out.append(_banner(res))
    out.append("<div class='tw'><table><tr><th>S.No</th><th>Name</th>"
               "<th>Amount (Rs.)</th><th style='min-width:200px'>Signature / "
               "हस्ताक्षर</th><th style='min-width:100px'>Date</th></tr>")
    for i, st in enumerate(res["staff"], 1):
        out.append("<tr style='height:40px'><td>%d</td><td><b>%s</b></td>"
                   "<td class='n'>%s</td><td></td><td></td></tr>"
                   % (i, e(st["name"]), money(st["net"])))
    out.append("</table></div>")
    out.append('<div class="sub">Received the above amount in full. / '
               'उपरोक्त राशि पूरी प्राप्त की।</div></div>')
    for _s in res["staff"]:                             # S489 (D681): a slip only where an instalment loan runs
        if has_slip(_s, res):
            out.append(slip_html(_s, res, cap))
    out.append(_SLIP_CSS)
    out.append(_OWN_SHEET_CSS)
    out.append(_S34_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


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
    # D345 ramp
    import tempfile as _tf
    _mtmp = _tf.mkdtemp()
    with open(os.path.join(_mtmp, "manual_advances_2026-07.json"), "w") as _f:
        json.dump([{"staff": "Alisha", "amount": 5000},
                   {"staff": "alisha", "amount": 100},
                   {"staff": "Bad", "amount": 0}], _f)
    _m = manual_advances("2026-07", base=_mtmp)
    assert _m == {"alisha": 5100.0}, _m
    assert manual_advances("2026-08", base=_mtmp) == {}, "no file -> empty"
    # settings-save round trip — snapshot the REAL file and put it back exactly,
    # so a selftest can never change live behaviour (the 0.5 save below would
    # otherwise stick and silently force the Sunday weight).
    _snap = None
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, encoding="utf-8") as _f:
            _snap = _f.read()
    try:
        ok, _ = save_settings({"sunday_weight_override": "0.5"})
        assert ok, "a forced 0..1 weight must save"
        ok, _ = save_settings({"sunday_weight_override": "-1"})
        assert ok, "the -1 derive sentinel must save"
        ok, _ = save_settings({"sunday_weight_override": "2"})
        assert not ok, "a weight above 1 must refuse"
        ok, _ = save_settings({"free_late_min": "-5"})
        assert not ok, "other negatives must still refuse"
    finally:
        if _snap is None:
            if os.path.exists(SETTINGS_PATH):
                os.remove(SETTINGS_PATH)
        else:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as _f:
                _f.write(_snap)
    assert ramp_fine(0, 10) == 0 and ramp_fine(1, 10) == 10
    assert ramp_fine(3, 10) == 60 and ramp_fine(6, 10) == 210 and ramp_fine(7, 10) == 280
    # D341 weight: derived / override / fail-safe
    import datetime as _dt
    _mk = lambda a, b, c, d: {"wd_start": _dt.time(*a), "wd_end": _dt.time(*b),
                              "sun_start": _dt.time(*c) if c else None,
                              "sun_end": _dt.time(*d) if d else None}
    assert sunday_weight(_mk((9,0),(21,0),(9,0),(15,0)), s) == 0.5      # half shift
    assert sunday_weight(_mk((9,0),(21,0),None,None), s) == 1.0         # no data -> whole
    assert sunday_weight(_mk((9,0),(21,0),(9,0),(15,0)),
                         dict(s, sunday_weight_override=0.25)) == 0.25  # forced
    # July acceptance numbers (the S200 workbook, to the paisa):
    # Shivani: 9 absents, 4 Sundays at 0.5 -> weighted 7; (7-2) x 8600/30.5 = 1409.84
    assert round((9 - 4*0.5 - 2) * 8600 / 30.5, 2) == 1409.84
    assert ramp_fine(9 - 2, 10) == 280                                  # her ramp
    assert _valid_ym("2026-08") and not _valid_ym("2026-13")
    assert prev_ym("2026-01") == "2025-12" and prev_ym("2026-08") == "2026-07"
    # ---- S489 (D681/D682): the views, the private split, the loan ledger -- made-up people and rows ----
    assert inr(234000) == "2,34,000" and inr(1500) == "1,500" and inr(0) == "0" and inr(-710) == "-710"
    assert inr(12345678.5) == "1,23,45,678.50" and inr(1337.7) == "1,337.70" and inr(999) == "999" and inr(100000) == "1,00,000"

    def _iss(i, staff, d, amt, inst=None, am="", interest=False, narr="", sched=None):
        return {"id": i, "category": "ADVANCE_ISSUE", "status": "APPROVED", "staff": staff, "date_from": d,
                "amount": amt, "instalment": inst, "against_month": am, "interest": interest,
                "narration": narr, "schedule": sched or [], "contra_of": "", "closed_month": "", "ts_entry": d}

    def _sys(i, staff, cat, m, amt, co):
        return {"id": i, "category": cat, "status": "APPROVED", "staff": staff, "date_from": m,
                "amount": amt, "contra_of": co, "closed_month": m, "narration": ""}
    _R = [
        # Asha: ONE loan of 6,000 handed over in three parts (1,500 a month) + two same-month advances
        _iss("a1", "Asha", "2031-08-04", 1500, 1500, "2031-08"),
        _iss("a2", "Asha", "2031-08-06", 2250, 1500, "2031-09"),
        _iss("a3", "Asha", "2031-08-09", 2250, 1500, "2031-10"),
        _sys("a1r", "Asha", "ADVANCE_INSTALMENT", "2031-08", -1500, "a1"),
        _iss("a4", "Asha", "2031-09-05", 700, 700, "2031-09"),
        _iss("a5", "Asha", "2031-09-21", 2600, 2600, "2031-09"),
        _sys("a2r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -1500, "a2"),
        _sys("a4r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -700, "a4"),
        _sys("a5r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -2600, "a5"),
        # Dev: a private long-term loan (with interest), its interest-free part, one ordinary advance,
        # and a schedule advance that is an ordinary instalment loan on the common sheet
        _iss("d1", "Dev", "2031-08-03", 97000, 6000, "", True, "opening balance migrated from workbook (interest-bearing tranche)"),
        _iss("d2", "Dev", "2031-08-03", 64000, 6000, "", False, "opening balance migrated from workbook (interest-free tranche)"),
        _sys("d1c", "Dev", "LOAN_CAPITALISE", "2031-04", -1000, "d1"),
        _sys("d1r8", "Dev", "ADVANCE_INSTALMENT", "2031-08", -5000, "d1"), _sys("d1i8", "Dev", "LOAN_INTEREST", "2031-08", -1000, "d1"),
        _sys("d1r9", "Dev", "ADVANCE_INSTALMENT", "2031-09", -5000, "d1"), _sys("d1i9", "Dev", "LOAN_INTEREST", "2031-09", -1000, "d1"),
        _iss("d3", "Dev", "2031-09-11", 2400, 2400, "2031-09"),
        _sys("d3r", "Dev", "ADVANCE_INSTALMENT", "2031-09", -2400, "d3"),
        _iss("d4", "Dev", "2031-08-12", 15000, 15000, "", False, "",
             [{"month": "2031-08", "amount": 6000}, {"month": "2031-09", "amount": 3000},
              {"month": "2031-10", "amount": 3000}, {"month": "2031-11", "amount": 3000}]),
        _sys("d4r8", "Dev", "ADVANCE_INSTALMENT", "2031-08", -6000, "d4"),
        _sys("d4r9", "Dev", "ADVANCE_INSTALMENT", "2031-09", -3000, "d4"),
    ]
    _G = [{"staff": "Asha", "ids": ["a1", "a2", "a3"], "given": "4-9 Aug 2031"}]
    _lm = ledger_money(_R, "Asha", "2031-09")
    _v = advance_views(_lm, "Asha", "2031-09", True, _G)
    assert [a["id"] for a in _v["month_adv"]] == ["a4", "a5"], _v["month_adv"]
    assert len(_v["loans"]) == 1, "three parts are ONE loan"
    _L = _v["loans"][0]
    assert (_L["amount"], _L["paid"], _L["n_paid"], _L["n_all"], _L["cut"], _L["balance"], _L["ends"]) \
        == (6000, 3000, 2, 4, 1500, 3000, "2031-11"), _L
    assert _L["strip"] == [("2031-08", 1500, "paid"), ("2031-09", 1500, "paid"),
                           ("2031-10", 1500, "due"), ("2031-11", 1500, "due")], _L["strip"]
    assert _L["inst"] == "1,500 a month" and _L["next"] == 1500
    assert round(sum(a["cut"] for a in _v["month_adv"]) + sum(L["cut"] for L in _v["loans"]), 2) == _lm["deducted"] == 4800
    _v0 = advance_views(_lm, "Asha", "2031-09", True, [])        # no group record: each advance its own loan
    assert len(_v0["loans"]) == 2 and sum(L["cut"] for L in _v0["loans"]) == 1500
    _va = advance_views(ledger_money(_R, "Asha", "2031-08"), "Asha", "2031-08", True, _G)
    assert not _va["month_adv"] and (_va["loans"][0]["paid"], _va["loans"][0]["n_paid"], _va["loans"][0]["n_all"]) == (1500, 1, 4)
    # the private split
    _lmd = ledger_money(_R, "Dev", "2031-09")
    _vd = advance_views(_lmd, "Dev", "2031-09", True, [], private=True)
    assert [t["id"] for t in _vd["priv_lines"]] == ["d1", "d2"] and [a["id"] for a in _vd["month_adv"]] == ["d3"]
    assert len(_vd["loans"]) == 1 and _vd["loans"][0]["ids"] == ["d4"] and _vd["loans"][0]["inst"] == "6,000, then 3,000 a month"
    _p = private_split(_vd["priv_lines"], "2031-09", True)
    assert (_p["kept"], _p["cut"], _p["cut_shown"], _p["paid"], _p["reserve"], _p["status"]) == (6000, 6000, 6000, 0, 0, "paid"), _p
    _common = round(sum(a["cut"] for a in _vd["month_adv"]) + sum(L["cut"] for L in _vd["loans"]), 2)
    assert _common + _p["cut_shown"] == _lmd["deducted"] == 11400, "common advances + private instalment = the ledger's figure"
    assert private_split([], "2031-09", True) is None
    _vn = advance_views(_lmd, "Dev", "2031-09", True, [], private=False)      # not private: nothing is held back
    assert not _vn["priv_lines"] and len(_vn["loans"]) == 3
    # a month it is skipped: the whole instalment is paid to him on the private page
    _R2 = _R + [_sys("d1s", "Dev", "LOAN_SKIP", "2031-10", 0, "d1"), _sys("d4r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -3000, "d4")]
    _lmo = ledger_money(_R2, "Dev", "2031-10")
    _po = private_split(advance_views(_lmo, "Dev", "2031-10", True, [], private=True)["priv_lines"], "2031-10", True)
    assert (_po["kept"], _po["cut"], _po["paid"], _po["reserve"], _po["status"]) == (6000, 0, 6000, 6000, "skip"), _po
    # before the ledger close: kept aside, not yet decided
    _lmp = ledger_money(_R, "Dev", "2031-10")
    _pp = private_split(advance_views(_lmp, "Dev", "2031-10", False, [], private=True)["priv_lines"], "2031-10", False)
    assert (_pp["kept"], _pp["paid"], _pp["reserve"], _pp["status"]) == (6000, None, 6000, "pending"), _pp
    # the loan ledger: months before the ledger from the history record, the rest the ledger's own
    _H = {"loan_id": "d1", "opening_date": "2031-03-31", "opening": 111000,
          "pre": [{"ym": "2031-04", "kind": "skip", "added": 0},
                  {"ym": "2031-05", "kind": "paid", "instalment": 6000, "interest": 1000},
                  {"ym": "2031-06", "kind": "paid", "instalment": 6000, "interest": 1000},
                  {"ym": "2031-07", "kind": "paid", "instalment": 6000, "interest": 1000}]}
    _d1 = _vd["priv_lines"][0]
    _rows, _op, _note = loan_ledger(_d1, _H, "2031-09", True)
    assert _op == 111000 and _note == "", _note
    assert [r["status"] for r in _rows] == ["skip", "paid", "paid", "paid", "paid", "paid", "next"], [r["status"] for r in _rows]
    assert [r["end"] for r in _rows] == [111000, 106000, 101000, 96000, 91000, 86000, 81000], [r["end"] for r in _rows]
    assert _rows[-2]["end"] == _d1["end"] == 86000 and skips_in_fy(_rows, "2031-09") == ["2031-04"]
    _rb, _ob, _nb = loan_ledger(_d1, dict(_H, opening=111500), "2031-09", True)
    assert _nb and "difference" in _nb, "a history that does not meet the ledger is SAID"
    _d1o = advance_views(_lmo, "Dev", "2031-10", True, [], private=True)["priv_lines"][0]
    _ro, _oo, _no = loan_ledger(_d1o, _H, "2031-10", True)
    assert _ro[-2]["status"] == "skip" and _ro[-2]["end"] == 86000 and skips_in_fy(_ro, "2031-10") == ["2031-04", "2031-10"]
    _rn, _on, _nn = loan_ledger(_d1, {}, "2031-09", True)          # no history record: the table starts where the
    assert _on == 96000 and _rn[0]["ym"] == "2031-08" and _rn[-2]["end"] == 86000 and _nn == "", (_on, _rn[0], _nn)   # LEDGER starts
    # a record that states no figure: 'paid' is the loan's standing terms, the opening is worked back
    _Hd = {"loan_id": "d1", "opening_date": "2031-03-31", "ledger_adjust": -1000,
           "pre": [{"ym": "2031-04", "kind": "skip"}, {"ym": "2031-05", "kind": "paid"},
                   {"ym": "2031-06", "kind": "paid"}, {"ym": "2031-07", "kind": "paid"}]}
    _rd, _od, _nd = loan_ledger(_d1, _Hd, "2031-09", True)
    assert _od == 111000 and _nd == "" and [r["end"] for r in _rd] == [r["end"] for r in _rows], (_od, _nd)
    assert [(r["inst"], r["interest"], r["principal"]) for r in _rd[:2]] == [(0, 0, 0), (6000, 1000, 5000)]
    _rx, _ox, _nx = loan_ledger(_d1, dict(_Hd, ledger_adjust=0), "2031-09", True)
    assert _nx and "adjustment" in _nx, "the ledger's adjustment is not the one the record was written for -- SAID"
    _d1bare = dict(_d1, caps=[])                                    # the same loan WITHOUT its adjustment row
    assert "adjustment" in loan_ledger(_d1bare, _Hd, "2031-09", True)[2]
    _re, _oe, _ne = loan_ledger(_d1, _Hd, "2031-05", True)          # a month inside the history: no ledger row, no note
    assert [r["ym"] for r in _re if r["status"] != "next"] == ["2031-04", "2031-05"] and _ne == ""
    # a DEFER on the loan with interest ALONE: the ledger takes the instalment for the interest-free part
    _R3 = _R + [_sys("d1f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1"),
                _sys("d2r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -6000, "d2"),
                _sys("d4r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -3000, "d4")]
    _v3 = advance_views(ledger_money(_R3, "Dev", "2031-10"), "Dev", "2031-10", True, [], private=True)
    _p3 = private_split(_v3["priv_lines"], "2031-10", True)
    assert (_p3["kept"], _p3["cut_shown"], _p3["paid"], _p3["reserve"], _p3["status"]) == (6000, 6000, 0, 0, "paid"), _p3
    _r3 = loan_ledger(_v3["priv_lines"][0], _H, "2031-10", True)[0]
    assert _r3[-2]["status"] == "defer" and _r3[-2]["end"] == 86000
    _lm3p = ledger_money(_R + [dict(_sys("d1f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1"), closed_month="")], "Dev", "2031-10")
    _d2p = [t for t in _lm3p["lines"] if t["id"] == "d2"][0]
    assert [(m, p) for m, p, _i in _d2p["proj"]][:1] == [("2031-10", 6000)], "before the close the plan already says where the instalment goes"
    # a recorded defer moves the plan as the close will: nothing that month, the schedule one month longer
    _R4 = _R + [_sys("d4f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d4")]
    _t4 = [t for t in ledger_money(_R4, "Dev", "2031-09")["lines"] if t["id"] == "d4"][0]
    assert [(m, p) for m, p, _i in _t4["proj"]] == [("2031-11", 3000), ("2031-12", 3000)], _t4["proj"]
    _t4o = [t for t in ledger_money(_R, "Dev", "2031-09")["lines"] if t["id"] == "d4"][0]
    assert [(m, p) for m, p, _i in _t4o["proj"]] == [("2031-10", 3000), ("2031-11", 3000)], _t4o["proj"]
    _R5 = _R + [_sys("d1k", "Dev", "LOAN_SKIP", "2031-10", 0, "d1")]          # a recorded skip: the waterfall waits
    _t5 = [t for t in ledger_money(_R5, "Dev", "2031-09")["lines"] if t["id"] == "d1"][0]
    assert _t5["proj"][0][0] == "2031-11" and _t5["proj"][0][1:] == (5000, 1000), _t5["proj"][:2]
    # money that comes back in ONE salary is not an instalment loan: no slip for it
    _R6 = [_iss("z1", "Zed", "2031-09-26", 1900, 1900, "2031-10")]
    _v6 = advance_views(ledger_money(_R6, "Zed", "2031-09"), "Zed", "2031-09", True, [])
    assert len(_v6["loans"]) == 1 and _v6["loans"][0]["n_all"] == 1 and _v6["loans"][0]["late_month"]
    assert not has_slip({"name": "Zed", "views": _v6}, {"ym": "2031-09"})
    assert has_slip({"name": "Asha", "views": _v}, {"ym": "2031-09"})
    # the loan record is cleaned on the way in, and a broken one never raises
    import tempfile as _tf, shutil as _sh
    _td = _tf.mkdtemp(prefix="sp_selftest_")
    _lpp = os.path.join(_td, "loan_pages.json")
    try:
        with open(_lpp, "w", encoding="utf-8") as _f:
            json.dump({"groups": [{"staff": "Asha", "ids": ["a1", "a2", "a2", 7, ["x"]], "given": 5},
                                  {"staff": "Asha", "ids": ["a2", "a3"]}, {"staff": "Asha", "ids": 9}, "junk",
                                  {"staff": 3, "ids": ["q"]}],
                       "history": {"DEV ": {"loan_id": "d1", "opening": "lots", "ledger_adjust": -1000,
                                            "pre": [{"ym": "2031-05", "kind": "paid"}, {"ym": "April 2031", "kind": "paid"},
                                                    "text", {"ym": "2031-04", "kind": "skip", "added": [1]},
                                                    {"ym": "2031-05", "kind": "paid", "instalment": 1}]},
                                   "Bad": "text"}}, _f)
        _c = loan_pages(_lpp)
        assert _c["groups"] == [{"staff": "Asha", "ids": ["a1", "a2"], "given": ""}, {"staff": "Asha", "ids": ["a3"], "given": ""}], _c["groups"]
        assert list(_c["history"]) == ["dev"] and _c["history"]["dev"]["pre"] == [{"ym": "2031-04", "kind": "skip"}, {"ym": "2031-05", "kind": "paid"}]
        assert "opening" not in _c["history"]["dev"] and loan_history("Dev", _c)["loan_id"] == "d1" and loan_history("Nobody", _c) == {}
        for _bad in ("[1, 2]", "{\"groups\": 5, \"history\": []}", "not json", ""):
            with open(_lpp, "w", encoding="utf-8") as _f:
                _f.write(_bad)
            assert loan_pages(_lpp) == {"groups": [], "history": {}}, _bad
    finally:
        _sh.rmtree(_td, ignore_errors=True)
    assert fy_of_ym("2031-03") == 2030 and fy_of_ym("2031-04") == 2031
    assert private_loan_names({}) == {"darpan"} and own_sheet_names({}) == set()
    assert loan_pages("/nonexistent/loan_pages.json") == {"groups": [], "history": {}}
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
