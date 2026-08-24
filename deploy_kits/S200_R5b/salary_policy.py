"""
salary_policy.py — v1.4 (S200/D346) — GO-LIVE: Sunday absence at derived shift
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
    "improve_pct": 30,          # % fewer chargeable minutes releases the hold
    "hold_enabled": 1,
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
        extra_rs = 0.0 if exempt else g.get("extra", 0) * s.get("extra_duty_rs", 200)
        outst_rs = 0.0 if exempt else outst * s.get("outstation_rs", 250)
        night_rs = 0.0

        # ledger side (advances/loans) — descriptive + a preview deduction
        advances_month, loans, adv_ded = [], [], 0.0
        open_bal = 0.0
        if L:
            for r in led_rows:
                if (r.get("category") == "NIGHT_DUTY" and r.get("status") == "APPROVED"
                        and r.get("staff") == name):
                    cm = r.get("closed_month")
                    if cm == ym or (not cm and str(r.get("date_from", ""))[:7] == ym):
                        night_rs += float(r.get("amount") or 0)
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

        leave_in_absent_cnt = (len(leave_dates & set(a["absent_dates"]))
                               if covered else 0)
        absent_excl = max(0, a["absent"] - leave_in_absent_cnt)
        duty_credits = round(night_rs + extra_rs + outst_rs, 2)
        deductions = round(collect + leave_amt + fine_uninf + fine_exc
                           + dress_rs + icard_rs + prior_collect, 2)
        # S199-D: incentive accrues to the Diwali pot — NOT in the month's net.
        # D342a: release is a CANCELLATION note only, never money added back.
        net = round(base - deductions - adv_ded + duty_credits, 2) if base else 0.0

        staff_out.append({
            "uid": uid, "name": name, "base": base, "exempt": exempt,
            "offs": offs, "shift_min": shift_min, "rate": round(rate, 4),
            "present": a["present"], "absent": a["absent"],
            "absent_excl": absent_excl, "leave_in_absent": leave_in_absent_cnt,
            "night_rs": night_rs, "extra_rs": extra_rs, "outst_rs": outst_rs,
            "outst_days": outst,
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
 body{font-family:Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.5;margin:16px;color:#222;background:#faf8f4}
 h1{font-size:22px;margin:0 0 2px} h2{font-size:17px;margin:16px 0 6px}
 .sub{color:#666;margin:0 0 8px;font-size:13px}
 .cap{display:inline-block;background:#eee7d8;border:1px solid #cbbfa4;border-radius:6px;
      padding:2px 10px;font-weight:bold;font-size:13px;letter-spacing:.5px}
 .banner{padding:8px 12px;margin:10px 0;border-radius:8px;font-weight:bold}
 .prev{background:#fff8e1;border:1px solid #e0c060}
 .enf{background:#e8f4e8;border:1px solid #7ab97a}
 .nav{position:sticky;top:0;background:#13233b;padding:8px 12px;margin:-16px -16px 12px;
      display:flex;gap:14px;flex-wrap:wrap;z-index:5}
 .nav a{color:#bfe3ff;text-decoration:none;font-size:14px;font-weight:bold}
 .nav a.here{color:#ffd868}
 .tw{overflow-x:auto} table{border-collapse:collapse;margin:8px 0}
 th,td{border:1px solid #b9b0a0;padding:5px 8px;text-align:left;white-space:nowrap;font-size:13.5px}
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
 .gcell{font-size:12.5px;text-align:center}
 a.door{color:#0a58ca;text-decoration:none}
 .note{background:#fff8e1;border:1px solid #e0c060;padding:6px 10px;margin:8px 0;font-size:13px}
 .hdr{text-align:center;margin-bottom:4px}
 @media print{ body{margin:6mm;background:#fff} .noprint,.nav{display:none} th,td{font-size:10.5px;padding:3px 5px} }
"""


