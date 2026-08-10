# SALARY & ATTENDANCE — CONSOLIDATED MASTER DOSSIER (SOLE REFERENCE)

**Dr. Manoj Agarwal Clinic · Bareilly · v1.0 · Session 164 · 2026-08-10**

> **Status: this is the single authoritative reference for the salary + attendance + staff-daily-register machine.**
> It consolidates and **supersedes** the three separate documents: `Attendance_System_Dossier_v1.2` (S153),
> `Salary_System_KB_v1` (S157), and `Staff_Daily_Register_Dossier_v1.1` (S161). Where this dossier and those
> disagree, **this wins**. Keep those three as historical references only.
>
> **F-31 applies throughout:** no staff financial *data*, salary CSVs, or patient numbers ever go into repos,
> chat, or this doc. This doc describes *mechanism and policy*, never live rupee figures per person.
>
> **How to use it.** Section 1 is the map. Sections 2–4 are the three subsystems. Section 5 is the month-end
> runbook (how a month actually gets paid). Section 10 is **Troubleshooting** — go there first when something
> looks wrong. Section 11 is the dated change history for these systems.

---

## 0. Golden rules (read once, obey always)

1. **Build only from md5-verified live VPS copies** (D160/D172/D188). A filename is not provenance — trust the hash.
2. **Full-file replacements only** (D202), never hand-edited diffs.
3. **Install order (F-66):** back up (`cp file{,.bak-SNNN}`) → upload as `.new` → `md5sum` the file **in place** →
   only then `mv` into position → **VPS-venv** `py_compile` → **VPS-venv** `--selftest` → restart the service.
4. **New/altered table → run the app's `--init` before `systemctl restart`** (F-65).
5. **VPS python is older than the sandbox** (F-53) — always compile/selftest with the VPS venv:
   `/root/wa/venv/bin/python3`. A sandbox pass is necessary, not sufficient.
6. **Any live Flask change must pass a test-client route hit** (HTTP 200 + expected content) in `--selftest`
   before install (F-63). "A check that cannot fail is not a check."
7. **One writer per table.** The engine and report are **read-only** over the register/ledger/attendance stores.
8. **Money is paid off the workbook until a clean, locked register run reproduces it** — see §5.

---

## 1. THE MACHINE — three subsystems and how data flows

Three independent systems feed one monthly number. **None writes another's store.**

```
  BIOMETRIC PUNCHES                 STAFF DAILY REGISTER              STAFF LEDGER
  (Secureye device)                 (day-by-day maker/checker)        (money events, maker/checker)
        │                                   │                                 │
        ▼                                   │                                 │
  attlistener → punches.csv                 │                                 │
        │                                   │                                 │
        ▼                                   ▼                                 ▼
  att_month_report.py  ───────►  salary_inputs_YYYY-MM.csv            compute_salary (read-only)
  (policy: bands, Option-B,      deductions_extras_YYYY-MM.csv        + uniform/i-card magnitudes
   departures, incentive, OT)           │                                 │
                                         │                                 │
                                         ▼                                 ▼
                        ┌──────────────────────────────────────────────────────┐
                        │  salary_engine.py  (STANDALONE monthly take-home)      │
                        │  reads: salary_inputs CSV  +  register grid            │
                        │         + register day_review (coverage)               │
                        │         + ledger money fold  +  EARLY-BIG rulings      │
                        │  page: attendance.dr-manoj.in/register/salary          │
                        └──────────────────────────────────────────────────────┘
                                         │
                                         ▼
                        Stage-B: APPROVE & LOCK  →  locked_run  (Manoj-only)
```

- **Absence is the biometric's job**, not the register's. A staff member missing from the punch feed on a
  working day is an absent; the register only records *exceptions* (leave, fines, OT, outstation, late).
- **The register's job** is the day-by-day maker→checker review that says "this day is captured/approved,"
  plus the exception grid.
- **The engine** joins all three into one standalone take-home per staff. It **prints no rupees to console**
  (F-31); output is an HTML page, chmod 600.

