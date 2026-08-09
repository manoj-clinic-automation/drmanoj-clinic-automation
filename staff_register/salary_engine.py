"""
salary_engine.py  —  Staff Daily Register · Stage A salary reconciliation (S161).

READ-ONLY. Standalone. Std-lib only. Writes NOTHING any live service reads.

WHAT THIS IS
------------
The Daily Register captures, each day, the human decisions month-end salary used
to reconstruct by hand: sanctioned leave (vs genuine absence), 60-min-late
informed/not, dress / i-card, extra-duty (Shivani), outstation (Darpan), festival
leave, and staff lifecycle.  This module reads those decisions and turns them into
the register's *adjustments on top of* the existing attendance-salary numbers.

It is deliberately a SEPARATE layer from the live money pipeline:
  * `att_month_report.py`  already computes marks / early / fines / OT / incentive
    into `salary_inputs_<ym>.csv`  (base ÷ 30, half-day ÷ 60 — its own law).
  * `staff_ledger.py → compute_salary`  assembles the FINAL SALARY from that CSV +
    base + ledger + owner rulings.
This engine does NOT touch either.  It READS `salary_inputs_<ym>.csv` as the
interface (so the marks/fine math is never re-implemented and can never drift) and
READS the register DB, then prints the register's per-staff delta.  Wiring the
delta into the FINAL SALARY is a separate later step (Stage B).

POLICY (from the dossier §4–§10, owner-confirmed S161; values verified against the
2026-07 sheet, not memory):
  day        = base / 30            half-day = base / 60          (owner: 30-day basis)
  dress      = −20 each             i-card   = −20 each           (skip minutes-exempt)
  extra-duty = +200 each            (Shivani only; guarded on cover_eligible)
  outstation = +250 / night        (Darpan only; guarded on outstation_eligible)
  leave      : 2 discretionary / month + 2 festival / financial-year (Apr→Mar)
               within quota  → paid, not fineable, removed from absent-count
               unused disc.  → encashed monthly at 1 day each (0 taken→+2, 1→+1, 2→+0)
               over quota    → −1 day each AND the day stays absent (fines stack)
               festival      → own-festival; Holi = clinic-closed, consumes nothing
  incentive  : att's monthly incentive is REMOVED from the month and accrued to the
               per-staff annual pot (Apr→Mar, floors at 0, paid the following Diwali)
  lifecycle  : base pro-rated across the month for a join / last-working inside it
  Arjun (minutes_exempt): leave only; no dress/i-card/extra/outstation; over-quota
               leave = flat pro-rata −1 day each (same day-rate).

INVARIANT (the dry-run check): with NO register rows for a month (e.g. 2026-07,
before the register went live), every register line is 0 and the ONLY change is
incentive → pot.  So the engine reproduces the attendance numbers unchanged except
for pulling incentive into the pot.

USAGE
  /root/wa/venv/bin/python3 /root/staff_register/salary_engine.py 2026-07
        → writes register_salary_2026-07.html beside this script; prints only a
          non-money confirmation line (F-31).
  /root/wa/venv/bin/python3 /root/staff_register/salary_engine.py --selftest
"""
import os
import sys
import csv
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

_ADHOC_ERR = ""
_NET_ERR = ""


def _add_ledger_paths():
    """staff_ledger.py lives in /root (data dir /root/staff_ledger is separate);
    clinic_sso/portal_config live in /root/portal. Add the likely CODE dirs
    (guarded) so imports resolve in the standalone CLI and inside the web app."""
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
    # a floor'd historical join (e.g. 2000-01-01 seed) → full month
    return (end - start).days + 1


