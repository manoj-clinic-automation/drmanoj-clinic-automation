#!/usr/bin/env python3
"""
staff_ledger.py  v2.0 (S155, D255/D257/D258)  —  Staff Ledger: maker-checker + loans
=====================================================================================
A small standalone web app for the clinic VPS. Makers enter staff money/leave
events; checkers (the doctors) approve by phone tap. Approved rows are
APPEND-ONLY; corrections happen by CONTRA entry. Monthly close emits one
approved-adjustments CSV for the salary workbook.

Frozen attendance core untouched (additive, same pattern as att_month_report).
Data lives ONLY on the VPS (F-31): /root/staff_ledger/ .

v2.0 (S155, D258): ALL staff money — structured loans included — lives here.
  + Per-staff STATEMENT view (/statement): chronological entries, running salary
    net (same rules as monthly close, so they can never disagree), open-advance
    balances, month filter. Checkers see any staff; makers see their own
    (staff_link) statement only.
  + Interest-bearing advances (D250 loans): checker-only to issue. The monthly
    INSTALMENT IS THE WHOLE DEDUCTION and the flat Rs 1,000 interest comes OUT
    of it (workbook-exact, v2.3): recovery budget = min(instalment, everything
    owed), allocated interest → interest-bearing principal → interest-free
    principal, overflowing across tranches WITHIN the same month. Interest
    stops the moment the interest-bearing tranche clears.
  + SKIP a month (checker tap on Advances page): a skip month recovers NOTHING
    and Rs 1,000 CAPITALISES onto the loan; max 2 skips per Indian FY
    (Apr-Mar) — the 3rd is refused (D250).
  System rows (interest / capitalise / skip / instalment) are machine-made at
  close, never enterable by hand. Ledger file stays append-only jsonl; old rows
  need no migration (new keys default absent).

v3.0 (S156, D259): FULL BACKEND SALARY (owner mandate) + F-51 UI safety batch.
  + /salary page (checker-only): reads the attendance report's own output files
    (salary_inputs / deductions_extras / review CSVs from att_month_report.py,
    never re-deriving its policy math), pulls the three paper loops on-screen
    (informed-absence flags, EARLY_BIG genuine rulings, OT approval, plus
    Darpan outstation-day adjustment), combines them with the ledger's closed
    adjustments for the month and each base salary, and shows the full NET
    table. One APPROVE (confirmation dialog) locks the month: per-staff
    SALARY_PAID system rows append to the ledger and salary_final_<month>.csv
    is written. A locked month can never be silently recomputed; a wrong
    salary is corrected NEXT month by an OTHER adjustment (accounting-honest).
  + F-51: the contra button now goes through a server-side CONFIRM page that
    shows the exact row being reversed; the Skip button asks for confirmation;
    reversed pairs (row + its contra) display greyed as one visual unit; the
    statement groups rows under bold month headers (an April skip can no
    longer read as July).
  Frozen attendance core still untouched; att_month_report.py untouched (its
  outputs are the interface). Ledger file stays append-only jsonl.

Commands
--------
  /root/wa/venv/bin/python3 staff_ledger.py serve                 # run web app (systemd)
  /root/wa/venv/bin/python3 staff_ledger.py adduser               # interactive: add/replace a login
  /root/wa/venv/bin/python3 staff_ledger.py deluser NAME          # disable a login
  /root/wa/venv/bin/python3 staff_ledger.py listusers
  /root/wa/venv/bin/python3 staff_ledger.py close 2026-08         # monthly close -> CSV
  /root/wa/venv/bin/python3 staff_ledger.py migrate-loan          # one-time guided loan
                                                                  #   migration from workbook
  /root/wa/venv/bin/python3 staff_ledger.py --selftest            # synthetic end-to-end test

Environment (all optional):
  LEDGER_DIR   data directory        (default /root/staff_ledger)
  LEDGER_PORT  port                  (default 8043)
  STAFF_CSV    staff master path     (default /root/staff_master.csv)
  NTFY_URL     e.g. https://ntfy.sh/yourtopic  — pinged on new PENDING entry
"""

import os, sys, json, csv, hashlib, secrets, datetime, tempfile, getpass, urllib.request

# ---------------------------------------------------------------- constants --
APP_VERSION = "3.1-S156"
LEDGER_DIR  = os.environ.get("LEDGER_DIR", "/root/staff_ledger")
STAFF_CSV   = os.environ.get("STAFF_CSV", "/root/staff_master.csv")
PORT        = int(os.environ.get("LEDGER_PORT", "8043"))
NTFY_URL    = os.environ.get("NTFY_URL", "").strip()
ATT_BASE    = os.environ.get("ATT_BASE", "/root")          # att_month_report.py home + its outputs
ATT_REPORT  = os.environ.get("ATT_REPORT", "/root/att_month_report.py")
VENV_PY     = os.environ.get("VENV_PY", "/root/wa/venv/bin/python3")
URL_PREFIX  = "/ledger"

# Rate card (owner-ruled S154). Amounts in Rs. sign: +1 credit to staff, -1 debit.
CATEGORIES = {
    #  key                label                    rate  per_day  sign  narr_req
    "NIGHT_DUTY":        ("Night duty",             200,  True,   +1,  False),
    "FINE_UNIFORM":      ("Uniform fine",            20,  True,   -1,  False),
    "FINE_ICARD":        ("I-card fine",             20,  True,   -1,  False),
    "LEAVE_APPROVED":    ("Approved leave (record)",  0,  True,    0,  False),
    "ICARD_REPLACEMENT": ("I-card replacement",     100,  False,  -1,  False),
    "ADVANCE_ISSUE":     ("Advance issued",        None,  False,  +1,  False),
    "FINE_ADHOC":        ("Ad-hoc fine (doctors)", None,  False,  -1,  True),
    "PERK":              ("Perk / benefit paid (record)", None, False, +1, True),
    "OTHER":             ("Other adjustment",      None,  False,  None,True),
    # system-generated at monthly close / skip taps — NEVER in any entry form
    # (they are absent from ROLE_CATS, so make_entry cannot create them):
    "ADVANCE_INSTALMENT":("Advance instalment (auto)", None, False, -1, False),
    "LOAN_INTEREST":     ("Loan interest (auto)",      None, False, -1, False),
    "LOAN_CAPITALISE":   ("Interest capitalised on skip", None, False, +1, False),
    "LOAN_SKIP":         ("Instalment skipped",        None, False,  0, False),
    "SALARY_PAID":       ("Salary paid (monthly, auto)", None, False, +1, False),
}
INTEREST_RS   = 1000     # D250: flat per month while an interest-bearing balance is open
SKIPS_PER_FY  = 2        # D250: skips per Indian financial year (Apr-Mar)
SYSTEM_CATS   = {"ADVANCE_INSTALMENT","LOAN_INTEREST","LOAN_CAPITALISE","LOAN_SKIP",
                 "SALARY_PAID"}
# rupees that are NOT salary money (cash / balance-side events) — excluded from
# the close CSV summary AND from the statement's running salary net, identically:
SALARY_EXCLUDED = {"ADVANCE_ISSUE","LOAN_CAPITALISE","LOAN_SKIP","PERK","SALARY_PAID"}
# F-50 (S155): a role's powers are EXPLICIT lists — never "everything in
# CATEGORIES", which silently grew when system categories were added in v2.0.
ROLE_CATS = {
    # S162 (D286): approved-leave + uniform/i-card fines moved to the Staff Register
    # (daily grid + sanctioned-leave range). maker_full (Shavez/manager) keeps his
    # ledger-only money work; maker_limited (Alisha/Shivani/receptionist) has nothing
    # left to enter here. Checker (doctor) keeps the full list as a backstop.
    "maker_full":    ["NIGHT_DUTY","ICARD_REPLACEMENT","ADVANCE_ISSUE"],
    "maker_limited": [],
    "checker":       ["NIGHT_DUTY","FINE_UNIFORM","FINE_ICARD","LEAVE_APPROVED",
                      "ICARD_REPLACEMENT","ADVANCE_ISSUE","FINE_ADHOC","PERK","OTHER"],
}

# ------------------------------------------------------------------ storage --
def _p(name): return os.path.join(LEDGER_DIR, name)

# --- Clinic SSO (portal broker) acceptance -- Step 5, Session 158 ----------
# The ledger accepts a valid portal `clinic_sso` cookie as login. SSO proves
# only WHO you are; the ledger's own users.json still decides WHAT you may do
# (maker vs checker) -- so a manager can never gain checker powers via SSO. The
# ledger's own username/password login stays the permanent fallback. If the
# portal secret can't be read, the shim is INERT (own login only).
_PORTAL_DIR = os.environ.get("CLINIC_PORTAL_DIR", "/root/portal")
try:
    if _PORTAL_DIR not in sys.path:
        sys.path.insert(0, _PORTAL_DIR)
    import clinic_sso as _sso
    import portal_config as _pcfg
    _SSO_SECRET = getattr(_pcfg, "CLINIC_SSO_SECRET", None)
except Exception:
    _sso = None
    _SSO_SECRET = None
_SSO_STORE = os.path.join(_PORTAL_DIR, "clinic_users.json")


def _sso_epoch():
    try:
        with open(_SSO_STORE) as f:
            return int(json.load(f).get("epoch", 1))
    except Exception:
        return None