---

## 2. ATTENDANCE SUBSYSTEM (biometric → att_month_report → salary_inputs CSV)

### 2.1 What it is
Self-hosted biometric attendance. Staff punch on a **Secureye S-B251CB**; a VPS listener records each punch;
an engine computes per-person shift-aware presence; a monthly **report** applies all salary policy and emits
the CSV the salary engine consumes. **Cloud-free since 28 Jun 2026.** Runs independently of patient-facing systems.

### 2.2 Live files (VPS `/root/`, repo `attendance/`)
| File | Role |
|---|---|
| `attlistener_v2.py` | capture; acks via **one HTTP response header only, empty body** (do NOT add a body). Writes `punches.csv`. De-dup key `(user_id, datetime)` — the same key the engine reads on. |
| `att_core.py` | per-person, Sunday-aware presence/late/early engine (frozen core). |
| `att_dashboard.py` | Flask day + month view, port **8042**, `https://attendance.dr-manoj.in`. |
| `att_month_report.py` **v2.5** (`e64cad19d135618dec1413553e6bdc80`) | the **policy layer** — reads `att_core.compute_day`, applies all money policy, writes the CSVs + HTML. Run: `/root/wa/venv/bin/python3 att_month_report.py YYYY-MM`. |
| `att_doctor.py` | watchdog (`--check`/`--fix`/`--cron`). |
| `build_staff_master.py` v2 (`9fe81d7b…`) | rebuilds `staff_master.csv` from the salary workbook. |

**Services:** `attlistener` (8041), `attendance-dashboard` (8042). **Cron:** mailer 11:30 / 21:00, doctor 14:00.
**Data (never in repo):** `punches.csv`, `staff_master.csv` (**contains base salaries**).

### 2.3 Policy engine (D256 — the current rules; supersedes the older D249 layer)
- **Late bands, per episode:** grace ≤10 min (capped 8 days/month; beyond the cap a ≤10 = 1 mark); 11–29 = 1 mark;
  30–59 = 2; ≥60 = **2 if informed / 3 if uninformed**.
- **Option-B slab deduction:** `floor(max(0, marks − half_limit) / 3)` half-days. `half_limit` = **8** for the
  Aug-2026 ramp, **5 from Sep** (Sept-strict — the **posted notice overrides** any old code ramp). Each half-day
  = salary ÷ 60.
- **Three-tier early departure** (F-47 — *a punch count is not a departure record; classify pairs first*):
  - last−first ≤ **30 min** = double-punch artefact → duty presumed done (grey cell), no deduction.
  - gap ≤ **120 min** = auto-deduct **1× per-day rate**.
  - gap > **120 min** = **EARLY_BIG** — *listed, never machine-applied*; the doctor rules it genuine/waived
    against the physical register.
  - single punch = stayed till end.
- **OT** = 2× per-minute rate (salary ÷ (30 × shift-min)); requires approval **and** a real out-punch;
  report lists **candidates only**. (NB: the standalone register salary **removes OT** — see §4.)
- **Incentive:** FULL = 1 day's salary, HALF = half day (attendance-tier).
- **30-day basis.** **Arjun** is `minutes_exempt` (salary by absents only).
- **Habitual tracker:** months with marks > half_limit; flag ≥3/yr.

### 2.4 Two-pass "informed" loop
First run writes `review_YYYY-MM.csv` (ABSENT + LATE60 rows, `informed=Y` default). Owner edits `N` against the
reception register; rerun applies ₹50 fines / +1 marks. **The review file is never overwritten once present.**

### 2.5 Outputs (beside the script, per run)
- `salary_inputs_YYYY-MM.csv` — the machine feed the salary engine reads. Columns include: `Name`,
  `Ded: marks Rs`, `Ded: early-dep Rs`, `Fine: uninformed Rs`, `Fine: excess-absent Rs`, `OT candidate Rs`,
  `Incentive`, `Incentive Rs`, `Absent`, `Absent dates`.
