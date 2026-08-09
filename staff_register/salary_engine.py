"""
salary_engine.py  —  Staff Register salary · STANDALONE (D288, S163).

READ-ONLY. Std-lib only for the core math. Writes NOTHING any live service reads.

WHAT CHANGED FROM STAGE A (net-borrow -> standalone)
----------------------------------------------------
Stage A produced  final_net = ledger.compute_salary(net)  +  register delta.
That permanently coupled the register to the ledger's salary code and could
double-count uniform/i-card. D288 makes /register/salary the ONE salary system
so the ledger salary page can be retired. This module now computes the WHOLE
monthly take-home itself from primitives, and keeps the old ledger net only as a
SHADOW column so any per-staff gap is visible until parity is proven, then dropped.

The standalone take-home per staff (OT removed; incentive -> annual pot):

    net = base
        - marks - early - uninformed - excess_absent(outstation-adjusted) - early_big
        + extra_duty + outstation                 (register grid credits)
        - dress - i_card                          (per-month source rule, below)
        - C_model_deduction + encashment          (only for register-COVERED months)
        + ledger_money_fold                       (month_adjustments MINUS uniform/i-card)
        + prorate_delta                           (partial month)
    incentive is NOT added to the month -> it accrues to the per-staff annual pot.

Two policy rules that make parity correct (S163, owner-confirmed):

  (1) C-model gating. base/30 absence cuts and unused-leave encashment need
      leave-sanction data. A month with NO register grid rows (e.g. 2026-07,
      before the register went live) has none, so the engine CANNOT tell
      sanctioned leave from genuine absence -> it applies NO base/30 cut and NO
      encashment for that month; those absences keep the attendance layer's
      existing Rs 100 excess-absence fine. This is what makes the July anchor
      reconcile: July net = compute_salary net - incentive + prorate, so
        sum(July net) + sum(July incentive->pot) == the old TOTAL PAYOUT.

  (2) Uniform/i-card source. Dress / i-card fines are counted from wherever they
      were recorded that month: the register GRID if the month is covered
      (Aug onward, D286), else the ledger's FINE_UNIFORM / FINE_ICARD rows (July).
      The ledger money fold ALWAYS excludes uniform/i-card, so they are never
      counted twice. If a covered month still has ledger uniform/i-card rows, the
      grid is used and a LOUD problem is raised (never silently double-count).

  The ledger fold = month_adjustments MINUS {FINE_UNIFORM, FINE_ICARD}. Using the
  same rule set as the ledger (every non-excluded category, incl. OTHER and any
  future one) guarantees parity for the whole ledger side, not just five names.

PARITY (proven on the VPS against real data; F-31 keeps pay off-repo/off-chat):
  * July  (no register rows): net + incentive_pot == old TOTAL PAYOUT, to the rupee.
  * August (register live): every difference vs the old figure is explainable
    line-by-line (grid fines/credits, C-model, incentive->pot, OT removed). The
    SHADOW column shows the old ledger net beside the new one per staff.

RETIRE-FOR-GOOD (staged, safe): the ledger salary PAGE is redirected to
/register/salary once parity holds; compute_salary stays dormant one cycle as a
fallback and is deleted next EOS after one real month is paid and matched.

USAGE
  /root/wa/venv/bin/python3 /root/staff_register/salary_engine.py 2026-07
  /root/wa/venv/bin/python3 /root/staff_register/salary_engine.py --selftest
"""
import os
import sys
import csv
import re
import html
import sqlite3
import datetime
import calendar

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SR_DB_PATH", os.path.join(BASE, "staff_register.db"))
ATT_DIR = os.environ.get("ATT_DIR", "/root")        # where salary_inputs_<ym>.csv lives

# ---- policy constants (mirror att_month_report / dossier) -------------------
DAYS_BASIS = 30
DRESS_RS = 20
ICARD_RS = 20
EXTRA_DUTY_RS = 200
OUTSTATION_RS = 250
DISC_QUOTA = 2          # discretionary leave / month
FEST_QUOTA = 2          # festival leave / financial year
ABSENT_FREE_DAYS = 3
FINE_UNINFORMED = 50
FINE_EXCESS_ABSENT = 100

# categories the REGISTER now owns (D286) -> excluded from the ledger money fold
# so a month's uniform/i-card/leave is never counted from both places.
REG_OWNED_CATS = {"FINE_UNIFORM", "FINE_ICARD", "LEAVE_APPROVED"}
# cash / balance-side events that are never salary money. Must match the ledger's
# own SALARY_EXCLUDED exactly; guarded at import time in _resolve_ledger().
SALARY_EXCLUDED = {"ADVANCE_ISSUE", "LOAN_CAPITALISE", "LOAN_SKIP", "PERK", "SALARY_PAID"}

_LEDGER_ERR = ""
_SHADOW_ERR = ""


def _add_ledger_paths():
    """staff_ledger.py lives in /root; its deps (clinic_sso/portal_config) live in
    /root/portal. Add the likely CODE dirs (guarded) so imports resolve both in the
    standalone CLI and inside the web app."""
    for d in ("/root", "/root/wa", "/root/portal",
              os.path.dirname(BASE), os.path.join(BASE, "..", "portal")):
        if d and os.path.isdir(d) and d not in sys.path:
            sys.path.append(d)


def fy_start(ym):
    """First day of the financial year (Apr 1) containing YYYY-MM."""
    y, m = int(ym[:4]), int(ym[5:7])
    return datetime.date(y if m >= 4 else y - 1, 4, 1)


