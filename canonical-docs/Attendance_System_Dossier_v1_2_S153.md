# FROZEN DOSSIER — Biometric Attendance System (v1.2, S153)

**Dr. Manoj Agarwal Clinic · Bareilly · Tier 2 (frozen, D247) · built from live GitHub source `drmanoj-clinic-automation/attendance/` + `sops/SOP_Biometric_Attendance.md`.**

> Canonical as-built reference for the frozen Attendance product. Not read in the session loop; hash-verified only. Changing the system requires an explicit owner waiver (D34 discipline) + version bump. Operational fix-it guide (separate): `SOP_Biometric_Attendance.md` (Tier 1).

---

## 1. What it is / does

Self-hosted **biometric staff attendance**. Staff punch in/out on a Secureye device at the clinic; each punch goes to a listener on the clinic's own VPS, which records it; an engine computes per-person shift-aware attendance; a mobile dashboard shows it, daily emails summarise it, and a watchdog self-checks it. **Cloud-free (no ONtime) since 28 Jun 2026.** It runs **independently of the patient-facing systems** — a fault here does not affect calls or follow-ups.

## 2. Where it lives

- **GitHub (code):** `attendance/` in `drmanoj-clinic-automation`. Folder digest md5 `dc12f4a0f9cb921b4cf2ce7c579aae16`.

  | File | md5 | Role |
  |---|---|---|
  | `attlistener_v2.py` | `94fc58ca…` | standalone capture + local ack (**critical path**) |
  | `att_core.py` | `08a815ea…` | attendance engine (per-person, Sunday-aware) |
  | `att_dashboard.py` | `225d6d9d…` | Flask web view, port 8042 |
  | `att_mailer.py` | `7d87910d…` | morning + evening summary emails |
  | `att_doctor.py` | `048257ee…` | watchdog + safe repair |
  | `build_staff_master.py` | `d7e0110c…` | rebuilds `staff_master.csv` from salary workbook |
  | `att_config.example.py` | `a919712e…` | settings **template** (real values VPS-only) |
  | `attlistener.service` | `28390740…` | systemd unit — listener |
  | `attendance-dashboard.service` | `7b3a0cf4…` | systemd unit — dashboard |
  | `README.md` | `64360a2c…` | component/deploy reference |

- **VPS (live):** `/root/att_*.py`, `/root/*.service`, `/root/build_staff_master.py`; the only settings file `/root/att_config.py` (**secrets — VPS only, never in repo**).
- **Data (NOT in repo — data, not code):** `punches.csv`, `staff_master.csv` (**contains base salaries**), salary `.xlsx` — Drive/local only.
- **URLs:** primary `https://attendance.dr-manoj.in` (D224); fallback `http://93.127.195.49:8042/`.
- **Ports:** 8041 (listener), 8042 (dashboard). **Services:** `attlistener`, `attendance-dashboard`.
- **Cron:** `att_mailer.py morning` 11:30 · `att_mailer.py evening` 21:00 · `att_doctor.py --cron` 14:00.

## 3. How it works

- **Capture (`attlistener_v2.py`).** Receives Secureye JSON punches and **acks purely via one HTTP response header** — `response_code: OK` for a real punch (`realtime_glog`, body has `user_id`+`io_time`), `ERROR_NO_CMD` for a heartbeat (`receive_cmd`); the body is always empty. No call to any external server. De-dup key `(user_id, datetime)` — the **same key the engine reads on** — so a device re-send cannot duplicate a row. Writes `punches.csv`.
- **Engine (`att_core.py`).** Per-person, Sunday-aware late/early logic over the punches.
- **Dashboard (`att_dashboard.py`).** Flask on :8042 — day view + responsive month register, basic auth from `att_config.py`.
- **Mailer (`att_mailer.py`).** Morning (11:30) and evening (21:00) summary emails via cron.
- **Watchdog (`att_doctor.py`).** `--check` (default), `--fix` (safe repair), `--cron` (emails only when attention is needed). A separate watchman (S61) also monitors both services and auto-restarts.
- **Device.** Secureye S-B251CB marks a record delivered from the response header alone; when offline it **buffers punches locally and syncs on reconnect** — so a gap can fill itself in.

## 4. Decisions & findings that shaped it

- Went **live S59**; watchman added **S61**.
- **28 Jun 2026** — cutover to cloud-free (standalone listener + doctor; ONtime cloud dropped).
- **D224** — canonical address is `https://attendance.dr-manoj.in`.
- **F-31 (closed)** — `.gitignore` cannot untrack what git already tracks; `att_config.py` untracked and `att_config.example.py` added so real secrets never ship.
- **S139** — portal https hotfix (attendance reachable over https via the portal).