- `deductions_extras_YYYY-MM.csv` — per-line ₹ explain log (also the EARLY-BIG event source).
- `salary_inputs_YYYY-MM.html` — landscape date-grid + bilingual policy legend + Big-Early-Exit ruling table.

### 2.6 Sunday semantics
Pre-Sep months follow `sun_start/sun_end`; from **`ROSTER_FROM = 2026-09`** the roster governs — **Group A**
(Shivani, Awdhesh, Pravesh, Darpan) 1st/3rd Sundays; **Group B** (Alisha, Shavez, Ranjeet, Sukhveer) 2nd/4th;
off-Sundays ignored; 5th Sunday = weekday shift for all; **Group C** (Sandip, Vikki, Surendra) + **ARJ** (Arjun)
work every Sunday. **July 2026 was diagnostic only; August is the first billing month.**

---

## 3. STAFF DAILY REGISTER SUBSYSTEM (`staff_register.py`)

### 3.1 What it is
The day-by-day **maker → checker** capture app + the single staff master + the onboarding vault, at
`attendance.dr-manoj.in/register` (systemd `staff-register`, local **127.0.0.1:8044**, VPS python
`/root/wa/venv/bin/python3`, DB `/root/staff_register/staff_register.db`, WAL). It is the **single staff master**
(the salary workbook Staff-Master sheet is retired for identity — D273).

### 3.2 Roles (config-driven; code defaults shown)
Resolved by `_register_role(username)` then `_caps(role)`. Config via `_cfg` = env → `staff_register_config` → default.
| Role | Users (default) | Caps |
|---|---|---|
| override | doctor (SSO) + `SR_OVERRIDE_USERS` | everything, incl. reverse-approval, bypass D272 |
| checker | `SR_CHECKER_USERS=shavez` | maker + one-click approve (not own dates, D272) |
| maker | `SR_MAKER_USERS=alisha,shivani` | enter days; leave/fines/OT/outstation grid |
| inactive | `SR_INACTIVE_MAKERS` (**empty since S164** — Shivani activated, D293) | can sign in, no active caps |
| salary view | `SR_SALARY_USERS=manoj,bhawna` | see the salary run |
| lock | `SR_LOCK_USERS=manoj` | APPROVE & LOCK / unlock |
| delete | `SR_DELETER_USERS=manoj` | delete rows |

### 3.3 Data model (tables in `staff_register.db`)
- **`staff`** — the master: `staff_id` (== biometric user_id), name, join/last-working, `base_salary`,
  `sunday_group`, `allowed_offs`, `minutes_exempt`, `cover_eligible`, `outstation_eligible`, `active`.
- **`day_review`** — **one row per calendar date** (`reg_date` PK): `state` (`all_clear|exceptions`),
  `maker_user/maker_ts`, `checker_user/checker_ts`, `override_user/override_ts/override_note`,
  `status` (`draft|approved`). **`status='approved'` = the day is captured & signed off.**
- **`daily_register`** — per-(date, staff) **exception** rows only: `absence_type`, `leave_kind`,
  `late_flag/late_approved_by`, `dress_improper`, `icard_missing`, `outstation_nights`, `extra_duty`,
  `ot_permitted`, `maker_user/maker_ts`. A clean/absent day writes **no row here**.
- **`festival_day`** — `fest_date`, `name`, `clinic_closed` (1 = clinic shut, no entry needed, e.g. Holi).
- **`leave_sanction`** — approved continuous-leave ranges (D284): pre-fills the grid only when `status='approved'`.
- **`locked_run`** — the Stage-B official locked salary run per `ym`.
- **`issuance` / `issuance_pause`** — uniform/i-card issuance gate (fines only apply if issued & not paused).
- **`staff_profile`, `degree_registration`, `document_vault`, `asset_issue`, `earlybig_ruling`,
  `incentive_pot`, `settings`, `audit_log`.**