def _banner(res):
    if res["enforced"]:
        return '<div class="banner enf">ENFORCED — this month is covered by the served notice.</div>'
    return ('<div class="banner prev">PREVIEW — nothing on this page is applied '
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
    items = [("flow", "Month-end flow", "%s/salary/flow?ym=%s" % (prefix, ym)),
             ("s1", "Sheet 1 · Attendance", "%s/salary/flow/sheet1?ym=%s" % (prefix, ym)),
             ("s2", "Sheet 2 · Money", "%s/salary/flow/sheet2?ym=%s" % (prefix, ym)),
             ("darpan", "Darpan", "%s/salary/flow/sheet2?ym=%s&staff=Darpan" % (prefix, ym)),
             ("prev", "Salary sheets", "%s/salary/flow/preview?ym=%s" % (prefix, ym)),
             ("set", "Settings", "%s/salary/policy-settings" % prefix),
             ("ledger", "Ledger", "/ledger/")]
    return ('<div class="nav noprint">' + "".join(
        '<a class="%s" href="%s">%s</a>' % ("here" if k == here else "", html.escape(u), html.escape(t))
        for k, t, u in items) + "</div>")


def sheet1_html(res, doors=False, prefix="/register", only_uid=None,
                back=None, print_=False):
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
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    if doors and only_uid is None:
        out.append('<div class="note noprint">Wrongly-absent days: fix a whole '
                   'month in one pass on the <a class="door" href="%s/fixabsents'
                   '?ym=%s">Fix-absents desk</a> (D339).</div>' % (e(prefix), e(ym)))

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

    for half in halves:
        days = [d for d in half]
        out.append('<div class="tw"><table><tr><th>Staff</th>')
        for d in days:
            _wd = datetime.date(year, mon, d).weekday()
            out.append('<th class="sun">%d<small>SUN</small></th>' % d
                       if _wd == 6 else "<th>%d</th>" % d)
        out.append("</tr>")
        for st in rows:
            out.append("<tr><td><b>%s</b></td>" % e(st["name"]))
            for d in days:
                _td = cell(st, d)
                out.append(_sunmark(_td)
                           if datetime.date(year, mon, d).weekday() == 6 else _td)
            out.append("</tr>")
        out.append("</table></div>")

    out.append("<h2>Month summary</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Present</th><th>Absent</th>"
               "<th>Leave (sanctioned)</th><th>Late marks</th><th>Late minutes</th></tr>")
    for st in rows:
        out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                   "<td class='n'>%d</td><td class='n'>%d</td><td class='n'>%d</td>%s</tr>"
                   % (e(st["name"]), st["present"], st["absent_excl"],
                      st["leave_in_absent"], st["marks"], st["late_min"],
                      "<td style='min-width:140px'></td>" if print_ else ""))
    if print_:
        out.append("</table></div>")
        out.append('<div class="sub">The blank last column is the staff-remark space.</div>')
    else:
        out.append("</table></div>")
    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red '
               '&ge;60). Hover for the out-punch. L sanctioned leave · A absent · '
               '&#42; approved present-request. Sundays carry the purple SUN column. '
               'The running day is excluded until '
               'it ends. Money appears on no staff copy.</div>')
    out.append("</body></html>")
    return "".join(out)