def month_bounds(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    ndays = calendar.monthrange(y, m)[1]
    return datetime.date(y, m, 1), datetime.date(y, m, ndays), ndays


def active_days(join_date, last_working, m_first, m_last, ndays):
    """Days in the month the staffer was employed (for base pro-rating).
    Missing/relaxed dates default to the full month."""
    try:
        jd = datetime.date.fromisoformat(join_date) if join_date else m_first
    except ValueError:
        jd = m_first
    lw = None
    if last_working:
        try:
            lw = datetime.date.fromisoformat(last_working)
        except ValueError:
            lw = None
    start = max(jd, m_first)
    end = min(lw, m_last) if lw else m_last
    if end < start:
        return 0
    return (end - start).days + 1


# ---------------------------------------------------------------- pure core --
def reconcile(name, base, minutes_exempt, att, reg, ndays, act_days,
              fold, uic_led, ruling_outst, eb_rs, covered):
    """Compute one staffer's STANDALONE monthly take-home (owner model S163).

    att   = salary_inputs row (attendance report): Ded: marks Rs, Ded: early-dep Rs,
            Fine: uninformed Rs, Fine: excess-absent Rs, Incentive Rs, Absent, ...
    reg   = register grid aggregates for the month: dress, icard, extra, outstation,
            disc_used, fest_used, fest_prior_fy, late_not_informed, leave_dates,
            absent_dates.
    fold  = {"credit":.., "debit":..} ledger money for the month EXCLUDING
            uniform/i-card/leave (the register-owned categories) and SALARY_EXCLUDED.
    uic_led = {"dress":Rs, "icard":Rs} ledger uniform/i-card magnitudes (used only
            when the month is NOT register-covered).
    ruling_outst = outstation days from the owner rulings (Darpan) -> used ONLY to
            re-derive the excess-absence fine exactly as the ledger does.
    eb_rs = EARLY_BIG rupees ruled genuine (from the owner rulings), already summed.
    covered = does the register hold grid data for this month? gates the C-model and
            selects the uniform/i-card source.
    """
    day = round(base / DAYS_BASIS, 2) if base else 0.0

    def fnum(k):
        try:
            return float(att.get(k) or 0)
        except (TypeError, ValueError):
            return 0.0

    ded_marks = fnum("Ded: marks Rs")
    ded_early = fnum("Ded: early-dep Rs")
    fine_uninf = fnum("Fine: uninformed Rs")
    fine_exc = fnum("Fine: excess-absent Rs")
    inc = fnum("Incentive Rs")
    att_absent = int(fnum("Absent"))

    # sanctioned leave + grid outstation nights were NOT genuine absence
    leave_in_absent = len(reg["leave_dates"] & reg["absent_dates"])
    genuine_absent = max(0, att_absent - leave_in_absent - reg["outstation"])

    # excess-absence fine, re-derived so approved leave / outstation days are not
    # fined. COVERED month -> fine only genuine absences (the register knows leave
    # and grid outstation). UNCOVERED month (July) -> match the ledger EXACTLY:
    # reduce only by rulings outstation (Darpan), no leave concept; else the CSV.
    if covered:
        outst_used = reg["outstation"]
        fine_exc_adj = float(max(0, genuine_absent - ABSENT_FREE_DAYS)
                             * FINE_EXCESS_ABSENT)
    else:
        outst_used = min(int(ruling_outst), att_absent) if ruling_outst else 0
        if outst_used:
            fine_exc_adj = float(max(0, (att_absent - outst_used) - ABSENT_FREE_DAYS)
                                 * FINE_EXCESS_ABSENT)
        else:
            fine_exc_adj = fine_exc

    disc_used = reg["disc_used"]
    fest_used = reg["fest_used"]
    fest_allow = max(0, FEST_QUOTA - reg["fest_prior_fy"])
    fest_over = max(0, fest_used - fest_allow)

    # C = discretionary leaves + genuine absences; over the 2-day buffer is cut at
    # base/30. Over-quota festival cuts separately. BOTH require register coverage
    # (rule 1): with no grid data we cannot reclassify absence, so no cut, no encash.
    C = disc_used + genuine_absent
    extra_days = max(0, C - DISC_QUOTA)
    deduct_days = (extra_days + fest_over) if covered else 0
    base30_ded = round(deduct_days * day, 2)
    encash_days = (max(0, DISC_QUOTA - C) if (covered and deduct_days == 0) else 0)
    encash_rs = round(encash_days * day, 2)

    # register money (minutes-exempt = leave only; base/30 + encash still apply, D276)
    if minutes_exempt:
        extra_rs = outst_rs = 0.0
    else:
        extra_rs = reg["extra"] * EXTRA_DUTY_RS
        outst_rs = reg["outstation"] * OUTSTATION_RS

    # uniform / i-card: rule 2 -> grid if covered, else the ledger's own rows
    if minutes_exempt:
        dress_rs = icard_rs = 0.0
    elif covered:
        dress_rs = reg["dress"] * DRESS_RS
        icard_rs = reg["icard"] * ICARD_RS
    else:
        dress_rs = float(uic_led.get("dress", 0.0))
        icard_rs = float(uic_led.get("icard", 0.0))

    # ledger money fold (already excludes uniform/i-card/leave + SALARY_EXCLUDED)
    ledger_fold = round(float(fold.get("credit", 0.0)) - float(fold.get("debit", 0.0)), 2)

    # base pro-rating for a partial month
    prorated_base = round(base * (act_days / ndays), 2) if ndays else float(base)
    prorate_delta = round(prorated_base - base, 2)      # <= 0

    # STANDALONE take-home. OT removed. Incentive NOT added (-> annual pot).
    net = round(
        base
        - ded_marks - ded_early - fine_uninf - fine_exc_adj - eb_rs
        + extra_rs + outst_rs
        - dress_rs - icard_rs
        - base30_ded + encash_rs
        + ledger_fold
        + prorate_delta
    )

    return {
        "name": name, "base": base, "day_rate": day,
        "att_absent": att_absent, "genuine_absent": genuine_absent, "C": C,
        "disc_used": disc_used, "fest_used": fest_used, "fest_over": fest_over,
        "extra_days": extra_days, "deduct_days": deduct_days,
        "late_not_informed": reg["late_not_informed"], "covered": covered,
        "ded_marks": ded_marks, "ded_early": ded_early,
        "fine_uninf": fine_uninf, "fine_exc": round(fine_exc_adj, 2),
        "early_big": round(eb_rs, 2), "outst_used": outst_used,
        "dress_rs": round(dress_rs, 2), "icard_rs": round(icard_rs, 2),
        "extra_rs": round(extra_rs, 2), "outst_rs": round(outst_rs, 2),
        "base30_ded": base30_ded,
        "encash_days": encash_days, "encash_rs": encash_rs,
        "ledger_fold": ledger_fold,
        "incentive_pot": round(inc, 2), "incentive_tier": att.get("Incentive", ""),
        "prorated_base": prorated_base, "prorate_delta": prorate_delta,
        "act_days": act_days, "ndays": ndays,
        "final_net": net,             # the standalone take-home (this IS the payout)
        "shadow_net": None,           # old ledger net, filled in build_report
        "shadow_diff": None,          # final_net - shadow_net
        "net_complete": True,         # False if the ledger fold was unavailable
    }


# ------------------------------------------------------------------ loaders --
def load_att_inputs(ym, att_dir=None):
    """Rows of salary_inputs_<ym>.csv keyed by lowercase Name, or None."""
    path = os.path.join(att_dir or ATT_DIR, "salary_inputs_%s.csv" % ym)
    if not os.path.exists(path):
        return None, path
    out = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(row.get("Name") or "").strip().lower()] = row
    return out, path


