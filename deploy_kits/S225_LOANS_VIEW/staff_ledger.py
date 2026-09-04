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
APP_VERSION = "3.5-S225-LOANS"
LEDGER_DIR  = os.environ.get("LEDGER_DIR", "/root/staff_ledger")
# D331: the shared clinic scan widget (camera + gallery, verified on the box
# S190) and the jspdf it needs — both served read-only by this app.
SCANNER_JS  = os.environ.get("LEDGER_SCANNER_JS", "/root/assetapp/scanner_widget.js")
JSPDF_JS    = os.environ.get("LEDGER_JSPDF_JS", "/root/finance/vendor/jspdf.umd.min.js")
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
    "COVER_DUTY":        ("Cover duty",             200,  True,   +1,  True),
    "FINE_UNIFORM":      ("Uniform fine",            15,  True,   -1,  False),
    "FINE_ICARD":        ("I-card fine",             15,  True,   -1,  False),
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
    # D332/SL6: DEFER replaces SKIP as the owner-facing verb. The whole
    # instalment shifts one month; the schedule extends by one. No automatic
    # capitalisation — interest rides inside each collected instalment, so a
    # deferral does not change total loan interest. The 2/FY discipline
    # survives as a WAIVABLE PENALTY on interest-bearing loans only.
    "ADVANCE_DEFER":     ("Collection deferred",       None, False,  0, False),
    "CAPACITY_HOLD":     ("Held — salary could not bear it", None, False, 0, False),
    "SALARY_PAID":       ("Salary paid (monthly, auto)", None, False, +1, False),
}
# S200/D346: the uniform / I-card day-rates follow the SALARY POLICY settings
# (dress_rs / icard_rs) so the two rate cards can never disagree again (the
# ledger said Rs 20 while D336 ruled Rs 15). Read fail-soft; file absent or
# unreadable -> the shipped defaults above stand.
POLICY_SETTINGS = os.environ.get("LEDGER_POLICY_SETTINGS",
                                 "/root/staff_register/salary_policy_settings.json")

def live_rate(cat):
    """Current Rs/day for a category, honouring the salary-policy settings."""
    base_rate = CATEGORIES[cat][1]
    key = {"FINE_UNIFORM": "dress_rs", "FINE_ICARD": "icard_rs"}.get(cat)
    if not key:
        return base_rate
    try:
        with open(POLICY_SETTINGS, encoding="utf-8") as f:
            v = json.load(f).get(key)
        return int(v) if v not in (None, "") else base_rate
    except Exception:
        return base_rate


INTEREST_RS   = 1000     # D250: flat per month while an interest-bearing balance is open
SKIPS_PER_FY  = 2        # D250: skips per Indian financial year (Apr-Mar)
DEFERS_FREE_FY = 2       # D332 §2.1: free defers per FY; the 3rd+ carries a
                         # waivable Rs 1000 penalty on interest-bearing loans
SYSTEM_CATS   = {"ADVANCE_INSTALMENT","LOAN_INTEREST","LOAN_CAPITALISE","LOAN_SKIP",
                 "SALARY_PAID","ADVANCE_DEFER","CAPACITY_HOLD"}
# rupees that are NOT salary money (cash / balance-side events) — excluded from
# the close CSV summary AND from the statement's running salary net, identically:
SALARY_EXCLUDED = {"ADVANCE_ISSUE","LOAN_CAPITALISE","LOAN_SKIP","PERK","SALARY_PAID",
                   "ADVANCE_DEFER","CAPACITY_HOLD"}