### 3.4 Capture flow (maker → checker)
- **Maker saves a day** (`/save`): writes/updates the `day_review` row to `status='draft'` (+ maker stamp);
  for exceptions, upserts `daily_register` rows; all-clear deletes that date's exception rows.
  Server-authoritative nullification/scoping (D276): outstation wins over leave; leave/absent carries no
  presence-behaviour fines; `minutes_exempt` (Arjun) = leave/absence only; fines gated on issuance.
- **Checker approves** (`/approve`): `day_review.status='approved'` (+ checker stamp). **D272:** a checker
  **cannot** approve a date he entered (`can_check_approve` = `maker_user != actor` unless override).
- **Override reverses** (`/reverse`): back to draft with a note.

### 3.5 Pending-review board (NEW S164, D292) — `/register/review`
The one place that shows where every working day is stuck, keyed off `approval_blockers(con, ym)` (the same
function the salary lock uses, so board and lock can never disagree):
- **Awaiting approval (checker-pending):** dates with a `draft` day_review, each with the **maker stamp**
  and a **one-click Approve** button (rendered only where `can_check_approve` allows — D272-safe).
- **Not yet entered (maker-pending):** dates with **no** day_review row, **up to today** (future dates show
  as a quiet "upcoming" note, not a nag).
- **Progress:** approved / working days (clinic-closed holidays excluded).
- **Portal tile** (D292): the Staff Register tile lands here and shows role-aware counts —
  **✍️ N to enter · ✅ M to approve** (checker/override) or **✍️ N to enter** only (maker). Counts come from
  the register endpoint **`GET /register/review/counts`** via a **same-origin portal proxy** (`/portal/review-counts`)
  — see F-68.

---

## 4. SALARY ENGINE SUBSYSTEM (`salary_engine.py`) — the standalone monthly take-home

### 4.1 What it is
A **read-only, standalone** engine (`/root/staff_register/salary_engine.py`, imported by the register app, page
`attendance.dr-manoj.in/register/salary`). It computes the **whole** monthly take-home itself — base + attendance
+ register grid C-model + ledger money fold — and keeps the old ledger net only as a **shadow/Delta** parity
column (D288). **OT removed; incentive → the annual pot** (not added to take-home).

### 4.2 Inputs
- `salary_inputs_YYYY-MM.csv` (attendance report) — marks/early/uninformed/excess-absent ₹, incentive, absents.
- Register grid aggregates (from `daily_register`): dress, i-card, extra, outstation, disc/festival leave, late.
- **`day_review` coverage** (see 4.4).
- Ledger money fold (approved, closed-month rows; **excludes** uniform/i-card/leave + `SALARY_EXCLUDED`;
  PERK is excluded).
- EARLY-BIG rulings — register-owned (`earlybig_ruling`, D290), overlaying the ledger's July fallback.

### 4.3 The C-model (per staff, monthly)
Constants: `DAYS_BASIS=30`, `DISC_QUOTA=2`, `FEST_QUOTA=2`, `ABSENT_FREE_DAYS=3`, `FINE_EXCESS_ABSENT=100`,
`DRESS_RS=20`, `ICARD_RS=20`, `EXTRA_DUTY_RS=200`, `OUTSTATION_RS=250`.
- `day = base / 30`.
- `genuine_absent = max(0, att_absent − (sanctioned-leave dates ∩ absent dates) − grid outstation nights)`.
- `C = disc_leave_used + genuine_absent`; `extra_days = max(0, C − 2)`.
- **`deduct_days = (extra_days + festival_over) if covered else 0`**; `base30_ded = deduct_days × day`.
- Encashment: unused discretionary quota is encashed at 1 day's salary **only if the month is covered AND has no
  deductible day** (D279/D280 — attendance-gated).
- `net = base − marks − early-dep − uninformed − excess-absent − early_big + extra + outstation − dress − icard
  − base30_ded + encash + ledger_fold + prorate_delta`.