def load_register(ym, db_path=None):
    """Per-staff register aggregates for the month + the staff table + a COVERED
    flag (does the register hold ANY grid data for this month?). Read-only."""
    dbp = db_path or DB_PATH
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    m_first, m_last, _ = month_bounds(ym)
    fs = fy_start(ym).isoformat()
    lo, hi = m_first.isoformat(), m_last.isoformat()

    staff = {r["staff_id"]: dict(r) for r in
             con.execute("SELECT * FROM staff").fetchall()}
    closed = {r["fest_date"] for r in
              con.execute("SELECT fest_date FROM festival_day WHERE clinic_closed=1")}

    agg = {}
    for sid in staff:
        agg[sid] = {"dress": 0, "icard": 0, "extra": 0, "outstation": 0,
                    "disc_used": 0, "fest_used": 0, "fest_prior_fy": 0,
                    "late_not_informed": 0, "leave_dates": set()}

    rowcount = 0
    for r in con.execute(
            "SELECT * FROM daily_register WHERE reg_date>=? AND reg_date<=?", (lo, hi)):
        rowcount += 1
        sid = r["staff_id"]
        a = agg.get(sid)
        if a is None:
            continue
        on_leave = bool(r["leave_kind"]) and r["reg_date"] not in closed
        if on_leave:
            a["leave_dates"].add(r["reg_date"])
            if r["leave_kind"] == "festival":
                a["fest_used"] += 1
            else:
                a["disc_used"] += 1
        else:
            if r["dress_improper"]:
                a["dress"] += 1
            if r["icard_missing"]:
                a["icard"] += 1
        a["extra"] += int(r["extra_duty"] or 0)
        a["outstation"] += int(r["outstation_nights"] or 0)
        if r["late_flag"] == "not_informed" and not on_leave:
            a["late_not_informed"] += 1

    for r in con.execute(
            "SELECT staff_id, COUNT(*) c FROM daily_register "
            "WHERE leave_kind='festival' AND reg_date>=? AND reg_date<? "
            "GROUP BY staff_id", (fs, lo)):
        if r["staff_id"] in agg:
            agg[r["staff_id"]]["fest_prior_fy"] = r["c"]

    con.close()
    covered = rowcount > 0
    return agg, staff, covered


def _resolve_ledger():
    """Import the live ledger (READ-ONLY use only) and hard-check that our
    SALARY_EXCLUDED still matches its own -- a silent drift there would mis-pay.
    Returns the module or None (sets _LEDGER_ERR)."""
    global _LEDGER_ERR
    _LEDGER_ERR = ""
    _add_ledger_paths()
    try:
        import staff_ledger as _L
    except Exception as e:
        _LEDGER_ERR = "%s: %s" % (type(e).__name__, e)
        return None
    try:
        if set(_L.SALARY_EXCLUDED) != SALARY_EXCLUDED:
            _LEDGER_ERR = ("ledger SALARY_EXCLUDED changed (%s) -- refusing to "
                           "compute salary against a drifted rule set"
                           % sorted(_L.SALARY_EXCLUDED))
            return None
    except AttributeError:
        pass
    return _L


def ledger_fold(ym, rows=None):
    """Per-staff ledger money for the month, split into:
        {name: {"credit":.., "debit":.., "uic":{"dress":.., "icard":..}}}
    Counts APPROVED rows stamped closed_month==ym, EXCLUDING SALARY_EXCLUDED and
    the register-owned categories (uniform/i-card/leave) from credit/debit; the
    uniform/i-card magnitudes are returned separately for the source rule. Returns
    (data, closed, problems). `rows` may be injected (selftest); otherwise the live
    ledger is read read-only."""
    problems = []
    if rows is None:
        L = _resolve_ledger()
        if L is None:
            return None, False, ["ledger money could not be read [%s] -- a run "
                                 "without it must not be locked." % (_LEDGER_ERR or "?")]
        rows = L.load_ledger()
        closed = L.ledger_closed(ym, rows)
    else:
        closed = any(r.get("closed_month") == ym for r in rows)
    out = {}
    for r in rows:
        if r.get("status") != "APPROVED" or r.get("closed_month") != ym:
            continue
        cat = r.get("category")
        if cat in SALARY_EXCLUDED or cat == "LEAVE_APPROVED":
            continue
        nm = r.get("staff")
        d = out.setdefault(nm, {"credit": 0.0, "debit": 0.0,
                                "uic": {"dress": 0.0, "icard": 0.0}})
        amt = float(r.get("amount") or 0)
        if cat == "FINE_UNIFORM":
            d["uic"]["dress"] += -amt
        elif cat == "FINE_ICARD":
            d["uic"]["icard"] += -amt
        elif amt >= 0:
            d["credit"] += amt
        else:
            d["debit"] += -amt
    return out, closed, problems


def load_shadow_net(ym):
    """OLD-model take-home per staff by REUSING the ledger's own compute_salary
    (read-only) -- kept ONLY as the parity shadow column. Returns ({name: net},
    problems) or (None, []) if unreachable."""
    global _SHADOW_ERR
    _SHADOW_ERR = ""
    L = _resolve_ledger()
    if L is None:
        _SHADOW_ERR = _LEDGER_ERR
        return None, []
    try:
        table, _tok, probs = L.compute_salary(ym)
    except Exception as e:
        _SHADOW_ERR = "%s: %s" % (type(e).__name__, e)
        return None, []
    return {t["name"]: float(t.get("net") or 0) for t in table}, list(probs or [])


# --- EARLY-BIG rulings owned by the REGISTER (S163) --------------------------
# The register now holds its own genuine/waived verdict per big early-exit, so the
# ledger's salary page can be retired. One writer: the register app (this module
# only READS the table). Keyed (ym, staff, ebdate) -> the engine key is name|date.
EARLYBIG_SCHEMA = """
CREATE TABLE IF NOT EXISTS earlybig_ruling (
    ym        TEXT NOT NULL,                       -- YYYY-MM
    staff     TEXT NOT NULL,                       -- staff name (matches the report)
    ebdate    TEXT NOT NULL,                       -- YYYY-MM-DD of the early-exit
    verdict   TEXT NOT NULL DEFAULT 'waived',      -- genuine | waived
    ruled_by  TEXT, ruled_ts TEXT,
    PRIMARY KEY (ym, staff, ebdate)
);
"""
_EB_RE = re.compile(r"would be Rs\.([0-9.]+) if confirmed")


def earlybig_events(ym, att_dir=None):
    """Big early-exit events for the month, straight from the attendance layer's
    deductions_extras_<ym>.csv (NOT via the ledger). Returns [{name,date,minutes,
    rs,note}]. Fail-loud if the amount pattern is gone -- a silent 0 would waive a
    real deduction. Missing file -> []."""
    path = os.path.join(att_dir or ATT_DIR, "deductions_extras_%s.csv" % ym)
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if len(r) >= 6 and r[2] == "EARLY_BIG":
                m = _EB_RE.search(r[5])
                if not m:
                    raise ValueError(
                        "EARLY_BIG note format changed in deductions_extras_%s.csv "
                        "(no would-be amount): %r -- refusing to guess" % (ym, r[5]))
                out.append({"name": r[0], "date": r[1], "minutes": r[3],
                            "rs": float(m.group(1)), "note": r[5]})
    return out