# F-50 (S155): a role's powers are EXPLICIT lists — never "everything in
# CATEGORIES", which silently grew when system categories were added in v2.0.
ROLE_CATS = {
    # S162 (D286): approved-leave + uniform/i-card fines moved to the Staff Register
    # (daily grid + sanctioned-leave range). maker_full (Shavez/manager) keeps his
    # ledger-only money work; maker_limited (Alisha/Shivani/receptionist) has nothing
    # left to enter here. Checker (doctor) keeps the full list as a backstop.
    "maker_full":    ["NIGHT_DUTY","COVER_DUTY","ICARD_REPLACEMENT","ADVANCE_ISSUE"],
    "maker_limited": [],
    "checker":       ["NIGHT_DUTY","COVER_DUTY","FINE_UNIFORM","FINE_ICARD","LEAVE_APPROVED",
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
    if rate is not None:
        rate = live_rate(cat)              # S200: settings-linked day-rates
    if cat == "LEAVE_APPROVED": return 0
    if cat == "PERK": return abs(int(manual_amount))
    if rate is None:
        amt = abs(int(manual_amount))
        if cat == "OTHER":
            return amt if int(manual_amount) >= 0 else -amt
        return sign * amt
    return sign * rate * (days if per_day else 1)

def make_entry(users, maker, staff, cat, date_from, date_to, days, manual_amount,
               narration, instalment=None, contra_of=None, interest=False,
               against_month=None, special=False, schedule=None):
    u = users[maker]
    role = u["role"]
    if cat not in ROLE_CATS[role]:
        raise PermissionError(f"{maker} may not enter {cat}")
    if interest and (cat != "ADVANCE_ISSUE" or role != "checker"):
        raise PermissionError("interest-bearing loans are checker-issued advances only")
    _,_,_,_, narr_req = CATEGORIES[cat]
    if narr_req and not narration.strip():
        raise ValueError("narration is required for this category")
    am = ""
    if cat == "ADVANCE_ISSUE":
        amount = abs(int(manual_amount))
        if amount <= 0:
            raise ValueError("an advance needs a positive amount — to SKIP a "
                             "loan month use the Skip button on the Advances "
                             "page, never a Rs 0 entry")
        inst = abs(int(instalment)) if instalment not in (None,"","0",0) else amount
        # D332 §4: an advance may carry a repayment SCHEDULE defined at entry.
        # It must add to the advance exactly — a schedule with a silent gap is
        # a promise the close cannot keep.
        sched = (parse_schedule(schedule, amount) if isinstance(schedule, str)
                 else (schedule or []))
        if sched and sum(e["amount"] for e in sched) != amount:
            raise ValueError("the schedule must add to the advance amount")
        if interest and inst < INTEREST_RS:
            raise ValueError(f"instalment must be at least Rs {INTEREST_RS} on an interest-bearing loan")
        # ---- D331: the month this advance counts against ------------------
        am = (against_month or "").strip() or date_from[:7]
        try:
            datetime.date.fromisoformat(am + "-01")
        except ValueError:
            raise ValueError("against-month must look like 2026-09")
        if am < date_from[:7]:
            raise ValueError("an advance cannot be attributed to a PAST month "
                             "— that would re-open a quota already spent")
        # ---- D331: the ceiling gate ---------------------------------------
        # SL3: interest-bearing loans BYPASS the quota gate, matching their
        # exclusion from the quota count — they are the parallel instalment
        # instrument (checker-only, D250 machinery), not a monthly-quota
        # draw. The application requirement for NEW loans is procedural
        # (checker-side) until wired; recorded in the contract.
        ceil = advance_ceiling(staff) if not interest else 0
        if ceil > 0:
            taken = advance_month_taken(staff, am)
            if taken + amount > ceil and not special:
                raise ValueError(
                    f"advance for {am} would be Rs {taken + amount} against the "
                    f"Rs {ceil} ceiling ({advance_pct(staff)}% of base, D331) — "
                    f"already taken Rs {taken}. Above the ceiling it must be "
                    f"entered as a SPECIAL advance, with the signed written "
                    f"application uploaded before approval.")
            if taken + amount <= ceil:
                special = False        # a special flag inside the ceiling is noise
        else:
            special = False            # no base salary on file: gate disabled,
                                       # shown inline as unenforced — never silent
    else:
        amount = compute_amount(cat, days, manual_amount)
        inst = None
        special = False
        sched = []
    # D331: a SPECIAL advance is never direct — even a checker's own entry
    # goes PENDING, so the application gate at decide() can never be bypassed.
    direct = (role == "checker") and not special
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
        "against_month": am if cat == "ADVANCE_ISSUE" else "",
        "special": bool(special),
        "schedule": (sched if cat == "ADVANCE_ISSUE" else []),
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
    # D331: an above-ceiling advance cannot be APPROVED until the signed
    # written application (Dr Manoj / Dr Bhawna) is on file. No escape hatch
    # — the D330 evidence rule, mirrored. Rejection needs no application.
    if approve and r.get("special") and not application_on_file(row_id):
        raise ValueError("an above-ceiling (SPECIAL) advance needs the signed "
                         "written application uploaded first — open the row "
                         "and attach it, then approve")
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
        "against_month": o.get("against_month", ""),   # F-153: inherit so a reversal nets the original's quota, not the entry month
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

# ---------------------------------------------------------------- D331 (S190)
# The advance ceiling: a per-staff percentage of base salary, floored to the
# last Rs 100. DERIVED, never typed (F-136): base comes from staff_master.csv
# (staff_bases -- the file /salary already reads), pct from advance_pct.json
# beside users.json (default 50; Darpan 75, the owner's ruling). Above the
# ceiling an advance is SPECIAL: it must say so, it is NEVER direct (even a
# checker's own entry goes PENDING), and approval refuses until the signed
# written application (Dr Manoj / Dr Bhawna) is uploaded against the row.
# An advance may be attributed AGAINST a FUTURE month's salary (the owner's
# 17-Aug device): it then counts against THAT month's ceiling and enters the
# close snapshot only from that month.

def advance_pct(staff):
    """Per-staff ceiling percentage. File read fail-soft: unreadable or
    missing means every staff is at the default 50."""
    try:
        with open(_p("advance_pct.json"), encoding="utf-8") as f:
            j = json.load(f)
        return int(j.get(staff, j.get("default", 50)))
    except Exception:
        return 50


def advance_ceiling(staff):
    """Rs, floored to the last Rs 100. Returns 0 when no base salary is on
    file -- and a 0 ceiling DISABLES the gate rather than freezing all
    advances (the degradation is shown inline, never silent): a missing
    staff_master row is a data gap to fix, not a reason the clinic stops."""
    base = staff_bases().get(staff, 0)
    return int(base * advance_pct(staff) / 100) // 100 * 100


def advance_against_month(row):
    """The month an ADVANCE_ISSUE row counts against (D331): the explicit
    attribution when present, else the entry's own calendar month."""
    return row.get("against_month") or (row.get("date_from") or "")[:7]


def advance_month_taken(staff, month, rows=None):
    """Advances counting against `month`'s quota for this staff — PENDING
    included (money asked for is quota spoken for), REJECTED excluded.
    SL3 (owner ruling, S190): the quota counts ONLY
      (a) rows carrying an EXPLICIT against_month — i.e. rows created under
          D331. Pre-install rows (including the S155 migration entries, which
          are DATED August 2026 but represent years of history — Darpan's
          row read "Rs 3,63,000 of Rs 15,000" before this fix) are
          grandfathered: visible in the position card and the statement,
          recovering as normal, but not eating the month's quota; and
      (b) NON-interest rows. An interest-bearing loan is the instalment-
          repayable SPECIAL instrument with its own recovery machinery — it
          never consumes the ordinary monthly quota."""
    return sum(r["amount"] for r in (rows or load_ledger())
               if r["category"] == "ADVANCE_ISSUE"
               and r["staff"] == staff
               and r["status"] in ("PENDING", "APPROVED")
               and not r.get("interest")
               and (r.get("against_month") or "") == month)


APPLICATION_DIR = "applications"


def application_path(row_id):
    return os.path.join(_p(APPLICATION_DIR), "%s.pdf" % row_id)


def application_on_file(row_id):
    p = application_path(row_id)
    return os.path.exists(p) and os.path.getsize(p) > 0


def save_application(row_id, blob, who):
    """Store the signed written application against a special advance and
    record its sha in the row itself, so the JSONL carries the proof."""
    rows = {r["id"]: r for r in load_ledger()}
    r = rows.get(row_id)
    if not r or r["category"] != "ADVANCE_ISSUE" or not r.get("special"):
        raise ValueError("no such special advance")
    if not blob:
        raise ValueError("empty file")
    os.makedirs(_p(APPLICATION_DIR), exist_ok=True)
    sha = hashlib.sha256(blob).hexdigest()
    with open(application_path(row_id), "wb") as f:
        f.write(blob)
    os.chmod(application_path(row_id), 0o600)
    update_row(row_id, {"application_sha": sha, "application_by": who,
                        "application_at": now()})
    return sha


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

# ---------------------------------------------------------- D332 · SL6 -----
# THE SCHEDULE. An advance is an amount PLUS a repayment schedule, defined at
# approval. The default schedule is uniform (the named instalment); the owner
# may set an uneven distribution (the 17-Aug Rs 20,000: 8,000 + 4,000 x 3).
# SL4's recover-in-full and a uniform instalment are both special cases of a
# schedule — one generalisation subsumes all three (D332 §4).
#
# A schedule is stored on the ADVANCE_ISSUE row as
#     [{"month": "2026-08", "amount": 8000}, {"month": "2026-09", ...}, ...]
# A row with no schedule behaves EXACTLY as before this kit.
def advance_schedule(row):
    s = row.get("schedule") or []
    out = []
    for e in s:
        try:
            m = str(e["month"]); a = int(e["amount"])
            datetime.date.fromisoformat(m + "-01")
        except Exception:
            continue
        if a > 0:
            out.append({"month": m, "amount": a})
    return sorted(out, key=lambda e: e["month"])

# =============================================================================
#  D349 (S202): WHICH LANE RECOVERS AN ADVANCE — ONE DEFINITION, ONE PLACE.
#
#  This test used to exist TWICE: once in close_month()'s quota lane and once in
#  the /statement page's card renderer. The two drifted, and the copy that drifted
#  was the one a human reads.
#
#  In the close the schedule check is IMPLICIT IN THE ORDERING — the schedule lane
#  runs first and REMOVES its advances from `snap`, so by the time the quota test
#  runs it can no longer see a scheduled advance. The display had no such ordering,
#  copied the quota test literally, and therefore told the owner that Darpan's
#  Rs 20,000 (8,000 then 4,000 x 3) "recovers in full at the 2026-08 close".
#  It does not. The close takes 8,000. The page was wrong for every scheduled
#  advance ever issued.
#
#  So the ordering is now written down as a value instead of being an emergent
#  property of statement order. PRECEDENCE IS DELIBERATE and matches close_month
#  exactly -- schedule BEFORE interest, because a scheduled loan is collected by
#  the schedule lane today and this function must describe what the code does,
#  not what would be tidier.
#
#  RULE (D349): one function decides what a difference or a lane MEANS, and every
#  surface reads it. A second copy of a rule is how two screens disagree.
# =============================================================================
def advance_lane(a):
    """The lane that will actually recover advance `a`. close_month() partitions
    by this; every display must describe this and nothing else."""
    if advance_schedule(a["issue"]):
        return "schedule"
    if (a["issue"].get("against_month")
            and not a["interest"]
            and a["instalment"] == a["issue"]["amount"]):
        return "quota"
    return "loan" if a["interest"] else "waterfall"


def parse_schedule(text, total=None):
    """'2026-08:8000, 2026-09:4000, 2026-10:4000, 2026-11:4000' -> list.
    Refuses a schedule whose sum does not equal the advance (no silent gap)."""
    out = []
    for part in (text or "").replace("\n", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError("each step must look like 2026-09:4000")
        m, a = part.split(":", 1)
        m = m.strip(); a = a.strip()
        datetime.date.fromisoformat(m + "-01")
        if int(a) <= 0:
            raise ValueError("a schedule step must be a positive amount")
        out.append({"month": m, "amount": int(a)})
    out.sort(key=lambda e: e["month"])
    if total is not None and out and sum(e["amount"] for e in out) != int(total):
        raise ValueError(f"the schedule adds to Rs {sum(e['amount'] for e in out)} "
                         f"but the advance is Rs {int(total)} — they must match")
    return out

def advance_defers(issue_id, rows=None, upto=None):
    """DEFER records against one advance, oldest first (optionally <= upto)."""
    return sorted([r for r in (rows or load_ledger())
                   if r["category"] == "ADVANCE_DEFER" and r["contra_of"] == issue_id
                   and r["status"] == "APPROVED"
                   and (upto is None or r["date_from"] <= upto)],
                  key=lambda r: r["date_from"])

def fy_defers(staff, month, rows=None):
    """Defers recorded for this staff in the FY containing `month` (D332 §2.1)."""
    fy = fy_of(month)
    return [r for r in (rows or load_ledger())
            if r["category"] == "ADVANCE_DEFER" and r["staff"] == staff
            and r["status"] == "APPROVED" and fy_of(r["date_from"]) == fy]

def is_deferred(issue_id, month, rows=None):
    return any(r["category"] == "ADVANCE_DEFER" and r["contra_of"] == issue_id
               and r["date_from"] == month and r["status"] == "APPROVED"
               for r in (rows or load_ledger()))

def schedule_due_cum(issue, month, rows=None):
    """Rupees the SCHEDULE says should have been collected by the end of
    `month`. Each DEFER shifts the whole remaining schedule one month, so the
    rule is simply: take the first (elapsed - deferred) steps.
    Returns None when the advance carries no schedule."""
    sched = advance_schedule(issue)
    if not sched:
        return None
    # Months elapsed since the schedule's FIRST step, 1-based and UNBOUNDED —
    # counting only the listed steps would cap the count at len(sched), and the
    # last step would then never fall due after a defer (a defer must EXTEND
    # the schedule, not swallow its tail).
    elapsed = _month_diff(sched[0]["month"], month) + 1
    deferred = len(advance_defers(issue["id"], rows, upto=month))
    k = max(0, min(len(sched), elapsed - deferred))
    return sum(e["amount"] for e in sched[:k])

def schedule_state(issue, month=None, rows=None):
    """What the Advances card and the statement show: the schedule, what has
    been recovered, how many months are left and when the next collection is."""
    rows = rows or load_ledger()
    month = month or datetime.date.today().strftime("%Y-%m")
    sched = advance_schedule(issue)
    rec = advance_recovered(issue["id"], rows)
    bal = issue["amount"] + advance_capitalised(issue["id"], rows) - rec
    defers = advance_defers(issue["id"], rows)
    st = {"schedule": sched, "recovered": rec, "balance": bal,
          "defers": [d["date_from"] for d in defers], "next_month": None,
          "next_amount": 0, "months_left": 0}
    if not sched:
        return st
    shift = len(defers)
    paid = 0
    for i, e in enumerate(sched):
        paid += e["amount"]
        if paid > rec:
            # step i is the next one still owed; every defer pushes it out by
            # one month from the schedule's own starting month.
            st["next_month"] = _month_plus(sched[0]["month"], i + shift)
            st["next_amount"] = e["amount"]
            st["months_left"] = len(sched) - i
            break
    return st

def _month_diff(a, b):
    """whole months from a to b ('2026-08','2026-11') -> 3."""
    return (int(b[:4]) * 12 + int(b[5:7])) - (int(a[:4]) * 12 + int(a[5:7]))

def _month_plus(month, n):
    y, m = int(month[:4]), int(month[5:7])
    t = (y * 12 + (m - 1)) + int(n)
    return f"{t // 12:04d}-{t % 12 + 1:02d}"

def record_defer(users, checker, issue_id, month, reason, waive_penalty=False):
    """DEFER one advance's collection for `month` (D332 §2.1). The instalment
    shifts whole; the schedule extends one month; NO automatic capitalisation.
    On an interest-bearing loan the first DEFERS_FREE_FY defers of the FY are
    free; from the next one a Rs 1000 penalty capitalises UNLESS the owner
    waives it with a reason. Interest-free advances defer penalty-free always."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers defer a collection")
    datetime.date.fromisoformat(month + "-01")
    if not (reason or "").strip():
        raise ValueError("a defer needs a written reason")
    rows = load_ledger()
    issue = next((r for r in rows if r["id"] == issue_id), None)
    if not issue or issue["category"] != "ADVANCE_ISSUE" or issue["status"] != "APPROVED":
        raise ValueError("no such approved advance")
    if is_deferred(issue_id, month, rows):
        raise ValueError(f"{month} is already deferred for this advance")
    if any(r.get("closed_month") == month and r["category"] == "ADVANCE_INSTALMENT"
           and r["contra_of"] == issue_id for r in rows):
        raise ValueError(f"{month} was already closed with a collection — it cannot be deferred now")
    used = fy_defers(issue["staff"], month, rows)
    penalty = bool(issue.get("interest")) and len(used) >= DEFERS_FREE_FY
    waived = bool(waive_penalty) and penalty
    row = {"id": secrets.token_hex(6), "ts_entry": now(), "maker": checker,
           "staff": issue["staff"], "category": "ADVANCE_DEFER",
           "date_from": month, "date_to": month, "days": 0,
           "amount": 0, "instalment": None,
           "narration": (f"collection deferred for {month} ({fy_of(month)} "
                         f"{len(used)+1}) — {reason.strip()}"
                         + (" [3rd+ defer: Rs %d penalty WAIVED by %s]" % (INTEREST_RS, checker)
                            if waived else
                            (" [3rd+ defer: Rs %d penalty capitalises]" % INTEREST_RS
                             if penalty else ""))),
           "self_flag": False, "direct": True, "status": "APPROVED",
           "checker": checker, "ts_decision": now(),
           "contra_of": issue_id, "closed_month": "", "interest": False,
           "defer_penalty": penalty, "penalty_waived": waived}
    append_ledger(row)
    return row

# THE CAPACITY RULE (F-147): nothing recovers that the salary cannot bear.
def recovery_capacity(staff, month, rows=None, settings=None):
    """Rupees available for recovery this month = base - other debits already
    booked into the month - the protected minimum take-home. Returns None when
    no base salary is on file: the gate DISABLES rather than freezing every
    recovery (the D331 ceiling's fail-open design, shown, never silent)."""
    base = staff_bases().get(staff, 0)
    if not base:
        return None
    s = settings or load_settings()
    floor = int(s.get("min_takehome") or 0)
    other = 0
    for r in (rows or load_ledger()):
        if (r["staff"] == staff and r["status"] == "APPROVED"
                and r["amount"] < 0 and r["category"] not in SALARY_EXCLUDED
                and r["category"] not in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")
                and (r.get("closed_month") in ("", month))):
            other += -r["amount"]
    return max(0, int(base) - other - floor)

def perk_records(staff=None, year=None, rows=None):
    """Approved PERK rows, newest first. A perk is a RECORD, not money owed —
    it never enters salary (SALARY_EXCLUDED), so before SL7 it could be entered
    and then never seen again anywhere (F-149). Contra rows are PERK rows with
    a negative amount, so the NET is simply the sum: a reversed perk cancels
    itself out without any special case."""
    out = [r for r in (rows or load_ledger())
           if r["category"] == "PERK" and r["status"] == "APPROVED"
           and (staff is None or r["staff"] == staff)
           and (year in (None, "all") or (r.get("date_from") or "")[:4] == str(year))]
    return sorted(out, key=lambda r: (r.get("date_from") or "", r["ts_entry"]), reverse=True)

def perk_years(rows=None):
    return sorted({(r.get("date_from") or "")[:4] for r in (rows or load_ledger())
                   if r["category"] == "PERK" and r["status"] == "APPROVED"
                   and (r.get("date_from") or "")}, reverse=True)

def perk_totals(year=None, rows=None):
    """{staff: net Rs} for the period — the lifetime view when year is None."""
    t = {}
    for r in perk_records(None, year, rows):
        t[r["staff"]] = t.get(r["staff"], 0) + r["amount"]
    return t

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

# =============================================================================
#  S225 (D371): THE LOANS VIEW -- the truth about advances, without the noise.
#
#  The owner, 04-Sep-2026: "staff advance ledger has all entries and it's confusing,
#  so the data should clearly display actual loans -- tranches with details and
#  instalments due -- and the ledger should be clear of the extra entries, as we
#  don't cancel any; then only we can plan which view to share with staff."
#
#  So: ONE pure function, loans_view(), reads the ledger and answers, per staff:
#  every advance actually issued (a TRANCHE), what kind it is, HOW it recovers
#  (advance_lane -- the one D349 rule, never a copy), what has come back, what is
#  left, when the next collection falls and how many months remain. System rows,
#  contras and reversed pairs are not listed -- they are summed into the figures.
#  Nothing is deleted or cancelled: the ledger file is untouched; this is a view.
#  "Falling due this month" is the per-lane instalment BEFORE the close's salary
#  capacity check (recovery_capacity) -- the page says so in as many words.
# =============================================================================
import math
from html import escape as _hesc


def loans_view(rows=None, month=None, staff=None):
    rows = rows if rows is not None else load_ledger()
    month = month or datetime.date.today().strftime("%Y-%m")
    issues = [r for r in rows if r["category"] == "ADVANCE_ISSUE" and r["status"] == "APPROVED"
              and (staff is None or r["staff"] == staff)]
    out = {}
    n_reversed = {}
    for r in issues:
        st = r["staff"]
        if r["amount"] < 0:                       # the contra half of a reversed pair
            continue
        if any(x["contra_of"] == r["id"] and x["category"] == "ADVANCE_ISSUE" and x["status"] == "APPROVED"
               and x["amount"] == -r["amount"] for x in rows):
            n_reversed[st] = n_reversed.get(st, 0) + 1   # the pair, counted once
            continue
        rec = advance_recovered(r["id"], rows)
        cap = advance_capitalised(r["id"], rows)
        bal = r["amount"] + cap - rec
        a = {"issue": r, "balance": bal, "instalment": r.get("instalment") or r["amount"],
             "interest": bool(r.get("interest"))}
        lane = advance_lane(a)
        stt = schedule_state(r, month, rows)
        kids = [x for x in rows if x.get("contra_of") == r["id"] and x["category"] == "ADVANCE_INSTALMENT"
                and x["status"] == "APPROVED"]
        last_paid = max((x.get("closed_month") or x["date_from"][:7]) for x in kids) if kids else None
        deferred_now = is_deferred(r["id"], month, rows)
        if lane == "schedule":
            due = stt["next_amount"] if (stt["next_month"] and stt["next_month"] <= month) else 0
            how = "agreed schedule: " + " → ".join("%s Rs %d" % (e["month"], e["amount"]) for e in stt["schedule"])
        elif lane == "quota":
            due = min(a["instalment"], bal) if (advance_against_month(r) or month) <= month else 0
            how = "in full at the %s close, against that month's salary" % advance_against_month(r)
        elif lane == "loan":
            due = min(a["instalment"], bal)
            how = "Rs %d a month, Rs %d of it interest, until clear" % (a["instalment"], INTEREST_RS)
        else:
            due = min(a["instalment"], bal)
            how = "Rs %d a month" % a["instalment"]
        if bal <= 0:
            due = 0
        if deferred_now:
            due = 0
        t = {"id": r["id"], "date": r["date_from"], "amount": r["amount"], "interest": a["interest"],
             "special": bool(r.get("special")), "lane": lane, "how": how, "instalment": a["instalment"],
             "recovered": rec, "capitalised": cap, "balance": max(0, bal), "open": bal > 0,
             "next_month": stt["next_month"] if lane == "schedule" else (month if (due and bal > 0) else None),
             "next_amount": stt["next_amount"] if lane == "schedule" else due,
             "months_left": stt["months_left"] if lane == "schedule" else
                            (int(math.ceil(bal / float(a["instalment"]))) if bal > 0 and a["instalment"] else 0),
             "defers": stt["defers"], "deferred_now": deferred_now, "due_this_month": due,
             "last_paid": last_paid, "narration": r.get("narration") or "",
             "against_month": r.get("against_month") or ""}
        out.setdefault(st, {"staff": st, "tranches": [], "pending": 0, "outstanding": 0, "due": 0,
                            "reversed": 0})["tranches"].append(t)
    # waterfall: an interest-free tranche waits while an interest loan is open (D250)
    for st, d in out.items():
        has_loan = any(t["open"] and t["interest"] for t in d["tranches"])
        for t in d["tranches"]:
            if t["open"] and t["lane"] == "waterfall" and has_loan:
                t["due_this_month"] = 0
                t["next_month"] = None
                t["how"] += " — waits until the interest loan clears (D250)"
        d["tranches"].sort(key=lambda t: (not t["open"], not t["interest"], t["date"]))
        d["outstanding"] = sum(t["balance"] for t in d["tranches"])
        d["due"] = sum(t["due_this_month"] for t in d["tranches"])
        d["reversed"] = n_reversed.get(st, 0)
    for r in rows:
        if r["category"] == "ADVANCE_ISSUE" and r["status"] == "PENDING" and (staff is None or r["staff"] == staff):
            out.setdefault(r["staff"], {"staff": r["staff"], "tranches": [], "pending": 0, "outstanding": 0,
                                        "due": 0, "reversed": 0})["pending"] += 1
    return {"month": month, "staff": sorted(out.values(), key=lambda d: (-d["outstanding"], d["staff"]))}


def loans_html(view, role, checker_pick=None, names=None):
    """The Loans page body. Plain English, one table per person, nothing a person
    has to decode. Rows the ledger holds as system entries or contras are NOT here
    -- they are inside the figures."""
    month = view["month"]
    body = ""
    if role == "checker":
        opts = "".join("<option%s>%s</option>" % (" selected" if s == checker_pick else "", _hesc(s))
                       for s in (names or []))
        body += ("<form method='get' class='card' style='display:flex;gap:8px;align-items:end;flex-wrap:wrap'>"
                 "<div><label>Person</label><select name='staff'><option value=''>everyone</option>%s</select></div>"
                 "<div><label>Month</label><input type='month' name='m' value='%s' style='width:auto'></div>"
                 "<button class='ok'>Show</button></form>" % (opts, _hesc(month)))
    if not view["staff"]:
        return body + "<p>No advances on record%s.</p>" % (" for this person" if checker_pick else "")
    for d in view["staff"]:
        rows_html = ""
        for t in d["tranches"]:
            kind = ("interest loan" if t["interest"] else "advance") + (" · SPECIAL" if t["special"] else "")
            if t["open"]:
                if t["deferred_now"]:
                    nxt = "<b style='color:#f87171'>deferred this month</b>"
                elif t["next_month"]:
                    nxt = "<b>Rs %d</b> in %s" % (t["next_amount"], _hesc(t["next_month"]))
                else:
                    nxt = "<span style='color:var(--muted)'>waits</span>"
                left = "%d month%s left" % (t["months_left"], "" if t["months_left"] == 1 else "s") if t["months_left"] else ""
                status = "open"
                style = ""
            else:
                nxt, left, status, style = "—", "", "recovered%s" % (" by " + t["last_paid"] if t["last_paid"] else ""), " style='color:#9fb6cc'"
            defers = (" · deferred: " + ", ".join(t["defers"])) if t["defers"] else ""
            note = _hesc(t["narration"])[:80]
            rows_html += ("<tr%s><td>%s</td><td style='text-align:right'>Rs %d</td><td>%s</td>"
                          "<td><small>%s%s</small></td><td style='text-align:right'>Rs %d</td>"
                          "<td style='text-align:right'><b>Rs %d</b></td><td>%s <small>%s</small></td><td><small>%s</small></td></tr>"
                          % (style, _hesc(t["date"]), t["amount"], kind, _hesc(t["how"]), defers,
                             t["recovered"], t["balance"], nxt, left, (status + (" · " + note if note else ""))))
        head = ("outstanding <b>Rs %d</b> · falling due in %s: <b>Rs %d</b>" % (d["outstanding"], _hesc(month), d["due"])
                if d["outstanding"] else "nothing outstanding")
        if d["pending"]:
            head += " · <b style='color:#f87171'>%d awaiting approval</b>" % d["pending"]
        if d["reversed"]:
            head += " · <small>%d corrected entr%s not counted</small>" % (d["reversed"], "y" if d["reversed"] == 1 else "ies")
        table = ("<div style='overflow-x:auto'><table><tr><th>taken</th><th>amount</th><th>kind</th><th>how it recovers</th>"
                 "<th>recovered</th><th>balance</th><th>next collection</th><th>status</th></tr>%s</table></div>"
                 % rows_html) if rows_html else "<p><small>no advance issued yet</small></p>"
        body += ("<details open style='margin:10px 0;background:var(--card);border:1px solid var(--line);"
                 "border-radius:14px;padding:4px 14px'><summary style='cursor:pointer;padding:10px 2px;"
                 "font-size:16.5px;font-weight:700;color:#fff'>%s <span style='font-weight:400;font-size:13.5px;"
                 "color:var(--muted)'>— %s</span></summary>%s</details>" % (_hesc(d["staff"]), head, table))
    body += ("<p><small>“Falling due” is each loan's own instalment for the month, by the lane that recovers it "
             "(schedule · against-salary · loan · waterfall — D349). The close then applies the salary "
             "capacity check (D333): what the salary cannot bear is held, not lost. Corrections in the ledger are never "
             "deleted — a reversed advance is counted out here, not shown as a loan.</small></p>")
    return body


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
    # D331: an advance attributed AGAINST a FUTURE month waits for its month —
    # it neither recovers nor pays interest before then. Only the eligibility
    # changes; the waterfall's order and arithmetic are untouched.
    snap = [a for a in snap if advance_against_month(a["issue"]) <= month]
    # ---- SL4 (owner ruling "A", S190): THE QUOTA LANE -----------------------
    # A quota advance — D331-era (explicit against_month), NOT a loan, and
    # taken with the default recover-fully instalment (instalment == amount) —
    # recovers IN FULL at its month's close in its OWN lane, beside the
    # waterfall, never inside its queue. Without this, the owner's Rs 15,000
    # August advance would have waited behind Rs 3.59 lakh of loan book
    # ("waiting for the loan to clear", in the statement's own words).
    # A deliberately PARTIAL instalment opts back into the waterfall — the
    # entry form says "blank = recover fully this month", and this lane is
    # that promise kept. The loan's Skip pauses ONLY the waterfall (its
    # historic meaning); the quota lane always recovers, because this is the
    # month's own salary money — attribution decided WHICH month, the close
    # collects it.
    rows_now = load_ledger()
    _settings = load_settings()
    # ---- SL6 (D332 §4): CAPACITY — nothing recovers that the salary cannot
    # bear (F-147). One budget per staff, spent by every lane below in order
    # (schedule, then quota, then waterfall). None = no base on file = the
    # gate is disabled rather than freezing recovery, and says so out loud.
    _cap = {}
    for a in snap:
        s = a["issue"]["staff"]
        if s not in _cap:
            _cap[s] = recovery_capacity(s, month, rows_now, _settings)
    _held = set()
    def _take(staff, want):
        """Spend from the staff's capacity; returns what may actually be taken."""
        c = _cap.get(staff)
        if c is None:
            return want
        give = max(0, min(want, c))
        _cap[staff] = c - give
        if give < want:
            _held.add(staff)
        return give
    # ---- SL6: DEFER — a deferred month collects NOTHING for that advance.
    # The whole instalment shifts; the schedule extends one month. On an
    # interest-bearing loan a 3rd+ defer in the FY capitalises Rs 1000 unless
    # the owner waived it at the tap (D332 §2.1). No other capitalisation:
    # interest rides inside each collected instalment, so deferral leaves
    # total loan interest unchanged.
    deferred_now = [a for a in snap if is_deferred(a["issue"]["id"], month, rows_now)]
    for a in deferred_now:
        d = next((x for x in advance_defers(a["issue"]["id"], rows_now)
                  if x["date_from"] == month), None)
        if d and d.get("defer_penalty") and not d.get("penalty_waived"):
            _sysrow(a["issue"]["staff"], "LOAN_CAPITALISE", INTEREST_RS, a["issue"]["id"],
                    f"deferred {month}: 3rd+ defer of {fy_of(month)} — Rs {INTEREST_RS} "
                    f"penalty capitalised onto loan {a['issue']['id']} (D332 §2.1)")
    snap = [a for a in snap if a not in deferred_now]
    # ---- SL6: THE SCHEDULE LANE (D332 §4) --------------------------------
    # An advance carrying a repayment SCHEDULE collects this month's scheduled
    # amount in its own lane, beside the waterfall — never queued behind the
    # loan book. Uneven distributions (8,000 then 4,000 x 3) are the point.
    scheduled = [a for a in snap if advance_lane(a) == "schedule"]   # D349
    snap = [a for a in snap if a not in scheduled]
    for a in scheduled:
        iid = a["issue"]["id"]; staff = a["issue"]["staff"]
        due_cum = schedule_due_cum(a["issue"], month, rows_now)
        want = min(a["balance"], max(0, (due_cum or 0) - advance_recovered(iid, rows_now)))
        got = _take(staff, want)
        if got > 0:
            _sysrow(staff, "ADVANCE_INSTALMENT", -got, iid,
                    f"scheduled instalment for {month} (D332 schedule lane; "
                    f"balance after: {a['balance']-got})")
        if got < want:
            _sysrow(staff, "CAPACITY_HOLD", 0, iid,
                    f"Rs {want-got} of the {month} scheduled instalment HELD — the "
                    f"salary could not bear it (F-147). It stays owed and collects later")
    # ---- SL4 (owner ruling "A", S190): THE QUOTA LANE ----------------------
    # A quota advance — D331-era (explicit against_month), NOT a loan, and
    # taken with the default recover-fully instalment (instalment == amount) —
    # recovers IN FULL at its month's close in its OWN lane, beside the
    # waterfall, never inside its queue.
    quota = [a for a in snap if advance_lane(a) == "quota"]          # D349
    snap = [a for a in snap if a not in quota]
    for a in quota:
        got = _take(a["issue"]["staff"], a["balance"])
        if got > 0:
            _sysrow(a["issue"]["staff"], "ADVANCE_INSTALMENT", -got,
                    a["issue"]["id"],
                    f"quota advance recovered in full against {advance_against_month(a['issue'])} "
                    f"salary (SL4 own lane; balance after: {a['balance']-got})")
        if got < a["balance"]:
            _sysrow(a["issue"]["staff"], "CAPACITY_HOLD", 0, a["issue"]["id"],
                    f"Rs {a['balance']-got} of the quota advance HELD — the salary "
                    f"could not bear it (F-147). It stays owed and collects later")
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
        # F-147: the waterfall may not spend more than the salary can bear.
        _wf_want = budget
        budget = _take(staff, budget)
        if budget < _wf_want:
            _sysrow(staff, "CAPACITY_HOLD", 0, advs[0]["issue"]["id"],
                    f"Rs {_wf_want-budget} of the {month} waterfall instalment HELD — "
                    f"the salary could not bear it (F-147); it stays owed")
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

# ============================ D332 · SL5 (S192) ============================
# The waiver instrument (§2.8), policy-date settings (§2.7 / F-150), and the
# F-151 attendance-wording fix. Built on the live SL4 bytes (470bb113…).
#
# WAIVE forgives a derived deduction. It is NEVER a frozen rupee amount: a
# waiver stores WHAT it targets (scope + line key), and compute_salary derives
# the forgiven figure at compute time, so a later ruling change flows through.
# Append-only + contra-reversed, exactly like the ledger: a reversal is a new
# record pointing at the original by `contra_of`; activeness is DERIVED, never
# mutated in place.
SETTINGS_FILE = "ledger_settings.json"
SETTINGS_DEFAULTS = {
    # None => the notice has NOT been served => the month is PREVIEW-ONLY and
    # attendance-policy deductions are shown but not applied (D332 §2.7; F-150).
    "attendance_enforce_from": None,      # 'YYYY-MM' inclusive
    "sunday_enforce_from":     None,      # 'YYYY-MM' inclusive (roster policy)
    "incentive_rungs":         [],        # [{'from':'YYYY-MM','limit_full':N,'limit_half':N}]
    # D332 / F-147: rupees of salary protected from advance & loan recovery.
    # 0 = only the "never push NET below zero" guard applies.
    "min_takehome":            0,
    # who may WAIVE — seeded Dr Manoj active, Dr Bhawna scoped-in but INACTIVE
    # (the owner flips bhawna to true when he chooses). Keyed by ledger username.
    "waiver_authority": {"manoj": True, "bhawna": False},
}
def load_settings():
    try:
        with open(_p(SETTINGS_FILE), encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        j = {}
    s = dict(SETTINGS_DEFAULTS)
    for k in SETTINGS_DEFAULTS:
        if k in j and k != "waiver_authority":
            s[k] = j[k]
    wa = dict(SETTINGS_DEFAULTS["waiver_authority"])
    wa.update({k: bool(v) for k, v in (j.get("waiver_authority") or {}).items()})
    s["waiver_authority"] = wa
    return s
def save_settings(patch, who):
    s = load_settings()
    for k, v in (patch or {}).items():
        if k in SETTINGS_DEFAULTS:
            s[k] = v
    os.makedirs(LEDGER_DIR, exist_ok=True)
    tmp = _p(SETTINGS_FILE + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    os.replace(tmp, _p(SETTINGS_FILE))
    os.chmod(_p(SETTINGS_FILE), 0o600)
    return s
def attendance_enforced(month, settings=None):
    """True only when the notice-served date is set AND this month is on/after
    it. Until then the month is preview-only: attendance-policy deductions are
    displayed struck-through and DO NOT reduce NET (D332 §2.7)."""
    s = settings or load_settings()
    d = s.get("attendance_enforce_from")
    return bool(d) and str(month) >= str(d)

# ------------------------------------------------------------- waivers (§2.8)
WAIVER_FILE = "waivers_%s.json"          # per-month store, append-only
WAIVABLE_ATT = ("marks", "early", "earlybig", "uninformed", "excess")
def _waiver_path(month): return _p(WAIVER_FILE % month)
def load_waivers(month):
    try:
        with open(_waiver_path(month), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
def _save_waivers(month, lst):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    tmp = _waiver_path(month) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lst, f, indent=2)
    os.replace(tmp, _waiver_path(month))
    os.chmod(_waiver_path(month), 0o600)
def active_waivers(month):
    """Activeness DERIVED from contra records (append-only): a waiver is active
    if it is not itself a reversal and no reversal points at it."""
    lst = load_waivers(month)
    reversed_ids = {w.get("contra_of") for w in lst if w.get("contra_of")}
    return [w for w in lst if not w.get("contra_of") and w["id"] not in reversed_ids]
def can_waive(who, settings=None):
    s = settings or load_settings()
    return bool((s.get("waiver_authority") or {}).get(who))
def make_waiver(users, who, month, scope, reason, staff="", line_key=""):
    """Forgive a deduction. Authority = a checker on the ACTIVE waiver list.
    Compulsory written reason (no escape hatch). Scopes: LINE (one deduction of
    one staff) / STAFF_MONTH (all of one staff's deductions) / ALL_MONTH."""
    if users.get(who, {}).get("role") != "checker":
        raise PermissionError("only a checker may waive")
    if not can_waive(who):
        raise PermissionError(f"{who} is not an active waiver authority (D332 §2.8)")
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("a written reason is required to waive (no escape hatch)")
    if scope not in ("LINE", "STAFF_MONTH", "ALL_MONTH"):
        raise ValueError("scope must be LINE, STAFF_MONTH or ALL_MONTH")
    if scope in ("LINE", "STAFF_MONTH") and not (staff or "").strip():
        raise ValueError("staff is required for a LINE or STAFF_MONTH waiver")
    if scope == "LINE" and not (line_key or "").strip():
        raise ValueError("a line is required for a LINE waiver")
    rec = {"id": secrets.token_hex(6), "ts": now(), "by": who, "scope": scope,
           "staff": (staff or "").strip(), "line_key": (line_key or "").strip(),
           "reason": reason, "contra_of": ""}
    lst = load_waivers(month); lst.append(rec); _save_waivers(month, lst)
    ntfy(f"WAIVE {scope} {rec['staff'] or 'ALL'} {rec['line_key']} by {who}: {reason[:40]}")
    return rec
def waiver_contra(users, who, month, waiver_id, reason):
    """Reverse a waiver by appending a contra record (append-only)."""
    if users.get(who, {}).get("role") != "checker" or not can_waive(who):
        raise PermissionError("only an active waiver authority may reverse a waiver")
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("a reason is required to reverse a waiver")
    orig = next((w for w in active_waivers(month) if w["id"] == waiver_id), None)
    if not orig:
        raise ValueError("no such active waiver")
    lst = load_waivers(month)
    lst.append({"id": secrets.token_hex(6), "ts": now(), "by": who,
                "scope": orig["scope"], "staff": orig["staff"],
                "line_key": orig["line_key"], "reason": "REVERSAL: " + reason,
                "contra_of": waiver_id})
    _save_waivers(month, lst)
def waived_amount(name, line_key, amount, wvs):
    """The forgiven rupees for one deduction line, derived from active waivers.
    A magnitude in, a magnitude out (0 if nothing applies)."""
    if amount <= 0:
        return 0.0
    for w in wvs:
        sc = w["scope"]
        if sc == "ALL_MONTH":
            return float(amount)
        if sc == "STAFF_MONTH" and w["staff"] == name:
            return float(amount)
        if sc == "LINE" and w["staff"] == name and w["line_key"] == line_key:
            return float(amount)
    return 0.0


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
    settings = load_settings()
    enforced = attendance_enforced(month, settings)
    wvs = active_waivers(month)
    table = []
    hasher = hashlib.md5()
    try:
        hasher.update(open(_att(f"salary_inputs_{month}.csv"), "rb").read())
    except FileNotFoundError:
        pass
    hasher.update(json.dumps(rul, sort_keys=True).encode())
    hasher.update(json.dumps(adj, sort_keys=True).encode())
    hasher.update(json.dumps(sorted(bases.items())).encode())
    hasher.update(json.dumps(load_waivers(month), sort_keys=True).encode())
    hasher.update(json.dumps(settings, sort_keys=True).encode())
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
        # D332 §2.7 (F-150): until the notice-served date is set, the month is
        # PREVIEW-ONLY — attendance-policy deductions are shown but not applied.
        att_raw = {"marks": ded_marks, "early": ded_early, "earlybig": eb_rs,
                   "uninformed": fine_uninf, "excess": fine_exc_adj}
        att_applied = {k: (v if enforced else 0.0) for k, v in att_raw.items()}
        # D332 §2.8: WAIVE forgives derived deductions. Any line: att:<type> or
        # led:<row id>; STAFF_MONTH / ALL_MONTH forgive every deduction in scope.
        waived_detail = []
        waived_att = 0.0
        for _k, _v in att_applied.items():
            _w = waived_amount(name, "att:" + _k, _v, wvs)
            if _w:
                waived_att += _w
                waived_detail.append({"line": "att:" + _k, "label": _k, "amount": _w})
        led_rows = [rr for rr in rows_l if rr["staff"] == name
                    and rr["status"] == "APPROVED"
                    and rr.get("closed_month") == month
                    and rr["category"] not in SALARY_EXCLUDED
                    and rr["amount"] < 0]
        waived_led = 0.0
        for rr in led_rows:
            _w = waived_amount(name, "led:" + rr["id"], -rr["amount"], wvs)
            if _w:
                waived_led += _w
                waived_detail.append({"line": "led:" + rr["id"],
                                      "label": CATEGORIES.get(rr["category"], [rr["category"]])[0],
                                      "amount": _w})
        sum_att = sum(att_applied.values())
        waived_total = round(waived_att + waived_led, 2)
        net = round(base + inc_rs + ot_ok + a["credit"] + waived_total
                    - sum_att - a["debit"])          # owner ruling: nearest rupee
        table.append({
            "name": name, "base": base, "absent": absent, "outstation": outst,
            "ded_marks": ded_marks, "ded_early": ded_early,
            "fine_uninf": fine_uninf, "fine_exc": fine_exc_adj,
            "earlybig_rs": eb_rs, "earlybig_n": len(eb_mine),
            "ot_cand": ot_cand, "ot_ok": ot_ok,
            "inc": inc_rs, "adj_cr": a["credit"], "adj_db": a["debit"],
            "leave_days": a["leave_days"], "net": net,
            "att_preview": (not enforced), "waived": waived_total,
            "deferred_n": len([rr for rr in rows_l
                               if rr["staff"] == name and rr["category"] == "ADVANCE_DEFER"
                               and rr["status"] == "APPROVED" and rr["date_from"] == month]),
            "waived_detail": waived_detail,
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
         "<th>&minus;early-big</th><th>&minus;att. ded.</th><th>&minus;ledger db</th><th>+waived</th>"
         "<th>deferred</th>"
         "<th>NET Rs</th></tr>")
    b = ""
    for t in table:
        fines = t["fine_uninf"] + t["fine_exc"]
        cls = "net-pos" if t["net"] >= 0 else "net-neg"
        pv = t.get("att_preview")
        _d = (lambda v: (f"<s>{v:g}</s>" if (pv and v) else f"{v:g}"))
        b += (f"<tr><td>{_esc(t['name'])}"
              + (f" <small>({t['outstation']} outstation)</small>" if t["outstation"] else "")
              + f"</td><td>{t['base']:g}</td><td>{t['inc']:g}</td><td>{t['ot_ok']:g}</td>"
              f"<td>{t['adj_cr']:g}</td><td>{_d(t['ded_marks'])}</td>"
              f"<td>{_d(t['ded_early'])}</td><td>{_d(t['earlybig_rs'])}</td>"
              f"<td>{_d(fines)}</td><td>{t['adj_db']:g}</td>"
              f"<td>{t.get('waived',0):g}</td>"
              + ("<td style='color:#c0392b'><b>%d deferred</b></td>" % t["deferred_n"]
                 if t.get("deferred_n") else "<td>&mdash;</td>")
              + f'<td><span class="{cls}"><b>{t["net"]}</b></span></td></tr>')
    final_tbl = (f'<table><tr>{h[4:-5]}</tr>{b}'
                 f'<tr><td colspan="12" style="text-align:right"><b>TOTAL PAYOUT'
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
            inner += (f"<tr><td>Uninformed-absence deduction</td><td>register-checked"
                      f"</td><td>&minus;{t['fine_uninf']:g}</td></tr>")
        if t["fine_exc"] or t["outstation"]:
            note = (f"absent {t['absent']} &minus; {t['outstation']} outstation"
                    if t["outstation"] else f"absent {t['absent']}")
            inner += (f"<tr><td>Excess-absence deduction</td><td>{note}</td>"
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
        if t.get("att_preview"):
            inner += ('<tr style="color:#c0392b"><td>Attendance deductions</td>'
                      '<td>PREVIEW &mdash; shown, not applied (notice not served, D332 §2.7)</td>'
                      '<td>0 applied</td></tr>')
        for wd in t.get("waived_detail", []):
            inner += (f'<tr style="color:#2f8f4e"><td>Waived: {_esc(str(wd["label"]))}</td>'
                      f'<td>D332 §2.8 waiver</td><td>+{wd["amount"]:g}</td></tr>')
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
&minus; early-departure &minus; genuine big-early-exits &minus; attendance deductions &minus; ledger
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
                          f" -attded {t['fine_uninf'] + t['fine_exc']}"
                          f" +waived {t.get('waived',0)}"
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
                    "ledger_debits_Rs", "waived_Rs", "NET_Rs", "leave_days", "outstation_days"])
        for t in table:
            w.writerow([t["name"], t["base"], t["inc"], t["ot_ok"], t["adj_cr"],
                        t["ded_marks"], t["ded_early"], t["earlybig_rs"],
                        t["fine_uninf"], t["fine_exc"], t["adj_db"], t.get("waived",0), t["net"],
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
                     + ("Statement" if role == "checker" else "My statement") + "</a>",
                     f'<a href="{URL_PREFIX}/loans"><b>'
                     + ("Loans" if role == "checker" else "My loans") + "</b></a>"]
            if role == "checker":
                links += [f'<a href="{URL_PREFIX}/pending"><b>Pending</b></a>',
                          f'<a href="{URL_PREFIX}/book">Full ledger</a>',
                          f'<a href="{URL_PREFIX}/advances">Advances</a>',
                          f'<a href="{URL_PREFIX}/perks">Perks</a>',
                          f'<a href="{URL_PREFIX}/salary"><b>Salary</b></a>',
                          f'<a href="{URL_PREFIX}/settings">Settings</a>']
            links.append(f'<a href="{URL_PREFIX}/logout">Logout ({u})</a>')
            nav = '<div class="nav">' + "".join(links) + "</div>"
        return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--bg:#0f2233;--card:#16324a;--ink:#eaf2fa;--muted:#9fb6cc;--blue:#3b82f6;
 --green:#22c55e;--red:#ef4444;--line:#274b66}}
*{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
 margin:0;background:var(--bg);color:var(--ink);line-height:1.45}}
.wrap{{max-width:900px;margin:0 auto;padding:14px 12px 40px}}
h2{{color:#fff;margin:6px 0;font-size:19px}} a{{color:#8fc3ff;text-decoration:none}}
.nav{{display:flex;flex-wrap:wrap;gap:4px 10px;margin:8px 0 14px;font-size:14px}}
.nav a{{background:var(--card);border:1px solid var(--line);border-radius:9px;
 padding:6px 11px;color:var(--ink)}} .nav a b{{color:#ffd868}}
table{{border-collapse:collapse;width:100%;background:var(--card)}}
td,th{{border:1px solid var(--line);padding:7px 6px;font-size:13.5px;text-align:left}}
th{{background:#1b3d5c;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.self{{background:rgba(239,68,68,.14)}} .direct{{color:var(--muted);font-style:italic}}
label{{display:block;font-size:12.5px;color:var(--muted);margin:10px 0 3px;font-weight:600}}
input,select,textarea{{font-size:16px;padding:10px;margin:0;width:100%;
 background:#0b1b29;border:1.5px solid var(--line);color:#fff;border-radius:10px}}
input:focus,select:focus,textarea:focus{{outline:none;border-color:var(--blue)}}
input[type=date],input[type=month]{{color-scheme:dark}}
button{{font-size:16px;font-weight:600;padding:12px 18px;margin:12px 2px 4px;border:0;
 border-radius:12px;cursor:pointer;width:100%}}
.ok{{background:var(--green);color:#08240f}} .no{{background:var(--red);color:#fff}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;
 padding:14px 16px;margin:10px 0}}
form .card,.card form{{max-width:640px}}
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}}
@media(max-width:520px){{.row2{{grid-template-columns:1fr}}}}
.rev{{color:#7d90a5;background:#122a40}} .rev td{{text-decoration:line-through}}
.mhead{{background:#1f3864;color:#fff;font-weight:bold}}
.amt-c{{color:#4ade80;font-weight:bold}} .amt-d{{color:#f87171;font-weight:bold}}
small{{color:var(--muted)}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}
</style></head><body><div class="wrap"><h2>&#128213; Staff Ledger</h2>{nav}{body}
<p><small>v{APP_VERSION} · append-only · corrections by contra entry only</small></p>
</div></body></html>"""

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
                                 interest=bool(f.get("interest")),
                                 against_month=f.get("against_month",""),
                                 special=bool(f.get("special")),
                                 schedule=f.get("schedule", ""))
                if row.get("special"):
                    msg_extra = (f"<p style='color:#b45309'><b>SPECIAL advance saved "
                                 f"PENDING.</b> <a href='{URL_PREFIX}/application/"
                                 f"{row['id']}'>Upload the signed application now</a> "
                                 f"— it cannot be approved without it.</p>")
                else:
                    msg_extra = ""
                amt = row["amount"]
                msg = (f"<p style='color:green'>Saved <b>{row['status']}</b>: "
                       f"{row['staff']} · {CATEGORIES[cat][0]} · Rs {amt}"
                       + (f" · {days} day(s)" if days else "") + "</p>") + msg_extra
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
        advmeta = {}
        if "ADVANCE_ISSUE" in cats:
            _rows_now = load_ledger()
            _m0 = datetime.date.today().strftime("%Y-%m")
            _m1 = (datetime.date.today().replace(day=1) + datetime.timedelta(days=32)
                   ).strftime("%Y-%m")
            for _s in staff_names():
                _c = advance_ceiling(_s)
                advmeta[_s] = {"ceiling": _c, "pct": advance_pct(_s),
                               "enforced": _c > 0,
                               "taken": {_m0: advance_month_taken(_s, _m0, _rows_now),
                                         _m1: advance_month_taken(_s, _m1, _rows_now)}}
        opts_cat = "".join(f'<option value="{c}">{CATEGORIES[c][0]}'
                           + (f" (Rs {live_rate(c)}"
                              + ("/day" if CATEGORIES[c][2] else "") + ")"
                              if CATEGORIES[c][1] else "")
                           + "</option>" for c in cats)
        catmeta = {c: {"rate": live_rate(c) if CATEGORIES[c][1] is not None else None,
                       "per_day": CATEGORIES[c][2],
                       "sign": CATEGORIES[c][3], "narr_req": CATEGORIES[c][4],
                       "advance": c == "ADVANCE_ISSUE",
                       "interest_ok": is_checker and c == "ADVANCE_ISSUE"} for c in cats}
        body = msg + f"""<div class="card"><form method="post" id="ef">
        <div class="row2">
          <div><label>Staff</label><select name="staff">{opts_staff}</select></div>
          <div><label>Category</label><select name="category" id="cat">{opts_cat}</select></div>
        </div>
        <div class="row2">
          <div id="f_d1"><label>Date</label><input type="date" name="date_from" required></div>
          <div id="f_d2"><label>To (blank = one day)</label>
            <input type="date" name="date_to"></div>
        </div>
        <div class="row2">
          <div id="f_amt"><label id="l_amt">Amount Rs</label>
            <input type="number" name="amount" value="0" min="0"></div>
          <div id="f_inst"><label>Instalment Rs/month (blank = full this month)</label>
            <input type="number" name="instalment" min="0">
            <label style="font-weight:normal;margin-top:4px">… or an agreed schedule (S225): one step per
            line as <code>2026-09:4000</code>, the steps adding up to the advance exactly</label>
            <textarea name="schedule" rows="2" placeholder="2026-09:4000&#10;2026-10:4000&#10;2026-11:5000"></textarea></div>
        </div>
        <div id="f_am"><label>Against which month's salary? (D331 — normally this month;
          a future month books it against THAT month's quota)</label>
          <input type="month" name="against_month" id="am"></div>
        <div id="f_sp"><label style="font-weight:normal"><input type="checkbox"
          name="special" value="1" id="sp" style="width:auto"> SPECIAL advance —
          above the ceiling. Needs the signed written application
          (Dr Manoj / Dr Bhawna) uploaded before it can be approved.</label></div>
        <div id="advline" style="font-weight:bold;margin:6px 0"></div>
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
        var A = {json.dumps(advmeta)};
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
        var amEl = document.getElementById("am");
        if (amEl && !amEl.value) {{
          amEl.value = new Date().toISOString().slice(0, 7);
        }}
        function advline() {{
          var el = document.getElementById("advline"), m = M[cat.value];
          if (!m.advance) {{ el.textContent = ""; return; }}
          var a = A[stf.value];
          if (!a) {{ el.textContent = ""; return; }}
          var mon = amEl.value || new Date().toISOString().slice(0, 7);
          if (!a.enforced) {{
            el.textContent = "Ceiling NOT enforced — no base salary on file for "
              + stf.value + " (fix staff_master.csv).";
            el.style.color = "#b45309"; return;
          }}
          var t = a.taken[mon];
          el.textContent = "Taken against " + mon + ": Rs "
            + (t === undefined ? "0 (computed exactly at save)" : t)
            + " of Rs " + a.ceiling + " max (" + a.pct + "% of base).";
          el.style.color = (t !== undefined && t >= a.ceiling) ? "#c0392b" : "#2f8f4e";
        }}
        stf.addEventListener("change", advline);
        if (amEl) amEl.addEventListener("change", advline);
        function refresh() {{
          var m = M[cat.value];
          show("f_d2", m.per_day);
          show("f_amt", m.rate === null);
          show("f_inst", !!m.advance);
          show("f_int", !!m.interest_ok);
          show("f_am", !!m.advance);
          show("f_sp", !!m.advance);
          advline();
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
            {(('<b style="color:#b45309">SPECIAL — above the ceiling'
               + (', against ' + r.get('against_month','') if r.get('against_month') else '')
               + '.</b> '
               + (f'<a href="{URL_PREFIX}/application/' + r['id'] + '/file">📄 application on file</a>'
                  if application_on_file(r['id'])
                  else f'<b style="color:red">application NOT uploaded</b> — '
                       f'<a href="{URL_PREFIX}/application/' + r['id'] + '">attach it</a>')
               + '<br>') if r.get('special') else '')}
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

    # ------------------------------------------------ D331: the application
    # The ledger's first attachment: the signed written application a SPECIAL
    # (above-ceiling) advance needs before it can be approved. The shared
    # clinic scan widget does the capturing (camera AND gallery — verified on
    # the box, S190); the file lives under LEDGER_DIR/applications/ and its
    # sha is recorded in the row itself.

    @app.route(URL_PREFIX + "/scan/widget.js")
    def d331_widget_js():
        try:
            with open(SCANNER_JS, "rb") as f:
                return app.response_class(f.read(), mimetype="application/javascript")
        except OSError:
            abort(404)

    @app.route(URL_PREFIX + "/scan/jspdf.js")
    def d331_jspdf_js():
        try:
            with open(JSPDF_JS, "rb") as f:
                return app.response_class(f.read(), mimetype="application/javascript")
        except OSError:
            abort(404)

    @app.route(URL_PREFIX + "/application/<rid>")
    def d331_application_page(rid):
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        rows = {r["id"]: r for r in load_ledger()}
        r = rows.get(rid)
        if not r or r["category"] != "ADVANCE_ISSUE" or not r.get("special"):
            return page("Application", "<div class='card'>No such special advance.</div>", u)
        title = (f"Signed application — {r['staff']} Rs {r['amount']}"
                 f" (against {r.get('against_month','')})")
        cfg = {"title": title,
               "uploadUrl": f"{URL_PREFIX}/application/{rid}/upload",
               "fileField": "file",
               "uploadFields": {"row_id": rid},
               "nameBase": f"Advance_application_{rid}",
               "backUrl": URL_PREFIX + ("/pending" if users[u]["role"] == "checker" else "/mine"),
               "allowIdCard": False, "allowBatch": False}
        try:
            ver = int(os.path.getmtime(SCANNER_JS))
        except OSError:
            ver = 0
        body = (("<div class='card'><b>📄 An application is already on file"
                 f"</b> — <a href='{URL_PREFIX}/application/{rid}/file'>view it</a>. "
                 "Uploading again replaces it.</div>") if application_on_file(rid) else "") + (
            "<div class='card'><b>%s</b><p>Photograph the signed application "
            "(Dr Manoj / Dr Bhawna), or upload the saved photo.</p></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='%s/scan/jspdf.js'></script>"
            "<script src='%s/scan/widget.js?v=%d'></script>"
            % (title, json.dumps(cfg), URL_PREFIX, URL_PREFIX, ver))
        return page("Application", body, u)

    @app.route(URL_PREFIX + "/application/<rid>/upload", methods=["POST"])
    def d331_application_upload(rid):
        u, users = user()
        if not u: abort(403)
        f = request.files.get("file")
        try:
            sha = save_application(rid, f.read() if f else b"", u)
        except ValueError as e:
            return {"ok": False, "error": str(e)}, 400
        return {"ok": True, "sha256": sha[:12]}

    @app.route(URL_PREFIX + "/application/<rid>/file")
    def d331_application_file(rid):
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if not application_on_file(rid):
            abort(404)
        with open(application_path(rid), "rb") as f:
            return app.response_class(f.read(), mimetype="application/pdf")

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
        groups = {}                       # staff -> [advance-card html]
        totals = {}                       # staff -> {bal, n, interest, special_pending}
        _rows_all = load_ledger()
        for a in open_advances():
            iid = a["issue"]["id"]
            tag = (("<b style='color:#e0a93e'> · INTEREST-BEARING LOAN "
                    f"(Rs {INTEREST_RS}/mo)</b>") if a["interest"]
                   else " · <b style='color:#4ade80'>interest-free</b>")
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
            am_note = ""
            if a["issue"].get("against_month"):
                am_note = f" · against <b>{a['issue']['against_month']}</b> salary"
            sp_note = ""
            if a["issue"].get("special"):
                sp_note = (" · <b style='color:#b45309'>SPECIAL</b> "
                           + (f"<a href='{URL_PREFIX}/application/{iid}/file'>📄 application</a>"
                              if application_on_file(iid)
                              else "<b style='color:red'>application missing</b>"))
            # ---- SL6 (D332): schedule state + loud defers -----------------
            stt = schedule_state(a["issue"], nxt)
            sched_note = ""
            if stt["schedule"]:
                steps = " → ".join(f"{e['month']}:Rs {e['amount']}" for e in stt["schedule"])
                nxt_txt = (f"next <b>Rs {stt['next_amount']} in {stt['next_month']}</b>"
                           if stt["next_month"] else "<b>schedule complete</b>")
                sched_note = (f"<br><small>schedule: {steps}<br>"
                              f"recovered Rs {stt['recovered']} of Rs {a['issue']['amount']} · "
                              f"{stt['months_left']} month(s) left · {nxt_txt}</small>")
            else:
                sched_note = ("<br><small>no schedule — recovering by instalment "
                              "(uniform)</small>")
            def_band = ""
            if stt["defers"]:
                def_band = ("<div style='background:#fdecea;border:1px solid #c0392b;"
                            "border-radius:6px;padding:6px;margin:6px 0;color:#c0392b'>"
                            "<b>DEFERRED:</b> " + ", ".join(stt["defers"])
                            + " — each shifted the whole schedule one month</div>")
            _usedd = fy_defers(a["issue"]["staff"], nxt)
            _pen = a["interest"] and len(_usedd) >= DEFERS_FREE_FY
            defer_form = f"""<form method="post" action="{URL_PREFIX}/defer" style="margin-top:4px">
                <input type="hidden" name="id" value="{iid}">
                <input type="month" name="month" value="{nxt}" style="width:auto">
                <input name="reason" placeholder="reason (required)" required>
                {"<label style='font-weight:normal'><input type='checkbox' name='waive' style='width:auto'> waive the Rs %d penalty (3rd+ defer this FY)</label>" % INTEREST_RS if _pen else ""}
                <button class="no" onclick="return confirm('Defer this collection? The whole instalment shifts one month and the schedule extends by one.{" Rs %d penalty capitalises unless you ticked waive." % INTEREST_RS if _pen else ""}')">Defer this month</button>
                <br><small>defers used {fy_of(nxt)}: {len(_usedd)}/{DEFERS_FREE_FY} free{" — the next one carries a waivable Rs %d penalty" % INTEREST_RS if _pen else ""}</small>
                </form>"""
            _st = a["issue"]["staff"]
            groups.setdefault(_st, []).append(
                     f"<div class='card' style='margin:8px 0'>advance "
                     f"Rs {a['issue']['amount']} ({a['issue']['date_from']}){tag}"
                     f"{am_note}{sp_note}<br>"
                     f"balance <b>Rs {a['balance']}</b> · recovering Rs {a['instalment']}/month"
                     f"{sched_note}{def_band}{defer_form}{skiprow}<br><small>id {iid}</small></div>")
            t = totals.setdefault(_st, {"bal": 0, "n": 0, "int": False, "sp": False})
            t["bal"] += a["balance"]; t["n"] += 1
            t["int"] = t["int"] or bool(a["interest"])
        # pending advances (awaiting approval) + lifetime perks, per staff
        pend = {}
        for r in _rows_all:
            if r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "PENDING":
                pend[r["staff"]] = pend.get(r["staff"], 0) + 1
        body = ""
        allnames = sorted(set(list(groups) + list(pend)))
        for _st in allnames:
            t = totals.get(_st, {"bal": 0, "n": 0, "int": False})
            perks_life = sum(x["amount"] for x in perk_records(_st, None, _rows_all))
            bits = [f"{t['n']} open" if t["n"] else "none open",
                    f"balance <b>Rs {t['bal']}</b>" if t["bal"] else ""]
            if t.get("int"): bits.append("<b style='color:#e0a93e'>interest loan</b>")
            if pend.get(_st): bits.append(f"<b style='color:#f87171'>{pend[_st]} PENDING approval</b>")
            if perks_life: bits.append(f"perks lifetime Rs {perks_life}")
            head_bits = " · ".join(b for b in bits if b)
            inner = "".join(groups.get(_st, []))
            if pend.get(_st):
                inner += (f"<div class='card' style='margin:8px 0;border-color:#7f1d1d'>"
                          f"{pend[_st]} advance(s) awaiting approval — decide on the "
                          f"<a href='{URL_PREFIX}/pending'><b>Pending</b></a> page.</div>")
            inner += (f"<div style='margin:6px 0'><a href='{URL_PREFIX}/perks?staff="
                      f"{html_esc(_st)}'>&#127873; perks history</a> · "
                      f"<a href='{URL_PREFIX}/statement?staff={html_esc(_st)}'>&#128220; full statement</a></div>")
            body += (f"<details {'open' if len(allnames)==1 else ''} "
                     f"style='margin:10px 0;background:var(--card);border:1px solid var(--line);"
                     f"border-radius:14px;padding:4px 14px'>"
                     f"<summary style='cursor:pointer;padding:10px 2px;font-size:16.5px;"
                     f"font-weight:700;color:#fff'>{html_esc(_st)} "
                     f"<span style='font-weight:400;font-size:13.5px;color:var(--muted)'>— {head_bits}</span>"
                     f"</summary>{inner}</details>")
        if not body: body = "<p>No open advances.</p>"
        return page("Open advances", body, u)

    @app.route(URL_PREFIX + "/loans")
    def loans():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        role = users[u]["role"]
        month = request.args.get("m", "").strip() or datetime.date.today().strftime("%Y-%m")
        try:
            datetime.date.fromisoformat(month + "-01")
        except ValueError:
            month = datetime.date.today().strftime("%Y-%m")
        if role == "checker":
            pick = request.args.get("staff", "").strip() or None
            view = loans_view(load_ledger(), month, pick)
            return page("Loans", "<h2>Loans and advances — the clean view</h2>"
                        + loans_html(view, role, pick, staff_names()), u)
        link = users[u].get("staff_link", "").strip()
        match = [s for s in staff_names() if s.strip().lower() == link.lower()] if link else []
        if not match:
            return page("My loans", "<p>Your login is not linked to a staff name — ask the doctor "
                        "to relink it (adduser).</p>", u)
        view = loans_view(load_ledger(), month, match[0])
        return page("My loans", "<h2>My loans and advances</h2>" + loans_html(view, role), u)

    @app.route(URL_PREFIX + "/perks")
    def perks():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        rows = load_ledger()
        who = request.args.get("staff", "").strip()
        yr = request.args.get("year", "all").strip() or "all"
        years = perk_years(rows)
        names = sorted(staff_names())
        y_opts = "".join(f"<option{' selected' if yr==y else ''}>{y}</option>" for y in years)
        s_opts = "".join(f"<option{' selected' if who==n else ''}>{html_esc(n)}</option>"
                         for n in names)
        form = f"""<div class="card"><form method="get">
          <label>Staff</label>
          <select name="staff"><option value="">— everyone —</option>{s_opts}</select>
          <label>Year</label>
          <select name="year"><option value="all"{' selected' if yr=='all' else ''}>all years</option>{y_opts}</select>
          <button class="ok">Show</button></form></div>"""
        body = form
        if who:
            recs = perk_records(who, yr, rows)
            net = sum(r["amount"] for r in recs)
            life = sum(r["amount"] for r in perk_records(who, None, rows))
            rws = ""
            for r in recs:
                grey = " class='rev'" if r["amount"] < 0 or r.get("contra_of") else ""
                rws += (f"<tr{grey}><td>{r['date_from']}</td>"
                        f"<td>{html_esc(r.get('narration',''))}</td>"
                        f"<td>{'&minus;' if r['amount']<0 else ''}Rs {abs(r['amount'])}</td>"
                        f"<td><small>{html_esc(r['maker'])}&rarr;{html_esc(r.get('checker',''))}</small></td></tr>")
            tbl = (f"<table><tr><th>date</th><th>what</th><th>Rs</th><th>entered</th></tr>{rws}"
                   f"<tr><td colspan='2' style='text-align:right'><b>NET "
                   f"{'(' + yr + ')' if yr != 'all' else '(all years)'}</b></td>"
                   f"<td colspan='2'><b>Rs {net}</b></td></tr></table>"
                   if rws else "<p>No perks recorded for this staff in that period.</p>")
            body += (f"<div class='card'><b>{html_esc(who)}</b><br>"
                     f"<b>Lifetime perks: Rs {life}</b>"
                     + (f" · shown period Rs {net}" if yr != "all" else "")
                     + f"<br><small>A perk is a RECORD of a benefit paid, not money owed — "
                     f"it never enters the salary calculation.</small></div>"
                     f"<div class='card'>{tbl}</div>")
        else:
            tot = perk_totals(None if yr == "all" else yr, rows)
            if tot:
                rws = "".join(
                    f"<tr><td><a href='{URL_PREFIX}/perks?staff={html_esc(s)}&year={yr}'>"
                    f"{html_esc(s)}</a></td><td>Rs {v}</td></tr>"
                    for s, v in sorted(tot.items(), key=lambda kv: -kv[1]))
                body += (f"<div class='card'><b>Perks by staff "
                         f"{'(all years)' if yr=='all' else '(' + yr + ')'}</b>"
                         f"<table><tr><th>staff</th><th>net Rs</th></tr>{rws}"
                         f"<tr><td style='text-align:right'><b>TOTAL</b></td>"
                         f"<td><b>Rs {sum(tot.values())}</b></td></tr></table>"
                         f"<small>Tap a name for the detail.</small></div>")
            else:
                body += "<p>No perks recorded yet.</p>"
        return page("Perks", body, u)

    @app.route(URL_PREFIX + "/defer", methods=["POST"])
    def defer_route():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        try:
            record_defer(users, u, request.form["id"], request.form["month"],
                         request.form.get("reason", ""),
                         waive_penalty=("waive" in request.form))
        except (PermissionError, ValueError, KeyError) as e:
            return page("Advances", f"<p style='color:red'>{html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/advances'>back to Advances</a></p>", u)
        return redirect(URL_PREFIX + "/advances")

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
            # SL4: a quota advance (explicit against_month, not a loan, default
            # recover-fully instalment) recovers in its OWN lane at its month's
            # close — it never waits behind the loan waterfall, so its card
            # must not say it does.
            # D349: ask the ONE rule. This card used to compute its own copy
            # of the quota test, which omitted the schedule the close applies
            # first -- so a scheduled advance was announced as recovering in
            # full. It never did.
            _lane = advance_lane(a)
            if a["interest"]:
                ded = f"Rs {a['instalment']} + Rs {INTEREST_RS} interest"
            elif _lane == "schedule":
                _plan = " \u2192 ".join(f"{e['month']}: Rs {e['amount']}"
                                        for e in advance_schedule(a["issue"]))
                ded = ("by agreed schedule \u2014 " + _plan
                       + " (it does NOT wait behind the loan, and it does NOT "
                         "recover in full this month)")
            elif _lane == "quota":
                # It recovers at the FIRST close on or after its month — an
                # advance against an already-closed month (the Rs 10,000
                # July backfill) collects at the next close that runs.
                _rm = max(advance_against_month(a["issue"]),
                          datetime.date.today().strftime("%Y-%m"))
                ded = (f"Rs {a['instalment']} — recovers in full at the "
                       f"{_rm} close (quota lane, against "
                       f"{advance_against_month(a['issue'])} salary)")
            elif not st['summary']['bal_interest']:
                ded = f"Rs {a['instalment']}"
            else:
                ded = f"Rs {a['instalment']} (waiting for the loan to clear)"
            advbox += (f"<div class='card'><b>Open {'loan' if a['interest'] else 'advance'}"
                       f"</b> Rs {a['issue']['amount']} ({a['issue']['date_from']})"
                       f" — balance <b>Rs {a['balance']}</b> · monthly deduction "
                       + ded + "</div>")
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
              reception register. N = uninformed (Rs 50 attendance deduction on an absence; +1 mark on a
              60-min late). Keep Darpan's OUTSTATION dates as Y.<br>
              <form method="post" action="{URL_PREFIX}/salary/review">
              <input type="hidden" name="m" value="{month}">
              <input type="hidden" name="n" value="{len(review)}">
              <table><tr><th>staff</th><th>date</th><th>event</th><th>informed?</th></tr>
              {rws}</table>
              <button class="ok">Save flags</button>
              <small> — then press Re-run above so the deductions recompute.</small>
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
            steps.append(f"<div class='card'><b>3 · Big early-exit rulings</b> — none this month. 👍 <small>These are now ruled in the register: <a href='/register/salary/earlybig?ym={month}'>Early-big rulings</a>.</small></div>")

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
              Outstation days were duty, not absence — they reduce the excess-absence deduction.<br>
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
              <div class='card' style='border-color:#7f1d1d;margin:8px 0'>
              <b style='color:#f87171'>The APPROVE &amp; LOCK of this old computation is RETIRED.</b>
              The month locks at the register
              <a href='/register/salary?ym={month}' style='color:#ffd868'><b>Lock desk</b></a>
              on the new engine (D337).</div></div>""")

        # step 7 — waivers (D332 §2.8) + preview-month banner
        if table and not problems:
            _s = load_settings()
            _enf = attendance_enforced(month, _s)
            pv_note = ("" if _enf else
                "<p style='color:#c0392b'><b>PREVIEW MONTH</b> — attendance-policy "
                "deductions are shown struck-through but NOT applied to NET. They start "
                f"applying from the month set in <a href='{URL_PREFIX}/settings'>Settings</a> "
                "(D332 §2.7).</p>")
            lbl_att = {"marks": "Late-marks", "early": "Early-departure",
                       "earlybig": "Big early-exit", "uninformed": "Uninformed-absence",
                       "excess": "Excess-absence"}
            line_opts = ""
            for t in table:
                nm = t["name"]
                amap = {"marks": t["ded_marks"], "early": t["ded_early"],
                        "earlybig": t["earlybig_rs"], "uninformed": t["fine_uninf"],
                        "excess": t["fine_exc"]}
                for k, v in amap.items():
                    if v:
                        line_opts += (f"<option value='{html_esc(nm)}|att:{k}'>"
                                      f"{html_esc(nm)} — {lbl_att[k]} (Rs {v:g})</option>")
                for rr in rows_l:
                    if (rr["staff"] == nm and rr["status"] == "APPROVED"
                            and rr.get("closed_month") == month
                            and rr["category"] not in SALARY_EXCLUDED and rr["amount"] < 0):
                        lab = CATEGORIES.get(rr["category"], [rr["category"]])[0]
                        line_opts += (f"<option value='{html_esc(nm)}|led:{rr['id']}'>"
                                      f"{html_esc(nm)} — {html_esc(lab)} (Rs {-rr['amount']:g})</option>")
            staff_opts = "".join(f"<option>{html_esc(t['name'])}</option>" for t in table)
            wv_rows = ""
            for w in active_waivers(month):
                wv_rows += (f"<tr><td>{html_esc(w['scope'])}</td>"
                            f"<td>{html_esc(w['staff'] or 'ALL')}</td>"
                            f"<td>{html_esc(w['line_key'] or '—')}</td>"
                            f"<td>{html_esc(w['reason'])}</td>"
                            f"<td><small>{html_esc(w['by'])}</small></td><td>"
                            f"<form method='post' action='{URL_PREFIX}/salary/waive/contra' "
                            f"onsubmit=\"return confirm('Reverse this waiver?')\">"
                            f"<input type='hidden' name='m' value='{month}'>"
                            f"<input type='hidden' name='id' value='{w['id']}'>"
                            f"<input name='reason' placeholder='reason' required style='width:auto'>"
                            f"<button class='no'>Reverse</button></form></td></tr>")
            wv_tbl = ("<table><tr><th>scope</th><th>staff</th><th>line</th><th>reason</th>"
                      f"<th>by</th><th></th></tr>{wv_rows}</table>" if wv_rows
                      else "<p>No active waivers this month.</p>")
            if can_waive(u, _s):
                add_form = f"""<hr><b>Add a waiver</b>
                  <form method="post" action="{URL_PREFIX}/salary/waive">
                  <input type="hidden" name="m" value="{month}">
                  <label>Scope</label>
                  <select name="scope">
                    <option value="LINE">LINE — one deduction of one staff</option>
                    <option value="STAFF_MONTH">STAFF_MONTH — all of one staff's deductions</option>
                    <option value="ALL_MONTH">ALL_MONTH — everyone this month</option>
                  </select>
                  <label>Staff (LINE / STAFF_MONTH)</label>
                  <select name="staff"><option value="">—</option>{staff_opts}</select>
                  <label>Line (LINE scope only)</label>
                  <select name="line"><option value="">—</option>{line_opts}</select>
                  <label>Reason (required)</label>
                  <input name="reason" required placeholder="why this is waived">
                  <button class="ok" onclick="return confirm('Waive as chosen? It forgives the derived amount and shows in the table with your reason.')">Waive</button>
                  </form>"""
            else:
                add_form = ("<p><small>You are signed in but not an active waiver authority "
                            "(D332 §2.8): you can view waivers but not add one.</small></p>")
            steps.append(f"<div class='card'><b>7 · Waivers (D332)</b> "
                         f"<small style='color:#f87171'>(applies to the RETIRED computation "
                         f"only — hold-waivers for the new engine come with the lock desk)</small>"
                         f"{pv_note}{wv_tbl}{add_form}</div>")

        retired = (f"<div class='card' style='border-color:#7f1d1d'>"
                   f"<b style='color:#f87171'>&#9888;&#65039; THIS PAGE'S SALARY COMPUTATION IS RETIRED "
                   f"(pre-D336 rules — struck-through preview only).</b><br>"
                   f"The month is computed and LOCKED at the register's "
                   f"<a href='/register/salary?ym={month}' style='color:#ffd868'><b>Lock desk</b></a>, "
                   f"on the new policy engine.<br><small>Still LIVE on this page: "
                   f"<b>step 2</b> (informed flags — they feed the new engine's uninformed fines) and "
                   f"<b>step 5</b> (the ledger close — advance/loan recovery). The rest is kept for "
                   f"reference only.</small></div>")
        return page("Salary", msg_html + head + f"<h3>Salary {month}</h3>" + retired + "".join(steps), u)

    def _salary_table(table):
        h = ("<tr><th>staff</th><th>base</th><th>+inc</th><th>+OT</th><th>+ledger cr</th>"
             "<th>-marks</th><th>-early</th><th>-early-big</th><th>-att. ded.</th>"
             "<th>-ledger db</th><th>+waived</th><th>defer</th><th><b>NET Rs</b></th></tr>")
        b = ""
        for t in table:
            fines = t["fine_uninf"] + t["fine_exc"]
            pv = t.get("att_preview")
            _d = (lambda v: (f"<s>{v:g}</s>" if (pv and v) else f"{v:g}"))
            b += (f"<tr><td>{html_esc(t['name'])}"
                  + (f" <small>({t['outstation']} outstation)</small>" if t["outstation"] else "")
                  + f"</td><td>{t['base']:g}</td>"
                  f"<td class='amt-c'>{t['inc']:g}</td><td class='amt-c'>{t['ot_ok']:g}</td>"
                  f"<td class='amt-c'>{t['adj_cr']:g}</td>"
                  f"<td class='amt-d'>{_d(t['ded_marks'])}</td><td class='amt-d'>{_d(t['ded_early'])}</td>"
                  f"<td class='amt-d'>{_d(t['earlybig_rs'])}</td><td class='amt-d'>{_d(fines)}</td>"
                  f"<td class='amt-d'>{t['adj_db']:g}</td>"
                  f"<td class='amt-c'>{t.get('waived',0):g}</td>"
                  + ("<td class='amt-d'><b>%d</b></td>" % t["deferred_n"]
                     if t.get("deferred_n") else "<td>&mdash;</td>")
                  + f"<td><b>{t['net']}</b></td></tr>")
        return f"<table>{h}{b}</table>"

    # ---------------------------------------------------- D332 · SL5 routes --
    def _settings_body(s, u):
        cur = s.get("attendance_enforce_from") or "(not served — preview only)"
        auth = ", ".join(k for k, v in (s.get("waiver_authority") or {}).items() if v) or "(none)"
        return f"""<div class="card"><b>Policy settings (D332 §2.7 / F-150)</b>
          <p>Attendance enforcement starts from: <b>{html_esc(str(cur))}</b>.
          Until a month is set, every month is PREVIEW-ONLY — attendance-policy
          deductions are shown but never applied to NET.</p>
          <form method="post" action="{URL_PREFIX}/settings">
            <label>Notice-served month (attendance enforced from this month on)</label>
            <input type="month" name="attendance_enforce_from" style="width:auto">
            <button class="ok" onclick="return confirm('Set attendance-enforcement month? Deductions apply from that month on.')">Save</button>
            <label style="font-weight:normal"><input type="checkbox" name="clear_att" style="width:auto"> clear (back to preview-only)</label>
          </form>
          <p><small>Active waiver authorities: {html_esc(auth)}. To activate Dr Bhawna,
          set waiver_authority.bhawna=true in ledger_settings.json on the box —
          deliberately not a one-tap web toggle (D332 §2.8).</small></p></div>"""

    @app.route(URL_PREFIX + "/settings", methods=["GET", "POST"])
    def settings_page():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        s = load_settings()
        if request.method == "POST":
            if not can_waive(u, s):
                return page("Settings", "<p style='color:red'>only an active waiver "
                            "authority may change policy settings</p>" + _settings_body(s, u), u)
            patch = {}
            d = request.form.get("attendance_enforce_from", "").strip()
            if d:
                try:
                    datetime.date.fromisoformat(d + "-01")
                except ValueError:
                    return page("Settings", "<p style='color:red'>month must look like 2026-09</p>"
                                + _settings_body(s, u), u)
                patch["attendance_enforce_from"] = d
            elif "clear_att" in request.form:
                patch["attendance_enforce_from"] = None
            s = save_settings(patch, u)
            return page("Settings", "<p style='color:green'>saved</p>" + _settings_body(s, u), u)
        return page("Settings", _settings_body(s, u), u)

    @app.route(URL_PREFIX + "/salary/waive", methods=["POST"])
    def salary_waive():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        if salary_locked(m):
            return page("Salary", "<p style='color:red'>month is locked — waive before "
                        "approving; a locked month is corrected next month</p>", u)
        scope = request.form.get("scope", "").strip()
        reason = request.form.get("reason", "")
        staff = request.form.get("staff", "").strip()
        line_key = ""
        if scope == "LINE":
            raw = request.form.get("line", "").strip()
            if "|" in raw:
                staff, line_key = raw.split("|", 1)
        elif scope == "ALL_MONTH":
            staff = ""
        try:
            make_waiver(users, u, m, scope, reason, staff=staff, line_key=line_key)
        except (PermissionError, ValueError) as e:
            return page("Salary", f"<p style='color:red'>{html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back to Salary {m}</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg=Waiver added.")

    @app.route(URL_PREFIX + "/salary/waive/contra", methods=["POST"])
    def salary_waive_contra():
        u, users = _ck_only()
        if not u: return redirect(URL_PREFIX + "/login")
        m = request.form["m"]
        if salary_locked(m):
            return page("Salary", "<p style='color:red'>month is locked</p>", u)
        try:
            waiver_contra(users, u, m, request.form["id"], request.form.get("reason", ""))
        except (PermissionError, ValueError) as e:
            return page("Salary", f"<p style='color:red'>{html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back to Salary {m}</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg=Waiver reversed.")

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
    ck(r2["amount"] == -45, "uniform 3d=-45 (D336 Rs 15/day, was the wrong Rs 20)")
    # S200: COVER_DUTY — a credit, narration compulsory, maker_full may enter it
    rc = make_entry(users, "mfull", "Alpha", "COVER_DUTY", "2026-08-04","2026-08-07",4,
                    "0","covered Beta's evening duty")
    ck(rc["amount"] == 800 and rc["status"] == "PENDING", "cover 4d=+800 pending")
    try:
        make_entry(users, "doc", "Alpha", "COVER_DUTY", "2026-08-04","2026-08-04",1,"0","")
        ck(False, "cover duty without narration must fail")
    except ValueError: ck(True, "cover duty narration (who was covered) required")
    # S200: the fine day-rates FOLLOW the salary-policy settings file
    import tempfile as _tf
    global POLICY_SETTINGS
    _oldps = POLICY_SETTINGS
    _psf = os.path.join(_tf.mkdtemp(), "sp.json")
    with open(_psf, "w") as _f:
        json.dump({"dress_rs": 25, "icard_rs": 30}, _f)
    POLICY_SETTINGS = _psf
    ck(live_rate("FINE_UNIFORM") == 25 and live_rate("FINE_ICARD") == 30,
       "fine rates follow the policy settings")
    ck(live_rate("NIGHT_DUTY") == 200 and live_rate("COVER_DUTY") == 200,
       "duty rates unaffected by the settings link")
    POLICY_SETTINGS = os.path.join(_tf.mkdtemp(), "absent.json")
    ck(live_rate("FINE_UNIFORM") == 15, "missing settings file -> shipped default")
    POLICY_SETTINGS = _oldps
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
    ck(c["amount"] == 45 and c["status"] == "APPROVED" and c["contra_of"] == r2["id"], "doctor contra direct +45 (rate now Rs 15)")
    c2 = make_contra(users, "mfull", rr["id"], "card was found")
    ck(c2["status"] == "PENDING", "maker contra pends")
    decide(users, "doc2", c2["id"], True)
    try:
        make_contra(users, "doc", r3["id"], "x"); ck(False, "contra of rejected must fail")
    except ValueError: ck(True, "contra only approved rows")
    # F-153: a contra inherits the original's against_month, so reversed money
    # nets that month's quota instead of leaking to the contra's entry month.
    _f153a = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE", "2026-08-09","2026-08-09",0,"5000","", instalment="", against_month="2026-11")
    ck(_f153a["against_month"] == "2026-11", "F-153: advance carries its explicit against_month")
    _f153c = make_contra(users, "doc", _f153a["id"], "reversed - attributed to wrong month")
    ck(_f153c["against_month"] == "2026-11", "F-153: the contra inherits the original's against_month")
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
    # Alpha: credits = night 400 + contra 45 = 445; debits = uniform 45 + adhoc 500
    # + instalment 3000 = 3545; net -3100 (contra and original cancel in net).
    # (The pending cover-duty +800 is correctly absent — only APPROVED rows count.)
    with open(out, encoding="utf-8") as f: txt = f.read()
    import re as _re
    m = _re.search(r"^Alpha,(\d+),(\d+),(-?\d+),(\d+)", txt, _re.M)
    ck(m is not None, "Alpha summary row present")
    cred, deb, net, ld = map(int, m.groups())
    ck(cred == 445 and deb == 3545 and net == -3100 and ld == 0,
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
    # D332/SL5: this legacy block asserts the ENFORCED path — set the
    # notice-served date so attendance deductions apply (the preview path
    # is covered by the new SL5 block below).
    save_settings({"attendance_enforce_from": YM}, "doc")
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

    # ================= D331 (S190): ceiling · special · application · month =
    # Self-contained: writes its own staff CSV (with base_salary) and its own
    # advance_pct.json, restores the CSV after. Delta-disciplined throughout.
    _csv_orig = open(STAFF_CSV, encoding="utf-8").read()
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "active", "base_salary"])
        w.writerow([1, "Alpha", "Y", 10000])
        w.writerow([2, "Beta", "Y", 20000])
        w.writerow([3, "Gamma", "Y", 8890])
    with open(_p("advance_pct.json"), "w", encoding="utf-8") as f:
        json.dump({"Beta": 75}, f)
    ck(advance_ceiling("Alpha") == 5000, "D331 ceiling: default 50% of 10000 = 5000")
    ck(advance_ceiling("Beta") == 15000, "D331 ceiling: pct-file 75% of 20000 = 15000")
    ck(advance_ceiling("Gamma") == 4400,
       "D331 ceiling floors to the last Rs 100 (50% of 8890 = 4445 -> 4400)")
    ck(advance_ceiling("Delta") == 0, "D331 ceiling: no base on file -> 0 (gate off)")

    # within the ceiling: nothing changes, month defaults to the entry month
    r31 = make_entry(users, "mfull", "Alpha", "ADVANCE_ISSUE",
                     "2027-03-05", "2027-03-05", 0, "2000", "")
    ck(r31["status"] == "PENDING" and r31["against_month"] == "2027-03"
       and not r31["special"],
       "D331: within-ceiling advance unchanged; month defaults to entry month")
    ck(advance_month_taken("Alpha", "2027-03") == 2000,
       "D331: PENDING counts against the month (quota spoken for)")

    # over the ceiling: refused unless SPECIAL, message carries the figures
    try:
        make_entry(users, "mfull", "Alpha", "ADVANCE_ISSUE",
                   "2027-03-06", "2027-03-06", 0, "4000", "")
        ck(False, "D331: over-ceiling without special must refuse")
    except ValueError as e:
        ck("5000" in str(e) and "2000" in str(e) and "SPECIAL" in str(e),
           "D331: the refusal names taken, ceiling and the way through")

    # special: allowed over the ceiling, but NEVER direct — even for a checker
    r32 = make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE",
                     "2027-03-06", "2027-03-06", 0, "4000", "",
                     special=True)
    ck(r32["special"] and r32["status"] == "PENDING" and not r32["direct"],
       "D331: a checker's own SPECIAL advance still goes PENDING (gate unskippable)")

    # the application gate at approve
    try:
        decide(users, "doc2", r32["id"], True)
        ck(False, "D331: approving a special advance without the application must refuse")
    except ValueError as e:
        ck("application" in str(e), "D331: approve refused until the application is on file")
    try:
        save_application(r31["id"], b"%PDF-1.4 x", "mfull")
        ck(False, "D331: an ordinary advance takes no application")
    except ValueError:
        ck(True, "D331: save_application refuses a non-special row")
    _sha = save_application(r32["id"], b"%PDF-1.4 signed application", "mfull")
    _r32b = {r["id"]: r for r in load_ledger()}[r32["id"]]
    ck(application_on_file(r32["id"]) and _r32b.get("application_sha") == _sha,
       "D331: the application stores and its sha lands in the row")
    decide(users, "doc2", r32["id"], True)
    _r32c = {r["id"]: r for r in load_ledger()}[r32["id"]]
    ck(_r32c["status"] == "APPROVED",
       "D331: with the application on file the approval goes through")
    ck(decide is not None and _r32c["checker"] == "doc2", "D331: checker recorded")

    # rejection never needs an application
    r33 = make_entry(users, "doc", "Beta", "ADVANCE_ISSUE",
                     "2027-03-07", "2027-03-07", 0, "16000", "", special=True)
    decide(users, "doc2", r33["id"], False)
    ck({r["id"]: r for r in load_ledger()}[r33["id"]]["status"] == "REJECTED",
       "D331: rejection needs no application")
    ck(advance_month_taken("Beta", "2027-03") == 0,
       "D331: a REJECTED advance releases its quota")

    # month attribution: a future month's quota, and the close waits for it
    r34 = make_entry(users, "doc", "Beta", "ADVANCE_ISSUE",
                     "2027-03-08", "2027-03-08", 0, "5000", "",
                     against_month="2027-04")
    ck(r34["status"] == "APPROVED" and r34["against_month"] == "2027-04",
       "D331: attribution to a future month accepted (within that month's ceiling)")
    ck(advance_month_taken("Beta", "2027-04") == 5000
       and advance_month_taken("Beta", "2027-03") == 0,
       "D331: it counts against ITS month, not the entry's")
    try:
        make_entry(users, "doc", "Beta", "ADVANCE_ISSUE",
                   "2027-03-09", "2027-03-09", 0, "1000", "",
                   against_month="2027-02")
        ck(False, "D331: a PAST against-month must refuse")
    except ValueError:
        ck(True, "D331: attribution to a past month refused (quota already spent)")

    close_month(users, "doc", "2027-03")
    _rows_a = load_ledger()
    ck(not any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == r34["id"]
               for r in _rows_a),
       "D331: the 2027-03 close does NOT recover the April-attributed advance")
    ck(any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == r32["id"]
           for r in _rows_a),
       "D331: the same close DOES recover the March special advance (waterfall intact)")
    close_month(users, "doc", "2027-04")
    _rows_b = load_ledger()
    ck(any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == r34["id"]
           for r in _rows_b),
       "D331: the 2027-04 close recovers it in ITS month")

    # no base on file: the gate stands down VISIBLY, never freezes the clinic
    r35 = make_entry(users, "doc", "Delta", "ADVANCE_ISSUE",
                     "2027-05-05", "2027-05-05", 0, "50000", "")
    ck(r35["status"] == "APPROVED" and not r35["special"],
       "D331: base 0 -> gate disabled (the entry page says so inline)")

    # SL3 (owner ruling): the quota is blind to pre-D331 rows and to loans
    _pre = advance_month_taken("Gamma", "2027-06")
    append_ledger({"id": secrets.token_hex(6), "ts_entry": now(), "maker": "doc",
                   "staff": "Gamma", "category": "ADVANCE_ISSUE",
                   "date_from": "2027-06-03", "date_to": "2027-06-03", "days": 0,
                   "amount": 999999, "instalment": 999999, "narration": "legacy shape",
                   "self_flag": False, "direct": True, "status": "APPROVED",
                   "checker": "doc", "ts_decision": now(), "contra_of": "",
                   "closed_month": "", "interest": False})
    ck(advance_month_taken("Gamma", "2027-06") == _pre,
       "SL3: a pre-D331 (no against_month) row never eats the quota — the "
       "S155 migration history stays out of the month")
    _pre2 = advance_month_taken("Gamma", "2027-07")
    rGl = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE",
                     "2027-07-02", "2027-07-02", 0, "9000", "loan not quota",
                     instalment="2000", interest=True)
    ck(advance_month_taken("Gamma", "2027-07") == _pre2,
       "SL3: an interest-bearing loan never consumes the ordinary quota")

    # ================= SL4 (owner ruling "A", S190): the quota lane =========
    # Gamma now carries an open Rs 9000 interest loan AND a legacy Rs 999999
    # advance — the exact live shape (Darpan: Rs 3.59 lakh loan book beside
    # this month's quota advances). Four proofs:
    #   1. a quota advance recovers IN FULL at its own month's close even
    #      while the loan is open (never "waiting for the loan to clear");
    #   2. the loan's waterfall still recovers its own interest + principal
    #      in the SAME close (the two lanes coexist);
    #   3. a deliberately PARTIAL instalment opts back into the waterfall
    #      and therefore waits behind the loan;
    #   4. a loan-skip month pauses ONLY the waterfall — the quota lane
    #      still collects, because attribution already named the month.
    rQ1 = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE",
                     "2027-07-03", "2027-07-03", 0, "3000", "quota advance")
    close_month(users, "doc", "2027-07")
    _rows_c = load_ledger()
    _q1 = [r for r in _rows_c if r["category"] == "ADVANCE_INSTALMENT"
           and r["contra_of"] == rQ1["id"] and r["closed_month"] == "2027-07"]
    ck(len(_q1) == 1 and _q1[0]["amount"] == -3000
       and not any(a["issue"]["id"] == rQ1["id"] for a in open_advances()),
       "SL4: a quota advance recovers IN FULL at its month's close while the "
       "loan is still open (own lane, not the waterfall queue)")
    ck(any(r["category"] == "LOAN_INTEREST" and r["contra_of"] == rGl["id"]
           and r["closed_month"] == "2027-07" and r["amount"] == -1000
           for r in _rows_c)
       and any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == rGl["id"]
               and r["closed_month"] == "2027-07" and r["amount"] == -1000
               for r in _rows_c),
       "SL4: the SAME close still runs the waterfall — the loan pays its "
       "Rs 1000 interest + Rs 1000 principal beside the quota lane")
    rP1 = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE",
                     "2027-08-02", "2027-08-02", 0, "3000", "partial by choice",
                     instalment="1000")
    close_month(users, "doc", "2027-08")
    ck(not any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == rP1["id"]
               for r in load_ledger())
       and any(a["issue"]["id"] == rP1["id"] and a["balance"] == 3000
               for a in open_advances()),
       "SL4: a deliberately PARTIAL instalment opts back into the waterfall "
       "and waits behind the loan (the promise is only for recover-fully rows)")
    record_skip(users, "doc", rGl["id"], "2027-09")
    rQ2 = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE",
                     "2027-09-02", "2027-09-02", 0, "2000", "quota in a skip month")
    close_month(users, "doc", "2027-09")
    _rows_d = load_ledger()
    ck(any(r["category"] == "LOAN_CAPITALISE" and r["contra_of"] == rGl["id"]
           and r["closed_month"] == "2027-09" for r in _rows_d)
       and not any(r["category"] in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")
                   and r["contra_of"] in (rGl["id"], rP1["id"])
                   and r["closed_month"] == "2027-09" for r in _rows_d)
       and any(r["category"] == "ADVANCE_INSTALMENT" and r["contra_of"] == rQ2["id"]
               and r["closed_month"] == "2027-09" and r["amount"] == -2000
               for r in _rows_d),
       "SL4: a skip month pauses ONLY the waterfall (Rs 1000 capitalises, "
       "nothing recovers there) — the quota lane still collects its Rs 2000")

    with open(STAFF_CSV, "w", encoding="utf-8") as f:
        f.write(_csv_orig)

    # ============== D332 · SL5 (S192): preview gate, waivers, wording ========
    _t5 = tempfile.mkdtemp(); LEDGER_DIR = _t5
    _att5 = tempfile.mkdtemp(); ATT_BASE = _att5
    save_users(users); users = load_users()
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id","name","active","base_salary"])
        w.writerow([1,"Alpha","Y",9000]); w.writerow([2,"Beta","Y",12000])
    YM5 = "2026-09"
    _heads5 = ["Name","Group","Present","Absent","Late marks","Late days",
        "Late minutes","Grace days used",">=60min days","Early-dep minutes",
        "No-out-punch days","Early-big days","Deduction half-days",
        "Ded: marks Rs","Ded: early-dep Rs","Fine: uninformed Rs",
        "Fine: excess-absent Rs","OT cand. minutes","OT candidate Rs",
        "Incentive","Incentive Rs","Net Rs","Months over cap (yr)",
        "Habitual flag","Absent dates"]
    def _r5(name, **kw):
        d = {h: 0 for h in _heads5}
        d.update({"Name": name, "Group":"A","Incentive":"-","Habitual flag":"","Absent dates":""})
        d.update(kw); return d
    with open(os.path.join(ATT_BASE, f"salary_inputs_{YM5}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_heads5); w.writeheader()
        w.writerow(_r5("Alpha", **{"Absent":0, "Ded: marks Rs":500, "Fine: excess-absent Rs":300}))
        w.writerow(_r5("Beta"))
    _adh = make_entry(users, "doc", "Alpha", "FINE_ADHOC", f"{YM5}-05", f"{YM5}-05", 0, "250", "broke a splint")
    close_month(users, "doc", YM5)
    # settings defaults
    _s0 = load_settings()
    ck(_s0["attendance_enforce_from"] is None
       and _s0["waiver_authority"] == {"manoj": True, "bhawna": False},
       "SL5: settings default = preview-only; Manoj active / Bhawna inactive")
    ck(can_waive("manoj") and not can_waive("bhawna") and not can_waive("doc"),
       "SL5: waiver authority seeded Manoj-only by default")
    # PREVIEW gate: attendance deductions shown but not applied
    tP = {t["name"]: t for t in compute_salary(YM5)[0]}
    ck(tP["Alpha"]["att_preview"] is True, "SL5: month is preview until notice served")
    ck(tP["Alpha"]["net"] == 8750,
       f"SL5 preview: att deductions not applied, ledger debit is (got {tP['Alpha']['net']})")
    ck(tP["Alpha"]["waived"] == 0 and tP["Beta"]["net"] == 12000, "SL5 preview: Beta clean")
    # wording (F-151)
    htmP = build_salary_html(YM5, compute_salary(YM5)[0], locked=False)
    ck("att. ded." in htmP and "Uninformed-absence fine" not in htmP
       and "Excess-absence fine" not in htmP,
       "SL5 (F-151): salary HTML says 'attendance deduction', not 'fine'")
    ck("PREVIEW &mdash; shown, not applied" in htmP,
       "SL5: preview breakdown states deductions are shown-not-applied")
    # enforce the month
    save_settings({"attendance_enforce_from": YM5}, "doc")
    tE = {t["name"]: t for t in compute_salary(YM5)[0]}
    ck(tE["Alpha"]["att_preview"] is False, "SL5: enforced once the notice month is set")
    ck(tE["Alpha"]["net"] == 7950,
       f"SL5 enforced: base 9000 less 500, less 300, less 250 = net 7950 (got {tE['Alpha']['net']})")
    # waiver authority + validation
    try:
        make_waiver(users, "doc", YM5, "ALL_MONTH", "x"); ck(False, "non-authority must fail")
    except PermissionError: ck(True, "SL5: a non-authority checker cannot waive")
    save_settings({"waiver_authority": {"doc": True, "bhawna": False}}, "doc")
    try:
        make_waiver(users, "doc", YM5, "LINE", "", staff="Alpha", line_key="att:marks")
        ck(False, "empty reason must fail")
    except ValueError: ck(True, "SL5: a waiver needs a written reason (no escape hatch)")
    try:
        make_waiver(users, "doc", YM5, "NONSENSE", "r", staff="Alpha")
        ck(False, "bad scope must fail")
    except ValueError: ck(True, "SL5: scope must be LINE / STAFF_MONTH / ALL_MONTH")
    # LINE waiver forgives one attendance line
    wL = make_waiver(users, "doc", YM5, "LINE", "genuine reason", staff="Alpha", line_key="att:marks")
    tW = {t["name"]: t for t in compute_salary(YM5)[0]}
    ck(tW["Alpha"]["waived"] == 500 and tW["Alpha"]["net"] == 8450,
       f"SL5 LINE waiver: marks 500 forgiven -> 8450 (got {tW['Alpha']['net']})")
    waiver_contra(users, "doc", YM5, wL["id"], "undo")
    ck(not active_waivers(YM5), "SL5: waiver reversed by contra (append-only)")
    ck({t['name']: t for t in compute_salary(YM5)[0]}["Alpha"]["net"] == 7950,
       "SL5: NET restored after the reversal")
    # STAFF_MONTH forgives all of one staff's deductions (att + ledger)
    wS = make_waiver(users, "doc", YM5, "STAFF_MONTH", "hardship", staff="Alpha")
    tS = {t["name"]: t for t in compute_salary(YM5)[0]}
    ck(tS["Alpha"]["net"] == 9000 and tS["Alpha"]["waived"] == 1050,
       f"SL5 STAFF_MONTH: marks+excess+ledger forgiven -> 9000 (got {tS['Alpha']['net']})")
    waiver_contra(users, "doc", YM5, wS["id"], "undo")
    # LINE waiver on a LEDGER debit (owner: any deduction line)
    wD = make_waiver(users, "doc", YM5, "LINE", "clinic covered it", staff="Alpha",
                     line_key="led:" + _adh["id"])
    ck({t['name']: t for t in compute_salary(YM5)[0]}["Alpha"]["net"] == 8200,
       "SL5: a LINE waiver can forgive a ledger debit (250) -> 8200")
    waiver_contra(users, "doc", YM5, wD["id"], "undo")
    # ALL_MONTH forgives every staff
    wA = make_waiver(users, "doc", YM5, "ALL_MONTH", "festival goodwill")
    tA = {t["name"]: t for t in compute_salary(YM5)[0]}
    ck(tA["Alpha"]["net"] == 9000 and tA["Beta"]["net"] == 12000,
       "SL5 ALL_MONTH: everyone's deductions forgiven")
    # the approval token covers waivers: a stale token refuses
    _tab0, _tok0, _ = compute_salary(YM5)
    waiver_contra(users, "doc", YM5, wA["id"], "undo")
    try:
        approve_salary(users, "doc", YM5, _tok0); ck(False, "stale token must refuse")
    except ValueError: ck(True, "SL5: the approval token covers waivers + settings")
    # route smoke: settings + waive endpoints
    _app5 = create_app(); _app5.testing = True; _cl5 = _app5.test_client()
    _cl5.post(URL_PREFIX + "/login", data={"u": "doc", "p": "pw"})
    ck(_cl5.get(URL_PREFIX + "/settings").status_code == 200, "SL5: settings page loads for a checker")
    _rw = _cl5.post(URL_PREFIX + "/salary/waive",
                    data={"m": YM5, "scope": "ALL_MONTH", "reason": "route test"})
    ck(_rw.status_code in (301, 302, 303) and len(active_waivers(YM5)) == 1,
       "SL5: /salary/waive adds a waiver")
    _wid = active_waivers(YM5)[0]["id"]
    _cl5.post(URL_PREFIX + "/salary/waive/contra", data={"m": YM5, "id": _wid, "reason": "route undo"})
    ck(not active_waivers(YM5), "SL5: /salary/waive/contra reverses it")

    # ============ D332 · SL6 (S192): schedule lane, DEFER, capacity =========
    _t6 = tempfile.mkdtemp(); LEDGER_DIR = _t6
    _att6 = tempfile.mkdtemp(); ATT_BASE = _att6
    save_users(users); users = load_users()
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id","name","active","base_salary"])
        w.writerow([1,"Darp","Y",20000]); w.writerow([2,"Tight","Y",6000])
        w.writerow([3,"Nobase","Y",""])
    # --- the schedule parses, and refuses a silent gap ---------------------
    _sc = parse_schedule("2027-04:8000, 2027-05:4000, 2027-06:4000, 2027-07:4000", 20000)
    ck(len(_sc) == 4 and _sc[0] == {"month": "2027-04", "amount": 8000},
       "SL6: an uneven schedule parses in order")
    try:
        parse_schedule("2027-04:8000, 2027-05:4000", 20000); ck(False, "gap must fail")
    except ValueError: ck(True, "SL6: a schedule that does not add to the advance is refused")
    try:
        parse_schedule("2027-04-8000", 8000); ck(False, "bad form must fail")
    except ValueError: ck(True, "SL6: a malformed schedule step is refused")
    # --- the owner's 17-Aug shape: Rs 20,000 as 8,000 + 4,000 x 3 ----------
    A = make_entry(users, "doc", "Darp", "ADVANCE_ISSUE", "2027-04-01", "2027-04-01", 0,
                   "20000", "the D332 worked example", against_month="2027-04",
                   special=True, schedule="2027-04:8000, 2027-05:4000, 2027-06:4000, 2027-07:4000")
    save_application(A["id"], b"%PDF-1.4 signed", "doc")
    decide(users, "doc", A["id"], True)
    ck(len(advance_schedule(A)) == 4, "SL6: the schedule is stored on the advance row")
    # ---- D349 (S202): ONE lane rule, and the display must obey it ----------
    _mk = lambda iss, interest, inst: {"issue": iss, "interest": interest,
                                       "instalment": inst, "balance": 0}
    ck(advance_lane(_mk(A, False, 20000)) == "schedule",
       "D349: a scheduled advance is named to the SCHEDULE lane")
    ck(advance_lane(_mk({"amount": 5000, "against_month": "2027-08",
                         "schedule": []}, False, 5000)) == "quota",
       "D349: an unscheduled recover-fully advance is named to the QUOTA lane")
    ck(advance_lane(_mk({"amount": 5000, "against_month": "2027-08",
                         "schedule": []}, True, 1000)) == "loan",
       "D349: an interest-bearing advance is named to the LOAN lane")
    ck(advance_lane(_mk({"amount": 5000, "against_month": "",
                         "schedule": []}, False, 1000)) == "waterfall",
       "D349: a plain partial-instalment advance is named to the WATERFALL")
    _pg349 = _cl5.get(URL_PREFIX + "/statement?staff=Darp").data.decode()
    ck("recovers in full" not in _pg349,
       "D349: the statement NEVER says a scheduled advance recovers in full "
       "(the exact sentence that was wrong about Darpan's Rs 20,000)")
    ck("2027-04: Rs 8000" in _pg349 and "2027-05: Rs 4000" in _pg349,
       "D349: the statement shows the agreed schedule instead")
    ck(advance_lane(_mk(A, False, 20000)) == "schedule"
       and advance_recovered(A["id"], load_ledger()) in (0, 8000, 12000),
       "D349: the lane the display names is the lane the close actually used")
    ck(schedule_due_cum(A, "2027-04") == 8000 and schedule_due_cum(A, "2027-05") == 12000,
       "SL6: due-by-month is cumulative over the schedule")
    close_month(users, "doc", "2027-04")
    _r6 = load_ledger()
    ck(advance_recovered(A["id"], _r6) == 8000,
       f"SL6 Aug-shape: the schedule lane collects 8000, not the whole 20000 "
       f"(got {advance_recovered(A['id'], _r6)})")
    close_month(users, "doc", "2027-05")
    ck(advance_recovered(A["id"]) == 12000, "SL6: the second step collects 4000")
    # --- DEFER: the whole step shifts, the tail extends --------------------
    try:
        record_defer(users, "doc", A["id"], "2027-06", ""); ck(False, "no reason must fail")
    except ValueError: ck(True, "SL6: a defer needs a written reason")
    D1 = record_defer(users, "doc", A["id"], "2027-06", "cash tight this month")
    ck(D1["category"] == "ADVANCE_DEFER" and D1["amount"] == 0
       and not D1["defer_penalty"], "SL6: an interest-free defer is penalty-free")
    try:
        record_defer(users, "doc", A["id"], "2027-06", "again"); ck(False, "double defer must fail")
    except ValueError: ck(True, "SL6: the same month cannot be deferred twice")
    close_month(users, "doc", "2027-06")
    ck(advance_recovered(A["id"]) == 12000, "SL6: a deferred month collects nothing")
    ck(not [r for r in load_ledger() if r["category"] == "LOAN_CAPITALISE"],
       "SL6: deferring an interest-free advance capitalises nothing")
    close_month(users, "doc", "2027-07")
    ck(advance_recovered(A["id"]) == 16000, "SL6: collection resumes the month after a defer")
    close_month(users, "doc", "2027-08")
    ck(advance_recovered(A["id"]) == 20000,
       "SL6: the defer EXTENDED the schedule — the final step still collects")
    ck(not [a for a in open_advances() if a["issue"]["id"] == A["id"]],
       "SL6: the advance closes out exactly, nothing left owing")
    _st = schedule_state(A)
    ck(_st["recovered"] == 20000 and _st["balance"] == 0 and _st["next_month"] is None,
       "SL6: schedule_state reports it complete")
    # --- the loan defer penalty: free twice, then waivable ------------------
    L = make_entry(users, "doc", "Nobase", "ADVANCE_ISSUE", "2027-04-02", "2027-04-02", 0,
                   "50000", "loan", instalment="5000", interest=True)
    ck(L["status"] == "APPROVED", "SL6: checker loan is direct")
    d1 = record_defer(users, "doc", L["id"], "2027-09", "one")
    d2 = record_defer(users, "doc", L["id"], "2027-10", "two")
    ck(not d1["defer_penalty"] and not d2["defer_penalty"],
       "SL6: the first two defers of the FY are free, loan or not")
    d3 = record_defer(users, "doc", L["id"], "2027-11", "three")
    ck(d3["defer_penalty"] and not d3["penalty_waived"],
       "SL6: the 3rd defer of the FY carries the penalty on an interest-bearing loan")
    close_month(users, "doc", "2027-11")
    ck([r for r in load_ledger() if r["category"] == "LOAN_CAPITALISE"
        and r["contra_of"] == L["id"] and r["amount"] == INTEREST_RS],
       "SL6: the unwaived 3rd-defer penalty capitalises Rs 1000")
    d4 = record_defer(users, "doc", L["id"], "2027-12", "four", waive_penalty=True)
    ck(d4["defer_penalty"] and d4["penalty_waived"], "SL6: the penalty can be waived at the tap")
    _cap_before = len([r for r in load_ledger() if r["category"] == "LOAN_CAPITALISE"])
    close_month(users, "doc", "2027-12")
    ck(len([r for r in load_ledger() if r["category"] == "LOAN_CAPITALISE"]) == _cap_before,
       "SL6: a WAIVED penalty capitalises nothing")
    # --- capacity (F-147): nothing recovers that the salary cannot bear -----
    ck(recovery_capacity("Nobase", "2028-01") is None,
       "SL6: no base salary on file disables the capacity gate (fail-open, never frozen)")
    B = make_entry(users, "doc", "Tight", "ADVANCE_ISSUE", "2028-01-01", "2028-01-01", 0,
                   "9000", "more than the month can bear", against_month="2028-01",
                   special=True, schedule="2028-01:9000")
    save_application(B["id"], b"%PDF-1.4 signed", "doc")
    decide(users, "doc", B["id"], True)
    ck(recovery_capacity("Tight", "2028-01") == 6000,
       f"SL6: capacity = base 6000 (got {recovery_capacity('Tight', '2028-01')})")
    close_month(users, "doc", "2028-01")
    ck(advance_recovered(B["id"]) == 6000,
       f"SL6 F-147: recovery capped at what the salary bears, not the scheduled 9000 "
       f"(got {advance_recovered(B['id'])})")
    ck([r for r in load_ledger() if r["category"] == "CAPACITY_HOLD"
        and r["contra_of"] == B["id"]],
       "SL6: the uncollected remainder is HELD out loud, never silently dropped")
    ck(any(a["issue"]["id"] == B["id"] and a["balance"] == 3000 for a in open_advances()),
       "SL6: the held Rs 3000 stays owed and collects later")
    # --- the surfaces ------------------------------------------------------
    _app6 = create_app(); _app6.testing = True; _cl6 = _app6.test_client()
    _cl6.post(URL_PREFIX + "/login", data={"u": "doc", "p": "pw"})
    _pg6 = _cl6.get(URL_PREFIX + "/advances").data.decode()
    ck("schedule:" in _pg6 and "Defer this month" in _pg6,
       "SL6: the Advances card shows the schedule and offers DEFER")
    ck("DEFERRED:" in _pg6, "SL6: deferred months show in a loud red band")
    C = make_entry(users, "doc", "Nobase", "ADVANCE_ISSUE", "2028-02-01", "2028-02-01", 0,
                   "3000", "route test", instalment="1000")
    _rd = _cl6.post(URL_PREFIX + "/defer",
                    data={"id": C["id"], "month": "2028-03", "reason": "route defer"})
    ck(_rd.status_code in (301, 302, 303) and is_deferred(C["id"], "2028-03"),
       "SL6: the /defer route records the deferral")

    # ================= D332 · SL7 (S192): the Perks view (F-149) ============
    _t7 = tempfile.mkdtemp(); LEDGER_DIR = _t7
    save_users(users); users = load_users()
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id","name","active","base_salary"])
        w.writerow([1,"Alpha","Y",9000]); w.writerow([2,"Beta","Y",12000])
    P1 = make_entry(users, "doc", "Alpha", "PERK", "2026-05-10", "2026-05-10", 0,
                    "13000", "School fee - Adarsh")
    P2 = make_entry(users, "doc", "Alpha", "PERK", "2027-01-04", "2027-01-04", 0,
                    "2500", "Spectacles")
    P3 = make_entry(users, "doc", "Beta", "PERK", "2026-06-01", "2026-06-01", 0,
                    "4000", "Cycle repair")
    ck(P1["amount"] == 13000 and P1["status"] == "APPROVED",
       "SL7: a perk is a positive record, checker-entered")
    ck(len(perk_records("Alpha")) == 2 and len(perk_records("Beta")) == 1,
       "SL7: perks are readable per staff — the F-149 gap closed")
    ck(perk_records("Alpha")[0]["date_from"] == "2027-01-04",
       "SL7: newest first")
    ck([r["amount"] for r in perk_records("Alpha", "2026")] == [13000],
       "SL7: the year filter narrows to that year only")
    ck(perk_totals() == {"Alpha": 15500, "Beta": 4000},
       f"SL7: lifetime totals per staff (got {perk_totals()})")
    ck(perk_totals("2027") == {"Alpha": 2500}, "SL7: totals respect the year filter")
    ck(perk_years() == ["2027", "2026"], "SL7: the year list is derived from the data")
    # a reversed perk cancels itself out, with no special case
    make_contra(users, "doc", P2["id"], "entered twice")
    ck(perk_totals()["Alpha"] == 13000,
       f"SL7: a contra'd perk nets to zero (got {perk_totals()['Alpha']})")
    ck(len(perk_records("Alpha")) == 3,
       "SL7: both the perk and its contra stay visible — append-only, nothing erased")
    # a perk never touches salary money
    close_month(users, "doc", "2026-05")
    _adj = month_adjustments(load_ledger(), "2026-05")
    ck("Alpha" not in _adj or _adj["Alpha"]["credit"] == 0,
       "SL7: a perk is excluded from salary — a record, not money owed")
    # the route
    _app7 = create_app(); _app7.testing = True; _cl7 = _app7.test_client()
    _cl7.post(URL_PREFIX + "/login", data={"u": "doc", "p": "pw"})
    _pg7 = _cl7.get(URL_PREFIX + "/perks").data.decode()
    ck("Perks by staff" in _pg7 and "Alpha" in _pg7, "SL7: the Perks index lists staff totals")
    _pg7a = _cl7.get(URL_PREFIX + "/perks?staff=Alpha&year=all").data.decode()
    ck("Lifetime perks: Rs 13000" in _pg7a and "School fee - Adarsh" in _pg7a,
       "SL7: the per-staff view shows the lifetime total and the detail")
    _clm7 = _app7.test_client(); _clm7.post(URL_PREFIX + "/login", data={"u": "mfull", "p": "pw"})
    ck(_clm7.get(URL_PREFIX + "/perks").status_code == 403,
       "SL7: a maker is fenced out of the Perks view")

    print(f"SELFTEST PASSED — {ok[0]} maker-checker, rate-card, advance, loan, "
          f"skip, statement, salary, report, F-51 and D332/SL5+SL6+SL7 checks OK")

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
