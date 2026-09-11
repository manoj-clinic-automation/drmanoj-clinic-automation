"""
salary_policy.py — v1.15 (S239, the owner, 11-Sep-2026) — PART-TIME staff (dates_only_staff: Amir
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
SEPARATE_PAGES = ["Darpan"]     # staff with their OWN money page on Sheet 2 (owner)

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
        if start > 0 or taken > 0 or rec > 0 or intr > 0 or end > 0:
            lines.append({"id": r["id"], "date": str(r.get("date_from", "")),
                          "amount": amt, "interest_loan": bool(r.get("interest")),
                          "start": start, "taken": taken, "recovered": round(rec, 2),
                          "interest": round(intr, 2), "end": end, "bf": bf,
                          "plan": recovery_plan(r)})
    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    # S238 v1.9: how each advance is recovered from here on (the close's own lanes)
    closed = any(x.get("closed_month") == ym for x in rows)
    proj = project_recovery(rows, lines, _ym_add(ym, 1) if closed else ym)
    for t in lines:
        t["terms"] = recovery_terms(proj.get(t["id"], []), t["end"])
    tot = lambda k: round(sum(t[k] for t in lines), 2)
    return {"lines": lines, "start": tot("start"), "taken": tot("taken"),
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
    against-month. Salary-capacity holds, skips and defers are NOT foreseen.
    Returns {advance id: [(month, principal, interest), ...]}."""
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
        for i in [x for x in elig if x["lane"] == "schedule"]:
            sch = sorted(((str(e["month"]), float(e["amount"])) for e in i["r"]["schedule"]
                          if float(e.get("amount") or 0) > 0))
            k = max(0, min(len(sch), (int(m[:4]) * 12 + int(m[5:7])) -
                           (int(sch[0][0][:4]) * 12 + int(sch[0][0][5:7])) + 1))
            want = min(i["bal"], max(0.0, sum(a for _, a in sch[:k]) - i["done"]))
            if want > 0:
                i["bal"] -= want; i["done"] += want; out[i["id"]].append((m, want, 0.0))
        for i in [x for x in elig if x["lane"] == "quota"]:
            out[i["id"]].append((m, i["bal"], 0.0)); i["done"] += i["bal"]; i["bal"] = 0.0
        wf = sorted([x for x in elig if x["lane"] in ("loan", "waterfall") and x["bal"] > 0.005],
                    key=lambda x: (not x["interest"], str(x["r"].get("date_from", "")),
                                   str(x["r"].get("ts_entry", ""))))
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
        net = round(base - deductions - adv_ded + duty_credits + ot_paid, 2) if base else 0.0

        staff_out.append({
            "uid": uid, "name": name, "base": base, "exempt": exempt,
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
            "open_bal": open_bal, "adv_ded": adv_ded, "manual_adv": m_adv,
            "ledger_money": lm,
            "grid": a["grid"], "absent_dates": a["absent_dates"],
            "leave_dates": leave_dates, "net": net,
        })

    notes = []
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
             ("darpan", "Darpan", "%s/salary/flow/sheet2?ym=%s&staff=Darpan" % (prefix, ym)),
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