def load_register_earlybig(ym, db_path=None):
    """Register verdicts for the month as {'<name>|<date>': True/False} (genuine).
    Read-only; a missing table / DB just yields {} (nothing ruled here yet)."""
    out = {}
    dbp = db_path or DB_PATH
    if not os.path.exists(dbp):
        return out
    con = sqlite3.connect(dbp)
    try:
        cur = con.execute("SELECT staff, ebdate, verdict FROM earlybig_ruling "
                          "WHERE ym=?", (ym,))
        for staff, ebdate, verdict in cur.fetchall():
            out["%s|%s" % (staff, ebdate)] = (verdict == "genuine")
    except sqlite3.OperationalError:
        pass                                # table not created yet
    finally:
        con.close()
    return out


def _rulings_for(ym, rulings, db_path=None):
    """Owner rulings dict {earlybig, ot, outstation}. earlybig verdicts from the
    REGISTER overlay the base per key (register wins) so a register-paid month is
    ruled in the register, while July still falls back to the ledger. `rulings`
    injected in tests; else the ledger's own loader (read-only) supplies ot /
    outstation and any pre-register earlybig."""
    if rulings is not None:
        base = rulings
    else:
        L = _resolve_ledger()
        if L is None:
            base = {"earlybig": {}, "ot": {}, "outstation": {}}
        else:
            try:
                base = L.load_rulings(ym)
            except Exception:
                base = {"earlybig": {}, "ot": {}, "outstation": {}}
    eb = dict(base.get("earlybig", {}))     # copy: never mutate the caller's dict
    for key, genuine in load_register_earlybig(ym, db_path).items():
        eb[key] = {"genuine": bool(genuine)}
    base = dict(base)
    base["earlybig"] = eb
    base.setdefault("ot", {})
    base.setdefault("outstation", {})
    return base


def _earlybig_for(ym, earlybig, att_dir=None):
    """Big early-exit events. Injected in tests; else read straight from the
    attendance CSV (no ledger dependency)."""
    if earlybig is not None:
        return earlybig
    return earlybig_events(ym, att_dir)


def _bases_for(bases):
    if bases is not None:
        return bases
    L = _resolve_ledger()
    if L is None:
        return {}
    try:
        return L.staff_bases()
    except Exception:
        return {}


def _eb_rs(name, ym, earlybig, rulings):
    """Sum of EARLY_BIG rupees ruled genuine for this staffer (matches the ledger:
    only owner-confirmed-genuine rows deduct, at the report's own amount)."""
    total = 0.0
    for e in earlybig:
        if e.get("name") != name:
            continue
        key = "%s|%s" % (name, e.get("date"))
        if rulings.get("earlybig", {}).get(key, {}).get("genuine"):
            total += float(e.get("rs") or 0)
    return round(total, 2)


def build_report(ym, db_path=None, att_dir=None, *,
                 ledger_rows=None, rulings=None, earlybig=None, bases=None):
    """Assemble the standalone salary. Returns (rows, problems, pot_total).
    The keyword inputs are injectable for the selftest; in production they default
    to the live ledger's own read-only loaders (no drift)."""
    att, att_path = load_att_inputs(ym, att_dir)
    problems = []
    if att is None:
        return [], ["salary_inputs_%s.csv not found (run the attendance report first): %s"
                    % (ym, att_path)], 0.0
    agg, staff, covered = load_register(ym, db_path)
    m_first, m_last, ndays = month_bounds(ym)

    fold, closed, fold_probs = ledger_fold(ym, ledger_rows)
    problems.extend(fold_probs)
    ledger_ok = fold is not None
    if ledger_ok and not closed:
        problems.append("ledger month %s is not closed yet -- loan instalments / "
                        "adjustments are missing until 'close %s' runs (view only; "
                        "do not lock)." % (ym, ym))
    rul = _rulings_for(ym, rulings, db_path)
    eb_all = _earlybig_for(ym, earlybig, att_dir)
    base_map = _bases_for(bases)

    shadow, shadow_probs = load_shadow_net(ym)
    if shadow is None:
        problems.append("old-model shadow net unavailable [%s] -- parity column "
                        "hidden (does not block the new run)." % (_SHADOW_ERR or "?"))
    else:
        for p in shadow_probs:
            problems.append("shadow note: " + p)

    by_name = {(s["name"] or "").strip().lower(): sid for sid, s in staff.items()}
    rows, pot_total = [], 0.0
    for key, arow in sorted(att.items()):
        sid = by_name.get(key)
        if sid is None:
            problems.append("%s is in the attendance report but not in the register"
                            % (arow.get("Name") or key))
            continue
        s = staff[sid]
        nm = s["name"]
        reg = agg[sid]
        reg["absent_dates"] = set((arow.get("Absent dates") or "").split())
        act = active_days(s.get("join_date"), s.get("last_working"),
                          m_first, m_last, ndays)
        base = float(s.get("base_salary") or 0)
        # parity guard: register base must match staff_master (else totals can't match)
        if base_map and nm in base_map and round(base_map[nm], 2) != round(base, 2):
            problems.append("BASE MISMATCH for %s: register %s vs staff_master %s "
                            "-- totals cannot reconcile until these agree."
                            % (nm, int(base), int(base_map[nm])))
        f = (fold or {}).get(nm, {"credit": 0.0, "debit": 0.0,
                                  "uic": {"dress": 0.0, "icard": 0.0}})
        uic = f.get("uic", {"dress": 0.0, "icard": 0.0})
        # covered month should have NO ledger uniform/i-card rows (D286); if it does,
        # the grid wins but we must say so -- never silently double-count.
        if covered and (uic.get("dress") or uic.get("icard")):
            problems.append("%s: ledger still carries uniform/i-card rows in a "
                            "register-covered month -- GRID used, ledger uic ignored; "
                            "verify there is no duplicate entry." % nm)
        eb_rs = _eb_rs(nm, ym, eb_all, rul)
        r = reconcile(nm, base, bool(s.get("minutes_exempt")), arow, reg, ndays, act,
                      f, uic, rul.get("outstation", {}).get(nm, 0), eb_rs, covered)
        if not ledger_ok:
            r["net_complete"] = False
            r["final_net"] = None       # incomplete run must never lock (D283)
        # shadow (old ledger net) + per-staff diff
        if shadow is not None and nm in shadow:
            r["shadow_net"] = round(shadow[nm], 2)
            if r["final_net"] is not None:
                r["shadow_diff"] = round(r["final_net"] - r["shadow_net"], 2)
        rows.append(r)
        pot_total += r["incentive_pot"]
    return rows, problems, round(pot_total, 2)