## 5. Known quirks / limits (read before ever reopening)

- The Secureye **acks via header only, empty body** — do not "fix" this by adding a response body.
- An **offline gap is not necessarily lost data** — buffered punches sync on reconnect.
- `staff_master.csv` **contains base salaries** — never commit it; Drive/local only.
- The **de-dup key `(user_id, datetime)` is shared** by listener and engine — change it on one side and you risk duplicate rows.
- Manual fallback: staff record on **paper**, reconcile once the listener is back.

## 6. Freeze note

**Frozen as of S147 / D247.** Artefact = the `attendance/` folder (digest `dc12f4a0f9cb921b4cf2ce7c579aae16`) + live VPS deployment. Not read or edited in the session loop; hash-verified only. Any change requires an **explicit owner waiver + version bump + a note**. The patient-facing systems are unaffected by this freeze. Operational guide: `SOP_Biometric_Attendance.md` (Tier 1).

---

**END — Attendance System Dossier v1 (S147).**

---

## S151 ADDENDUM (dossier v1 → v1.1, 05 Aug 2026) — salary reporting layer added (ADDITIVE; frozen core untouched)

- **NEW file `att_month_report.py`** — md5 `c925198895ea146b37a0c69b0ef85b6b` — lives beside the engine on
  the VPS (`/root/`) and belongs in the repo `attendance/` folder (commit owed; **folder digest re-pin owed
  at that commit** — the v1 pin covers the 10-file frozen core, which is byte-unchanged). Read-only,
  std-lib; **imports `att_core`** so engine and report share one rule set; adds the D249 policy layer
  (10-min grace marks; >30 min = 2 marks; >60 review column; marks//3 half-day deductions; incentive tier
  with Aug–Sep 2026 ramp). Run monthly: `/root/wa/venv/bin/python3 att_month_report.py YYYY-MM` → console
  table + `salary_inputs_YYYY-MM.csv` + `salary_inputs_YYYY-MM.html` (A4 landscape) beside itself. Has
  `--selftest` (synthetic month proving grace, doubling, Sunday exclusion, plausible-arrival, out-punch-only
  extra, inactive exclusion, both incentive schedules).
- **`staff_master.csv` state (S151):** 12 active staff, all with base salaries (Darpan, Arjun added);
  Sandip 09:00–21:00 (was stale 08:00); Darpan's workbook timing is a split-shift string
  ("09:30-15:30 + 18:00-21:00") which `build_staff_master.py` parses to wd 09:30–21:00 (first start, last
  end) — correct for late/extra judging. Live md5 `f8f3a23908d2007ccdc1bd9af5e87725`.