def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None,
                staff=None, prefix="/register", approve_html=""):
    """Sheet 2 — money review. staff=<name> renders that person's OWN page
    (Darpan separate, owner ruling); the main page covers everyone else and
    the all-staff fines table. No bottom totals (owner ruling)."""
    e = html.escape
    ym = res["ym"]
    cur_month = ym == ((_TODAY_OVERRIDE or datetime.date.today()).strftime("%Y-%m"))
    sep = set(SEPARATE_PAGES) if staff is None else set()
    pick = [st for st in res["staff"]
            if (staff is None and st["name"] not in sep and (st["advances_month"] or st["loans"] or st["open_bal"]))
            or (staff is not None and st["name"].lower() == staff.lower())]
    title = ("SHEET 2 · %s — MONEY PAGE — %s" % (staff.upper(), month_words(ym))
             if staff else "SHEET 2 · ADVANCES, LOANS & HOLDS — %s" % month_words(ym))

    out = [_head("Money %s" % ym), _nav(prefix, ym, "darpan" if staff else "s2"),
           _clinic_hdr(title)]
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    if approve_html and staff is None:
        out.append('<div class="noprint">%s</div>' % approve_html)
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    if staff is None and sep:
        out.append('<div class="note">%s has a separate money page — use the '
                   '<b>Darpan</b> link in the bar above.</div>'
                   % e(", ".join(sorted(sep))))

    out.append("<section class='s2sec'><h2>Advances taken this month</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Date</th><th>Amount</th><th>Against month</th>"
               "<th>How it is recovered</th><th>Check</th><th class='noprint'></th></tr>")
    any_a = False
    n_late = 0
    for st in pick:
        for r in st["advances_month"]:
            any_a = True
            door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                    % (ledger_prefix, e(st["name"]))) if doors else ""
            _ln = {x["id"]: x for x in (st.get("ledger_money") or {}).get("lines", [])}
            _am = str(r.get("against_month") or "")
            _late = bool(_am) and _am > str(r.get("date_from", ""))[:7]
            if _late:
                n_late += 1
            out.append("<tr%s><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='flag'" if _late else "", e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(month_words(_am) if _am else "-"),
                          e(terms_words(_ln[r.get("id")], ym) if r.get("id") in _ln else recovery_plan(r)),
                          ("&#9888; later month — check" if _late else "ok"), door))
    if not any_a:
        out.append("<tr><td colspan='7'>none recorded</td></tr>")
    out.append("</table></div>")
    if n_late:
        out.append("<div class='note'>%d advance%s above %s booked against a LATER month than "
                   "the month it was given. Advances are normally against the running month — "
                   "if one is a slip, correct it in the ledger (reverse it and enter it again), "
                   "then reload this sheet.</div>" % (n_late, "" if n_late == 1 else "s",
                                                      "is" if n_late == 1 else "are"))
    out.append("</section>")

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

    # S238 v1.9 (the owner): per advance, is it recovered IN ONE GO or ON INSTALMENTS
    # -- and for instalments, how much a month and till when. As at the month's end.
    out.append("<section class='s2sec'><h2>Advances &amp; loans still being recovered — "
               "as at the end of %s</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Advance (date · amount)</th>"
               "<th>Recovered in one go</th><th>On instalments</th>"
               "<th>Recovered this month</th><th>Balance at month end</th>"
               "<th class='noprint'></th></tr>" % month_words(ym))
    any_l = False
    for st in pick:
        lm = st.get("ledger_money") or {}
        lines = [t for t in lm.get("lines", []) if t["end"] > 0 or t["recovered"] > 0]
        if not lines:
            continue
        any_l = True
        door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                % (ledger_prefix, e(st["name"]))) if doors else ""
        for i, t in enumerate(lines):
            tt = t.get("terms") or {}
            if tt.get("kind") == "one_go":
                one = "Rs %s from the <b>%s</b> salary" % (money(tt["one_go_amt"]), month_words(tt["one_go_month"]))
                inst = "—"
            elif tt.get("kind") == "instalments":
                one = "—"
                span = "%s → <b>%s</b>" % (month_words(tt["from"]), month_words(tt["until"]))
                if tt.get("per"):
                    inst = "<b>Rs %s a month</b> · %s%s" % (
                        money(tt["per"]), span,
                        ("<br><small>%s</small>" % e(tt["per_note"])) if tt.get("per_note") else "")
                else:
                    inst = "%s<br><small>%s</small>" % (span, e(tt.get("per_note", "")))
            elif tt.get("kind") == "unplanned":
                one, inst = "—", "no recovery terms on the ledger"
            else:
                one, inst = "cleared", "—"
            label = ("brought forward · " if t.get("bf") else e(t["date"]) + " · ") + money(t["amount"])
            if t["interest_loan"]:
                label += " <small>(interest loan)</small>"
            out.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='n'>%s</td>"
                       "<td class='n'><b>%s</b></td><td class='noprint'>%s</td></tr>"
                       % (("<b>%s</b>" % e(st["name"])) if i == 0 else "", label, one, inst,
                          money(t["recovered"] + t["interest"]), money(t["end"]),
                          door if i == 0 else ""))
        if len(lines) > 1:
            out.append("<tr class='tot'><td></td><td>total</td><td></td><td></td>"
                       "<td class='n'>%s</td><td class='n'><b>%s</b></td><td class='noprint'></td></tr>"
                       % (money(lm["recovered"] + lm["interest"]), money(lm["end"])))
    if not any_l:
        out.append("<tr><td colspan='7'>nothing being recovered</td></tr>")
    out.append("</table></div>")
    out.append("<div class='sub'>'Recovered this month' is what the ledger took from this "
               "month's salary (interest included). The months ahead follow the ledger's own "
               "recovery rules and current terms; a month skipped, deferred or held because the "
               "salary could not bear it moves them later.</div>")
    if not res.get("ledger_closed", True):
        out.append("<div class='note'>The staff ledger is not closed for %s yet — "
                   "'Recovered this month' fills in at the ledger close.</div>" % month_words(ym))
    out.append("</section>")

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
    out.append('<div class="sub">Leave amt: (leaves − allowed) × salary÷%d, '
               'negative = credit. Late charge: after %d free min, progressive '
               'at own salary minute-rate (charges under Rs.%s ignored). Hold: '
               '%d%% of the charge is marked, not deducted; cancelled on %d%% improvement next month, '
               'otherwise deducted next month. Duty '
               'credits: night + extra duty + outstation. Incentive accrues to '
               'the annual pot (paid at Diwali) — not in this month&#39;s net. D+I fine: Rs.%s/day '
               'each without.</div>'
               % (s["day_divisor"], s["free_late_min"], money(s.get("min_charge_rs", 0)),
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