def total_payout(rows):
    """Headline TOTAL PAYOUT = sum of each staffer's standalone take-home (final_net),
    to the rupee. Returns (total, complete). complete=False if ANY staffer's net is
    unavailable (ledger unreachable / base missing) -- an incomplete run is never
    lockable (D283). READS only; no new math."""
    total, complete = 0.0, True
    for r in rows:
        v = r.get("final_net")
        if v is None or not r.get("net_complete", True):
            complete = False
        if v is not None:
            total += v
    return round(total, 0), complete


def shadow_summary(rows):
    """(old_total, new_total, diff, all_shadow) across staff with a shadow net --
    the one-line parity headline for the page."""
    old = new = 0.0
    all_shadow = True
    for r in rows:
        s = r.get("shadow_net")
        n = r.get("final_net")
        if s is None or n is None:
            all_shadow = False
            continue
        old += s
        new += n
    return round(old, 0), round(new, 0), round(new - old, 0), all_shadow


# -------------------------------------------------------------- html render --
_CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0b1220;color:#e5edf5;margin:0;padding:18px}
h1{font-size:20px;margin:0 0 4px}.sub{color:#93a4b8;font-size:13px;margin:0 0 14px}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0}
th,td{border:1px solid #24344a;padding:6px 8px;text-align:right;white-space:nowrap}
th{background:#13233b;color:#cfe0f2;position:sticky;top:0}
td.nm,th.nm{text-align:left}
.pos{color:#7ee0a2}.neg{color:#ff9b9b}.zero{color:#6b7c90}
.tot{background:#10203a;font-weight:600}
.note{color:#93a4b8;font-size:12px;margin:8px 0}
.warn{background:#3a1414;border:1px solid #7f1d1d;color:#ffc9c9;padding:8px 10px;border-radius:8px;margin:8px 0;font-size:13px}
.ok{background:#123020;border:1px solid #1d7f4d;color:#c9ffe0;padding:8px 10px;border-radius:8px;margin:8px 0;font-size:13px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid #24344a;color:#9fb4cc}
"""

_COLS = [
    ("nm", "Staff", "name"),
    ("", "Base", "base"),
    ("", "Att absent", "att_absent"),
    ("", "Genuine abs", "genuine_absent"),
    ("", "Leave (D/F)", "_leave"),
    ("", "Marks -", "ded_marks"),
    ("", "Early -", "ded_early"),
    ("", "Uninf -", "fine_uninf"),
    ("", "Exc-abs -", "fine_exc"),
    ("", "Early-big -", "early_big"),
    ("", "Extra-abs -", "base30_ded"),
    ("", "Encash +", "encash_rs"),
    ("", "Dress -", "dress_rs"),
    ("", "I-card -", "icard_rs"),
    ("", "Extra duty +", "extra_rs"),
    ("", "Outstation +", "outst_rs"),
    ("", "Ledger fold", "ledger_fold"),
    ("", "Incentive->pot", "incentive_pot"),
    ("", "Pro-rate", "prorate_delta"),
    ("", "NET (new)", "final_net"),
    ("", "Old (shadow)", "shadow_net"),
    ("", "Delta", "shadow_diff"),
]
# columns rendered as a deduction (shown negative)
_NEG_COLS = {"ded_marks", "ded_early", "fine_uninf", "fine_exc", "early_big",
             "base30_ded", "dress_rs", "icard_rs", "incentive_pot"}
_SUMKEYS = ["ded_marks", "ded_early", "fine_uninf", "fine_exc", "early_big",
            "base30_ded", "encash_rs", "dress_rs", "icard_rs", "extra_rs",
            "outst_rs", "ledger_fold", "incentive_pot", "prorate_delta"]


def _money(v):
    if not v:
        return '<span class="zero">0</span>'
    cls = "pos" if v > 0 else "neg"
    return '<span class="%s">%s%s</span>' % (
        cls, "+" if v > 0 else "", ("%.2f" % v).rstrip("0").rstrip("."))


def _net(v):
    if v is None:
        return '<span class="zero">&mdash;</span>'
    cls = "pos" if v >= 0 else "neg"
    return '<span class="%s">%s</span>' % (cls, "%.0f" % v)


def _diff(v):
    if v is None:
        return '<span class="zero">&mdash;</span>'
    if v == 0:
        return '<span class="pos">0</span>'
    cls = "pos" if v > 0 else "neg"
    return '<span class="%s">%s%.0f</span>' % (cls, "+" if v > 0 else "", v)


def render_html(ym, rows, problems, pot_total, embed=False):
    parts = []
    if not embed:
        parts.append("<!doctype html><meta charset='utf-8'><style>%s</style>" % _CSS)
    parts.append("<h1>Register salary &mdash; %s <span class='pill'>standalone</span></h1>"
                 % html.escape(ym))
    parts.append("<p class='sub'>The register computes the whole month itself "
                 "(base + attendance + register grid + ledger money). The old ledger "
                 "net is shown as a <b>shadow</b> for parity; this screen writes nothing.</p>")
    for p in problems:
        parts.append("<div class='warn'>%s</div>" % html.escape(p))
    if not rows:
        parts.append("<p class='note'>No staff to show.</p>")
        return "\n".join(parts)

    old_t, new_t, dlt, all_shadow = shadow_summary(rows)
    if all_shadow:
        cls = "ok" if dlt == 0 else "warn"
        parts.append("<div class='%s'>Parity headline &mdash; new total <b>%s</b> vs "
                     "old total <b>%s</b>; difference <b>%+d</b>. Incentive moved to "
                     "the annual pot this month totals <b>%s</b> (so for a month with "
                     "no register rows, new + pot should equal old). Every remaining "
                     "rupee of difference must be explainable line-by-line before "
                     "locking.</div>" % (cls, "{:,.0f}".format(new_t),
                     "{:,.0f}".format(old_t), int(dlt), "{:,.2f}".format(pot_total)))
    else:
        parts.append("<div class='note'>Old-model shadow not fully available &mdash; "
                     "parity headline hidden. Incentive&rarr;pot this month totals "
                     "<b>%s</b>.</div>" % "{:,.2f}".format(pot_total))

    parts.append("<table><thead><tr>")
    for cls, label, _ in _COLS:
        parts.append("<th class='%s'>%s</th>" % (cls, html.escape(label)))
    parts.append("</tr></thead><tbody>")
    tot = {k: 0.0 for k in _SUMKEYS}
    net_tot = 0.0
    net_all = True
    for r in rows:
        parts.append("<tr>")
        for cls, _, key in _COLS:
            if key == "name":
                cov = "" if r.get("covered") else " <span class='pill'>no grid</span>"
                parts.append("<td class='nm'>%s%s</td>" % (html.escape(r["name"]), cov))
            elif key == "base":
                parts.append("<td>%d</td>" % int(r["base"]))
            elif key in ("att_absent", "genuine_absent"):
                parts.append("<td>%d</td>" % r[key])
            elif key == "_leave":
                extra = ""
                if r["fest_over"]:
                    extra = " <span class='pill'>fest over %d</span>" % r["fest_over"]
                elif r["extra_days"]:
                    extra = " <span class='pill'>%d over</span>" % r["extra_days"]
                parts.append("<td>%d / %d%s</td>" % (r["disc_used"], r["fest_used"], extra))
            elif key == "final_net":
                v = r.get("final_net")
                if v is None:
                    net_all = False
                else:
                    net_tot += v
                parts.append("<td><b>%s</b></td>" % _net(v))
            elif key == "shadow_net":
                parts.append("<td>%s</td>" % _net(r.get("shadow_net")))
            elif key == "shadow_diff":
                parts.append("<td>%s</td>" % _diff(r.get("shadow_diff")))
            elif key == "ledger_fold":
                parts.append("<td>%s</td>" % _money(round(r.get("ledger_fold", 0.0), 2)))
            else:
                v = r.get(key, 0.0)
                if key in tot:
                    tot[key] += v
                shown = -v if key in _NEG_COLS else v
                parts.append("<td>%s</td>" % _money(round(shown, 2)))
        parts.append("</tr>")

    # totals row
    parts.append("<tr class='tot'><td class='nm'>TOTAL</td><td></td><td></td><td></td><td></td>")
    for cls, _, key in _COLS[5:]:
        if key == "final_net":
            parts.append("<td><b>%s</b></td>" % (_net(round(net_tot, 0)) if net_all
                                                 else _net(None)))
        elif key == "shadow_net":
            o, n, d, ok = shadow_summary(rows)
            parts.append("<td>%s</td>" % (_net(round(o, 0)) if ok else _net(None)))
        elif key == "shadow_diff":
            o, n, d, ok = shadow_summary(rows)
            parts.append("<td>%s</td>" % (_diff(round(d, 0)) if ok else _diff(None)))
        elif key == "ledger_fold":
            parts.append("<td>%s</td>" % _money(round(tot.get("ledger_fold", 0.0), 2)))
        else:
            v = tot.get(key, 0.0)
            shown = -v if key in _NEG_COLS else v
            parts.append("<td>%s</td>" % _money(round(shown, 2)))
    parts.append("</tr></tbody></table>")
    parts.append("<p class='note'>NET (new) is the standalone take-home the register "
                 "computes and will lock: base + attendance (marks / early / uninformed / "
                 "excess-absence, outstation-adjusted / early-big) + register grid "
                 "(extra-duty / outstation / dress / i-card / C-model absences &amp; "
                 "encashment) + the ledger money fold (night-duty / ad-hoc fine / i-card "
                 "replacement / advance instalment / loan interest / other &mdash; "
                 "uniform, i-card and leave excluded because the register grid owns "
                 "them). Overtime is removed. Incentive is out of the month and accrues "
                 "to the annual pot (paid the following Diwali). <b>Old (shadow)</b> is "
                 "the ledger's current-model net; the <b>Delta</b> column must be fully "
                 "explained before APPROVE &amp; LOCK.</p>")
    return "\n".join(parts)


# ---------------------------------------------------------- early-big screen --
def earlybig_unruled(events, verdicts):
    """How many of this month's early-big events have no register verdict yet.
    An un-ruled event WAIVES by default (matches the ledger), so this count is a
    'please look' signal, surfaced on the salary page."""
    n = 0
    for e in (events or []):
        if ("%s|%s" % (e["name"], e["date"])) not in verdicts:
            n += 1
    return n


def render_earlybig_html(ym, events, verdicts, locked, prefix, embed=True):
    """The doctor's big early-exit ruling screen for one month. `events` from
    earlybig_events(); `verdicts` from load_register_earlybig() ({key: bool}).
    Genuine = deduct the shown rupees; default / waived = no deduction. When the
    month's salary run is LOCKED the screen is read-only. The register app owns
    the POST + write; this only draws the form."""
    parts = []
    if not embed:
        parts.append("<!doctype html><meta charset='utf-8'><style>%s</style>" % _CSS)
    parts.append("<h1>Big early-exit rulings &mdash; %s</h1>" % html.escape(ym))
    parts.append("<p class='sub'>Each big early departure is <b>waived</b> unless you "
                 "rule it <b>genuine</b> against the physical register. Only genuine "
                 "exits deduct. This is the register's own record &mdash; it replaces "
                 "the old ledger ruling screen.</p>")
    if events is None:
        parts.append("<div class='warn'>Could not read the early-exit list for %s "
                     "(deductions_extras_%s.csv missing or its note format changed). "
                     "Run the attendance report, then reload.</div>"
                     % (html.escape(ym), html.escape(ym)))
        return "\n".join(parts)
    if not events:
        parts.append("<div class='ok'>No big early exits recorded this month. "
                     "Nothing to rule.</div>")
        return "\n".join(parts)
    unruled = earlybig_unruled(events, verdicts)
    if locked:
        parts.append("<div class='warn'>The %s salary run is LOCKED &mdash; rulings "
                     "are read-only. Unlock the run (doctor-only) to change them.</div>"
                     % html.escape(ym))
    elif unruled:
        parts.append("<div class='warn'>%d event(s) not yet ruled &mdash; each stays "
                     "<b>waived</b> (no deduction) until you decide.</div>" % unruled)
    else:
        parts.append("<div class='ok'>Every event has a ruling. Nothing pending.</div>")

    if not locked:
        parts.append("<form method='post' action='%s/salary/earlybig'>" % html.escape(prefix))
        parts.append("<input type='hidden' name='ym' value='%s'>" % html.escape(ym))
    parts.append("<table><thead><tr><th class='nm'>Staff</th><th>Date</th>"
                 "<th>Early by</th><th>Would deduct</th><th>Ruling</th>"
                 "</tr></thead><tbody>")
    for e in events:
        key = "%s|%s" % (e["name"], e["date"])
        g = verdicts.get(key)                       # True / False / None(un-ruled)
        amt = ("%.2f" % float(e.get("rs") or 0)).rstrip("0").rstrip(".")
        if locked:
            state = ("GENUINE &mdash; deducted" if g
                     else ("waived" if g is False else "un-ruled (waived)"))
            cell = "<b>%s</b>" % state
        else:
            gsel = " selected" if g else ""
            wsel = "" if g else " selected"          # default + explicit-waive both show waived
            cell = ("<select name='eb_%s'>"
                    "<option value='waived'%s>waived &mdash; no deduction</option>"
                    "<option value='genuine'%s>genuine &mdash; deduct Rs %s</option>"
                    "</select>") % (html.escape(key), wsel, gsel, amt)
        parts.append("<tr><td class='nm'>%s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td><td>%s</td></tr>"
                     % (html.escape(e["name"]), html.escape(e["date"]),
                        html.escape(str(e.get("minutes", ""))), amt, cell))
    parts.append("</tbody></table>")
    if not locked:
        parts.append("<p><button class='pill' type='submit' "
                     "style='padding:8px 16px;font-size:14px'>Save rulings</button> "
                     "<a class='pill' href='%s/salary?ym=%s' "
                     "style='padding:8px 16px'>&larr; Back to salary</a></p></form>"
                     % (html.escape(prefix), html.escape(ym)))
    return "\n".join(parts)


# ---------------------------------------------------------------- selftest ---
def _selftest():
    import tempfile
    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "t.db")
    con = sqlite3.connect(dbp)
    con.executescript("""
      CREATE TABLE staff(staff_id INTEGER PRIMARY KEY, name TEXT, join_date TEXT,
        last_working TEXT, base_salary INTEGER, minutes_exempt INTEGER DEFAULT 0,
        cover_eligible INTEGER DEFAULT 0, outstation_eligible INTEGER DEFAULT 0);
      CREATE TABLE daily_register(id INTEGER PRIMARY KEY, reg_date TEXT, staff_id INTEGER,
        absence_type TEXT, leave_kind TEXT, late_flag TEXT, late_approved_by TEXT,
        dress_improper INTEGER DEFAULT 0, icard_missing INTEGER DEFAULT 0,
        outstation_nights INTEGER DEFAULT 0, extra_duty INTEGER DEFAULT 0,
        ot_permitted INTEGER DEFAULT 0);
      CREATE TABLE festival_day(fest_date TEXT PRIMARY KEY, name TEXT, clinic_closed INTEGER DEFAULT 0);
    """)
    # base 30000 -> day 1000
    con.execute("INSERT INTO staff VALUES(1,'Tester','2000-01-01',NULL,30000,0,1,1)")
    con.execute("INSERT INTO staff VALUES(2,'Clean','2000-01-01',NULL,30000,0,0,0)")
    con.execute("INSERT INTO staff VALUES(3,'July','2000-01-01',NULL,30000,0,0,0)")
    con.commit(); con.close()

    def att_csv(dirp, ym, rows):
        with open(os.path.join(dirp, "salary_inputs_%s.csv" % ym), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Ded: marks Rs", "Ded: early-dep Rs",
                        "Fine: uninformed Rs", "Fine: excess-absent Rs",
                        "OT candidate Rs", "Incentive", "Incentive Rs",
                        "Absent", "Absent dates"])
            for r in rows:
                w.writerow(r)

    # ---- CASE A: AUGUST, register COVERED -----------------------------------
    con = sqlite3.connect(dbp)
    # Tester: 1 discretionary leave (05, no-punch), 2 genuine absents (12,13),
    # 1 dress + 1 i-card (15), 2 extra-duty (16,17), 3 outstation nights (06).
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-08-05',1,'discretionary','leave_sanctioned')")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,dress_improper,icard_missing) "
                "VALUES('2026-08-15',1,1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,extra_duty) VALUES('2026-08-16',1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,extra_duty) VALUES('2026-08-17',1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,outstation_nights) VALUES('2026-08-06',1,3)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-08-05',2,'discretionary','leave_sanctioned')")
    con.commit(); con.close()

    att_csv(tmp, "2026-08", [
        # Tester att-absent = leave(05)+outstation(06,07,08)+genuine(12,13)=6
        ["Tester", "0", "0", "0", "300", "0", "FULL", "1000", "6",
         "2026-08-05 2026-08-06 2026-08-07 2026-08-08 2026-08-12 2026-08-13"],
        ["Clean",  "0", "0", "0", "0",   "0", "FULL", "1000", "1", "2026-08-05"],
    ])
    # ledger money for Aug: Tester night-duty +200, ad-hoc fine -100
    aug_led = [
        {"staff": "Tester", "category": "NIGHT_DUTY", "amount": 200,
         "status": "APPROVED", "closed_month": "2026-08"},
        {"staff": "Tester", "category": "FINE_ADHOC", "amount": -100,
         "status": "APPROVED", "closed_month": "2026-08"},
        {"staff": "Tester", "category": "PERK", "amount": 5000,
         "status": "APPROVED", "closed_month": "2026-08"},   # excluded -> ignored
    ]
    rows, problems, pot = build_report(
        "2026-08", db_path=dbp, att_dir=tmp, ledger_rows=aug_led,
        rulings={"earlybig": {}, "ot": {}, "outstation": {}}, earlybig=[], bases={})
    problems = [p for p in problems if "shadow" not in p]   # ledger not imported here
    assert not problems, problems
    r = {x["name"]: x for x in rows}
    t = r["Tester"]
    assert t["covered"] is True
    assert t["day_rate"] == 1000.0
    # genuine = 6 - 1(leave) - 3(outstation grid) = 2 ; C = 1 + 2 = 3 ; extra 1 -> -1000
    assert t["genuine_absent"] == 2 and t["C"] == 3
    assert t["extra_days"] == 1 and t["base30_ded"] == 1000.0
    assert t["encash_rs"] == 0.0                       # a deductible day forfeits encash
    assert t["dress_rs"] == 20.0 and t["icard_rs"] == 20.0
    assert t["extra_rs"] == 400.0 and t["outst_rs"] == 750.0
    assert t["ledger_fold"] == 100.0                   # +200 night - 100 adhoc (perk excluded)
    assert t["incentive_pot"] == 1000.0                # out of the month
    # net = 30000 +400 +750 -20 -20 -1000(base30) +0(encash) +100(fold) = 30210
    assert t["final_net"] == 30210, t["final_net"]
    # Clean: 1 leave, 0 genuine -> C=1 -> encash (2-1)=1 day=1000; net=30000+1000
    c = r["Clean"]
    assert c["encash_rs"] == 1000.0 and c["final_net"] == 31000, c["final_net"]
    total, complete = total_payout(rows)
    assert complete and total == 30210 + 31000

    # ---- CASE B: JULY, register NOT covered (no grid rows) -------------------
    # uniform/i-card live in the LEDGER; C-model must NOT apply; conservation holds.
    att_csv(tmp, "2026-07", [
        # July: 4 absents -> excess-absence fine already = (4-3)*100 = 100 in the CSV
        ["July", "0", "0", "0", "100", "0", "FULL", "800", "4",
         "2026-07-10 2026-07-11 2026-07-12 2026-07-13"],
    ])
    jul_led = [
        {"staff": "July", "category": "FINE_UNIFORM", "amount": -40,
         "status": "APPROVED", "closed_month": "2026-07"},   # 2 dress fines
        {"staff": "July", "category": "FINE_ICARD", "amount": -20,
         "status": "APPROVED", "closed_month": "2026-07"},   # 1 i-card fine
        {"staff": "July", "category": "NIGHT_DUTY", "amount": 200,
         "status": "APPROVED", "closed_month": "2026-07"},
    ]
    rows2, prob2, pot2 = build_report(
        "2026-07", db_path=dbp, att_dir=tmp, ledger_rows=jul_led,
        rulings={"earlybig": {}, "ot": {}, "outstation": {}}, earlybig=[], bases={})
    prob2 = [p for p in prob2 if "shadow" not in p]
    assert not prob2, prob2
    j = {x["name"]: x for x in rows2}["July"]
    assert j["covered"] is False
    assert j["base30_ded"] == 0.0 and j["encash_rs"] == 0.0     # C-model gated OFF
    assert j["dress_rs"] == 40.0 and j["icard_rs"] == 20.0      # from the LEDGER (rule 2)
    assert j["ledger_fold"] == 200.0                            # only night-duty; uic excluded
    assert j["incentive_pot"] == 800.0
    # net = 800base... no: base 30000 - fine_exc 100 - dress 40 - icard 20 + fold 200 = 30040
    assert j["final_net"] == 30040, j["final_net"]

    # CONSERVATION: reconstruct the OLD ledger net by hand for July and check
    #   new_net + incentive_pot == old_net.  Old (compute_salary): base + inc + adj_cr
    #   - fine_exc - adj_db.  adj here: +200 night, -40 dress, -20 icard -> cr 200, db 60.
    old_net = 30000 + 800 + 200 - 100 - 60           # = 30840
    assert j["final_net"] + j["incentive_pot"] == old_net, (j["final_net"], old_net)

    # ---- CASE C: ledger unreachable -> incomplete, unlockable ---------------
    rows3, prob3, _ = build_report(
        "2026-08", db_path=dbp, att_dir=tmp, ledger_rows=None,
        rulings={"earlybig": {}, "ot": {}, "outstation": {}}, earlybig=[], bases={})
    # with no live ledger importable in the sandbox, fold is None -> nets incomplete
    if any("could not be read" in p for p in prob3):
        _t, comp = total_payout(rows3)
        assert comp is False
        assert all(x["final_net"] is None for x in rows3)

    # ---- CASE D: register-owned EARLY-BIG rulings ---------------------------
    # events come straight from deductions_extras_<ym>.csv; register verdicts
    # overlay the base per key and drive the deduction.
    with open(os.path.join(tmp, "deductions_extras_2026-08.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Tester", "2026-08-12", "EARLY_BIG", "219 min", 0.0,
                    "left early, would be Rs.219.0 if confirmed"])
        w.writerow(["Tester", "2026-08-20", "EARLY_BIG", "100 min", 0.0,
                    "left early, would be Rs.100.0 if confirmed"])
        w.writerow(["Clean", "2026-08-05", "OTHER", "x", 0.0, "not an early-big row"])
    evs = earlybig_events("2026-08", tmp)
    assert len(evs) == 2 and evs[0]["rs"] == 219.0 and evs[1]["rs"] == 100.0, evs
    # fail-loud on a mangled note (never silently waive a real deduction)
    with open(os.path.join(tmp, "deductions_extras_2026-09.csv"), "w", newline="") as f:
        csv.writer(f).writerow(["Tester", "2026-09-01", "EARLY_BIG", "90 min", 0.0,
                                "format drifted"])
    try:
        earlybig_events("2026-09", tmp); assert False, "mangled note must fail loud"
    except ValueError:
        pass

    con = sqlite3.connect(dbp)
    con.executescript(EARLYBIG_SCHEMA)
    con.execute("INSERT INTO earlybig_ruling(ym,staff,ebdate,verdict,ruled_by,ruled_ts)"
                " VALUES('2026-08','Tester','2026-08-12','genuine','manoj','t')")
    con.execute("INSERT INTO earlybig_ruling(ym,staff,ebdate,verdict,ruled_by,ruled_ts)"
                " VALUES('2026-08','Tester','2026-08-20','waived','manoj','t')")
    con.commit(); con.close()
    v = load_register_earlybig("2026-08", dbp)
    assert v == {"Tester|2026-08-12": True, "Tester|2026-08-20": False}, v
    # overlay: register verdict WINS over the base per key; base-only keys survive
    merged = _rulings_for("2026-08", {"earlybig": {
        "Tester|2026-08-20": {"genuine": True}, "Zzz|2026-08-01": {"genuine": True}},
        "ot": {}, "outstation": {}}, db_path=dbp)["earlybig"]
    assert merged["Tester|2026-08-12"]["genuine"] is True    # from register
    assert merged["Tester|2026-08-20"]["genuine"] is False   # register overrode base
    assert merged["Zzz|2026-08-01"]["genuine"] is True       # base kept
    # end-to-end: Tester now loses the genuine (219) exit but not the waived (100)
    rows4, prob4, _ = build_report(
        "2026-08", db_path=dbp, att_dir=tmp, ledger_rows=aug_led,
        rulings=None, earlybig=None, bases=None)
    t4 = {x["name"]: x for x in rows4}["Tester"]
    assert t4["early_big"] == 219.0 and t4["final_net"] == 30210 - 219, \
        (t4["early_big"], t4["final_net"])
    # ruling-screen render (editable + locked)
    heb = render_earlybig_html("2026-08", evs, v, False, "/register")
    assert "genuine" in heb and "Save rulings" in heb and "2026-08-12" in heb
    hebL = render_earlybig_html("2026-08", evs, v, True, "/register")
    assert "LOCKED" in hebL and "Save rulings" not in hebL
    assert "Nothing to rule" in render_earlybig_html("2026-08", [], {}, False, "/register")

    # ---- render smoke (must survive missing shadow) -------------------------
    h = render_html("2026-08", rows, [p for p in problems], pot)
    assert "standalone" in h and "Tester" in h and "NET (new)" in h and "Old (shadow)" in h

    print("SELFTEST OK -- standalone net (attendance + grid C-model + ledger fold), "
          "OT removed, incentive->pot, uniform/i-card per-month source, C-model gated "
          "on coverage, ledger-fold excludes uniform/i-card, JULY CONSERVATION "
          "(new + pot == old), fold-excluded PERK, incomplete-when-ledger-absent, "
          "register-owned EARLY-BIG (events parse + fail-loud, verdict overlay wins, "
          "deducts per register ruling, screen render), html render.")


# --------------------------------------------------------------------- cli ---
def _cli():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        _selftest()
        return
    if len(sys.argv) < 2:
        print("usage: salary_engine.py YYYY-MM   |   --selftest")
        sys.exit(2)
    ym = sys.argv[1]
    rows, problems, pot = build_report(ym)
    out = os.path.join(BASE, "register_salary_%s.html" % ym)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_html(ym, rows, problems, pot))
    os.chmod(out, 0o600)
    # F-31: never print rupee values to the console
    print("wrote %s  (%d staff, %d problem(s))" % (out, len(rows), len(problems)))
    for p in problems:
        print("  problem:", p)


if __name__ == "__main__":
    _cli()