- **Workbook home:** `D:\clinic_salary\Salary_System_2026.xlsx` (owner PC, never in a git tree — F-31).
  Rebuild loop: edit Staff Master sheet → run repo `build_staff_master.py` FROM `D:\clinic_salary` → WinSCP
  the CSV to VPS `/root/` (no restart; read per request). Monthly report archive:
  `D:\clinic_salary\reports\`.
- **Companion (not part of this product):** `Darpan_Loan_System_v2_3.xlsx` (md5 `dd6689e1…`) — workbook-layer
  loan/perks/outstation module (D250); integration into the salary workbook parked top-of-backlog S152.
- Roadmap context: D251 (Phase 2 Google-Sheet migration; Phase 3 doctor-portal tile). The staff-facing
  attendance site remains frozen and salary-free by design.

---

## S153 ADDENDUM (dossier v1.1 → v1.2, 07 Aug 2026) — report layer rebuilt v2→v2.5 under D256 (ADDITIVE; frozen 10-file core byte-unchanged)

- **`att_month_report.py` v1 → v2.5** (owner-directed S153; six selftested versions in one session).
  Lineage: v2 `d293f822…` → v2.1 `8fb21d69…` → v2.2 `6116fca0…` → v2.3 `6d50e7a8…` →
  **v2.4 `608f2a90bf9ff65f196ac4f2f13c00bb` (INSTALLED on VPS, July-verified)** →
  **v2.5 `e64cad19d135618dec1413553e6bdc80` (delivered; install pending at S153 close)**.
  Still read-only, std-lib, additive: `att_core.compute_day` supplies presence + punch pairs;
  **ALL policy math now lives in the report** (roster-based Sunday shifts are owner policy, not
  engine data). ~40-assert `--selftest` on synthetic fixtures (F-31).
- **D256 policy engine (supersedes the D249 layer described in the S151 addendum):**
  late bands per episode (grace ≤10 min capped 8 days/month, beyond cap ≤10 = 1 mark; 11–29 = 1;
  30–59 = 2; ≥60 = 2 informed / 3 uninformed) · **Option-B slab deduction**
  `floor(max(0, marks − half_limit)/3)` half-days (half_limit 8 Aug-2026 ramp, 5 from Sep —
  **Sept-strict: the posted notice overrides the old Aug+Sep code ramp**) · incentive FULL = 1 day's
  salary, HALF = half day · OT = 2× per-minute rate (salary÷(30×wd shift min)), approval +
  punch-out compulsory, **candidates only** · **three-tier early departure** (last−first ≤30 min =
  double-punch artefact → duty presumed done (F-47); gap ≤120 min = auto-deduct 1×; >120 =
  EARLY_BIG, sheet-ruled vs the physical register, never machine-applied) · single punch = stayed
  till end · 30-day basis · Arjun `minutes_exempt` · **Net = incentive + OT − deductions/fines** ·
  habitual tracker (months with marks > half_limit; flag ≥3/yr).
- **Two-pass informed-flag loop:** first run writes `review_YYYY-MM.csv` (ABSENT + LATE60 rows,
  informed=Y defaults); owner edits N against the reception register; rerun applies ₹50 fines and
  +1 marks. The file is never overwritten once present.
- **Outputs per run** (beside the script): `salary_inputs_YYYY-MM.csv` ·
  `deductions_extras_YYYY-MM.csv` (per-line ₹ explain log) · `salary_inputs_YYYY-MM.html` —
  **landscape date-grid** (per-cell punch times, red L-marks, E/E!/bold-OT, artefact greys, bold
  row separators) + summary page with bilingual policy legend + **Big Early-Exit ruling table**
  (punch times + pre-computed deductible ₹ + blank Genuine/₹-applied boxes) + collapsible
  per-staff money log (screen-only; print = 2 sheets).
- **`staff_master.csv` v2** `3b1ebcb1e339fdcdb8b47389ee206108` (INSTALLED; VPS backup
  `staff_master_BACKUP_preS153.csv`): +`sunday_group` (A: Shivani, Awdhesh, Pravesh, Darpan ·
  B: Alisha, Shavez, Ranjeet, Sukhveer · C: Sandip, Vikki, Surendra · ARJ: Arjun) +
  `minutes_exempt` (Arjun). The frozen engine ignores the new columns (DictReader-additive);
  the report reads them itself. ⚠️ **The workbook Staff Master sheet and `build_staff_master.py`
  do NOT yet carry these columns — a rebuild would silently drop them** (open backlog item;
  until fixed, do not run the rebuild loop without re-adding the two columns).
- **Sunday semantics:** pre-Sep months follow `sun_start/sun_end`; from `ROSTER_FROM = 2026-09`
  the roster governs (A = 1st/3rd, B = 2nd/4th at weekday shift; off-Sundays fully ignored;
  5th Sunday = weekday shift for all; C/ARJ = sun columns every Sunday). July 2026 was ruled
  **diagnostic only**; August is the first billing month.
- **F-47 (new quirk — read before touching departure logic):** staff double-punch on arrival and
  essentially never punch out (July: Sukhveer 31/31 no-out days). A punch count is not a departure
  record — classify pairs before money math. OT can never pay without a real out-punch.
- **Print/policy artefacts (owner-side, non-repo, Register-pinned):** attendance notice
  **v6 FINAL** `b29dfa1317024d1d622d79d6de6f5c17` · `Staff_Rate_Card_v2_S153.xlsx`
  `8e9cf6462d63b9d229bcbf973d25f88c` (both `D:\clinic_salary\`, F-31).
- **Folder digest:** the v1 pin `dc12f4a0…` still covers the 10-file frozen core (byte-unchanged
  S153); the full-folder re-pin lands at the repo commit of v2.5.
- S151-addendum staleness corrected by S152/S153 events: the Darpan workbook integration COMPLETED
  at S152 (`Salary_System_2026.xlsx` v3, standalone retired); the S151 description of the D249
  policy layer (`marks//3`, Aug–Sep ramp, Sunday exclusion) is historical — D256 above is current.

**END OF ATTENDANCE SYSTEM DOSSIER v1.2 — the S153 ADDENDUM is the last section; if absent, this file is truncated and must not be used as canonical.**