def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None,
                staff=None, prefix="/register"):
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
             if staff else "SHEET 2 · ADVANCES, LOANS &amp; HOLDS — %s" % month_words(ym))

    out = [_head("Money %s" % ym), _nav(prefix, ym, "darpan" if staff else "s2"),
           _clinic_hdr(title)]
    if back:
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))
    if staff is None and sep:
        out.append('<div class="note">%s has a separate money page — use the '
                   '<b>Darpan</b> link in the bar above.</div>'
                   % e(", ".join(sorted(sep))))

    out.append("<h2>Advances taken this month</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Date</th><th>Amount</th><th>Against month</th>"
               "<th>Instalment</th><th></th></tr>")
    any_a = False
    for st in pick:
        for r in st["advances_month"]:
            any_a = True
            door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                    % (ledger_prefix, e(st["name"]))) if doors else ""
            out.append("<tr><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(str(r.get("against_month") or "-")),
                          money(r.get("instalment") or r.get("amount") or 0), door))
    if not any_a:
        out.append("<tr><td colspan='6'>none recorded</td></tr>")
    out.append("</table></div>")

    out.append("<h2>Current open loans &amp; advances (as of today)</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Taken</th>"
               "<th>Instalment</th>%s<th>Balance</th><th></th></tr>"
               % ("<th>Due this month</th>" if cur_month else ""))
    any_l = False
    for st in pick:
        for lo in st["loans"]:
            any_l = True
            o = lo["o"]
            door = ('<a class="door" href="%s/advances">ledger</a>' % ledger_prefix) if doors else ""
            out.append("<tr><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>%s"
                       "<td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]), e(str(o["issue"].get("date_from", ""))),
                          money(o["instalment"]),
                          ("<td class='n'>%s</td>" % money(lo["due"])) if cur_month else "",
                          money(o["balance"]), door))
    if not any_l:
        out.append("<tr><td colspan='6'>none open</td></tr>")
    out.append("</table></div>")

    if staff:
        st = pick[0] if pick else None
        if st:
            out.append("<h2>Duty credits this month</h2><div class='tw'><table>"
                       "<tr><th>Outstation nights</th><th>Outstation Rs</th>"
                       "<th>Extra duty Rs</th><th>Night duty Rs (ledger)</th></tr>"
                       "<tr><td class='n'>%d</td><td class='n'>%s</td>"
                       "<td class='n'>%s</td><td class='n'>%s</td></tr></table></div>"
                       % (int(st.get("outst_days", 0)),
                          money(st["outst_rs"]), money(st["extra_rs"]), money(st["night_rs"])))

    out.append("<h2>Improvement holds</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Last month held</th><th>This month</th>"
               "<th>New charge</th><th>Collect now</th><th>New hold</th></tr>")
    for st in pick if staff else [x for x in res["staff"] if x["name"] not in sep]:
        if not (st["held"] or st["release"] or st.get("prior_collect")
                or st["release_note"] or st["late_charge"]):
            continue
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]),
                      (money(st["release"]) if st["release"] else
                       ("COLLECT " + money(st.get("prior_collect", 0))
                        if st.get("prior_collect") else "-")),
                      e(st["release_note"] or "-"),
                      money(st["late_charge"]), money(st["collect"]),
                      money(st["held"])))
    out.append("</table></div>")

    if staff is None:
        out.append("<h2>All fines, leaves &amp; credits (every staff — for review)</h2>"
                   "<div class='tw'><table><tr><th>Staff</th><th>Leaves</th>"
                   "<th>Absent</th><th>Late charge</th><th>Collect now</th><th>Hold</th>"
                   "<th>Leave amt (+ded/-cr)</th><th>Uninformed</th><th>Excess-absent</th>"
                   "<th>Dress</th><th>I-card</th><th>Night duty (+)</th>"
                   "<th>Incentive (+)</th></tr>")
        for st in res["staff"]:
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                       % (e(st["name"]), st["leaves_total"], st["absent_excl"])
                       + "".join("<td class='n'>%s</td>" % money(v) for v in (
                           st["late_charge"], st["collect"], st["held"], st["leave_amt"],
                           st["fine_uninf"], st["fine_exc"], st["dress_rs"],
                           st["icard_rs"], st["night_rs"], st["incentive"]))
                       + "</tr>")
        out.append("</table></div>")

    out.append('<div class="sub">Advance/loan figures are the ledger\'s own; '
               'corrections happen in the ledger (defer / waive there), then '
               'reload this sheet.</div>')
    out.append("</body></html>")
    return "".join(out)


def sheets34_html(res, back=None, approved=None, prefix="/register"):
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
        out.append('<div class="noprint"><a class="door" href="%s">&larr; Back</a></div>' % e(back))
    out.append(_banner(res))
    cols = ["Name", "Salary", "Advance ded.", "Leaves", "Leave amt", "Late min",
            "Marks", "Late charge", "Collect now", "Hold", "Hold released",
            "Dress", "I-card", "D+I fine", "Fines", "Duty credits", "Incentive→pot",
            "NET PAYABLE"]
    out.append("<div class='tw'><table><tr>" +
               "".join("<th>%s</th>" % c for c in cols) + "</tr>")
    tot = dict.fromkeys(range(len(cols)), 0.0)
    for st in res["staff"]:
        di = st["dress_rs"] + st["icard_rs"]
        fines = st["fine_uninf"] + st["fine_exc"]
        vals = [st["name"], st["base"], st["adv_ded"], st["leaves_total"],
                st["leave_amt"], st["late_min"], st["marks"], st["late_charge"],
                st["collect"], st["held"], st["release"], st["dress_days"],
                st["icard_days"], di, fines, st["duty_credits"], st["incentive"],
                st["net"]]
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
               '%d%% of the charge, returnable on %d%% improvement. Duty '
               'credits: night + extra duty + outstation. Incentive accrues to '
               'the annual pot (paid at Diwali) — not in this month&#39;s net. D+I fine: Rs.%s/day '
               'each without.</div>'
               % (s["day_divisor"], s["free_late_min"], money(s.get("min_charge_rs", 0)),
                  100 - s["collect_now_pct"], s["improve_pct"], money(s["dress_rs"])))
    out.append('<div style="page-break-before:always"></div>')
    out.append(_clinic_hdr("SHEET 4 · SALARY PAYMENT &amp; SIGNATURE — %s" % month_words(ym), cap))
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
               'उपरोक्त राशि पूरी प्राप्त की।</div>')
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