### 4.4 COVERED — the F-67 rule (fixed S164, D291) ⭐
`covered` decides whether the whole C-model (base÷30 absence cut, encashment, grid-vs-ledger fine source) applies.
- **Rule:** `covered = (the month has ≥1 `day_review` row with `status='approved'`)`. It keys off **capture
  (the checker's approve), NOT the presence of `daily_register` exception rows.**
- **Why (the bug that was fixed):** with minimal-input entry, a genuinely captured month can have real biometric
  absences but **zero** exception rows. The old rule (`covered = any daily_register row`) then read the month as
  *uncovered* and silently **skipped the base÷30 cut → overpayment**. Proven ₹2,100 overpay on the test scenario.
- **`'approved'`, not any row:** a stray **draft** day_review row (the live 2026-07 one) must not flip a month to
  covered, or July's proven parity breaks. Draft ≠ covered.
- **Legacy months** (no `day_review` table / no approved rows, e.g. July) → `covered=False` → ledger supplies
  uniform/i-card, C-model off — parity preserved.
- **Regression test:** `salary_engine.py --selftest` CASE E — a captured month (approved day_review) with real
  absences and zero exception rows must return `covered=True` and `base30_ded>0`.

### 4.5 Stage-B — APPROVE & LOCK (`/register/salary/lock`)
- **Lock C-rule:** every working date (calendar dates minus clinic-closed holidays) must have an **approved**
  `day_review` row. Missing/draft dates hard-block the lock; `approval_blockers()` lists them (the pending board).
- Lock requires: month ended, ledger complete/closed, zero blockers, `lock` cap (**Manoj-only**). Writes
  `locked_run`. An incomplete run (ledger unreachable) can never lock (`final_net=None`).
- Salary **view** = `manoj`, `bhawna`. **APPROVE & LOCK / unlock** = `manoj` only.

### 4.6 Parity anchor
July 2026 (register **uncovered**) reproduces the attendance FINAL SALARY **TOTAL PAYOUT ₹1,07,447** to the
rupee (ties within ₹0.66 rounding; `new_net + incentive_pot == old_net`). **This number is the acceptance test —
any change to the engine must keep July at ₹1,07,447 and July `covered=False`.**

---

## 5. THE MONTH-END RUNBOOK (how a month actually gets paid)

1. **During the month:** makers capture each day in the register; the checker approves (pending board keeps the
   queue at zero). Biometric punches accrue automatically.
2. **Month-end:** run the attendance report — `/root/wa/venv/bin/python3 att_month_report.py YYYY-MM`. First run
   writes `review_YYYY-MM.csv`; owner edits `informed` flags vs the reception register; **rerun**. Produces
   `salary_inputs_YYYY-MM.csv` + `deductions_extras` + HTML.
3. **Ledger:** close the month in the Staff Ledger so loan instalments/adjustments fold in.
4. **Salary page:** open `attendance.dr-manoj.in/register/salary?ym=YYYY-MM`. Reconcile the **Delta** column
   line-by-line (grid fines, C-model, incentive→pot, OT removal, Darpan outstation).
5. **Rule EARLY-BIG** exits (`/register/salary/earlybig`) — genuine vs waived.
6. **Clear the pending board** — every working day approved (lock C-rule).
7. **APPROVE & LOCK** (Manoj only) once ended + complete + zero blockers. Writes `locked_run`.
8. **Until a clean locked run reproduces the workbook figure, money is still paid off the workbook.** A clean
   verdict demotes the workbook to read-only. First real approval target: August 2026.

---

## 6. ROLES, ACCESS & CONFIG KEYS

**Config precedence (`_cfg`):** environment variable → `staff_register_config.py` (VPS, chmod 600) → code default.
*An empty value is treated as "unset"* and falls through to the default — so "nobody" is expressed by the code
default `""`, not by blanking a config value.

| Key | Default | Meaning |
|---|---|---|
| `SR_CHECKER_USERS` | `shavez` | checkers |
| `SR_MAKER_USERS` | `alisha,shivani` | makers |
| `SR_INACTIVE_MAKERS` | `""` (**S164**) | provisioned-but-parked makers |
| `SR_OVERRIDE_USERS` | `""` | extra overrides (doctor is override via SSO) |
| `SR_SALARY_USERS` | `manoj,bhawna` | salary view |
| `SR_LOCK_USERS` | `manoj` | approve & lock |
| `SR_DELETER_USERS` | `manoj` | delete |
| `SR_PUNCH_CSV` | `/root/punches.csv` | biometric feed (read-only) |
| `SR_DB_PATH` | `…/staff_register.db` | register DB |
| `PORTAL_USER_ADMINS` | `manoj` | who may open `/portal/users` (D294) |
| `REGISTER_COUNTS_URL` | `http://127.0.0.1:8044/register/review/counts` | portal→register counts (F-68) |

**Portal roles** (store `clinic_users`): doctor / manager / staff → map to register override / checker / maker.
**Portal user admin** (`/portal/users`, D294) is **Manoj-only**: add/role/reset-password/activate/delete over
`clinic_users`; guards block self-lockout and removing the last active doctor. Portal "active" = the **login master
switch** (blocks all apps); per-app maker/checker powers stay in each app's role list.

---

## 7. LIVE FILE INVENTORY (as of S164 close, 2026-08-10)

| File | md5 (live) | Location / service |
|---|---|---|
| `salary_engine.py` | `5514918067243e3f39e7074144ee7db4` | `/root/staff_register/` (imported by register) |
| `staff_register.py` | `cef768594bee5360a388e66028456495` | `/root/staff_register/`, `staff-register.service`, 8044 |
| `portal.py` | `4b75ee7b50b5530eaca7c347e4a432d0` | `/root/portal/`, `clinic-portal.service`, 8090 |
| `clinic_users.py` / `clinic_sso.py` | (unchanged) | `/root/portal/`; store `clinic_users.json` (chmod 600) |
| `staff_ledger.py` | `92665b64…` | `/root/`, `staff-ledger.service`, 8043, `/ledger` |
| `att_month_report.py` v2.5 | `e64cad19d135618dec1413553e6bdc80` | `/root/` |
| attendance core (`attlistener_v2`, `att_core`, `att_dashboard`, `att_doctor`) | see §2.2 | `/root/`, `attlistener`/`attendance-dashboard` |

**All three S164 files (`salary_engine`, `staff_register`, `portal`) are commit-owed to GitHub.**
Backup chain this session: staff_register `f24664db → 7c6bae8b → cef76859`; portal `bd37157f → 5cf81346 → 4b75ee7b`;
salary_engine `303c7059 → 5514918`.

---

## 8. DECISIONS INDEX (salary / attendance / register)

- **D247** canonical data management (tiers). **D256** attendance policy engine (bands/Option-B/departures).
- **D257** Staff Ledger (maker-checker). **D271** Staff Daily Register subsystem.
- **D272** checker cannot approve own date. **D273** register = single staff master; workbook retired for identity.
- **D276** per-staff scoping/nullification. **D277** OT approved-by-default, reviewed next day. **D278** festival-by-date.
- **D279/D280** C-model encashment, attendance-gated. **D282** Sunday pre-Sep half-day automatic.
- **D284** continuous sanctioned-leave range. **D286** ledger salary page redirect (staged). **D288** standalone
  register salary; July parity ₹1,07,447. **D290** register-owned EARLY-BIG rulings.
- **S164 new:** **D291** coverage keys off `day_review` approved (F-67 fix). **D292** pending-review board +
  role-aware portal tile + same-origin counts proxy. **D293** Shivani activated (INACTIVE_MAKERS default empty).
  **D294** portal user management (manoj-only).

---

## 10. TROUBLESHOOTING — symptom → cause → fix

> Go here first. Each entry is: **symptom**, the likely **cause**, and the **fix / check**.

### 10A. Salary numbers wrong

- **A captured month underpays absentees / base÷30 cut didn't apply.**
  Cause: coverage not detected. Check the month has ≥1 `day_review` row with `status='approved'`
  (`SELECT status,COUNT(*) FROM day_review WHERE reg_date LIKE 'YYYY-MM%' GROUP BY status`). If only `draft`
  rows exist, the checker hasn't approved — approve at least the reviewed days (pending board). This is the
  F-67/D291 rule: **covered = approved capture, not exception rows.**

- **July total drifted off ₹1,07,447 after an engine change.**
  Cause: a change flipped July to `covered=True` (e.g. a stray approved 2026-07 day_review row, or coverage keyed
  on any row). July must stay `covered=False`. Run `salary_engine.py --selftest` (CASE B + conservation) and open
  `/register/salary?ym=2026-07` — every July row must show the **"no grid"** pill and the total tie to ₹1,07,447.

- **Salary page says "ledger month not closed" / net incomplete / can't lock.**
  Cause: the Staff Ledger month isn't closed, so loan instalments/adjustments aren't folded. Close the month in
  the ledger. An incomplete run (`final_net=None`) is **designed** to be unlockable (D283).

- **Uniform/i-card fine double-counted or missing.**
  Rule: **covered month → grid supplies fines** (ledger uic ignored, with a warning); **uncovered month → ledger
  supplies fines**. If a covered month still has ledger uniform/i-card rows, the page flags it — remove the
  duplicate ledger entry.

- **Incentive appears in take-home.** It shouldn't — incentive goes to the **annual pot** (paid Diwali after FY
  close). It shows only in the `incentive_pot` column.