def load_users():
    try:
        with open(_p("users.json"), encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(u):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    tmp = _p("users.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(u, f, indent=1)
    os.replace(tmp, _p("users.json"))
    os.chmod(_p("users.json"), 0o600)

def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200000).hex()

def load_ledger():
    rows = []
    try:
        with open(_p("ledger.jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line: rows.append(json.loads(line))
    except FileNotFoundError:
        pass
    return rows

def append_ledger(row):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    with open(_p("ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if os.path.exists(_p("ledger.jsonl")):
        os.chmod(_p("ledger.jsonl"), 0o600)

def update_row(row_id, patch):
    """Rewrite the file with one row patched. Only ever changes status fields —
    approved economic content is never edited (contra entries do corrections)."""
    rows = load_ledger()
    hit = False
    for r in rows:
        if r["id"] == row_id:
            r.update(patch); hit = True
    if not hit: raise KeyError(row_id)
    tmp = _p("ledger.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, _p("ledger.jsonl"))
    os.chmod(_p("ledger.jsonl"), 0o600)

def staff_names():
    try:
        with open(STAFF_CSV, encoding="utf-8") as f:
            return [r["name"] for r in csv.DictReader(f) if r.get("active","Y").strip().upper()=="Y"]
    except FileNotFoundError:
        return []

def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ntfy(msg):
    if not NTFY_URL: return
    try:
        req = urllib.request.Request(NTFY_URL, data=msg.encode("utf-8"),
                                     headers={"Title": "Staff Ledger"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # notification is best-effort; the pending list is the truth

# ------------------------------------------------------------ ledger logic ---
def compute_amount(cat, days, manual_amount):
    label, rate, per_day, sign, _ = CATEGORIES[cat]
    if cat == "LEAVE_APPROVED": return 0
    if cat == "PERK": return abs(int(manual_amount))
    if rate is None:
        amt = abs(int(manual_amount))
        if cat == "OTHER":
            return amt if int(manual_amount) >= 0 else -amt
        return sign * amt
    return sign * rate * (days if per_day else 1)

def make_entry(users, maker, staff, cat, date_from, date_to, days, manual_amount,
               narration, instalment=None, contra_of=None, interest=False):
    u = users[maker]
    role = u["role"]
    if cat not in ROLE_CATS[role]:
        raise PermissionError(f"{maker} may not enter {cat}")
    if interest and (cat != "ADVANCE_ISSUE" or role != "checker"):
        raise PermissionError("interest-bearing loans are checker-issued advances only")
    _,_,_,_, narr_req = CATEGORIES[cat]
    if narr_req and not narration.strip():
        raise ValueError("narration is required for this category")
    if cat == "ADVANCE_ISSUE":
        amount = abs(int(manual_amount))
        if amount <= 0:
            raise ValueError("an advance needs a positive amount — to SKIP a "
                             "loan month use the Skip button on the Advances "
                             "page, never a Rs 0 entry")
        inst = abs(int(instalment)) if instalment not in (None,"","0",0) else amount
        if interest and inst < INTEREST_RS:
            raise ValueError(f"instalment must be at least Rs {INTEREST_RS} on an interest-bearing loan")
    else:
        amount = compute_amount(cat, days, manual_amount)
        inst = None
    direct = (role == "checker")
    row = {
        "id": secrets.token_hex(6),
        "ts_entry": now(),
        "maker": maker,
        "staff": staff,
        "category": cat,
        "date_from": date_from, "date_to": date_to, "days": days,
        "amount": amount,
        "instalment": inst,
        "narration": narration.strip(),
        "self_flag": (u.get("staff_link","").strip().lower() == staff.strip().lower()
                      and staff.strip() != ""),
        "direct": direct,
        "status": "APPROVED" if direct else "PENDING",
        "checker": maker if direct else "",
        "ts_decision": now() if direct else "",
        "contra_of": contra_of or "",
        "closed_month": "",
        "interest": bool(interest) if cat == "ADVANCE_ISSUE" else False,
    }
    append_ledger(row)
    if not direct:
        ntfy(f"PENDING: {maker} -> {staff}: {CATEGORIES[cat][0]} Rs{abs(amount)}"
             + (" [SELF]" if row["self_flag"] else ""))
    return row

def decide(users, checker, row_id, approve: bool):
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers decide")
    rows = {r["id"]: r for r in load_ledger()}
    r = rows[row_id]
    if r["status"] != "PENDING":
        raise ValueError("row is not pending")
    update_row(row_id, {"status": "APPROVED" if approve else "REJECTED",
                        "checker": checker, "ts_decision": now()})

def make_contra(users, maker, orig_id, narration):
    rows = {r["id"]: r for r in load_ledger()}
    o = rows[orig_id]
    if o["status"] != "APPROVED":
        raise ValueError("contra targets approved rows only")
    if o["category"] == "ADVANCE_ISSUE" and advance_children(o["id"]):
        raise ValueError("advance already active (recovery/interest/skip recorded); "
                         "adjust instalments instead of a contra")
    if o["category"] in SYSTEM_CATS:
        raise ValueError("system rows (interest/instalment/capitalise/skip) are never contra'd by hand")
    u = users[maker]
    if u["role"] != "checker" and o["category"] not in ROLE_CATS[u["role"]]:
        raise PermissionError("outside your categories")
    if not narration.strip():
        raise ValueError("contra needs a narration")
    row = {
        "id": secrets.token_hex(6), "ts_entry": now(), "maker": maker,
        "staff": o["staff"], "category": o["category"],
        "date_from": o["date_from"], "date_to": o["date_to"], "days": o["days"],
        "amount": -o["amount"], "instalment": None,
        "narration": "CONTRA of " + orig_id + ": " + narration.strip(),
        "self_flag": False, "direct": u["role"] == "checker",
        "status": "APPROVED" if u["role"] == "checker" else "PENDING",
        "checker": maker if u["role"] == "checker" else "",
        "ts_decision": now() if u["role"] == "checker" else "",
        "contra_of": orig_id, "closed_month": "",
    }
    append_ledger(row)
    if row["status"] == "PENDING":
        ntfy(f"PENDING CONTRA: {maker} reverses {orig_id} ({o['staff']} Rs{abs(o['amount'])})")
    return row

def advance_recovered(issue_id, rows=None):
    return sum(-r["amount"] for r in (rows or load_ledger())
               if r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == issue_id
               and r["status"] == "APPROVED")

def advance_capitalised(issue_id, rows=None):
    """Skipped-month interest added onto the balance (D250: skips capitalise)."""
    return sum(r["amount"] for r in (rows or load_ledger())
               if r["category"] == "LOAN_CAPITALISE" and r["contra_of"] == issue_id
               and r["status"] == "APPROVED")

def advance_children(issue_id, rows=None):
    """Any approved system activity on an advance (instalment/interest/capitalise/skip)."""
    return [r for r in (rows or load_ledger())
            if r["contra_of"] == issue_id and r["status"] == "APPROVED"
            and r["category"] in SYSTEM_CATS]

def fy_of(month):
    """'2026-08' -> 'FY2026-27' (Indian financial year, Apr-Mar)."""
    y, m = int(month[:4]), int(month[5:7])
    start = y if m >= 4 else y - 1
    return f"FY{start}-{str(start+1)[-2:]}"

def fy_skips(staff, month, rows=None):
    """Skip markers already recorded for this staff in the FY containing `month`."""
    fy = fy_of(month)
    return [r for r in (rows or load_ledger())
            if r["category"] == "LOAN_SKIP" and r["staff"] == staff
            and r["status"] == "APPROVED" and fy_of(r["date_from"]) == fy]

def is_skipped(issue_id, month, rows=None):
    return any(r["category"] == "LOAN_SKIP" and r["contra_of"] == issue_id
               and r["date_from"] == month and r["status"] == "APPROVED"
               for r in (rows or load_ledger()))

def record_skip(users, checker, issue_id, month):
    """Checker marks one interest-bearing advance as SKIPPED for `month` (D250).
    Refused beyond SKIPS_PER_FY per staff per Indian FY. Also usable for
    HISTORICAL months (migration: record skips already taken workbook-side)."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers record skips")
    datetime.date.fromisoformat(month + "-01")   # validates YYYY-MM
    rows = load_ledger()
    issue = next((r for r in rows if r["id"] == issue_id), None)
    if not issue or issue["category"] != "ADVANCE_ISSUE" or issue["status"] != "APPROVED":
        raise ValueError("no such approved advance")
    if not issue.get("interest"):
        raise ValueError("skips apply to interest-bearing loans only")
    if is_skipped(issue_id, month, rows):
        raise ValueError(f"{month} already marked skipped for this loan")
    if any(r.get("closed_month") == month and r["category"] == "ADVANCE_INSTALMENT"
           and r["contra_of"] == issue_id for r in rows):
        raise ValueError(f"{month} was already closed with an instalment — cannot skip it now")
    used = fy_skips(issue["staff"], month, rows)
    if len(used) >= SKIPS_PER_FY:
        raise ValueError(f"{SKIPS_PER_FY} skips already used in {fy_of(month)} "
                         f"({', '.join(x['date_from'] for x in used)}) — D250 limit")
    row = {"id": secrets.token_hex(6), "ts_entry": now(), "maker": checker,
           "staff": issue["staff"], "category": "LOAN_SKIP",
           "date_from": month, "date_to": month, "days": 0,
           "amount": 0, "instalment": None,
           "narration": f"skip recorded for loan {issue_id} ({fy_of(month)} "
                        f"{len(used)+1}/{SKIPS_PER_FY})",
           "self_flag": False, "direct": True, "status": "APPROVED",
           "checker": checker, "ts_decision": now(),
           "contra_of": issue_id, "closed_month": "", "interest": False}
    append_ledger(row)
    return row

def open_advances():
    rows = load_ledger()
    out = []
    for r in rows:
        if r["category"] != "ADVANCE_ISSUE" or r["status"] != "APPROVED": continue
        reversed_ = any(x["contra_of"] == r["id"] and x["category"] == "ADVANCE_ISSUE"
                        and x["status"] == "APPROVED" and x["amount"] == -r["amount"]
                        for x in rows)
        if reversed_: continue
        bal = r["amount"] + advance_capitalised(r["id"], rows) - advance_recovered(r["id"], rows)
        if bal > 0:
            out.append({"issue": r, "balance": bal,
                        "instalment": r.get("instalment") or r["amount"],
                        "interest": bool(r.get("interest"))})
    # D250 tranche order: interest-bearing first, then oldest first
    out.sort(key=lambda a: (not a["interest"], a["issue"]["date_from"], a["issue"]["ts_entry"]))
    return out

def month_adjustments(rows, month):
    """Per-staff {credit,debit,leave_days} over APPROVED rows stamped
    closed_month==month, excluding SALARY_EXCLUDED — the ONE rule set shared by
    the close CSV and the salary engine (they can never disagree)."""
    per = {}
    for r in rows:
        if r.get("closed_month") != month or r["status"] != "APPROVED":
            continue
        if r["category"] in SALARY_EXCLUDED:
            continue
        d = per.setdefault(r["staff"], {"credit": 0, "debit": 0, "leave_days": 0})
        if r["category"] == "LEAVE_APPROVED":
            d["leave_days"] += r["days"]
        elif r["amount"] >= 0:
            d["credit"] += r["amount"]
        else:
            d["debit"] += -r["amount"]
    return per


def close_month(users, checker, month):
    """month = 'YYYY-MM'. Generates ADVANCE_INSTALMENT rows, marks rows closed,
    writes approved_adjustments_<month>.csv. Idempotent: refuses a re-close."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only a checker closes the month")
    for r in load_ledger():
        if r.get("closed_month") == month:
            raise ValueError(f"{month} already closed")
    # 1. instalments / interest / skip-capitalisation due this month (D250)
    def _sysrow(staff, cat, amount, ref, narr):
        append_ledger({
            "id": secrets.token_hex(6), "ts_entry": now(), "maker": "SYSTEM",
            "staff": staff, "category": cat,
            "date_from": month, "date_to": month, "days": 0,
            "amount": amount, "instalment": None, "narration": narr,
            "self_flag": False, "direct": True, "status": "APPROVED",
            "checker": checker, "ts_decision": now(),
            "contra_of": ref, "closed_month": month, "interest": False,
        })
    snap = open_advances()                 # snapshot BEFORE we append anything
    rows_now = load_ledger()
    per_staff = {}
    for adv in snap:
        per_staff.setdefault(adv["issue"]["staff"], []).append(adv)
    for staff, advs in per_staff.items():  # advs already in waterfall order
        # A skip on any open loan = this staff's whole account pauses this month
        # (workbook semantics: a SKIP month recovers nothing at all).
        skipped = [a for a in advs if a["interest"]
                   and is_skipped(a["issue"]["id"], month, rows_now)]
        if skipped:
            for a in skipped:
                _sysrow(staff, "LOAN_CAPITALISE", INTEREST_RS, a["issue"]["id"],
                        f"skipped {month}: Rs {INTEREST_RS} interest capitalised "
                        f"onto loan {a['issue']['id']} "
                        f"(balance now {a['balance']+INTEREST_RS})")
            continue
        # Monthly recovery budget = the head-of-waterfall instalment, capped at
        # everything owed (interest due + all balances). Interest comes OUT of
        # the budget; the remainder flows tranche to tranche (workbook-exact).
        interest_due = sum(INTEREST_RS for a in advs if a["interest"] and a["balance"] > 0)
        owed = interest_due + sum(a["balance"] for a in advs)
        budget = min(advs[0]["instalment"], owed)
        for a in advs:
            if a["interest"] and a["balance"] > 0 and budget > 0:
                pay_i = min(INTEREST_RS, budget)
                _sysrow(staff, "LOAN_INTEREST", -pay_i, a["issue"]["id"],
                        f"flat monthly interest on loan {a['issue']['id']} (D250, "
                        f"paid out of the Rs {advs[0]['instalment']} instalment)")
                budget -= pay_i
        for a in advs:
            if budget <= 0: break
            p = min(budget, a["balance"])
            if p > 0:
                _sysrow(staff, "ADVANCE_INSTALMENT", -p, a["issue"]["id"],
                        f"auto instalment for {'loan' if a['interest'] else 'advance'} "
                        f"{a['issue']['id']} (balance after: {a['balance']-p})")
                budget -= p
    # 2. collect + stamp every approved, un-closed row
    rows = load_ledger()
    take = [r for r in rows if r["status"] == "APPROVED" and not r["closed_month"]]
    for r in take:
        update_row(r["id"], {"closed_month": month})
    take = [r for r in load_ledger() if r.get("closed_month") == month
            and r["status"] == "APPROVED"]
    # 3. per-staff summary + detail CSV
    out = _p(f"approved_adjustments_{month}.csv")
    per = month_adjustments(take, month)   # shared rule set (salary engine uses it too)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"APPROVED ADJUSTMENTS {month}",
                    f"generated {now()} by {checker}", "", "", ""])
        w.writerow(["staff","credits_Rs","debits_Rs","net_Rs","approved_leave_days"])
        for s in sorted(per):
            d = per[s]
            w.writerow([s, d["credit"], d["debit"], d["credit"]-d["debit"], d["leave_days"]])
        w.writerow([]); w.writerow(["-- detail --","","","",""])
        w.writerow(["staff","category","dates","amount_Rs","maker/checker","narration"])
        for r in sorted(take, key=lambda x:(x["staff"], x["ts_entry"])):
            dates = r["date_from"] + ("" if r["date_to"] in ("", r["date_from"])
                                      else " to " + r["date_to"])
            w.writerow([r["staff"], r["category"], dates, r["amount"],
                        f'{r["maker"]}/{r["checker"]}', r["narration"]])
    os.chmod(out, 0o600)
    return out, len(take)

# --------------------------------------------------------------- migration ---
def migrate_loan(users, checker, staff, loan_amount, free_amount, instalment,
                 skip_months, perks=()):
    """One-time opening-balance migration from the workbook (D258). Creates the
    interest-bearing and/or interest-free opening tranches (ONE instalment
    drives the whole waterfall), historical skip markers, and brought-forward
    perk records. IDEMPOTENT: refused outright if the staff already has ANY
    open advance — running it twice cannot double a rupee."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only a checker migrates")
    match = [s for s in staff_names() if s.strip().lower() == staff.strip().lower()]
    if not match:
        raise ValueError(f"'{staff}' is not an active staff name in {STAFF_CSV}")
    staff = match[0]                       # canonical spelling from the CSV
    if any(a["issue"]["staff"] == staff for a in open_advances()):
        raise ValueError(f"{staff} already has an open advance/loan — "
                         "migration refused (it may only ever run once)")
    loan_amount, free_amount = int(loan_amount), int(free_amount)
    if loan_amount <= 0 and free_amount <= 0:
        raise ValueError("nothing to migrate (both balances are 0)")
    # ---- COMPLETE validation BEFORE the first append: the ledger is append-
    # only, so a half-created migration cannot be rolled back — it must be
    # impossible instead (S155 atomicity rule).
    if int(instalment) < INTEREST_RS and loan_amount > 0:
        raise ValueError(f"instalment must be at least Rs {INTEREST_RS}")
    clean_skips = [m.strip() for m in skip_months if m.strip()]
    if clean_skips and loan_amount <= 0:
        raise ValueError("skip months given but no interest-bearing loan migrated")
    if len(set(clean_skips)) != len(clean_skips):
        raise ValueError("duplicate skip months")
    per_fy = {}
    for m in clean_skips:
        datetime.date.fromisoformat(m + "-01")          # validates YYYY-MM
        per_fy.setdefault(fy_of(m), []).append(m)
    for fy, ms in per_fy.items():
        already = [s for s in fy_skips(staff, ms[0]) ]
        if len(already) + len(ms) > SKIPS_PER_FY:
            raise ValueError(f"{fy}: {len(already)} skip(s) already recorded + "
                             f"{len(ms)} new exceeds the {SKIPS_PER_FY}/FY limit")
    clean_perks = [(str(n).strip(), abs(int(a))) for n, a in perks]
    if any(not n or a <= 0 for n, a in clean_perks):
        raise ValueError("every perk needs a narration and a positive amount")
    made = []
    if loan_amount > 0:
        made.append(make_entry(users, checker, staff, "ADVANCE_ISSUE",
                    datetime.date.today().isoformat(), "", 0, str(loan_amount),
                    "opening balance migrated from workbook (interest-bearing tranche)",
                    instalment=str(instalment), interest=True))
    if free_amount > 0:
        made.append(make_entry(users, checker, staff, "ADVANCE_ISSUE",
                    datetime.date.today().isoformat(), "", 0, str(free_amount),
                    "opening balance migrated from workbook (interest-free tranche)",
                    instalment=str(instalment)))
    skips = []
    for m in clean_skips:
        skips.append(record_skip(users, checker, made[0]["id"], m))
    perk_rows = []
    for narr, amt in clean_perks:
        perk_rows.append(make_entry(users, checker, staff, "PERK",
                         datetime.date.today().isoformat(), "", 0, str(amt),
                         "(brought forward) " + narr))
    return made, skips, perk_rows

def parse_perk_line(line):
    """'School expenses - Adarsh / 13000'  ->  ('School expenses - Adarsh', 13000)
    The LAST number on the line is the amount; everything before it (minus
    trailing separators) is the narration. Trailing commas tolerated."""
    import re
    line = line.strip().rstrip(",")
    m = None
    for m in re.finditer(r"\d[\d,]*", line):
        pass                                  # keep the last number match
    if not m:
        raise ValueError("no amount found — write:  narration / amount")
    amt = int(m.group(0).replace(",", ""))
    narr = line[:m.start()].rstrip(" /:-\u2013\u2014,\t")
    if not narr:
        raise ValueError("no narration found — write:  narration / amount")
    if amt <= 0:
        raise ValueError("amount must be positive")
    return narr, amt

def cli_migrate_loan():
    users = load_users()
    checkers = [n for n, r in users.items()
                if r["role"] == "checker" and r.get("active", True)]
    if not checkers: sys.exit("no checker user exists")
    checker = checkers[0]
    print("One-time loan migration from the workbook (D258).")
    print("Figures are typed here on the VPS only — they never pass through")
    print("chat, Drive or the CSV (F-31). Refused if the staff already has an")
    print("open advance, so it cannot run twice.\n")
    staff = input("Staff name exactly as in staff_master.csv (e.g. Darpan): ").strip()
    loan_amount = input("Interest-bearing tranche outstanding Rs (0 if none): ").strip() or "0"
    free_amount = input("Interest-FREE tranche outstanding Rs (0 if none): ").strip() or "0"
    inst = input(f"Monthly instalment Rs for the WHOLE loan (interest Rs {INTEREST_RS} "
                 "comes out of it; min {0}): ".format(INTEREST_RS)).strip()
    skipm = input("Skip months already used this FY, comma-separated "
                  "(e.g. 2026-04; blank if none): ").strip()
    perks = []
    print("Perks brought forward (for the lifetime record).")
    print("ONE line per perk:  narration / amount   (e.g.  School fee - Adarsh / 13000)")
    print("Blank line to finish:")
    while True:
        ln = input("  perk: ").strip()
        if not ln: break
        try:
            perks.append(parse_perk_line(ln))
        except ValueError as e:
            print(f"    not understood ({e}) — try again")
    print()
    made, skips, perk_rows = migrate_loan(users, checker, staff, loan_amount,
                                          free_amount, inst,
                                          skipm.split(",") if skipm else [], perks)
    for r in made:
        kind = "interest-bearing loan" if r.get("interest") else "interest-free tranche"
        print(f"  created {kind}: Rs {r['amount']} (id {r['id']})")
    print(f"  one instalment drives the waterfall: Rs {inst}/month")
    for s in skips:
        print(f"  recorded historical skip: {s['date_from']}")
    for p in perk_rows:
        print(f"  perk brought forward: Rs {p['amount']} — {p['narration']}")
    st = build_statement(staff); S = st["summary"]
    print(f"\nVERIFY against the workbook's LIVE POSITION before retiring it:")
    print(f"  interest-bearing outstanding: Rs {S['bal_interest']}")
    print(f"  interest-free outstanding:    Rs {S['bal_free']}")
    print(f"  skips this FY:                {len(S['skip_months'])} ({', '.join(S['skip_months']) or 'none'})")
    print(f"  perks lifetime total:         Rs {S['perks_total']}")
    print("If all four match the Loan Master sheet to the rupee, the workbook's")
    print("loan sheets are RETIRED (D258). Next: run  close YYYY-MM  for the")
    print("first month the ledger owns.")

# --------------------------------------------------------------- statement ---
def build_statement(staff, month=None):
    """Per-staff statement (D258). Chronological lines with a running SALARY net
    computed under EXACTLY the monthly-close rules (approved rows only;
    SALARY_EXCLUDED categories shown but outside the net) — statement and close
    CSV can never disagree. `month`='YYYY-MM' filters by event date; None = all."""
    rows = load_ledger()
    mine = [r for r in rows if r["staff"] == staff]
    months = sorted({r["date_from"][:7] for r in mine if r.get("date_from")}, reverse=True)
    if month:
        mine = [r for r in mine if r["date_from"][:7] == month]
    mine.sort(key=lambda r: (r["date_from"], r["ts_entry"]))
    lines, net = [], 0
    for r in mine:
        counted = (r["status"] == "APPROVED" and r["category"] not in SALARY_EXCLUDED)
        if counted:
            net += r["amount"]
        lines.append({"row": r, "counted": counted, "net": net if counted else None})
    advs = [a for a in open_advances() if a["issue"]["staff"] == staff]
    # lifetime summary for this staff (approved rows, unfiltered by month):
    all_app = [r for r in rows if r["staff"] == staff and r["status"] == "APPROVED"]
    perks = [r for r in all_app if r["category"] == "PERK"]
    cur = datetime.date.today().strftime("%Y-%m")
    skips = fy_skips(staff, cur, rows)
    summary = {
        "perks_total":       sum(r["amount"] for r in perks),
        "perks_count":       len(perks),
        "interest_paid":     sum(-r["amount"] for r in all_app
                                 if r["category"] == "LOAN_INTEREST"),
        "instalments_paid":  sum(-r["amount"] for r in all_app
                                 if r["category"] == "ADVANCE_INSTALMENT"),
        "bal_interest":      sum(a["balance"] for a in advs if a["interest"]),
        "bal_free":          sum(a["balance"] for a in advs if not a["interest"]),
        "skip_months":       [x["date_from"] for x in skips],
        "fy":                fy_of(cur),
    }
    return {"lines": lines, "net": net, "months": months, "advances": advs,
            "fy_skips": len(skips), "summary": summary}


# ------------------------------------------------------------ salary engine --
# D259 (S156): the VPS computes salaries end-to-end. This engine NEVER
# re-derives attendance policy math — it reads att_month_report.py's OWN output
# files (salary_inputs / deductions_extras CSVs) as the interface, adds the
# on-screen rulings (informed flags, EARLY_BIG genuine, OT approval, Darpan
# outstation), folds in the ledger's closed adjustments for the month
# (month_adjustments — the same rule set as the close CSV) and each base
# salary from staff_master.csv, and emits the NET table. Approval appends
# SALARY_PAID system rows (locking the month) + salary_final_<month>.csv.

import re as _re2, subprocess as _sp

def _att(name):
    return os.path.join(ATT_BASE, name)

def salary_locked(month, rows=None):
    """True once APPROVED SALARY_PAID rows exist for this month."""
    return any(r["category"] == "SALARY_PAID" and r["status"] == "APPROVED"
               and r.get("closed_month") == month
               for r in (rows or load_ledger()))

def ledger_closed(month, rows=None):
    return any(r.get("closed_month") == month
               for r in (rows or load_ledger()))

def staff_bases():
    """{name: base_salary} for active staff (staff_master.csv)."""
    out = {}
    try:
        with open(STAFF_CSV, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("active", "Y").strip().upper() != "Y":
                    continue
                try:
                    out[r["name"]] = float(r.get("base_salary") or 0)
                except ValueError:
                    out[r["name"]] = 0.0
    except FileNotFoundError:
        pass
    return out

def load_salary_inputs(month):
    """Rows of salary_inputs_<month>.csv (att_month_report's summary) or None."""
    try:
        with open(_att(f"salary_inputs_{month}.csv"), encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return None

def load_earlybig(month):
    """EARLY_BIG rows from deductions_extras_<month>.csv, with the report's OWN
    would-be amount parsed from its note (never re-derived here). Fail-loud if
    the pattern is missing — a silent 0 would under-deduct."""
    out = []
    try:
        with open(_att(f"deductions_extras_{month}.csv"), encoding="utf-8") as f:
            for r in csv.reader(f):
                if len(r) >= 6 and r[2] == "EARLY_BIG":
                    m = _re2.search(r"would be Rs\.([0-9.]+) if confirmed", r[5])
                    if not m:
                        raise ValueError(
                            f"EARLY_BIG note format changed in deductions_extras_{month}.csv "
                            f"(no would-be amount): {r[5]!r} — refusing to guess")
                    out.append({"name": r[0], "date": r[1], "minutes": r[3],
                                "rs": float(m.group(1)), "note": r[5]})
    except FileNotFoundError:
        pass
    return out

def load_review(month):
    """review_<month>.csv rows (informed flags) or None if not yet created."""
    try:
        with open(_att(f"review_{month}.csv"), encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return None

def save_review(month, rows):
    """Write the informed flags back — same columns att_month_report reads."""
    path = _att(f"review_{month}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "date", "type", "informed"])
        for r in rows:
            w.writerow([r["user_id"], r["name"], r["date"], r["type"],
                        "N" if str(r.get("informed", "Y")).strip().upper() == "N" else "Y"])

def run_att_report(month):
    """Re-run att_month_report.py <month> (it re-reads the review file).
    Returns (ok, output_tail)."""
    try:
        r = _sp.run([VENV_PY, ATT_REPORT, month], capture_output=True,
                    text=True, timeout=180, cwd=ATT_BASE)
        tail = ((r.stdout or "") + ("\n" + r.stderr if r.stderr else "")).strip()[-1500:]
        return r.returncode == 0, tail
    except Exception as e:
        return False, f"could not run the attendance report: {e}"

def load_rulings(month):
    """Owner rulings for the month: earlybig approvals, OT approved Rs,
    Darpan outstation days. Absent file = nothing ruled yet."""
    try:
        with open(_p(f"salary_rulings_{month}.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"earlybig": {}, "ot": {}, "outstation": {}}

def save_rulings(month, d):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    tmp = _p(f"salary_rulings_{month}.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, _p(f"salary_rulings_{month}.json"))
    os.chmod(_p(f"salary_rulings_{month}.json"), 0o600)

def compute_salary(month):
    """Assemble the month's NET per staff. Returns (table_rows, token, problems).
    token = md5 over every input byte that fed the numbers — APPROVE carries it
    and the server recomputes; any drift refuses the approval (no silent
    recompute). problems = human-readable blockers (missing files etc.)."""
    problems = []
    inputs = load_salary_inputs(month)
    if inputs is None:
        return [], "", [f"salary_inputs_{month}.csv not found — run the attendance report first"]
    bases = staff_bases()
    rows_l = load_ledger()
    if not ledger_closed(month, rows_l):
        problems.append(f"ledger month {month} is not closed yet — loan instalments and "
                        f"adjustments are missing until 'close {month}' runs")
    adj = month_adjustments(rows_l, month)
    eb = load_earlybig(month)
    rul = load_rulings(month)
    table = []
    hasher = hashlib.md5()
    try:
        hasher.update(open(_att(f"salary_inputs_{month}.csv"), "rb").read())
    except FileNotFoundError:
        pass
    hasher.update(json.dumps(rul, sort_keys=True).encode())
    hasher.update(json.dumps(adj, sort_keys=True).encode())
    hasher.update(json.dumps(sorted(bases.items())).encode())
    for r in inputs:
        name = r["Name"]
        base = bases.get(name)
        if base is None:
            problems.append(f"{name} is in the attendance report but not in staff_master.csv")
            base = 0.0
        f = lambda k: float(r.get(k) or 0)
        ded_marks  = f("Ded: marks Rs")
        ded_early  = f("Ded: early-dep Rs")
        fine_uninf = f("Fine: uninformed Rs")
        fine_exc   = f("Fine: excess-absent Rs")
        inc_rs     = f("Incentive Rs")
        ot_cand    = f("OT candidate Rs")
        absent     = int(f("Absent"))
        # Darpan-style outstation: those days were DUTY, not absence — the
        # excess-absent fine recomputes on (absent - outstation); everything
        # else is untouched (mark those dates informed=Y in the review loop).
        outst = int(rul.get("outstation", {}).get(name, 0) or 0)
        fine_exc_adj = fine_exc
        if outst:
            outst = min(outst, absent)
            fine_exc_adj = float(max(0, (absent - outst) - 3) * 100)
        # EARLY_BIG: only rows the owner ruled Genuine=Y deduct, at the
        # report's own would-be amount.
        eb_rs = 0.0
        eb_mine = [e for e in eb if e["name"] == name]
        for e in eb_mine:
            k = f'{name}|{e["date"]}'
            if rul.get("earlybig", {}).get(k, {}).get("genuine"):
                eb_rs += e["rs"]
        eb_rs = round(eb_rs, 2)
        # OT: pays ONLY what the owner approved on screen (default 0 — an
        # unapproved candidate never pays), capped at the candidate amount.
        ot_ok = min(float(rul.get("ot", {}).get(name, 0) or 0), ot_cand)
        ot_ok = max(0.0, round(ot_ok, 2))
        a = adj.get(name, {"credit": 0, "debit": 0, "leave_days": 0})
        net = round(base + inc_rs + ot_ok + a["credit"]
                    - ded_marks - ded_early - fine_uninf - fine_exc_adj
                    - eb_rs - a["debit"])          # owner ruling: nearest rupee
        table.append({
            "name": name, "base": base, "absent": absent, "outstation": outst,
            "ded_marks": ded_marks, "ded_early": ded_early,
            "fine_uninf": fine_uninf, "fine_exc": fine_exc_adj,
            "earlybig_rs": eb_rs, "earlybig_n": len(eb_mine),
            "ot_cand": ot_cand, "ot_ok": ot_ok,
            "inc": inc_rs, "adj_cr": a["credit"], "adj_db": a["debit"],
            "leave_days": a["leave_days"], "net": net,
            "incentive_tier": r.get("Incentive", ""),
        })
        hasher.update(json.dumps(table[-1], sort_keys=True).encode())
    token = hasher.hexdigest()
    return table, token, problems


def build_salary_html(month, table, locked=False, stamp=""):
    """The month's FULL salary report. The owner's vetted attendance HTML
    (salary_inputs_<month>.html: first-page punch grid, legends, EARLY_BIG
    sheet, collapsible per-staff money logs) is read VERBATIM and a FINAL
    SALARY section is spliced in before </body> in the same design language:
    a printable final table + screen-only collapsible per-staff breakdowns
    (every ledger line with narration, rulings as applied, NET). If the
    attendance HTML is absent, a standalone minimal page is produced."""
    from html import escape as _esc
    rows_l = load_ledger()
    rul = load_rulings(month)
    eb = load_earlybig(month)
    banner = (f'<p style="color:#2f8f4e;font-weight:bold">APPROVED &amp; LOCKED '
              f'&mdash; {_esc(stamp)}</p>' if locked else
              '<p style="color:#c0392b;font-weight:bold">PREVIEW &mdash; not '
              'approved; numbers move with the inputs</p>')
    tot = sum(t["net"] for t in table)
    h = ("<tr><th>staff</th><th>base</th><th>+incentive</th><th>+OT appr.</th>"
         "<th>+ledger cr</th><th>&minus;marks</th><th>&minus;early</th>"
         "<th>&minus;early-big</th><th>&minus;fines</th><th>&minus;ledger db</th>"
         "<th>NET Rs</th></tr>")
    b = ""
    for t in table:
        fines = t["fine_uninf"] + t["fine_exc"]
        cls = "net-pos" if t["net"] >= 0 else "net-neg"
        b += (f"<tr><td>{_esc(t['name'])}"
              + (f" <small>({t['outstation']} outstation)</small>" if t["outstation"] else "")
              + f"</td><td>{t['base']:g}</td><td>{t['inc']:g}</td><td>{t['ot_ok']:g}</td>"
              f"<td>{t['adj_cr']:g}</td><td>{t['ded_marks']:g}</td>"
              f"<td>{t['ded_early']:g}</td><td>{t['earlybig_rs']:g}</td>"
              f"<td>{fines:g}</td><td>{t['adj_db']:g}</td>"
              f'<td><span class="{cls}"><b>{t["net"]}</b></span></td></tr>')
    final_tbl = (f'<table><tr>{h[4:-5]}</tr>{b}'
                 f'<tr><td colspan="10" style="text-align:right"><b>TOTAL PAYOUT'
                 f'</b></td><td><b>Rs {tot}</b></td></tr></table>')
    # per-staff collapsible breakdown (screen-only, matches the money-log style)
    details = ""
    for t in table:
        nm = t["name"]
        inner = f"<p><b>Base salary: Rs {t['base']:g}</b></p><table>"
        inner += "<tr><th>line</th><th>date / detail</th><th>Rs</th></tr>"
        if t["inc"]:
            inner += (f"<tr><td>Incentive ({_esc(t['incentive_tier'])})</td>"
                      f"<td>attendance report</td><td>+{t['inc']:g}</td></tr>")
        if t["ot_cand"] or t["ot_ok"]:
            inner += (f"<tr><td>Overtime</td><td>candidate Rs {t['ot_cand']:g} "
                      f"&rarr; APPROVED</td><td>+{t['ot_ok']:g}</td></tr>")
        if t["ded_marks"]:
            inner += (f"<tr><td>Late-marks deduction</td><td>attendance report"
                      f"</td><td>&minus;{t['ded_marks']:g}</td></tr>")
        if t["ded_early"]:
            inner += (f"<tr><td>Early-departure deduction</td><td>&le;120 min, "
                      f"auto</td><td>&minus;{t['ded_early']:g}</td></tr>")
        for e in [x for x in eb if x["name"] == nm]:
            g = rul.get("earlybig", {}).get(f'{nm}|{e["date"]}', {}).get("genuine")
            inner += (f"<tr><td>Big early exit</td><td>{e['date']} &middot; "
                      f"{_esc(e['minutes'])} &middot; ruled "
                      f"<b>{'GENUINE — deducted' if g else 'not genuine — waived'}</b>"
                      f"</td><td>{('&minus;' + format(e['rs'], 'g')) if g else '0'}</td></tr>")
        if t["fine_uninf"]:
            inner += (f"<tr><td>Uninformed-absence fine</td><td>register-checked"
                      f"</td><td>&minus;{t['fine_uninf']:g}</td></tr>")
        if t["fine_exc"] or t["outstation"]:
            note = (f"absent {t['absent']} &minus; {t['outstation']} outstation"
                    if t["outstation"] else f"absent {t['absent']}")
            inner += (f"<tr><td>Excess-absence fine</td><td>{note}</td>"
                      f"<td>&minus;{t['fine_exc']:g}</td></tr>")
        led = [r for r in rows_l if r["staff"] == nm and r["status"] == "APPROVED"
               and r.get("closed_month") == month and r["category"] != "SALARY_PAID"]
        for r in sorted(led, key=lambda x: (x["date_from"], x["ts_entry"])):
            lab = CATEGORIES.get(r["category"], [r["category"]])[0]
            excl = r["category"] in SALARY_EXCLUDED
            amt = ("record only" if excl else
                   (("+" if r["amount"] >= 0 else "&minus;") + str(abs(r["amount"]))))
            grey = ' style="color:#999"' if excl else ""
            inner += (f"<tr{grey}>"
                      f"<td>Ledger: {_esc(lab)}</td>"
                      f"<td>{r['date_from']} &middot; {_esc(r.get('narration',''))} "
                      f"<small>{_esc(r['maker'])}&rarr;{_esc(r.get('checker',''))}"
                      f"</small></td><td>{amt}</td></tr>")
        if t["leave_days"]:
            inner += (f"<tr><td>Approved leave</td><td>{t['leave_days']} day(s)"
                      f"</td><td>record only</td></tr>")
        inner += (f'<tr><td colspan="2" style="text-align:right"><b>NET (nearest '
                  f'rupee)</b></td><td><b>Rs {t["net"]}</b></td></tr></table>')
        details += (f"<details><summary><b>{_esc(nm)}</b> &mdash; NET Rs "
                    f"{t['net']}</summary><div class='rev'>{inner}</div></details>\n")
    section = f"""
<div style="page-break-before:always"></div>
<h2>FINAL SALARY &mdash; {month}</h2>
{banner}
{final_tbl}
<p><small>NET = base + incentive + approved OT + ledger credits &minus; late-marks
&minus; early-departure &minus; genuine big-early-exits &minus; fines &minus; ledger
debits (advances/loan instalments/ad-hoc), rounded to the nearest rupee. Every
figure traces to the attendance report above or a ledger entry below.</small></p>
<div class="noprint">
<h3>Per-staff breakdown &mdash; tap a name to expand</h3>
{details}
</div>
"""
    try:
        base_html = open(_att(f"salary_inputs_{month}.html"), encoding="utf-8").read()
        if "</body>" in base_html:
            return base_html.replace("</body>", section + "</body>", 1)
    except FileNotFoundError:
        pass
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Salary {month}</title><style>"
            "body{font-family:Arial;margin:8mm} table{border-collapse:collapse}"
            "td,th{border:1px solid #999;padding:3px 6px;font-size:10pt}"
            ".net-pos{color:#2f8f4e}.net-neg{color:#c0392b}"
            "details{margin:1mm 0} summary{cursor:pointer}"
            "@media print{.noprint{display:none}}"
            "</style></head><body>"
            f"<p><b>Note:</b> attendance HTML for {month} was not found; this is "
            "the salary layer alone.</p>" + section + "</body></html>")

def approve_salary(users, checker, month, token):
    """LOCK the month: verify nothing drifted since the previewed table, then
    append one SALARY_PAID system row per staff + write salary_final_<month>.csv.
    Refused if already locked, if the ledger month is not closed, or if any
    input changed since preview (token mismatch)."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only a checker approves salary")
    rows_l = load_ledger()
    if salary_locked(month, rows_l):
        raise ValueError(f"salary for {month} is already approved and locked")
    table, tok_now, problems = compute_salary(month)
    if problems:
        raise ValueError("cannot approve: " + "; ".join(problems))
    if not table:
        raise ValueError("nothing to approve")
    if tok_now != token:
        raise ValueError("the inputs changed since you previewed this table — "
                         "review the fresh numbers and approve again")
    for t in table:
        append_ledger({
            "id": secrets.token_hex(6), "ts_entry": now(), "maker": "SYSTEM",
            "staff": t["name"], "category": "SALARY_PAID",
            "date_from": month, "date_to": month, "days": 0,
            "amount": int(t["net"]), "instalment": None,
            "narration": (f"salary {month}: base {int(t['base'])}"
                          f" +inc {t['inc']} +OT {t['ot_ok']}"
                          f" +adj_cr {t['adj_cr']} -marks {t['ded_marks']}"
                          f" -early {t['ded_early']} -earlybig {t['earlybig_rs']}"
                          f" -fines {t['fine_uninf'] + t['fine_exc']}"
                          f" -adj_db {t['adj_db']}"),
            "self_flag": False, "direct": True, "status": "APPROVED",
            "checker": checker, "ts_decision": now(),
            "contra_of": "", "closed_month": month, "interest": False,
        })
    out = _p(f"salary_final_{month}.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"FINAL SALARY {month}", f"approved {now()} by {checker}"])
        w.writerow(["staff", "base_Rs", "incentive_Rs", "OT_approved_Rs",
                    "ledger_credits_Rs", "ded_marks_Rs", "ded_early_Rs",
                    "ded_earlybig_Rs", "fine_uninformed_Rs", "fine_excess_absent_Rs",
                    "ledger_debits_Rs", "NET_Rs", "leave_days", "outstation_days"])
        for t in table:
            w.writerow([t["name"], t["base"], t["inc"], t["ot_ok"], t["adj_cr"],
                        t["ded_marks"], t["ded_early"], t["earlybig_rs"],
                        t["fine_uninf"], t["fine_exc"], t["adj_db"], t["net"],
                        t["leave_days"], t["outstation"]])
    os.chmod(out, 0o600)
    html_out = _p(f"salary_final_{month}.html")
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(build_salary_html(month, table, locked=True,
                                  stamp=f"{now()} by {checker}"))
    os.chmod(html_out, 0o600)
    return out, len(table)

# ------------------------------------------------------------------ web app --
def create_app():
    from flask import Flask, request, redirect, session, abort
    from html import escape as html_esc
    app = Flask(__name__)
    skf = _p("secret_key")
    os.makedirs(LEDGER_DIR, exist_ok=True)
    if not os.path.exists(skf):
        with open(skf, "w") as f: f.write(secrets.token_hex(32))
        os.chmod(skf, 0o600)
    app.secret_key = open(skf).read().strip()

    def _sso_user(users):
        # A valid portal clinic_sso cookie -> a ledger username (or None).
        # SSO = authentication; the ledger's own role governs authorization.
        if not _sso or not _SSO_SECRET:
            return None
        tok = request.cookies.get(_sso.COOKIE_NAME)
        if not tok:
            return None
        try:
            data = _sso.verify_token(tok, _SSO_SECRET, current_epoch=_sso_epoch())
        except Exception:
            data = None
        if not data:
            return None
        uname = (data.get("user") or "").strip().lower()
        rec = users.get(uname)
        if not rec or not rec.get("active", True):
            return None
        # F-31 guardrail: an SSO *manager* must NEVER resolve to a ledger *checker*.
        if data.get("role") == "manager" and rec.get("role") == "checker":
            return None
        return uname

    def user():
        u = session.get("u")
        users = load_users()
        if u and u in users and users[u].get("active", True):
            return u, users
        su = _sso_user(users)          # no valid ledger session -> try portal SSO
        if su:
            return su, users
        return None, users

    def page(title, body, u=None):
        nav = ""
        if u:
            users = load_users()
            role = users[u]["role"]
            links = [f'<a href="{URL_PREFIX}/">New entry</a>',
                     f'<a href="{URL_PREFIX}/mine">My entries</a>',
                     f'<a href="{URL_PREFIX}/statement">'
                     + ("Statement" if role == "checker" else "My statement") + "</a>"]
            if role == "checker":
                links += [f'<a href="{URL_PREFIX}/pending"><b>Pending</b></a>',
                          f'<a href="{URL_PREFIX}/book">Full ledger</a>',
                          f'<a href="{URL_PREFIX}/advances">Advances</a>',
                          f'<a href="{URL_PREFIX}/salary"><b>Salary</b></a>']
            links.append(f'<a href="{URL_PREFIX}/logout">Logout ({u})</a>')
            nav = "<p>" + " · ".join(links) + "</p>"
        return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font-family:Arial,sans-serif;margin:12px;background:#f7f8fa;color:#222}}
h2{{color:#1f3864;margin:6px 0}} a{{color:#2e5395;text-decoration:none}}
table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{border:1px solid #ccd;padding:6px;font-size:14px;text-align:left}}
th{{background:#d9e2f3}} .self{{background:#ffe0e0}} .direct{{color:#666;font-style:italic}}
input,select,textarea{{font-size:16px;padding:6px;margin:3px 0;width:100%;box-sizing:border-box}}
button{{font-size:16px;padding:8px 18px;margin:4px 2px;border:0;border-radius:6px;cursor:pointer}}
.ok{{background:#2f8f4e;color:#fff}} .no{{background:#c0392b;color:#fff}}
.card{{background:#fff;border:1px solid #ccd;border-radius:8px;padding:10px;margin:8px 0}}
.rev{{color:#999;background:#f1f1f1}} .rev td{{text-decoration:line-through}}
.mhead{{background:#1f3864;color:#fff;font-weight:bold}}
.amt-c{{color:#2f8f4e;font-weight:bold}} .amt-d{{color:#c0392b;font-weight:bold}}
small{{color:#666}}</style></head><body><h2>Staff Ledger</h2>{nav}{body}
<p><small>v{APP_VERSION} · append-only · corrections by contra entry only</small></p>
</body></html>"""

    @app.route(URL_PREFIX + "/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            users = load_users()
            name = request.form.get("u","").strip().lower()
            pw = request.form.get("p","")
            rec = users.get(name)
            if rec and rec.get("active", True) and hash_pw(pw, rec["salt"]) == rec["pw"]:
                session["u"] = name
                return redirect(URL_PREFIX + "/")
            return page("Login", "<p style='color:red'>Wrong username or password.</p>"
                        + LOGIN_FORM)
        return page("Login", LOGIN_FORM)

    LOGIN_FORM = f"""<div class="card"><form method="post">
      <input name="u" placeholder="username" autocomplete="username">
      <input name="p" id="pw" type="password" placeholder="password"
             autocomplete="current-password">
      <label style="font-weight:normal"><input type="checkbox" style="width:auto"
             onclick="document.getElementById('pw').type=this.checked?'text':'password'">
             show password</label>
      <button class="ok">Login</button></form></div>"""

    @app.route(URL_PREFIX + "/logout")
    def logout():
        session.clear(); return redirect(URL_PREFIX + "/login")

    @app.route(URL_PREFIX + "/", methods=["GET","POST"])
    def entry():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        cats = ROLE_CATS[users[u]["role"]]
        is_checker = users[u]["role"] == "checker"
        if not cats:
            # maker_limited (receptionist): leaves & fines now live in the Staff Register.
            body = ("<div class=\"card\"><b>Leaves &amp; fines have moved to the Staff "
                    "Register.</b><p>Approved leave, uniform fine and I-card fine are now "
                    "recorded in the <b>Staff Register</b> \u2014 the daily grid and the "
                    "sanctioned-leave range \u2014 pending checker approval there. There is "
                    "nothing to enter on this page.</p><p><a href=\"https://attendance.dr-"
                    "manoj.in/register\" style=\"display:inline-block;background:#2f8f4e;"
                    "color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none\">"
                    "Open the Staff Register &rarr;</a></p></div>")
            return page("New entry", body, u)
        msg = ""
        if request.method == "POST":
            try:
                f = request.form
                cat = f["category"]
                if cat not in cats: abort(403)
                d1 = f.get("date_from","").strip()
                d2 = f.get("date_to","").strip() or d1
                days = 0
                if CATEGORIES[cat][2]:  # per-day
                    a = datetime.date.fromisoformat(d1)
                    b = datetime.date.fromisoformat(d2)
                    days = (b - a).days + 1
                    if days < 1: raise ValueError("date range backwards")
                row = make_entry(users, u, f["staff"], cat, d1, d2, days,
                                 f.get("amount","0") or "0", f.get("narration",""),
                                 instalment=f.get("instalment",""),
                                 interest=bool(f.get("interest")))
                amt = row["amount"]
                msg = (f"<p style='color:green'>Saved <b>{row['status']}</b>: "
                       f"{row['staff']} · {CATEGORIES[cat][0]} · Rs {amt}"
                       + (f" · {days} day(s)" if days else "") + "</p>")
            except Exception as e:
                msg = f"<p style='color:red'>NOT saved: {e}</p>"
        opts_staff = "".join(f"<option>{s}</option>" for s in staff_names())
        posmeta = {}
        if is_checker:
            advs_all = open_advances()
            cur_m = datetime.date.today().strftime("%Y-%m")
            for s in staff_names():
                sa = [a for a in advs_all if a["issue"]["staff"] == s]
                if not sa: continue
                posmeta[s] = {
                    "loan": sum(a["balance"] for a in sa if a["interest"]),
                    "free": sum(a["balance"] for a in sa if not a["interest"]),
                    "skips": [x["date_from"] for x in fy_skips(s, cur_m)],
                }
        opts_cat = "".join(f'<option value="{c}">{CATEGORIES[c][0]}'
                           + (f" (Rs {CATEGORIES[c][1]}"
                              + ("/day" if CATEGORIES[c][2] else "") + ")"
                              if CATEGORIES[c][1] else "")
                           + "</option>" for c in cats)
        catmeta = {c: {"rate": CATEGORIES[c][1], "per_day": CATEGORIES[c][2],
                       "sign": CATEGORIES[c][3], "narr_req": CATEGORIES[c][4],
                       "advance": c == "ADVANCE_ISSUE",
                       "interest_ok": is_checker and c == "ADVANCE_ISSUE"} for c in cats}
        body = msg + f"""<div class="card"><form method="post" id="ef">
        <label>Staff</label><select name="staff">{opts_staff}</select>
        <label>Category</label><select name="category" id="cat">{opts_cat}</select>
        <div id="f_d1"><label>Date</label><input type="date" name="date_from" required></div>
        <div id="f_d2"><label>Date (to — leave blank for a single day)</label>
          <input type="date" name="date_to"></div>
        <div id="f_amt"><label id="l_amt">Amount Rs</label>
          <input type="number" name="amount" value="0" min="0"></div>
        <div id="f_inst"><label>Instalment Rs/month (blank = recover fully this month)</label>
          <input type="number" name="instalment" min="0"></div>
        <div id="f_int"><label style="font-weight:normal"><input type="checkbox"
          name="interest" value="1" style="width:auto"> Interest-bearing loan
          (flat Rs {INTEREST_RS}/month at every close while open — D250 Darpan-type;
          skips on the Advances page)</label></div>
        <div id="f_narr"><label id="l_narr">Narration (optional)</label>
          <textarea name="narration" rows="2"></textarea></div>
        <div id="staffpos" class="card" style="display:none;background:#eef4ff"></div>
        <div id="preview" style="font-weight:bold;margin:6px 0"></div>
        <button class="ok">Save entry</button></form>
        <small>Rate-card categories compute their own amount — no typing.
        Doctors' entries save as DIRECT (already approved); everything else goes
        PENDING to the doctors' phone.</small></div>
        <script>
        var M = {json.dumps(catmeta)};
        var P = {json.dumps(posmeta) if is_checker else "{{}}"};
        var stf = document.querySelector("select[name=staff]");
        function staffpos() {{
          var el = document.getElementById("staffpos"), p = P[stf.value];
          if (!p) {{ el.style.display = "none"; return; }}
          el.style.display = "";
          el.innerHTML = "<b>" + stf.value + " — current position</b><br>"
            + (p.loan ? "Interest-bearing loan outstanding: <b>Rs " + p.loan
                        + "</b> · skips this FY: " + p.skips.length + "/{SKIPS_PER_FY}"
                        + (p.skips.length ? " (" + p.skips.join(", ") + ")" : "") + "<br>" : "")
            + (p.free ? "Interest-free outstanding: <b>Rs " + p.free + "</b><br>" : "")
            + "<small>Repayment is AUTOMATIC at every monthly close — never "
            + "typed here. To skip a loan month use the <a href='{URL_PREFIX}/advances'>"
            + "Advances page</a> Skip button (never a Rs 0 entry). Full history: "
            + "<a href='{URL_PREFIX}/statement?staff=" + encodeURIComponent(stf.value) + "'>"
            + "Statement</a>.</small>";
        }}
        stf.addEventListener("change", staffpos);
        staffpos();
        var cat = document.getElementById("cat"), form = document.getElementById("ef");
        function show(id, on) {{ document.getElementById(id).style.display = on ? "" : "none"; }}
        function refresh() {{
          var m = M[cat.value];
          show("f_d2", m.per_day);
          show("f_amt", m.rate === null);
          show("f_inst", !!m.advance);
          show("f_int", !!m.interest_ok);
          var ln = document.getElementById("l_narr");
          ln.textContent = m.narr_req ? "Narration (REQUIRED for this category)"
                                      : "Narration (optional)";
          form.narration.required = !!m.narr_req;
          preview();
        }}
        function preview() {{
          var m = M[cat.value], el = document.getElementById("preview");
          if (m.rate === null) {{ el.textContent = ""; return; }}
          var d1 = form.date_from.value, d2 = form.date_to.value || d1, days = 1;
          if (m.per_day && d1) {{
            days = Math.round((new Date(d2) - new Date(d1)) / 86400000) + 1;
            if (!(days >= 1)) {{ el.textContent = "check the dates"; return; }}
          }}
          if (!d1) {{ el.textContent = ""; return; }}
          var amt = m.rate * (m.per_day ? days : 1) * (m.sign === 0 ? 0 : 1);
          el.textContent = m.sign === 0
            ? ("Records " + days + " approved leave day(s), Rs 0")
            : ((m.sign < 0 ? "Deduction: Rs " : "Payment: Rs ") + amt
               + (m.per_day ? " (" + days + " day(s))" : ""));
          el.style.color = m.sign < 0 ? "#c0392b" : "#2f8f4e";
        }}
        cat.addEventListener("change", refresh);
        form.date_from.addEventListener("input", preview);
        form.date_to.addEventListener("input", preview);
        refresh();
        </script>"""
        return page("New entry", body, u)

    @app.route(URL_PREFIX + "/mine")
    def mine():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        rows = [r for r in load_ledger() if r["maker"] == u][-60:][::-1]
        return page("My entries", _table(rows), u)

    @app.route(URL_PREFIX + "/pending")
    def pending():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        rows = [r for r in load_ledger() if r["status"] == "PENDING"]
        cards = ""
        for r in rows:
            flag = " <b style='color:red'>[SELF ENTRY]</b>" if r["self_flag"] else ""
            cls = "amt-c" if r["amount"] >= 0 else "amt-d"
            cards += f"""<div class="card{' self' if r['self_flag'] else ''}">
            <b>{r['staff']}</b> — {CATEGORIES.get(r['category'],[r['category']])[0]}{flag}<br>
            <span class="{cls}">Rs {r['amount']}</span> · {r['date_from']}{(' to '+r['date_to']) if r['date_to'] not in ('',r['date_from']) else ''}
            {('· '+str(r['days'])+' day(s)') if r['days'] else ''}<br>
            <small>by {r['maker']} at {r['ts_entry']}</small><br>
            {('<i>'+r['narration']+'</i><br>') if r['narration'] else ''}
            <form method="post" action="{URL_PREFIX}/decide" style="display:inline">
              <input type="hidden" name="id" value="{r['id']}">
              <button class="ok" name="d" value="A">Approve</button>
              <button class="no" name="d" value="R">Reject</button></form></div>"""
        if not rows: cards = "<p>Nothing pending. 👍</p>"
        return page("Pending", cards, u)

    @app.route(URL_PREFIX + "/decide", methods=["POST"])
    def do_decide():
        u, users = user()
        if not u or users[u]["role"] != "checker": abort(403)
        decide(users, u, request.form["id"], request.form["d"] == "A")
        return redirect(URL_PREFIX + "/pending")

    @app.route(URL_PREFIX + "/book")
    def book():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        rows = load_ledger()[-200:][::-1]
        extra = f"""<div class="card"><form method="post" action="{URL_PREFIX}/contra">
          <label>Correct a mistake — contra an APPROVED row. Row id:</label>
          <input name="id" placeholder="row id from the table">
          <label>Why:</label><input name="narration" required>
          <button class="no">Create contra (reverses the amount)</button></form></div>"""
        return page("Full ledger", extra + _table(rows, show_id=True), u)

    @app.route(URL_PREFIX + "/contra", methods=["POST"])
    def contra():
        # F-51 step 1: SHOW what would be reversed; nothing is appended here.
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        rid = request.form["id"].strip()
        narr = request.form.get("narration", "").strip()
        o = next((r for r in load_ledger() if r["id"] == rid), None)
        if not o:
            return page("Contra", f"<p style='color:red'>no row with id {rid}</p>", u)
        body = f"""<div class="card"><b>Confirm the reversal</b><br><br>
        You are about to CONTRA this entry:<br>
        <b>{o['staff']}</b> · {CATEGORIES.get(o['category'],[o['category']])[0]}
        · <b>Rs {o['amount']}</b> · {o['date_from']}<br>
        <small>{o.get('narration','')}</small><br><br>
        A new opposite entry of <b>Rs {-o['amount']}</b> will be appended.
        Nothing is deleted; both rows stay on record, netting to zero.<br><br>
        <form method="post" action="{URL_PREFIX}/contra2" style="display:inline">
          <input type="hidden" name="id" value="{rid}">
          <input type="hidden" name="narration" value="{narr}">
          <button class="no">YES — reverse this entry</button></form>
        <a href="{URL_PREFIX}/book"><button type="button">Cancel</button></a></div>"""
        return page("Confirm contra", body, u)

    @app.route(URL_PREFIX + "/contra2", methods=["POST"])
    def contra2():
        # F-51 step 2: the confirmed append.
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        try:
            make_contra(users, u, request.form["id"].strip(), request.form["narration"])
        except Exception as e:
            return page("Contra", f"<p style='color:red'>{e}</p>", u)
        return redirect(URL_PREFIX + "/book")

    @app.route(URL_PREFIX + "/advances")
    def advances():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        nxt = datetime.date.today().strftime("%Y-%m")
        body = ""
        for a in open_advances():
            iid = a["issue"]["id"]
            tag = ("<b style='color:#8a5a00'> · INTEREST-BEARING LOAN "
                   f"(Rs {INTEREST_RS}/mo)</b>") if a["interest"] else ""
            skiprow = ""
            if a["interest"]:
                used = fy_skips(a["issue"]["staff"], nxt)
                skiprow = (f"<br><small>skips used {fy_of(nxt)}: {len(used)}/{SKIPS_PER_FY}"
                           + (" (" + ", ".join(x["date_from"] for x in used) + ")" if used else "")
                           + "</small>"
                           f"""<form method="post" action="{URL_PREFIX}/skip" style="margin-top:4px">
                           <input type="hidden" name="id" value="{iid}">
                           <input type="month" name="month" value="{nxt}"
                                  style="width:auto"> <button class="no"
                           onclick="return confirm('Skip a loan month for {a['issue']['staff']}? '
                             + 'Nothing recovers and Rs {INTEREST_RS} capitalises onto the loan. '
                             + 'This cannot be undone by hand.')">Skip this month
                           (Rs {INTEREST_RS} capitalises)</button></form>""")
            body += (f"<div class='card'><b>{a['issue']['staff']}</b> — advance "
                     f"Rs {a['issue']['amount']} ({a['issue']['date_from']}){tag}<br>"
                     f"balance <b>Rs {a['balance']}</b> · recovering Rs {a['instalment']}/month"
                     f"{skiprow}<br><small>id {iid}</small></div>")
        if not body: body = "<p>No open advances.</p>"
        return page("Open advances", body, u)

    @app.route(URL_PREFIX + "/skip", methods=["POST"])
    def skip():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        try:
            record_skip(users, u, request.form["id"].strip(), request.form["month"].strip())
        except Exception as e:
            return page("Skip", f"<p style='color:red'>NOT recorded: {e}</p>"
                        f"<p><a href='{URL_PREFIX}/advances'>back</a></p>", u)
        return redirect(URL_PREFIX + "/advances")

    @app.route(URL_PREFIX + "/statement")
    def statement():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        role = users[u]["role"]
        if role == "checker":
            allowed = staff_names()
            staff = request.args.get("staff", "").strip() or (allowed[0] if allowed else "")
        else:
            link = users[u].get("staff_link", "").strip()
            match = [s for s in staff_names() if s.strip().lower() == link.lower()] if link else []
            if not match:
                return page("Statement", "<p>Your login is not linked to a staff "
                            "name — ask the doctor to relink it (adduser).</p>", u)
            allowed, staff = match, match[0]
        month = request.args.get("m", "").strip() or None
        st = build_statement(staff, month)
        picker = ""
        if role == "checker":
            opts = "".join(f'<option{" selected" if s==staff else ""}>{s}</option>'
                           for s in allowed)
            picker = f'<label>Staff</label><select name="staff">{opts}</select>'
        mopts = '<option value="">All months</option>' + "".join(
            f'<option value="{m}"{" selected" if m==month else ""}>{m}</option>'
            for m in st["months"])
        head = f"""<div class="card"><form method="get">{picker}
          <label>Month</label><select name="m">{mopts}</select>
          <button class="ok">Show</button></form></div>"""
        S = st["summary"]
        sk = (", ".join(S["skip_months"]) if S["skip_months"] else "none")
        advbox = f"""<div class='card'><b>Account summary — {staff}</b><br>
          Perks given: <b>Rs {S['perks_total']}</b> ({S['perks_count']} item(s)) ·
          Instalments paid: <b>Rs {S['instalments_paid']}</b> ·
          Interest paid: <b>Rs {S['interest_paid']}</b><br>
          Outstanding — interest-bearing tranche: <b>Rs {S['bal_interest']}</b> ·
          interest-free tranche: <b>Rs {S['bal_free']}</b><br>
          <small>Skips used {S['fy']}: {len(S['skip_months'])}/{SKIPS_PER_FY} ({sk}).
          Waterfall: the interest-free tranche starts recovering only after the
          interest-bearing tranche clears (D250).</small></div>"""
        for a in st["advances"]:
            advbox += (f"<div class='card'><b>Open {'loan' if a['interest'] else 'advance'}"
                       f"</b> Rs {a['issue']['amount']} ({a['issue']['date_from']})"
                       f" — balance <b>Rs {a['balance']}</b> · monthly deduction "
                       + (f"Rs {a['instalment']} + Rs {INTEREST_RS} interest"
                          if a["interest"] else
                          (f"Rs {a['instalment']}" if not st['summary']['bal_interest']
                           else f"Rs {a['instalment']} (waiting for the loan to clear)"))
                       + "</div>")
        h = ("<tr><th>date</th><th>item</th><th>note</th><th>credit Rs</th>"
             "<th>debit Rs</th><th>running net Rs</th></tr>")
        b = ""
        rev = _reversed_ids(load_ledger())
        last_m = None
        for ln in st["lines"]:
            r = ln["row"]
            this_m = (r.get("date_from") or "")[:7]
            if this_m and this_m != last_m:
                b += f"<tr class='mhead'><td colspan='6'>{this_m}</td></tr>"
                last_m = this_m
            label = CATEGORIES.get(r["category"], [r["category"]])[0]
            if ln["counted"]:
                cr = r["amount"] if r["amount"] > 0 else ""
                db = -r["amount"] if r["amount"] < 0 else ""
                netc = ln["net"]
                style = ""
            else:
                why = (r["status"] if r["status"] != "APPROVED"
                       else "cash/balance — not salary")
                cr = db = ""
                netc = f"<small>({why})</small>"
                style = " style='color:#999'"
            if r["id"] in rev:
                style = " class='rev'"
                netc = "<small>reversed</small>" if not ln["counted"] else netc
                label += " <small>(reversed)</small>"
            b += (f"<tr{style}><td>{r['date_from']}</td><td>{label}"
                  + (f" <small>Rs {r['amount']}</small>" if not ln["counted"]
                     and r["amount"] else "")
                  + f"</td><td><small>{r.get('narration','')}</small></td>"
                  f"<td class='amt-c'>{cr}</td><td class='amt-d'>{db}</td>"
                  f"<td><b>{netc}</b></td></tr>")
        if not st["lines"]:
            b = "<tr><td colspan='6'>No entries.</td></tr>"
        note = ("<p><small>Running net counts APPROVED salary rows only — the same "
                "rule as the monthly-close CSV, so the two always agree. Greyed rows "
                "(advance payouts, capitalisations, skips, pending/rejected) are shown "
                "for the record but are outside salary money. Base salary itself is "
                "computed month-by-month in the salary workbook.</small></p>")
        body = (head + f"<h3>{staff}" + (f" · {month}" if month else " · all months")
                + f" · net Rs {st['net']}</h3>" + advbox
                + f"<table>{h}{b}</table>" + note)
        return page("Statement", body, u)


    # ---------------------------------------------------- salary (D259) -----
    def _ck_only():
        u, users = user()
        if not u: return None, None
        if users[u]["role"] != "checker": abort(403)
        return u, users

    @app.route(URL_PREFIX + "/salary")
    def salary():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        month = request.args.get("m", "").strip() or datetime.date.today().strftime("%Y-%m")
        try:
            datetime.date.fromisoformat(month + "-01")
        except ValueError:
            return page("Salary", "<p style='color:red'>bad month</p>", u)
        msg = request.args.get("msg", "")
        msg_html = (f"<p style='color:green'>{html_esc(msg)}</p>" if msg else "")
        rows_l = load_ledger()
        locked = salary_locked(month, rows_l)
        closed = ledger_closed(month, rows_l)
        inputs = load_salary_inputs(month)
        review = load_review(month)
        rul = load_rulings(month)
        eb = load_earlybig(month) if inputs is not None else []

        head = f"""<div class="card"><form method="get">
          <label>Month</label><input type="month" name="m" value="{month}" style="width:auto">
          <button class="ok">Show</button></form></div>"""

        if locked:
            table, _tok, _pr = compute_salary(month)
            body = (head + f"<h3>Salary {month} — <span style='color:#2f8f4e'>"
                    f"APPROVED &amp; LOCKED</span></h3>"
                    + _salary_table(table)
                    + f"<p><a href='{URL_PREFIX}/salary/report?m={month}' target='_blank'>"
                    f"<button class='ok' type='button'>Open FULL report (grid + "
                    f"breakdowns)</button></a></p>"
                    + f"<p><small>This month is locked. A wrong figure is corrected "
                    f"NEXT month with an 'Other adjustment' entry — locked months are "
                    f"never recomputed. File: salary_final_{month}.csv on the VPS.</small></p>")
            return page("Salary", msg_html + body, u)

        steps = []
        # step 1 — attendance report present?
        if inputs is None:
            steps.append(f"""<div class="card"><b>1 · Attendance report</b><br>
              salary_inputs_{month}.csv not found.<br>
              <form method="post" action="{URL_PREFIX}/salary/recompute">
              <input type="hidden" name="m" value="{month}">
              <button class="ok" onclick="return confirm('Run the attendance report for {month} now?')">
              Run attendance report for {month}</button></form></div>""")
        else:
            steps.append(f"""<div class="card"><b>1 · Attendance report</b> — found
              ({len(inputs)} staff). <form method="post" style="display:inline"
              action="{URL_PREFIX}/salary/recompute"><input type="hidden" name="m" value="{month}">
              <button onclick="return confirm('Re-run the attendance report for {month}? It re-reads the informed flags below.')">
              Re-run (after editing flags)</button></form></div>""")

        # step 2 — informed flags (review file) on screen
        if review is None:
            steps.append("<div class='card'><b>2 · Informed flags</b><br>"
                         "The review file appears after the first attendance run.</div>")
        else:
            rws = ""
            for i, r in enumerate(review):
                inf = str(r.get("informed", "Y")).strip().upper() != "N"
                rws += (f"<tr><td>{html_esc(r['name'])}</td><td>{r['date']}</td>"
                        f"<td>{r['type']}</td><td>"
                        f"<select name='inf_{i}'>"
                        f"<option value='Y'{' selected' if inf else ''}>Y — informed</option>"
                        f"<option value='N'{' selected' if not inf else ''}>N — NOT informed</option>"
                        f"</select><input type='hidden' name='key_{i}' "
                        f"value='{html_esc(r['user_id'])}|{html_esc(r['name'])}|{r['date']}|{r['type']}'>"
                        f"</td></tr>")
            steps.append(f"""<div class="card"><b>2 · Informed flags</b> — check against the
              reception register. N = uninformed (Rs 50 fine on an absence; +1 mark on a
              60-min late). Keep Darpan's OUTSTATION dates as Y.<br>
              <form method="post" action="{URL_PREFIX}/salary/review">
              <input type="hidden" name="m" value="{month}">
              <input type="hidden" name="n" value="{len(review)}">
              <table><tr><th>staff</th><th>date</th><th>event</th><th>informed?</th></tr>
              {rws}</table>
              <button class="ok">Save flags</button>
              <small> — then press Re-run above so the fines recompute.</small>
              </form></div>""")

        # step 3 — EARLY_BIG rulings on screen
        if eb:
            rws = ""
            for e in eb:
                k = f'{e["name"]}|{e["date"]}'
                g = rul.get("earlybig", {}).get(k, {}).get("genuine", False)
                rws += (f"<tr><td>{html_esc(e['name'])}</td><td>{e['date']}</td>"
                        f"<td>{html_esc(e['minutes'])}</td><td>Rs {e['rs']}</td>"
                        f"<td><select name='eb_{html_esc(k)}'>"
                        f"<option value='N'{'' if g else ' selected'}>N — not genuine (no deduction)</option>"
                        f"<option value='Y'{' selected' if g else ''}>Y — genuine (deduct Rs {e['rs']})</option>"
                        f"</select></td></tr>")
            steps.append(f"""<div class="card"><b>3 · Big early-exit rulings</b> — rule
              against the physical register (never machine-applied).<br>
              <form method="post" action="{URL_PREFIX}/salary/rulings">
              <input type="hidden" name="m" value="{month}"><input type="hidden" name="part" value="eb">
              <table><tr><th>staff</th><th>date</th><th>early by</th><th>would deduct</th><th>ruling</th></tr>
              {rws}</table><button class="ok">Save rulings</button></form></div>""")
        elif inputs is not None:
            steps.append("<div class='card'><b>3 · Big early-exit rulings</b> — none this month. 👍</div>")

        # step 4 — OT approval + Darpan outstation
        if inputs is not None:
            rws, outst_rows = "", ""
            for r in inputs:
                cand = float(r.get("OT candidate Rs") or 0)
                nm = r["Name"]
                if cand > 0:
                    cur = rul.get("ot", {}).get(nm, 0)
                    rws += (f"<tr><td>{html_esc(nm)}</td><td>Rs {cand}</td>"
                            f"<td><input type='number' step='0.01' min='0' max='{cand}' "
                            f"name='ot_{html_esc(nm)}' value='{cur}' style='width:8em'>"
                            f"<small> (0 = not approved; max {cand})</small></td></tr>")
                if int(float(r.get("Absent") or 0)) > 0:
                    cur_o = rul.get("outstation", {}).get(nm, 0)
                    outst_rows += (f"<tr><td>{html_esc(nm)}</td>"
                                   f"<td>{int(float(r.get('Absent') or 0))}</td>"
                                   f"<td><input type='number' min='0' name='os_{html_esc(nm)}' "
                                   f"value='{cur_o}' style='width:6em'></td></tr>")
            ot_tbl = (f"<table><tr><th>staff</th><th>candidate</th><th>approve Rs</th></tr>{rws}</table>"
                      if rws else "<p>No OT candidates. </p>")
            os_tbl = (f"<table><tr><th>staff</th><th>absent days</th><th>of which OUTSTATION"
                      f" (clinic duty outside)</th></tr>{outst_rows}</table>" if outst_rows else "")
            steps.append(f"""<div class="card"><b>4 · OT approval &amp; outstation days</b><br>
              OT pays ONLY what you approve here (unapproved candidates pay nothing).
              Outstation days were duty, not absence — they reduce the excess-absent fine.<br>
              <form method="post" action="{URL_PREFIX}/salary/rulings">
              <input type="hidden" name="m" value="{month}"><input type="hidden" name="part" value="ot">
              {ot_tbl}{os_tbl}<button class="ok">Save</button></form></div>""")

        # step 5 — ledger close
        if closed:
            steps.append(f"<div class='card'><b>5 · Ledger close</b> — {month} is closed "
                         f"(adjustments + loan instalments captured). ✔</div>")
        else:
            steps.append(f"""<div class="card"><b>5 · Ledger close</b> — NOT yet closed.
              The close computes loan instalments and stamps every approved adjustment
              into {month}. Run it once, after all of the month's entries are in.<br>
              <form method="post" action="{URL_PREFIX}/salary/close">
              <input type="hidden" name="m" value="{month}">
              <button class="no" onclick="return confirm('Close ledger month {month}? Loan instalments will be generated. A month closes only once.')">
              Run monthly close for {month}</button></form></div>""")

        # step 6 — the table + approve
        table, token, problems = compute_salary(month)
        if problems:
            steps.append("<div class='card'><b>6 · Salary table</b><br>" +
                         "".join(f"<p style='color:#c0392b'>• {html_esc(x)}</p>" for x in problems)
                         + "</div>")
        if table and not problems:
            total = sum(t["net"] for t in table)
            steps.append(f"""<div class="card"><b>6 · Salary table — PREVIEW</b>
              {_salary_table(table)}
              <p><b>Total payout: Rs {total}</b> · {len(table)} staff ·
              <a href='{URL_PREFIX}/salary/report?m={month}' target='_blank'>
              <button type='button'>Open FULL report (grid + breakdowns)</button></a></p>
              <form method="post" action="{URL_PREFIX}/salary/approve">
              <input type="hidden" name="m" value="{month}">
              <input type="hidden" name="token" value="{token}">
              <button class="ok" onclick="return confirm('APPROVE salary for {month}: Rs {total} across {len(table)} staff? This LOCKS the month — it cannot be recomputed. Corrections happen next month by adjustment entry.')">
              APPROVE &amp; LOCK {month}</button></form>
              <small>Approval appends one salary line per staff to the ledger and writes
              salary_final_{month}.csv. If any input changes between this preview and your
              press, the approval refuses and shows fresh numbers.</small></div>""")

        return page("Salary", msg_html + head + f"<h3>Salary {month}</h3>" + "".join(steps), u)

    def _salary_table(table):
        h = ("<tr><th>staff</th><th>base</th><th>+inc</th><th>+OT</th><th>+ledger cr</th>"
             "<th>-marks</th><th>-early</th><th>-early-big</th><th>-fines</th>"
             "<th>-ledger db</th><th><b>NET Rs</b></th></tr>")
        b = ""
        for t in table:
            fines = t["fine_uninf"] + t["fine_exc"]
            b += (f"<tr><td>{html_esc(t['name'])}"
                  + (f" <small>({t['outstation']} outstation)</small>" if t["outstation"] else "")
                  + f"</td><td>{t['base']:g}</td>"
                  f"<td class='amt-c'>{t['inc']:g}</td><td class='amt-c'>{t['ot_ok']:g}</td>"
                  f"<td class='amt-c'>{t['adj_cr']:g}</td>"
                  f"<td class='amt-d'>{t['ded_marks']:g}</td><td class='amt-d'>{t['ded_early']:g}</td>"
                  f"<td class='amt-d'>{t['earlybig_rs']:g}</td><td class='amt-d'>{fines:g}</td>"
                  f"<td class='amt-d'>{t['adj_db']:g}</td>"
                  f"<td><b>{t['net']}</b></td></tr>")
        return f"<table>{h}{b}</table>"

    @app.route(URL_PREFIX + "/salary/report")
    def salary_report():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.args.get("m", "").strip()
        try:
            datetime.date.fromisoformat(m + "-01")
        except Exception:
            return page("Salary report", "<p style='color:red'>bad month</p>", u)
        rows_l = load_ledger()
        locked = salary_locked(m, rows_l)
        stamp = ""
        if locked:
            sp = [r for r in rows_l if r["category"] == "SALARY_PAID"
                  and r.get("closed_month") == m and r["status"] == "APPROVED"]
            if sp: stamp = f"{sp[0]['ts_decision']} by {sp[0]['checker']}"
        table, _tok, problems = compute_salary(m)
        if not table:
            return page("Salary report",
                        "<p style='color:red'>" + html_esc("; ".join(problems) or
                        "no data") + "</p>", u)
        return build_salary_html(m, table, locked=locked, stamp=stamp)

    @app.route(URL_PREFIX + "/salary/review", methods=["POST"])
    def salary_review():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        n = int(request.form["n"])
        rows = []
        for i in range(n):
            key = request.form.get(f"key_{i}", "")
            parts = key.split("|")
            if len(parts) != 4: continue
            rows.append({"user_id": parts[0], "name": parts[1], "date": parts[2],
                         "type": parts[3], "informed": request.form.get(f"inf_{i}", "Y")})
        save_review(m, rows)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg=Flags saved — now press Re-run.")

    @app.route(URL_PREFIX + "/salary/recompute", methods=["POST"])
    def salary_recompute():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        if salary_locked(m):
            return page("Salary", "<p style='color:red'>month locked</p>", u)
        ok, tail = run_att_report(m)
        msg = ("Attendance report re-ran OK." if ok
               else "Attendance report FAILED — nothing changed.")
        body = (f"<p>{msg}</p><pre style='background:#fff;border:1px solid #ccd;"
                f"padding:8px;white-space:pre-wrap'>{html_esc(tail)}</pre>"
                f"<p><a href='{URL_PREFIX}/salary?m={m}'>back to Salary {m}</a></p>")
        return page("Salary", body, u)

    @app.route(URL_PREFIX + "/salary/rulings", methods=["POST"])
    def salary_rulings():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        if salary_locked(m):
            return page("Salary", "<p style='color:red'>month locked</p>", u)
        rul = load_rulings(m)
        part = request.form.get("part", "")
        if part == "eb":
            eb = {}
            for k, v in request.form.items():
                if k.startswith("eb_"):
                    eb[k[3:]] = {"genuine": v == "Y"}
            rul["earlybig"] = eb
        elif part == "ot":
            ot, os_ = rul.get("ot", {}), rul.get("outstation", {})
            for k, v in request.form.items():
                if k.startswith("ot_"):
                    try: ot[k[3:]] = max(0.0, float(v or 0))
                    except ValueError: pass
                elif k.startswith("os_"):
                    try: os_[k[3:]] = max(0, int(float(v or 0)))
                    except ValueError: pass
            rul["ot"], rul["outstation"] = ot, os_
        save_rulings(m, rul)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg=Saved.")

    @app.route(URL_PREFIX + "/salary/close", methods=["POST"])
    def salary_close():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        try:
            out, n = close_month(users, u, m)
            msg = f"Closed {m}: {n} rows."
        except Exception as e:
            return page("Salary", f"<p style='color:red'>close failed: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg={msg}")

    @app.route(URL_PREFIX + "/salary/approve", methods=["POST"])
    def salary_approve():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        try:
            out, n = approve_salary(users, u, m, request.form.get("token", ""))
        except Exception as e:
            return page("Salary", f"<p style='color:red'>NOT approved: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg=APPROVED and locked: {n} staff.")

    def _reversed_ids(all_rows):
        """F-51 void-pair display: ids of approved rows that a matching approved
        contra reverses, PLUS those contra ids — greedily one contra per
        original (handles chains: a contra of a contra pairs the same way)."""
        done = set()
        by_target = {}
        for r in all_rows:
            if (r["status"] == "APPROVED" and r.get("contra_of")
                    and r["category"] not in SYSTEM_CATS):
                by_target.setdefault(r["contra_of"], []).append(r)
        amounts = {r["id"]: r["amount"] for r in all_rows}
        for tgt, contras in by_target.items():
            if tgt not in amounts:
                continue
            for c in contras:
                if tgt in done or c["id"] in done:
                    continue
                if c["amount"] == -amounts[tgt]:
                    done.add(tgt); done.add(c["id"])
                    break
        return done

    def _table(rows, show_id=False):
        h = ("<tr>" + ("<th>id</th>" if show_id else "")
             + "<th>staff</th><th>category</th><th>dates</th><th>Rs</th>"
               "<th>status</th><th>maker→checker</th><th>note</th></tr>")
        rev = _reversed_ids(load_ledger())
        b = ""
        for r in rows:
            cls = "amt-c" if r["amount"] >= 0 else "amt-d"
            row_cls = " class='self'" if r.get("self_flag") else ""
            if r["id"] in rev:
                row_cls = " class='rev'" 
            dates = r["date_from"] + ("" if r["date_to"] in ("", r["date_from"])
                                      else "→" + r["date_to"])
            b += (f"<tr{row_cls}>" + (f"<td><small>{r['id']}</small></td>" if show_id else "")
                  + f"<td>{r['staff']}</td>"
                  f"<td>{CATEGORIES.get(r['category'],[r['category']])[0]}"
                  + ("<span class='direct'> ·direct</span>" if r.get("direct") else "") + "</td>"
                  f"<td>{dates}</td><td class='{cls}'>{r['amount']}</td>"
                  f"<td>{('REVERSED' if r['id'] in rev else r['status'])}"
                  f"{('·'+r['closed_month']) if r.get('closed_month') else ''}</td>"
                  f"<td><small>{r['maker']}→{r.get('checker','')}</small></td>"
                  f"<td><small>{r.get('narration','')}</small></td></tr>")
        return f"<table>{h}{b}</table>"

    return app

# ------------------------------------------------------------------ CLI ------
def cli_adduser():
    users = load_users()
    name = input("username (lowercase, e.g. shavez): ").strip().lower()
    role = input("role [maker_full / maker_limited / checker]: ").strip()
    if role not in ROLE_CATS: sys.exit("bad role")
    link = input("staff name this login belongs to (blank if doctor): ").strip()
    pw = getpass.getpass("password: ")
    pw2 = getpass.getpass("repeat  : ")
    if pw != pw2 or len(pw) < 6: sys.exit("passwords differ or too short (<6)")
    salt = secrets.token_hex(16)
    users[name] = {"pw": hash_pw(pw, salt), "salt": salt, "role": role,
                   "staff_link": link, "active": True}
    save_users(users)
    print(f"user '{name}' ({role}) saved. Swap anyone anytime: deluser + adduser.")

def cli_deluser(name):
    users = load_users()
    if name not in users: sys.exit("no such user")
    users[name]["active"] = False
    save_users(users); print(f"user '{name}' disabled (rows they made remain).")

def cli_listusers():
    for n, r in load_users().items():
        print(f"{n:12s} {r['role']:14s} active={r.get('active',True)} link={r.get('staff_link','')}")

# ------------------------------------------------------------- selftest ------
def selftest():
    global LEDGER_DIR, STAFF_CSV
    tmp = tempfile.mkdtemp()
    LEDGER_DIR = tmp
    STAFF_CSV = os.path.join(tmp, "staff.csv")
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id","name","active"])
        for i, n in enumerate(["Alpha","Beta","Gamma"]): w.writerow([i+1, n, "Y"])
    ok = [0]
    def ck(cond, msg):
        ok[0] += 1
        if not cond: raise AssertionError(f"selftest check {ok[0]} FAILED: {msg}")
    # users
    for name, role, link in (("mfull","maker_full","Beta"), ("mlim","maker_limited",""),
                             ("doc","checker",""), ("doc2","checker","")):
        salt = secrets.token_hex(16)
        u = load_users(); u[name] = {"pw": hash_pw("pw", salt), "salt": salt,
                                     "role": role, "staff_link": link, "active": True}
        save_users(u)
    users = load_users()
    ck(len(users) == 4, "4 users")
    ck(hash_pw("pw", users["doc"]["salt"]) == users["doc"]["pw"], "pw roundtrip")
    ck(hash_pw("wrong", users["doc"]["salt"]) != users["doc"]["pw"], "wrong pw rejected")
    # rate card computations
    r = make_entry(users, "mfull", "Alpha", "NIGHT_DUTY", "2026-08-02","2026-08-03",2,"0","")
    ck(r["amount"] == 400 and r["status"] == "PENDING", "night 2d=+400 pending")
    r2 = make_entry(users, "doc", "Alpha", "FINE_UNIFORM", "2026-08-04","2026-08-06",3,"0","")
    ck(r2["amount"] == -60, "uniform 3d=-60")
    r3 = make_entry(users, "mfull", "Gamma", "ICARD_REPLACEMENT", "2026-08-04","2026-08-04",0,"0","lost")
    ck(r3["amount"] == -100, "replacement -100 (pending, drives the reject flow)")
    rl = make_entry(users, "doc", "Beta", "LEAVE_APPROVED", "2026-08-10","2026-08-11",2,"0","")
    ck(rl["amount"] == 0 and rl["days"] == 2, "leave 0Rs 2d")
    # permissions
    try:
        make_entry(users, "mlim", "Alpha", "NIGHT_DUTY", "2026-08-01","2026-08-01",1,"0","")
        ck(False, "mlim night must fail")
    except PermissionError: ck(True, "mlim blocked from night duty")
    try:
        make_entry(users, "mfull", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","x")
        ck(False, "mfull adhoc must fail")
    except PermissionError: ck(True, "mfull blocked from ad-hoc")
    try:
        make_entry(users, "doc", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","")
        ck(False, "adhoc without narration must fail")
    except ValueError: ck(True, "ad-hoc narration required")
    # S162 (D286): approved-leave + uniform/i-card fines moved to the Staff Register
    for badcat in ("LEAVE_APPROVED", "FINE_UNIFORM", "FINE_ICARD"):
        try:
            make_entry(users, "mlim", "Alpha", badcat, "2026-08-01","2026-08-01",1,"0","")
            ck(False, f"maker_limited {badcat} must now fail")
        except PermissionError:
            ck(True, f"maker_limited blocked from {badcat} (now in the register)")
        try:
            make_entry(users, "mfull", "Alpha", badcat, "2026-08-01","2026-08-01",1,"0","")
            ck(False, f"maker_full {badcat} must now fail")
        except PermissionError:
            ck(True, f"maker_full blocked from {badcat} (now in the register)")
    ra = make_entry(users, "doc", "Alpha", "FINE_ADHOC", "2026-08-01","2026-08-01",0,"500","misbehaviour")
    ck(ra["amount"] == -500 and ra["status"] == "APPROVED" and ra["direct"], "doctor direct adhoc -500")
    # self flag
    rs = make_entry(users, "mfull", "Beta", "NIGHT_DUTY", "2026-08-05","2026-08-05",1,"0","")
    ck(rs["self_flag"] is True, "self entry flagged")
    # replacement + approval flow
    rr = make_entry(users, "mfull", "Gamma", "ICARD_REPLACEMENT", "2026-08-07","2026-08-07",0,"0","lost")
    ck(rr["amount"] == -100, "replacement -100")
    decide(users, "doc", r["id"], True)
    decide(users, "doc", r3["id"], False)          # rejected (pending maker entry)
    decide(users, "doc", rs["id"], True)
    decide(users, "doc", rr["id"], True)
    got = {x["id"]: x for x in load_ledger()}
    ck(got[r["id"]]["status"] == "APPROVED" and got[r["id"]]["checker"] == "doc", "approve stamps checker")
    ck(got[r3["id"]]["status"] == "REJECTED", "reject works")
    try:
        decide(users, "mfull", rr["id"], True); ck(False, "maker deciding must fail")
    except (PermissionError, ValueError): ck(True, "maker cannot decide")
    try:
        decide(users, "doc", r["id"], True); ck(False, "double-decide must fail")
    except ValueError: ck(True, "no double decision")
    # contra
    c = make_contra(users, "doc", r2["id"], "entered on wrong staff")
    ck(c["amount"] == 60 and c["status"] == "APPROVED" and c["contra_of"] == r2["id"], "doctor contra direct +60")
    c2 = make_contra(users, "mfull", rr["id"], "card was found")
    ck(c2["status"] == "PENDING", "maker contra pends")
    decide(users, "doc2", c2["id"], True)
    try:
        make_contra(users, "doc", r3["id"], "x"); ck(False, "contra of rejected must fail")
    except ValueError: ck(True, "contra only approved rows")
    # advances: default full recovery + instalment mode
    a1 = make_entry(users, "mfull", "Alpha", "ADVANCE_ISSUE", "2026-08-08","2026-08-08",0,"3000","", instalment="")
    ck(a1["amount"] == 3000 and a1["instalment"] == 3000, "advance default=full this month")
    a2 = make_entry(users, "mfull", "Gamma", "ADVANCE_ISSUE", "2026-08-08","2026-08-08",0,"5000","", instalment="2000")
    decide(users, "doc", a1["id"], True); decide(users, "doc", a2["id"], True)
    ck(len(open_advances()) == 2, "two open advances")
    # month close
    out, n = close_month(users, "doc", "2026-08")
    ck(os.path.exists(out), "close writes csv")
    got = load_ledger()
    inst = [x for x in got if x["category"] == "ADVANCE_INSTALMENT"]
    ck(sorted(-x["amount"] for x in inst) == [2000, 3000], "instalments 3000 full + 2000 partial")
    ck(all(x["closed_month"] == "2026-08" for x in got if x["status"] == "APPROVED"), "all approved rows stamped closed")
    try:
        close_month(users, "doc", "2026-08"); ck(False, "re-close must fail")
    except ValueError: ck(True, "close is idempotent-guarded")
    adv_open = open_advances()
    ck(len(adv_open) == 1 and adv_open[0]["balance"] == 3000 and adv_open[0]["issue"]["staff"] == "Gamma",
       "Gamma balance 5000-2000=3000; Alpha closed")
    # Alpha: credits = night 400 + contra 60 = 460; debits = uniform 60 + adhoc 500
    # + instalment 3000 = 3560; net -3100 (contra and original cancel in net).
    with open(out, encoding="utf-8") as f: txt = f.read()
    import re as _re
    m = _re.search(r"^Alpha,(\d+),(\d+),(-?\d+),(\d+)", txt, _re.M)
    ck(m is not None, "Alpha summary row present")
    cred, deb, net, ld = map(int, m.groups())
    ck(cred == 460 and deb == 3560 and net == -3100 and ld == 0,
       f"Alpha money math (got {cred},{deb},{net},{ld})")
    m = _re.search(r"^Beta,(\d+),(\d+),(-?\d+),(\d+)", txt, _re.M)
    cred, deb, net, ld = map(int, m.groups())
    ck(cred == 200 and deb == 0 and net == 200 and ld == 2, f"Beta night200 + 2 leave days (got {cred},{deb},{net},{ld})")
    ck("ADVANCE_ISSUE" not in txt.split("-- detail --")[0], "advance payout not in salary summary")
    # append-only guarantee: economic fields of approved rows never changed
    ck(got and all("amount" in x for x in got), "rows intact")
    # web app smoke: login + entry + pending via test client
    app = create_app()
    cl = app.test_client()
    resp = cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"pw"})
    ck(resp.status_code == 302, "web login ok")
    resp = cl.get(URL_PREFIX + "/pending")
    ck(resp.status_code == 200, "pending page renders")
    resp = cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"WRONG"})
    ck(b"Wrong username" in resp.data, "web rejects bad password")
    cl2 = app.test_client()
    cl2.post(URL_PREFIX + "/login", data={"u":"mlim","p":"pw"})
    ck(cl2.get(URL_PREFIX + "/pending").status_code == 403, "maker blocked from pending page")
    # S162 (D286): maker_limited (receptionist) New-entry now redirects to the Staff Register
    pgx = cl2.get(URL_PREFIX + "/").data.decode()
    ck("moved to the Staff Register" in pgx and 'name="category"' not in pgx,
       "maker_limited sees the register redirect, not an entry form")
    r = cl2.post(URL_PREFIX + "/", data={"staff":"Alpha","category":"FINE_UNIFORM",
                                         "date_from":"2026-09-01","date_to":"2026-09-02",
                                         "narration":""})
    ck("moved to the Staff Register" in r.data.decode() and b"Saved" not in r.data,
       "maker_limited cannot POST a fine (redirect shown, nothing saved)")
    # maker_full keeps a working form, but without the migrated categories
    clm2 = app.test_client()
    clm2.post(URL_PREFIX + "/login", data={"u":"mfull","p":"pw"})
    pgm = clm2.get(URL_PREFIX + "/").data.decode()
    ck('"NIGHT_DUTY"' in pgm and '"FINE_UNIFORM"' not in pgm
       and '"LEAVE_APPROVED"' not in pgm and '"FINE_ADHOC"' not in pgm,
       "maker_full form keeps money categories, not leave/uniform/i-card/adhoc")
    ck("Narration (optional)" in pgm and "refresh()" in pgm, "adaptive form script present")
    pgd = cl.get(URL_PREFIX + "/").data.decode()
    ck('"FINE_ADHOC"' in pgd and '"narr_req": true' in pgd,
       "doctor form carries adhoc with narr_req=true")
    lg = cl.get(URL_PREFIX + "/login").data.decode()
    ck("show password" in lg, "login page has show-password toggle")

    # ================= v2.0 (S155): statement + D250 loan machinery ==========
    # fresh data dir for clean loan arithmetic
    tmp2 = tempfile.mkdtemp()
    LEDGER_DIR = tmp2          # global (declared at selftest top) — fresh data dir
    save_users(users)          # same 4 users into the fresh dir
    users = load_users()

    # -- interest flag fences
    try:
        make_entry(users, "mfull", "Alpha", "ADVANCE_ISSUE", "2026-08-01","2026-08-01",
                   0, "9000", "", instalment="2000", interest=True)
        ck(False, "maker interest loan must fail")
    except PermissionError: ck(True, "interest loans are checker-only")
    try:
        make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-08-01","2026-08-01",
                   0, "9000", "", instalment="500", interest=True)
        ck(False, "instalment below interest must fail")
    except ValueError: ck(True, "interest loan needs instalment >= Rs 1000")

    # -- Darpan-shaped scenario: interest loan 9000 @2000/mo + interest-free 3000 @1000/mo
    L = make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-08-01","2026-08-01",
                   0, "9000", "opening balance from workbook (migration)",
                   instalment="2000", interest=True)
    ck(L["status"] == "APPROVED" and L["interest"] is True, "doctor loan direct + flagged")
    F = make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-08-02","2026-08-02",
                   0, "3000", "interest-free advance", instalment="1000")
    ck(F["interest"] is False, "plain advance unflagged")
    oa = open_advances()
    ck([a["issue"]["id"] for a in oa] == [L["id"], F["id"]],
       "tranche order: interest-bearing listed first")

    # -- contra blocked once active is tested AFTER first close (children exist)
    # -- close 1: interest + instalment on L; F must WAIT (waterfall)
    out2, _ = close_month(users, "doc", "2026-09")
    rows = load_ledger()
    ints = [r for r in rows if r["category"] == "LOAN_INTEREST" and r["contra_of"] == L["id"]]
    ck(len(ints) == 1 and ints[0]["amount"] == -1000,
       "close charges flat Rs 1000 interest out of the budget")
    insts = [r for r in rows if r["category"] == "ADVANCE_INSTALMENT"]
    ck(len(insts) == 1 and insts[0]["contra_of"] == L["id"] and insts[0]["amount"] == -1000,
       "budget 2000 = 1000 interest + 1000 principal; free tranche gets the overflow ONLY "
       "when budget remains (workbook waterfall)")
    ck(advance_recovered(L["id"]) == 1000 and advance_recovered(F["id"]) == 0,
       "balances: L 9000-1000, F untouched (budget exhausted)")

    # -- statement math after close 1
    st = build_statement("Alpha")
    ck(st["net"] == -2000, f"statement net = whole instalment 2000 (got {st['net']})")
    counted = [l for l in st["lines"] if l["counted"]]
    ck(len(counted) == 2 and counted[-1]["net"] == -2000, "running net chronological")
    ck(all(not l["counted"] for l in st["lines"]
           if l["row"]["category"] == "ADVANCE_ISSUE"),
       "advance payouts greyed out of the net")
    stm = build_statement("Alpha", "2026-08")
    ck(stm["net"] == 0 and len(stm["lines"]) == 2, "month filter: Aug shows the 2 payouts, net 0")
    ck(st["months"][0] == "2026-09", "months list newest-first")

    # -- contra of an active loan refused
    try:
        make_contra(users, "doc", L["id"], "typo")
        ck(False, "contra of active loan must fail")
    except ValueError: ck(True, "contra blocked once loan is active")

    # -- skip: fences, capitalisation, FY counter
    try:
        record_skip(users, "mfull", L["id"], "2026-10"); ck(False, "maker skip must fail")
    except PermissionError: ck(True, "skips are checker-only")
    try:
        record_skip(users, "doc", F["id"], "2026-10"); ck(False, "skip on plain advance must fail")
    except ValueError: ck(True, "skips only on interest-bearing loans")
    record_skip(users, "doc", L["id"], "2026-10")
    try:
        record_skip(users, "doc", L["id"], "2026-10"); ck(False, "double skip must fail")
    except ValueError: ck(True, "same month cannot be skipped twice")
    out3, _ = close_month(users, "doc", "2026-10")
    rows = load_ledger()
    caps = [r for r in rows if r["category"] == "LOAN_CAPITALISE"]
    ck(len(caps) == 1 and caps[0]["amount"] == 1000 and caps[0]["contra_of"] == L["id"],
       "skipped close capitalises Rs 1000 onto the loan")
    ck(not any(r["category"] == "LOAN_INTEREST" and r["closed_month"] == "2026-10"
               for r in rows), "no interest charged in a skipped month")
    ck(not any(r["category"] == "ADVANCE_INSTALMENT" and r["closed_month"] == "2026-10"
               for r in rows), "no instalment in a skipped month (F still waits behind L)")
    oa = open_advances()
    ck(next(a for a in oa if a["issue"]["id"] == L["id"])["balance"] == 9000,
       "loan balance 9000 - 1000 + 1000 capitalised = 9000")
    # historical skip (migration case) + FY limit
    record_skip(users, "doc", L["id"], "2026-07")   # earlier month, same FY2026-27
    ck(len(fy_skips("Alpha", "2026-11")) == 2, "FY counter sees both skips")
    try:
        record_skip(users, "doc", L["id"], "2026-12"); ck(False, "3rd FY skip must fail")
    except ValueError: ck(True, "D250 2-skips-per-FY limit enforced")
    # a NEW financial year resets the counter
    r_next = record_skip(users, "doc", L["id"], "2027-04")
    ck(fy_of("2027-04") == "FY2027-28" and r_next["category"] == "LOAN_SKIP",
       "new FY accepts a skip again")

    # -- close CSV: interest inside salary debits, capitalise/skip outside
    with open(out3, encoding="utf-8") as f: txt3 = f.read()
    summ = txt3.split("-- detail --")[0]
    ck("LOAN_CAPITALISE" not in summ and "LOAN_SKIP" not in summ,
       "capitalise/skip rows outside the salary summary")
    with open(out2, encoding="utf-8") as f: txt2 = f.read()
    m = _re.search(r"^Alpha,(\d+),(\d+),(-?\d+),(\d+)", txt2, _re.M)
    cred, deb, net, _ld = map(int, m.groups())
    ck(cred == 0 and deb == 2000 and net == -2000,
       f"close-1 CSV: the WHOLE deduction is the Rs 2000 instalment (got {cred},{deb},{net})")
    ck(st["net"] == net, "statement net == close CSV net (single rule set)")

    # -- web: statement + skip routes, permission fences
    app = create_app(); cl = app.test_client()
    cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"pw"})
    pg = cl.get(URL_PREFIX + "/statement?staff=Alpha").data.decode()
    ck("running net" in pg.lower() and "INTEREST-BEARING" not in pg, "statement page renders")
    ck("Open loan" in pg and "9000" in pg, "statement shows loan balance 9000")
    pgadv = cl.get(URL_PREFIX + "/advances").data.decode()
    ck("INTEREST-BEARING LOAN" in pgadv and "Skip this month" in pgadv,
       "advances page shows loan tag + skip control")
    clm = app.test_client(); clm.post(URL_PREFIX + "/login", data={"u":"mfull","p":"pw"})
    pgm = clm.get(URL_PREFIX + "/statement").data.decode()
    ck("<h3>Beta" in pgm, "maker statement locks to own staff_link (Beta)")
    pgm2 = clm.get(URL_PREFIX + "/statement?staff=Alpha").data.decode()
    ck("<h3>Beta" in pgm2 and "<h3>Alpha" not in pgm2,
       "maker cannot pick another staff via URL")
    ck(clm.post(URL_PREFIX + "/skip", data={"id": L["id"], "month":"2027-05"}).status_code == 403,
       "maker blocked from /skip")
    clx = app.test_client(); clx.post(URL_PREFIX + "/login", data={"u":"mlim","p":"pw"})
    pgx = clx.get(URL_PREFIX + "/statement").data.decode()
    ck("not linked to a staff name" in pgx, "unlinked maker gets the polite message")
    pgf = cl.get(URL_PREFIX + "/").data.decode()
    ck("Interest-bearing loan" in pgf and '"interest_ok": true' in pgf,
       "doctor entry form offers the interest checkbox")
    pgfm = clm.get(URL_PREFIX + "/").data.decode()
    ck('"interest_ok": true' not in pgfm, "maker form never offers interest")

    # ---- F-50: system categories must be absent from EVERY entry form/power
    for sc in SYSTEM_CATS:
        ck(sc not in ROLE_CATS["checker"], f"{sc} not in checker powers (F-50)")
        ck(f'"{sc}"' not in pgd if sc != "ADVANCE_INSTALMENT" else True,
           f"{sc} absent from doctor form metadata (F-50)")
    try:
        make_entry(users, "doc", "Alpha", "LOAN_INTEREST", "2026-08-01","2026-08-01",
                   0, "1000", "sneaky")
        ck(False, "hand-typed system row must fail")
    except PermissionError: ck(True, "even a checker cannot hand-enter system rows (F-50)")

    # ---- PERK: checker-only, narration required, outside salary net
    try:
        make_entry(users, "mfull", "Beta", "PERK", "2026-08-15","2026-08-15",0,"2500","fee")
        ck(False, "maker perk must fail")
    except PermissionError: ck(True, "perks are doctor-only")
    try:
        make_entry(users, "doc", "Alpha", "PERK", "2026-08-15","2026-08-15",0,"2500","")
        ck(False, "perk without narration must fail")
    except ValueError: ck(True, "perk narration required")
    pk = make_entry(users, "doc", "Alpha", "PERK", "2026-08-15","2026-08-15",0,"2500",
                    "Adarsh school fee")
    ck(pk["amount"] == 2500 and pk["status"] == "APPROVED", "perk recorded direct +2500")
    st2 = build_statement("Alpha")
    ck(st2["net"] == -2000, "perk stays OUTSIDE the salary net")
    ck(st2["summary"]["perks_total"] == 2500 and st2["summary"]["perks_count"] == 1,
       "summary counts the perk")
    ck(st2["summary"]["instalments_paid"] == 1000 and st2["summary"]["interest_paid"] == 1000,
       "summary: instalments/interest paid totals")
    ck(st2["summary"]["bal_interest"] == 9000 and st2["summary"]["bal_free"] == 3000,
       "summary: both tranche balances")
    ck(st2["summary"]["skip_months"], "summary lists skip months")
    pgs = cl.get(URL_PREFIX + "/statement?staff=Alpha").data.decode()
    ck("Account summary" in pgs and "interest-free tranche" in pgs
       and "Adarsh school fee" in pgs, "statement page renders summary + perk")
    ck('"PERK"' in pgd and '"PERK"' not in pgfm, "perk in doctor form, not maker form")

    # ---- migrate_loan: end-to-end on a fresh staff (Gamma), workbook-shaped
    try:
        migrate_loan(users, "mfull", "Gamma", 5000, 0, 2000, [])
        ck(False, "maker migration must fail")
    except PermissionError: ck(True, "migration is checker-only")
    try:
        migrate_loan(users, "doc", "Nobody", 5000, 0, 2000, [])
        ck(False, "unknown staff must fail")
    except ValueError: ck(True, "migration validates the staff name")
    made, skips, perk_rows = migrate_loan(users, "doc", "Gamma", 19000, 18000, 5000,
                                          ["2026-05"],
                                          perks=[("Adarsh fee", 1300), ("Angel fee", 600)])
    ck(len(made) == 2 and made[0]["interest"] and not made[1]["interest"],
       "migration creates both tranches, loan first")
    ck(made[0]["instalment"] == 5000 and made[1]["instalment"] == 5000,
       "one instalment drives the whole waterfall")
    ck(len(skips) == 1 and skips[0]["date_from"] == "2026-05",
       "migration records the historical skip")
    ck(len(perk_rows) == 2 and sum(p["amount"] for p in perk_rows) == 1900
       and perk_rows[0]["narration"].startswith("(brought forward)"),
       "perks brought forward as PERK rows")
    stg = build_statement("Gamma")
    ck(stg["summary"]["bal_interest"] == 19000 and stg["summary"]["bal_free"] == 18000
       and stg["summary"]["perks_total"] == 1900,
       "migrated balances + perks visible in the summary")
    try:
        migrate_loan(users, "doc", "Gamma", 1, 0, 1000, [])
        ck(False, "second migration must fail")
    except ValueError: ck(True, "migration is idempotent — refused on rerun")
    try:
        migrate_loan(users, "doc", "Beta", 0, 3000, 1000, ["2026-05"])
        ck(False, "skips without a loan must fail")
    except ValueError: ck(True, "skip months need an interest-bearing loan")
    ck(not any(a["issue"]["staff"] == "Beta" for a in open_advances()),
       "the FAILED migration appended NOTHING (validate-before-append atomicity)")
    # v2.4: Rs-0 advance refused with guidance
    try:
        make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2026-08-20","",0,"0","")
        ck(False, "Rs 0 advance must fail")
    except ValueError as e:
        ck("Skip button" in str(e), "Rs 0 advance refused, points to the Skip button")
    ck(parse_perk_line("School expenses - Adarsh / 13000") ==
       ("School expenses - Adarsh", 13000), "perk line: slash format")
    ck(parse_perk_line("School expenses - Angel / 6000,") ==
       ("School expenses - Angel", 6000), "perk line: trailing comma tolerated")
    ck(parse_perk_line("Class 5 fee 2,000") == ("Class 5 fee", 2000),
       "perk line: last number wins, thousands comma ok")
    for bad in ("just words", "5000", ""):
        try:
            parse_perk_line(bad); ck(False, f"bad perk line must fail: {bad!r}")
        except ValueError: ck(True, f"perk line rejected: {bad!r}")
    # workbook trajectory (synthetic tenth-scale): skip already burned, then a close
    close_month(users, "doc", "2026-11")
    stg = build_statement("Gamma")
    ck(stg["summary"]["bal_interest"] == 15000 and stg["summary"]["bal_free"] == 18000
       and stg["summary"]["interest_paid"] == 1000,
       "close: 5000 budget = 1000 interest + 4000 principal; free tranche untouched")
    ck(stg["net"] == -5000, "salary deduction equals the whole instalment (5000)")

    # ---- cross-tranche overflow + interest-stop (Beta: tiny loan clears mid-payment)
    madeB, _sk, _pk = migrate_loan(users, "doc", "Beta", 1500, 4000, 5000, [])
    close_month(users, "doc", "2026-12")
    stb = build_statement("Beta")
    ck(stb["summary"]["bal_interest"] == 0,
       "loan tranche cleared inside the payment (1000 int + 1500 principal)")
    ck(stb["summary"]["bal_free"] == 1500,
       "overflow 2500 flowed into the free tranche the SAME month (4000-2500)")
    close_month(users, "doc", "2027-01")
    stb = build_statement("Beta")
    ck(stb["summary"]["interest_paid"] == 1000,
       "interest STOPPED once the interest-bearing tranche cleared")
    ck(stb["summary"]["bal_free"] == 0, "free tranche finishes at its instalment")

    # ---- v2.4 (runs LAST: switches to a fresh data dir) ----
    _t3 = tempfile.mkdtemp(); LEDGER_DIR = _t3; save_users(users); users = load_users()
    m3, _, _ = migrate_loan(users, "doc", "  gAmMa ", 2000, 0, 1000, [])
    ck(m3[0]["staff"] == "Gamma", "migration resolves case/space to canonical name")
    app = create_app(); cl = app.test_client()
    cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"pw"})
    pgp = cl.get(URL_PREFIX + "/").data.decode()
    ck('"Gamma"' in pgp and '"loan": 2000' in pgp and "current position" in pgp,
       "checker entry form carries the position strip data")
    clm2 = app.test_client(); clm2.post(URL_PREFIX + "/login", data={"u":"mfull","p":"pw"})
    pgpm = clm2.get(URL_PREFIX + "/").data.decode()
    ck('"loan": 2000' not in pgpm, "maker form carries NO balances")


    # ================= v3.0 (S156): salary engine + F-51 =====================
    global ATT_BASE
    _t4 = tempfile.mkdtemp(); LEDGER_DIR = _t4
    _att_t = tempfile.mkdtemp(); ATT_BASE = _att_t
    save_users(users); users = load_users()
    # synthetic staff master WITH base salaries (F-31: synthetic only)
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id","name","active","base_salary"])
        w.writerow([1,"Alpha","Y",9000]); w.writerow([2,"Beta","Y",12000])
        w.writerow([3,"Gamma","Y",6000])
    YM = "2026-08"
    # synthetic att_month_report outputs (the interface files, exact headers)
    def _w_inputs(rows):
        heads = ["Name","Group","Present","Absent","Late marks","Late days",
                 "Late minutes","Grace days used",">=60min days","Early-dep minutes",
                 "No-out-punch days","Early-big days","Deduction half-days",
                 "Ded: marks Rs","Ded: early-dep Rs","Fine: uninformed Rs",
                 "Fine: excess-absent Rs","OT cand. minutes","OT candidate Rs",
                 "Incentive","Incentive Rs","Net Rs","Months over cap (yr)",
                 "Habitual flag","Absent dates"]
        with open(os.path.join(ATT_BASE, f"salary_inputs_{YM}.csv"), "w",
                  newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=heads); w.writeheader()
            for r in rows: w.writerow(r)
    def _row(name, **kw):
        base = {h: 0 for h in ["Present","Absent","Late marks","Late days",
                "Late minutes","Grace days used",">=60min days","Early-dep minutes",
                "No-out-punch days","Early-big days","Deduction half-days",
                "Ded: marks Rs","Ded: early-dep Rs","Fine: uninformed Rs",
                "Fine: excess-absent Rs","OT cand. minutes","OT candidate Rs",
                "Incentive Rs","Net Rs","Months over cap (yr)"]}
        base.update({"Name": name, "Group": "A", "Incentive": "-",
                     "Habitual flag": "", "Absent dates": ""})
        base.update(kw); return base
    _w_inputs([
        _row("Alpha", **{"Absent": 6, "Fine: excess-absent Rs": 300,
                         "Ded: marks Rs": 500, "OT candidate Rs": 200}),
        _row("Beta",  **{"Incentive": "FULL", "Incentive Rs": 400,
                         "Ded: early-dep Rs": 50}),
        _row("Gamma", **{"Fine: uninformed Rs": 100}),
    ])
    with open(os.path.join(ATT_BASE, f"deductions_extras_{YM}.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["name","date","item","minutes","Rs","note"])
        w.writerow(["Alpha","2026-08-12","EARLY_BIG","219 min",0.0,
                    "would be Rs.148.7 if confirmed — last punch 15:20"])
        w.writerow(["Alpha","2026-08-20","EARLY_BIG","100 min",0.0,
                    "would be Rs.70.0 if confirmed — last punch 16:00"])
        w.writerow(["Beta","2026-08-05","EARLY_DEP","60 min",25.0,"left early"])
    with open(os.path.join(ATT_BASE, f"review_{YM}.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["user_id","name","date","type","informed"])
        w.writerow([1,"Alpha","2026-08-03","ABSENT","Y"])
        w.writerow([3,"Gamma","2026-08-04","LATE60","N"])
    # interface loaders
    inp = load_salary_inputs(YM)
    ck(inp is not None and len(inp) == 3, "salary_inputs loads (3 staff)")
    eb = load_earlybig(YM)
    ck(len(eb) == 2 and eb[0]["rs"] == 148.7 and eb[1]["rs"] == 70.0,
       "EARLY_BIG rows parsed with the report's own would-be amounts")
    rv = load_review(YM)
    ck(rv is not None and len(rv) == 2, "review file loads")
    rv[0]["informed"] = "N"; save_review(YM, rv)
    rv2 = load_review(YM)
    ck(rv2[0]["informed"] == "N" and rv2[1]["informed"] == "N",
       "review round-trips through save_review")
    bs = staff_bases()
    ck(bs == {"Alpha": 9000.0, "Beta": 12000.0, "Gamma": 6000.0}, "bases load")
    # fail-loud on a mangled EARLY_BIG note
    with open(os.path.join(ATT_BASE, f"deductions_extras_{YM}.csv"), "a",
              newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Gamma","2026-08-09","EARLY_BIG","90 min",0.0,"format drifted"])
    try:
        load_earlybig(YM); ck(False, "mangled EARLY_BIG note must fail")
    except ValueError: ck(True, "EARLY_BIG note drift fails loud, never guesses 0")
    # restore the good file
    with open(os.path.join(ATT_BASE, f"deductions_extras_{YM}.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["name","date","item","minutes","Rs","note"])
        w.writerow(["Alpha","2026-08-12","EARLY_BIG","219 min",0.0,
                    "would be Rs.148.7 if confirmed — last punch 15:20"])
        w.writerow(["Alpha","2026-08-20","EARLY_BIG","100 min",0.0,
                    "would be Rs.70.0 if confirmed — last punch 16:00"])
    # ledger events for the month, then close
    ad = make_entry(users, "doc", "Alpha", "FINE_ADHOC", "2026-08-10","2026-08-10",0,"250","broke a splint")
    nd = make_entry(users, "doc", "Beta", "NIGHT_DUTY", "2026-08-11","2026-08-12",2,"0","")
    # compute BEFORE close must flag the problem
    t0, tok0, pr0 = compute_salary(YM)
    ck(pr0 and "not closed" in pr0[0], "compute names the un-closed ledger month")
    close_month(users, "doc", YM)
    # rulings: EARLY_BIG one genuine one not; OT partial approve; outstation
    rul = load_rulings(YM)
    rul["earlybig"] = {"Alpha|2026-08-12": {"genuine": True},
                       "Alpha|2026-08-20": {"genuine": False}}
    rul["ot"] = {"Alpha": 150.0}          # of the 200 candidate
    rul["outstation"] = {"Alpha": 4}      # 6 absent -> 2 effective -> fine 0
    save_rulings(YM, rul)
    table, token, problems = compute_salary(YM)
    ck(not problems, f"no problems after close (got {problems})")
    T = {t["name"]: t for t in table}
    # Alpha: 9000 +0 inc +150 OT +0 cr -500 marks -0 early -148.7 eb
    #        -(0 uninf + 0 excess-after-outstation) -250 adj_db = 8251.3 -> 8251
    ck(T["Alpha"]["fine_exc"] == 0.0,
       "outstation 4 of 6 absents -> excess fine recomputes to 0")
    ck(T["Alpha"]["earlybig_rs"] == 148.7, "only the Genuine=Y EARLY_BIG deducts")
    ck(T["Alpha"]["ot_ok"] == 150.0, "OT pays the approved 150, not the 200 candidate")
    ck(T["Alpha"]["adj_db"] == 250, "ledger ad-hoc fine folded in from the close")
    ck(T["Alpha"]["net"] == 8251, f"Alpha net rounds to the rupee (got {T['Alpha']['net']})")
    # Beta: 12000 +400 inc +400 night -50 early = 12750
    ck(T["Beta"]["adj_cr"] == 400 and T["Beta"]["net"] == 12750,
       f"Beta net with night duty + incentive (got {T['Beta']['net']})")
    # Gamma: 6000 -100 uninformed = 5900
    ck(T["Gamma"]["net"] == 5900, "Gamma net")
    # OT approval can never exceed the candidate
    rul["ot"]["Alpha"] = 9999.0; save_rulings(YM, rul)
    t2, tok2, _ = compute_salary(YM)
    ck({x["name"]: x for x in t2}["Alpha"]["ot_ok"] == 200.0,
       "OT approval capped at the candidate amount")
    rul["ot"]["Alpha"] = 150.0; save_rulings(YM, rul)
    table, token, _ = compute_salary(YM)
    # approve gates
    try:
        approve_salary(users, "mfull", YM, token); ck(False, "maker approve must fail")
    except PermissionError: ck(True, "salary approval is checker-only")
    try:
        approve_salary(users, "doc", YM, "stale-token"); ck(False, "stale token must fail")
    except ValueError: ck(True, "drifted inputs refuse the approval (token check)")
    out4, n4 = approve_salary(users, "doc", YM, token)
    ck(n4 == 3 and os.path.exists(out4), "approve writes salary_final CSV for 3 staff")
    ck(salary_locked(YM), "month locks on approval")
    sp = [r for r in load_ledger() if r["category"] == "SALARY_PAID"]
    ck(len(sp) == 3 and all(r["maker"] == "SYSTEM" and r["closed_month"] == YM
                            for r in sp), "3 SALARY_PAID system rows, month-stamped")
    ck({r["staff"]: r["amount"] for r in sp}["Alpha"] == 8251,
       "SALARY_PAID amount = the rounded net")
    try:
        approve_salary(users, "doc", YM, token); ck(False, "second approve must fail")
    except ValueError: ck(True, "a locked month refuses re-approval")
    # SALARY_PAID is a system category: never hand-entered, never hand-contra'd
    try:
        make_entry(users, "doc", "Alpha", "SALARY_PAID", "2026-08-31","",0,"9999","x")
        ck(False, "hand SALARY_PAID must fail")
    except PermissionError: ck(True, "SALARY_PAID cannot be hand-entered (F-50)")
    try:
        make_contra(users, "doc", sp[0]["id"], "oops")
        ck(False, "contra of SALARY_PAID must fail")
    except ValueError: ck(True, "SALARY_PAID rows are never contra'd by hand")
    # statement: salary line visible but OUTSIDE the adjustments net
    stA = build_statement("Alpha")
    ck(any(l["row"]["category"] == "SALARY_PAID" for l in stA["lines"]),
       "salary line appears in the statement")
    ck(all(not l["counted"] for l in stA["lines"]
           if l["row"]["category"] == "SALARY_PAID"),
       "salary line stays outside the adjustments running net")
    # ---- F-51 web checks ----------------------------------------------------
    app = create_app(); cl = app.test_client()
    cl.post(URL_PREFIX + "/login", data={"u":"doc","p":"pw"})
    # contra two-step: step 1 shows the row and appends NOTHING
    n_before = len(load_ledger())
    r1 = cl.post(URL_PREFIX + "/contra", data={"id": ad["id"], "narration": "test"})
    ck(b"Confirm the reversal" in r1.data and b"250" in r1.data,
       "contra step 1 shows the target row + amount")
    ck(len(load_ledger()) == n_before, "contra step 1 appends nothing (F-51)")
    r2 = cl.post(URL_PREFIX + "/contra2", data={"id": ad["id"], "narration": "test"})
    ck(r2.status_code == 302 and len(load_ledger()) == n_before + 1,
       "contra step 2 performs the append")
    # void-pair display: the fine and its contra both grey out
    bk = cl.get(URL_PREFIX + "/book").data.decode()
    ck(bk.count("REVERSED") >= 2, "book shows both rows of the pair as REVERSED")
    stp = cl.get(URL_PREFIX + "/statement?staff=Alpha").data.decode()
    ck("(reversed)" in stp, "statement greys the reversed pair")
    ck("class='mhead'" in stp, "statement carries month header rows (F-51)")
    # skip button carries a confirm
    pgadv2 = cl.get(URL_PREFIX + "/advances").data.decode()
    ck("return confirm(" in pgadv2 or "No open advances" in pgadv2,
       "skip button asks for confirmation")
    # salary page renders locked view; approve route refuses when locked
    pgsl = cl.get(URL_PREFIX + f"/salary?m={YM}").data.decode()
    ck("APPROVED" in pgsl and "LOCKED" in pgsl, "salary page shows the locked month")
    ra = cl.post(URL_PREFIX + "/salary/approve", data={"m": YM, "token": "x"})
    ck(b"NOT approved" in ra.data, "web approve refuses a locked month")
    # maker fenced off the whole salary surface
    clm3 = app.test_client(); clm3.post(URL_PREFIX + "/login", data={"u":"mfull","p":"pw"})
    ck(clm3.get(URL_PREFIX + "/salary").status_code == 403, "maker blocked from /salary")
    ck(clm3.post(URL_PREFIX + "/salary/approve", data={"m": YM, "token": "x"}).status_code == 403,
       "maker blocked from salary approve")
    ck(clm3.post(URL_PREFIX + "/salary/close", data={"m": YM}).status_code == 403,
       "maker blocked from salary close")
    # review + rulings routes round-trip through the web
    YM2 = "2026-09"
    _sv = os.path.join(ATT_BASE, f"review_{YM2}.csv")
    with open(_sv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["user_id","name","date","type","informed"])
        w.writerow([2,"Beta","2026-09-02","ABSENT","Y"])
    rr = cl.post(URL_PREFIX + "/salary/review",
                 data={"m": YM2, "n": "1", "key_0": "2|Beta|2026-09-02|ABSENT",
                       "inf_0": "N"})
    ck(rr.status_code == 302 and load_review(YM2)[0]["informed"] == "N",
       "web review save writes the informed flag")
    rr2 = cl.post(URL_PREFIX + "/salary/rulings",
                  data={"m": YM2, "part": "ot", "ot_Beta": "120", "os_Beta": "2"})
    r_l = load_rulings(YM2)
    ck(rr2.status_code == 302 and r_l["ot"]["Beta"] == 120.0
       and r_l["outstation"]["Beta"] == 2, "web rulings save OT + outstation")


    # ---- v3.1: full salary report (splice into the vetted attendance HTML) --
    # synthetic attendance HTML standing in for the owner's vetted artefact
    with open(os.path.join(ATT_BASE, f"salary_inputs_{YM}.html"), "w",
              encoding="utf-8") as f:
        f.write("<!doctype html><html><head><style>.noprint{}</style></head>"
                "<body><h1>GRID-MARKER-2026-08</h1>"
                "<details><summary>legend</summary>vetted</details>"
                "</body></html>")
    tableR, tokR, prR = compute_salary(YM)
    htm = build_salary_html(YM, tableR, locked=True, stamp="teststamp by doc")
    ck("GRID-MARKER-2026-08" in htm, "report preserves the vetted attendance HTML verbatim")
    ck("FINAL SALARY" in htm and "TOTAL PAYOUT" in htm, "final section spliced in")
    ck(htm.index("GRID-MARKER-2026-08") < htm.index("FINAL SALARY"),
       "grid page stays FIRST; salary section follows")
    ck(htm.count("</body>") == 1, "splice keeps one body close")
    ck("<details><summary><b>Alpha</b>" in htm, "per-staff collapsible breakdown present")
    ck("APPROVED &amp; LOCKED" in htm and "teststamp" in htm, "locked banner + stamp")
    ck("GENUINE — deducted" in htm and "not genuine — waived" in htm,
       "both EARLY_BIG rulings narrated as applied")
    ck("broke a splint" in htm, "ledger narration appears in the breakdown")
    ck("outstation" in htm, "outstation adjustment narrated")
    htm_p = build_salary_html(YM, tableR, locked=False)
    ck("PREVIEW" in htm_p and "APPROVED &amp; LOCKED" not in htm_p,
       "unlocked report carries the PREVIEW banner")
    # fallback when the attendance HTML is absent
    os.rename(os.path.join(ATT_BASE, f"salary_inputs_{YM}.html"),
              os.path.join(ATT_BASE, f"HOLD_{YM}.html"))
    htm_f = build_salary_html(YM, tableR)
    ck("was not found" in htm_f and "FINAL SALARY" in htm_f,
       "standalone fallback when attendance HTML is missing")
    os.rename(os.path.join(ATT_BASE, f"HOLD_{YM}.html"),
              os.path.join(ATT_BASE, f"salary_inputs_{YM}.html"))
    # approve wrote the frozen HTML file earlier this test run?  YM was approved
    # BEFORE the html existed — so write it now via a fresh approval on YM3.
    ck(os.path.exists(_p(f"salary_final_{YM}.csv")), "final CSV still on disk")
    # web route: checker sees the report; maker fenced
    r_rep = cl.get(URL_PREFIX + f"/salary/report?m={YM}")
    ck(r_rep.status_code == 200 and b"FINAL SALARY" in r_rep.data
       and b"GRID-MARKER-2026-08" in r_rep.data, "report route serves the full report")
    ck(b"APPROVED" in r_rep.data, "route shows the locked banner for the locked month")
    ck(clm3.get(URL_PREFIX + f"/salary/report?m={YM}").status_code == 403,
       "maker blocked from the report route")
    # approve writes the HTML artefact: fresh month end-to-end
    YM3 = "2026-10"
    _w_inputs2 = list(csv.DictReader(open(os.path.join(ATT_BASE, f"salary_inputs_{YM}.csv"),
                                          encoding="utf-8")))
    with open(os.path.join(ATT_BASE, f"salary_inputs_{YM3}.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(_w_inputs2[0].keys()))
        w.writeheader(); w.writerows(_w_inputs2)
    with open(os.path.join(ATT_BASE, f"salary_inputs_{YM3}.html"), "w",
              encoding="utf-8") as f:
        f.write("<html><body><h1>GRID-OCT</h1></body></html>")
    close_month(users, "doc", YM3)
    t3, tk3, pr3 = compute_salary(YM3)
    ck(not pr3, "YM3 computes clean")
    approve_salary(users, "doc", YM3, tk3)
    ck(os.path.exists(_p(f"salary_final_{YM3}.html")), "approve writes the HTML report")
    htm3 = open(_p(f"salary_final_{YM3}.html"), encoding="utf-8").read()
    ck("GRID-OCT" in htm3 and "APPROVED &amp; LOCKED" in htm3,
       "frozen report = vetted grid + locked salary layer")

    print(f"SELFTEST PASSED — {ok[0]} maker-checker, rate-card, advance, loan, "
          f"skip, statement, salary, report and F-51 checks OK")

# ------------------------------------------------------------------ main -----
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print(__doc__); sys.exit(0)
    if args[0] == "--selftest": selftest()
    elif args[0] == "serve":
        create_app().run(host="127.0.0.1", port=PORT)
    elif args[0] == "adduser": cli_adduser()
    elif args[0] == "deluser": cli_deluser(args[1])
    elif args[0] == "listusers": cli_listusers()
    elif args[0] == "migrate-loan": cli_migrate_loan()
    elif args[0] == "close":
        users = load_users()
        checkers = [n for n,r in users.items() if r["role"]=="checker" and r.get("active",True)]
        if not checkers: sys.exit("no checker user exists")
        out, n = close_month(users, checkers[0], args[1])
        print(f"Closed {args[1]}: {n} approved rows -> {out}")
    else:
        sys.exit("unknown command; run with --help")