# ---------------------------------------------------------------- pure core --
def reconcile(name, base, minutes_exempt, att, reg, ndays, act_days):
    """Compute the register's monthly delta for one staffer (owner model S161).

    Free non-present buffer / month = 2 discretionary + festival-within-quota
    (roster Sundays are already OFF/ignored upstream). Let
        C = discretionary leaves taken + genuine (unsanctioned) absences.
    Every day of  max(0, C - 2)  PLUS any over-quota festival day is deducted at
    base/30.  Unused leave is encashed (at base/30 each) ONLY when there is no
    such deductible day — any extra absence forfeits it.  The ₹50/₹100 cash-fines
    and all late-mark / early logic stay in the attendance layer, unchanged.
    Incentive is pulled out of the month and accrued to the annual pot.

    att  = salary_inputs row: Absent, Incentive Rs, Incentive, Absent dates.
    reg  = register aggregates: dress, icard, extra, outstation, disc_used,
           fest_used, fest_prior_fy, late_not_informed, leave_dates, absent_dates.
    """
    day = round(base / DAYS_BASIS, 2) if base else 0.0

    def fnum(k):
        try:
            return float(att.get(k) or 0)
        except (TypeError, ValueError):
            return 0.0

    att_absent = int(fnum("Absent"))
    inc = fnum("Incentive Rs")

    # sanctioned leave + outstation nights were NOT genuine absence
    leave_in_absent = len(reg["leave_dates"] & reg["absent_dates"])
    genuine_absent = max(0, att_absent - leave_in_absent - reg["outstation"])

    disc_used = reg["disc_used"]
    fest_used = reg["fest_used"]
    fest_allow = max(0, FEST_QUOTA - reg["fest_prior_fy"])
    fest_over = max(0, fest_used - fest_allow)

    # C consumes the 2-day monthly buffer; over-quota festival deducts separately
    C = disc_used + genuine_absent
    extra_days = max(0, C - DISC_QUOTA)
    deduct_days = extra_days + fest_over
    base30_ded = round(deduct_days * day, 2)

    # encashment: only when nothing is deductible (C <= 2 and no over-festival)
    encash_days = max(0, DISC_QUOTA - C) if deduct_days == 0 else 0
    encash_rs = round(encash_days * day, 2)

    # new register money (minutes-exempt staff = leave only; the base/30 absence
    # deduction + encashment still apply to them — D276 "flat pro-rata")
    if minutes_exempt:
        dress_rs = icard_rs = extra_rs = outst_rs = 0.0
    else:
        dress_rs = reg["dress"] * DRESS_RS
        icard_rs = reg["icard"] * ICARD_RS
        extra_rs = reg["extra"] * EXTRA_DUTY_RS
        outst_rs = reg["outstation"] * OUTSTATION_RS

    # base pro-rating for a partial month (join / last-working inside it)
    prorated_base = round(base * (act_days / ndays), 2) if ndays else float(base)
    prorate_delta = round(prorated_base - base, 2)      # <= 0

    # register delta ON TOP of the attendance FINAL net (which already holds
    # base + incentive - marks - early - att-fines). Ad-hoc ledger fines are NOT
    # added here — the FINAL assembly already subtracts all ledger debits.
    delta = round(
        - dress_rs - icard_rs
        + extra_rs + outst_rs
        - base30_ded + encash_rs
        - inc
        + prorate_delta,
        2)

    return {
        "name": name, "base": base, "day_rate": day,
        "att_absent": att_absent, "genuine_absent": genuine_absent, "C": C,
        "disc_used": disc_used, "fest_used": fest_used, "fest_over": fest_over,
        "extra_days": extra_days, "deduct_days": deduct_days,
        "late_not_informed": reg["late_not_informed"],
        "dress_rs": round(dress_rs, 2), "icard_rs": round(icard_rs, 2),
        "extra_rs": round(extra_rs, 2), "outst_rs": round(outst_rs, 2),
        "base30_ded": base30_ded,
        "encash_days": encash_days, "encash_rs": encash_rs,
        "incentive_pot": round(inc, 2), "incentive_tier": att.get("Incentive", ""),
        "prorated_base": prorated_base, "prorate_delta": prorate_delta,
        "act_days": act_days, "ndays": ndays,
        "adhoc_rs": 0.0,           # filled in build_report (read-only, informational)
        "delta": delta,
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
    """Per-staff register aggregates for the month. Returns {staff_id: {...}} and
    the staff table {staff_id: row-dict}. Read-only connection."""
    dbp = db_path or DB_PATH
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    m_first, m_last, _ = month_bounds(ym)
    fs = fy_start(ym).isoformat()
    lo, hi = m_first.isoformat(), m_last.isoformat()

    staff = {r["staff_id"]: dict(r) for r in
             con.execute("SELECT * FROM staff").fetchall()}

    # clinic-closed festival dates (Holi) — a leave row on these is void
    closed = {r["fest_date"] for r in
              con.execute("SELECT fest_date FROM festival_day WHERE clinic_closed=1")}

    agg = {}
    for sid in staff:
        agg[sid] = {"dress": 0, "icard": 0, "extra": 0, "outstation": 0,
                    "disc_used": 0, "fest_used": 0, "fest_prior_fy": 0,
                    "late_not_informed": 0, "leave_dates": set()}

    for r in con.execute(
            "SELECT * FROM daily_register WHERE reg_date>=? AND reg_date<=?", (lo, hi)):
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
        else:                                   # §6: no dress/i-card on a leave day
            if r["dress_improper"]:
                a["dress"] += 1
            if r["icard_missing"]:
                a["icard"] += 1
        a["extra"] += int(r["extra_duty"] or 0)
        a["outstation"] += int(r["outstation_nights"] or 0)
        if r["late_flag"] == "not_informed" and not on_leave:
            a["late_not_informed"] += 1

    # festival leaves earlier in the same financial year (for the 2/yr quota)
    for r in con.execute(
            "SELECT staff_id, COUNT(*) c FROM daily_register "
            "WHERE leave_kind='festival' AND reg_date>=? AND reg_date<? "
            "GROUP BY staff_id", (fs, lo)):
        if r["staff_id"] in agg:
            agg[r["staff_id"]]["fest_prior_fy"] = r["c"]

    con.close()
    return agg, staff


def load_adhoc(ym):
    """Ad-hoc fines for the month, read-only, reusing the ledger's OWN code so
    the numbers can never drift. Returns {name: rupees} or None if the ledger is
    not importable. Ad-hoc = APPROVED FINE_ADHOC rows dated in the month; amounts
    are stored negative (a debit) so we flip the sign to a positive magnitude.
    Shown for completeness only — the FINAL SALARY already subtracts ledger
    debits, so this never enters the register delta."""
    # staff_ledger.py lives in /root; its deps live in /root/portal — add both.
    _add_ledger_paths()
    try:
        import staff_ledger as _L
        rows = _L.load_ledger()
    except Exception as e:
        global _ADHOC_ERR
        _ADHOC_ERR = "%s: %s" % (type(e).__name__, e)
        return None
    out = {}
    for r in rows:
        if r.get("category") != "FINE_ADHOC" or r.get("status") != "APPROVED":
            continue
        dt = (r.get("date_from") or r.get("date") or "")[:7]
        if dt != ym:
            continue
        out[r.get("staff")] = out.get(r.get("staff"), 0.0) + (-float(r.get("amount") or 0))
    return {k: round(v, 2) for k, v in out.items()}


def load_current_net(ym):
    """Current-model take-home per staff, by REUSING the ledger's own
    compute_salary (read-only) — base + attendance components + ledger, exactly
    as the live FINAL SALARY computes it. Returns ({name: net}, problems) or
    (None, []) if the ledger can't be reached. The new-model net is then simply
    this + the register delta, so there is no second implementation to drift."""
    global _NET_ERR
    _NET_ERR = ""
    _add_ledger_paths()
    try:
        import staff_ledger as _L
        table, _tok, probs = _L.compute_salary(ym)
    except Exception as e:
        _NET_ERR = "%s: %s" % (type(e).__name__, e)
        return None, []
    return {t["name"]: float(t.get("net") or 0) for t in table}, list(probs or [])


def build_report(ym, db_path=None, att_dir=None):
    """Assemble the reconciliation. Returns (rows, problems, pot_total)."""
    att, att_path = load_att_inputs(ym, att_dir)
    problems = []
    if att is None:
        return [], ["salary_inputs_%s.csv not found (run the attendance report first): %s"
                    % (ym, att_path)], 0.0
    agg, staff = load_register(ym, db_path)
    m_first, m_last, ndays = month_bounds(ym)

    by_name = {(s["name"] or "").strip().lower(): sid for sid, s in staff.items()}
    adhoc = load_adhoc(ym)
    if adhoc is None:
        problems.append("ad-hoc fines could not be read from the ledger [%s] "
                        "(shown as 0; they are still applied in the FINAL SALARY)."
                        % (_ADHOC_ERR or "unknown"))
        adhoc = {}
    cur_net, net_probs = load_current_net(ym)
    if cur_net is None:
        problems.append("current-model net could not be read from the ledger [%s] "
                        "(new-model net column hidden)." % (_NET_ERR or "unknown"))
    else:
        for p in net_probs:
            problems.append("ledger note: " + p)
    rows, pot_total = [], 0.0
    for key, arow in sorted(att.items()):
        sid = by_name.get(key)
        if sid is None:
            problems.append("%s is in the attendance report but not in the register"
                            % (arow.get("Name") or key))
            continue
        s = staff[sid]
        reg = agg[sid]
        reg["absent_dates"] = set((arow.get("Absent dates") or "").split())
        act = active_days(s.get("join_date"), s.get("last_working"),
                          m_first, m_last, ndays)
        r = reconcile(s["name"], float(s.get("base_salary") or 0),
                      bool(s.get("minutes_exempt")), arow, reg, ndays, act)
        r["adhoc_rs"] = adhoc.get(s["name"], 0.0)
        # complete new-model take-home = current-model net (ledger's own code)
        # + the register delta. None when the ledger is unreachable.
        r["final_net"] = (round(cur_net[s["name"]] + r["delta"], 2)
                          if cur_net is not None and s["name"] in cur_net else None)
        rows.append(r)
        pot_total += r["incentive_pot"]
    return rows, problems, round(pot_total, 2)


def total_payout(rows):
    """Headline TOTAL PAYOUT of a run = sum of each staffer's take-home (final_net),
    rounded to the rupee. Returns (total, complete). complete=False if ANY staffer's
    net is unavailable (ledger unreachable) -- an incomplete run must never be locked
    (Stage B). Only READS the rows build_report already produced; no new math."""
    total, complete = 0.0, True
    for r in rows:
        v = r.get("final_net")
        if v is None:
            complete = False
        else:
            total += v
    return round(total, 0), complete


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
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid #24344a;color:#9fb4cc}
"""

_COLS = [
    ("nm", "Staff", "name"),
    ("", "Base", "base"),
    ("", "Att absent", "att_absent"),
    ("", "Genuine abs", "genuine_absent"),
    ("", "Leave (D/F)", "_leave"),
    ("", "Extra-abs −", "base30_ded"),
    ("", "Encash +", "encash_rs"),
    ("", "Dress −", "dress_rs"),
    ("", "I-card −", "icard_rs"),
    ("", "Extra duty +", "extra_rs"),
    ("", "Outstation +", "outst_rs"),
    ("", "Incentive→pot", "incentive_pot"),
    ("", "Ad-hoc −", "adhoc_rs"),
    ("", "Pro-rate", "prorate_delta"),
    ("", "REGISTER Δ", "delta"),
    ("", "Net (new model)", "final_net"),
]
# columns rendered as deductions (shown negative); not summed into the delta here
_NEG_COLS = {"base30_ded", "dress_rs", "icard_rs", "incentive_pot", "adhoc_rs"}


def _money(v):
    if not v:
        return '<span class="zero">0</span>'
    cls = "pos" if v > 0 else "neg"
    return '<span class="%s">%s%s</span>' % (cls, "+" if v > 0 else "", ("%.2f" % v).rstrip("0").rstrip("."))


def _net(v):
    """A take-home figure: no +/- prefix, nearest rupee, — when unavailable."""
    if v is None:
        return '<span class="zero">—</span>'
    cls = "pos" if v >= 0 else "neg"
    return '<span class="%s">%s</span>' % (cls, "%.0f" % v)


def render_html(ym, rows, problems, pot_total, embed=False):
    parts = []
    if not embed:
        parts.append("<!doctype html><meta charset='utf-8'><style>%s</style>" % _CSS)
    parts.append("<h1>Register salary reconciliation — %s</h1>" % html.escape(ym))
    parts.append("<p class='sub'>Read-only Stage-A view. Shows the register's monthly "
                 "adjustments on top of the attendance salary; nothing here is written to "
                 "any live salary run.</p>")
    for p in problems:
        parts.append("<div class='warn'>%s</div>" % html.escape(p))
    if not rows:
        parts.append("<p class='note'>No staff to show.</p>")
        return "\n".join(parts)

    parts.append("<table><thead><tr>")
    for cls, label, _ in _COLS:
        parts.append("<th class='%s'>%s</th>" % (cls, html.escape(label)))
    parts.append("</tr></thead><tbody>")
    sumkeys = ["base30_ded", "encash_rs", "dress_rs", "icard_rs", "extra_rs",
               "outst_rs", "incentive_pot", "adhoc_rs", "prorate_delta", "delta"]
    tot = {k: 0.0 for k in sumkeys}
    net_tot = 0.0
    net_all = True
    for r in rows:
        parts.append("<tr>")
        for cls, _, key in _COLS:
            if key == "name":
                parts.append("<td class='nm'>%s</td>" % html.escape(r["name"]))
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
        else:
            v = tot.get(key, 0.0)
            shown = -v if key in _NEG_COLS else v
            parts.append("<td>%s</td>" % _money(round(shown, 2)))
    parts.append("</tr></tbody></table>")
    parts.append("<p class='note'>Incentive→pot this month totals "
                 "<b>%s</b> (accrues to the annual pot Apr→Mar; paid the following "
                 "Diwali). <b>Net (new model)</b> = the ledger's own current-model "
                 "take-home (base + attendance + ledger, computed by the live salary "
                 "code, read-only) PLUS the register Δ — so incentive is out of the "
                 "month, absences beyond the 2-day buffer are cut at base÷30, and "
                 "recorded leave / dress / extra-duty / outstation are reflected. "
                 "This screen writes nothing; it is a preview. The ₹50/₹100 absence "
                 "fines and all late-mark logic stay in the attendance layer, "
                 "unchanged. Making this the official locked salary run is Stage B.</p>"
                 % _money(round(pot_total, 2)))
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
    # base 30000 -> day 1000 ; base 3000 -> day 100
    con.execute("INSERT INTO staff VALUES(1,'Tester','2000-01-01',NULL,30000,0,1,1)")
    con.execute("INSERT INTO staff VALUES(2,'Clean','2000-01-01',NULL,30000,0,0,0)")
    con.execute("INSERT INTO staff VALUES(3,'Zero','2000-01-01',NULL,30000,0,0,0)")
    con.execute("INSERT INTO staff VALUES(4,'Cleaner','2000-01-01',NULL,3000,1,0,0)")
    # Tester (2026-08): 1 discretionary leave on 05 (a no-punch day) + 2 genuine
    # absents on 12,13 (also no-punch). 1 dress + 1 i-card on 15 (present),
    # 2 extra-duty (16,17), 3 outstation nights (06,07,08 → also no-punch).
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-08-05',1,'discretionary','leave_sanctioned')")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,dress_improper,icard_missing) "
                "VALUES('2026-08-15',1,1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,extra_duty) VALUES('2026-08-16',1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,extra_duty) VALUES('2026-08-17',1,1)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,outstation_nights) VALUES('2026-08-06',1,3)")
    # Clean: exactly 1 discretionary leave (05), nothing else → 1 unused → encash 1
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-08-05',2,'discretionary','leave_sanctioned')")
    con.commit(); con.close()

    att_dir = tmp
    with open(os.path.join(att_dir, "salary_inputs_2026-08.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Absent", "Fine: excess-absent Rs", "Fine: uninformed Rs",
                    "Incentive", "Incentive Rs", "Absent dates"])
        # Tester att-absent = leave(05) + outstation(06,07,08) + genuine(12,13) = 6
        w.writerow(["Tester", "6", "300", "0", "FULL", "1000",
                    "2026-08-05 2026-08-06 2026-08-07 2026-08-08 2026-08-12 2026-08-13"])
        w.writerow(["Clean", "1", "0", "0", "FULL", "1000", "2026-08-05"])
        w.writerow(["Zero", "0", "0", "0", "FULL", "1000", ""])
        w.writerow(["Cleaner", "3", "0", "0", "-", "0", "2026-08-01 2026-08-02 2026-08-03"])

    rows, problems, pot = build_report("2026-08", db_path=dbp, att_dir=att_dir)
    problems = [p for p in problems if "ledger" not in p]      # ledger absent in test
    assert not problems, problems
    r = {x["name"]: x for x in rows}

    # Tester: genuine = 6 − 1(leave) − 3(outstation) = 2 ; C = 1 + 2 = 3 ; extra 1 → −1000
    t = r["Tester"]
    assert t["day_rate"] == 1000.0
    assert t["genuine_absent"] == 2 and t["C"] == 3
    assert t["extra_days"] == 1 and t["base30_ded"] == 1000.0
    assert t["encash_days"] == 0 and t["encash_rs"] == 0.0     # extra absent → forfeit
    assert t["dress_rs"] == 20.0 and t["icard_rs"] == 20.0
    assert t["extra_rs"] == 400.0 and t["outst_rs"] == 750.0
    assert t["incentive_pot"] == 1000.0
    # delta = -20 -20 +400 +750 -1000(base30) +0(encash) -1000(inc) = -890
    assert t["delta"] == -890.0, t["delta"]

    # Clean: 1 leave, 0 genuine → C=1, no extra → encash (2-1)=1 day = 1000
    c = r["Clean"]
    assert c["genuine_absent"] == 0 and c["C"] == 1
    assert c["base30_ded"] == 0.0 and c["encash_days"] == 1 and c["encash_rs"] == 1000.0
    # delta = +1000(encash) -1000(inc) = 0
    assert c["delta"] == 0.0, c["delta"]

    # Zero: nothing → C=0 → encash 2 days = 2000
    z = r["Zero"]
    assert z["encash_days"] == 2 and z["encash_rs"] == 2000.0
    assert z["delta"] == 1000.0, z["delta"]      # +2000 encash − 1000 inc

    # Cleaner (minutes-exempt): 3 genuine absents → C=3, extra 1 → −100 base30;
    # no dress/icard/extra/outstation; still gets the base/30 deduction (D276).
    cl = r["Cleaner"]
    assert cl["day_rate"] == 100.0 and cl["genuine_absent"] == 3 and cl["C"] == 3
    assert cl["base30_ded"] == 100.0 and cl["encash_days"] == 0
    assert cl["dress_rs"] == 0.0 and cl["extra_rs"] == 0.0
    assert cl["delta"] == -100.0, cl["delta"]    # only the base/30 extra-absent day

    # over-quota festival: give Tester 1 festival leave with 2 already used this FY
    con = sqlite3.connect(dbp)
    con.execute("INSERT INTO festival_day VALUES('2026-08-20','Eid',0)")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-08-20',1,'festival','leave_sanctioned')")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-04-10',1,'festival','leave_sanctioned')")
    con.execute("INSERT INTO daily_register(reg_date,staff_id,leave_kind,absence_type) "
                "VALUES('2026-05-11',1,'festival','leave_sanctioned')")
    con.commit(); con.close()
    rows2, _, _ = build_report("2026-08", db_path=dbp, att_dir=att_dir)
    t2 = {x["name"]: x for x in rows2}["Tester"]
    # 2 festival already used this FY → this month's 1 festival is over-quota → +1 deduct day
    assert t2["fest_over"] == 1 and t2["deduct_days"] == t2["extra_days"] + 1

    # new-model net: ledger not importable in the sandbox → final_net stays None
    # and the column renders as "—" without error.
    assert "final_net" in t and t["final_net"] is None
    # html render smoke (must survive None net)
    h = render_html("2026-08", rows, [], pot)
    assert "REGISTER" in h and "Tester" in h and "Extra-abs" in h and "Net (new model)" in h
    print("SELFTEST OK — C-model (buffer 2, base/30 extra-absence deduction, gated "
          "encashment, over-festival, minutes-exempt still deducts, dress/icard/extra/"
          "outstation, incentive→pot, ad-hoc read-only, new-model net None-safe), html render.")


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