### 10B. Attendance report issues

- **Someone shows huge OT or looks "never left."**
  Cause: F-47 — staff double-punch on arrival and rarely punch out. A punch count is not a departure record.
  OT never pays without a real out-punch; the three-tier departure logic classifies pairs first (≤30 artefact,
  ≤120 auto-1×, >120 EARLY-BIG doctor-ruled).

- **An absence/late looks unfair; informed flag wrong.**
  Use the two-pass loop: edit `review_YYYY-MM.csv` (`informed=N/Y`) against the reception register and **rerun**.
  The review file is never overwritten once present.

- **Sunday marked wrong.**
  Pre-Sep months use `sun_start/sun_end`; from `ROSTER_FROM=2026-09` the roster governs (groups A/B/C/ARJ).
  Confirm `sunday_group` in `staff_master.csv`.

- **`staff_master.csv` lost the `sunday_group`/`minutes_exempt` columns after a rebuild.**
  Cause: the workbook Staff-Master sheet / `build_staff_master.py` must carry both columns or a rebuild drops
  them. Use `build_staff_master.py` v2 (`9fe81d7b…`, fail-loud if columns missing) and rebuild from
  `D:\clinic_salary`.

- **Punch gap / listener looks down.**
  An offline gap is not necessarily lost — the Secureye buffers and syncs on reconnect. The listener acks via
  **response header only, empty body** — never "fix" it by adding a body. De-dup key `(user_id, datetime)` is
  shared with the engine; don't change it on one side.

### 10C. Register / pending board

- **Pending board / tile shows a big "to enter" count.**
  That's real: those are working days up to today with no register entry. A maker must record them (or mark
  all-clear). Future days are not counted (they show as "upcoming").

- **A checker can't approve a date.** D272: he entered it himself. Another checker or an override must approve.

- **A day won't save.** It's already approved (override must reverse first) or it's a clinic-closed holiday.

- **Fines won't apply for a staffer.** The item isn't issued (or issuance is paused), or the staffer is
  `minutes_exempt` (Arjun), or the day is leave/absent (fines nullified), or outstation (wins over everything).

### 10D. Portal / SSO / counts tile

- **Staff Register tile shows no counts (just the static text).**
  Cause: the register counts weren't fetched. This is **F-68** — cross-origin credentialed fetch through the
  OpenLiteSpeed proxy is fragile (Origin/CORS headers stripped). The fix in place routes counts through the
  **portal's own origin** (`/portal/review-counts`), which server-side calls the register over localhost
  (`REGISTER_COUNTS_URL`, default `127.0.0.1:8044`). If it still shows nothing:
  `curl -s -o /dev/null -w "%{http_code}\n" -m 3 http://127.0.0.1:8044/register/review/counts` →
  302/401/403 = port+route OK (cookie missing in curl only); 000 = wrong port (set `REGISTER_COUNTS_URL` in
  `portal_config.py`); 404 = prefix mismatch.

- **A user can log in but has no powers (register "not activated" screen).**
  They're an **inactive** maker (`SR_INACTIVE_MAKERS`) — remove them from that list. (Shivani was this until S164.)
  Adding a portal login grants a **role**, not app powers — maker/checker rights are per-app username lists.

- **Manage Users tile missing / 403.** It's **Manoj-only** (`PORTAL_USER_ADMINS`, D294) — invisible to everyone
  else, and the route 403s non-admins. You cannot deactivate/delete yourself or the last active doctor by design.

- **A deactivated user can still get in right now.** Deactivation blocks **future** sign-ins; an open session
  lasts until expiry or "Sign out everywhere" (the epoch is global — no per-user instant kick).

### 10E. Install / deploy failures

- **File installed but behaves like the old one.** You didn't restart (`staff-register` holds `salary_engine` in
  memory — it's imported), or the md5 didn't match (WinSCP wrong-bytes: drag to the local pane first, re-upload).
  Follow F-66 exactly: `.new` → md5 in place → `mv` → compile → selftest → restart.

- **Selftest passes in sandbox but the app breaks on the VPS.** F-53 — VPS python is older. Always compile +
  selftest with `/root/wa/venv/bin/python3`.

- **A new/altered table causes errors after install.** F-65 — run the app's `--init` before `systemctl restart`.

- **A Flask change 500s in production though it "compiled."** F-63 — `py_compile` alone is insufficient; the
  selftest must hit the route via the test client (HTTP 200 + expected content) before install.

---

## 11. CHANGE HISTORY (these systems only)

- **S59** attendance live; **S61** watchman. **28 Jun 2026** cloud-free cutover.
- **S147/D247** frozen dossiers. **S151** `att_month_report` added. **S153** report → v2.5 (D256 policy);
  `staff_master` v2 (sunday_group/minutes_exempt); F-47.
- **S154** Staff Ledger live (D257). **S157** Salary System KB, Portal SSO. **S160/D271** Staff Daily Register.
- **S161** Staff Register onboarding + Salary Engine Stage A; C-model policy (D272–D282). **S163/D288** standalone
  register salary; **July parity ₹1,07,447**; **D290** register-owned EARLY-BIG. F-65, F-66 minted.
- **S164 (2026-08-10) — this dossier's baseline:**
  - **F-67 CLOSED / D291:** salary coverage keys off `day_review` approved, not exception rows
    (`salary_engine.py 5514918…`, CASE E regression). July parity re-verified ₹1,07,447, still uncovered.
  - **D292:** pending-review board `/register/review` (maker-pending + checker-pending, D272-safe one-click
    approve, maker stamps) + `GET /register/review/counts` + portal Staff Register tile with role-aware counts
    (`staff_register.py cef76859…`, `portal.py 4b75ee7b…`).
  - **F-68:** cross-origin credentialed fetch through OLS is fragile → same-origin portal proxy
    (`/portal/review-counts`) calling the register over localhost.
  - **D293:** Shivani activated as a maker (`SR_INACTIVE_MAKERS` default emptied).
  - **D294:** Manoj-only portal user management (`/portal/users`) over `clinic_users` with self-lockout /
    last-active-doctor guards.

---

**END — SALARY & ATTENDANCE MASTER DOSSIER v1.0 (S164, 2026-08-10). This is the sole reference; if any section
above is missing this file is truncated and must not be trusted.**
