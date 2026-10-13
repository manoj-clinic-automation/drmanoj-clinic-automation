# S552_PHYSIO_REGISTER — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the parent (session 313). Kit **S552** claimed on the board `_numbers` (v401 → v402) with its PLANNED line (D646). This file is the whole scope. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S552_PHYSIO_REGISTER` — the same work you would do from the owner's one Claude Code line.*

## 0 · For the owner (3 lines in the report, plain English)

Bhati gets his own **Physio register** page. **Clinic:** from the day's numbered Physio slips he enters each one — slip number (filled in), patient (Clinic ID or name, or a new name and mobile), ₹250, Cash or UPI. His day's cash and UPI are matched against what reception writes on the counter sheet; a day that differs is flagged until they agree. **Home visits:** a patient, one tap per visit (₹500), *Payment received* any time; Bhati keeps that money; it is a separate report and never in the accountants' income. You get a day-wise, patient-wise and month report. Installed **switched off** for Bhati until you have looked at it.

## 1 · The owner's words (13-Oct, 14:16 → 14:42 IST, and 14-Oct 04:32)

- *"Physiotherapist also wants to log his home visits in the physiotherapy section. And this he will be doing himself. Patients can be either of the clinic which are registered here in doctors or can be those who are still not registered here. In the home visits, they go for indefinite periods with some gaps in between and have variable charges which are paid at variable times."*
- *"He keeps the money with himself. And it should not count in the monthly income for the accountants and stay as a separate report for the physiotherapy part. The usual charge per visit is 500 rupees. And instead of paisa mila, payment received is a better word. And for the clinic physiotherapy he is doing, now we should be able to expand it similarly to patient-wise."*
- *"clinic physiotherapy charge is ₹250 and the clinic payments are done at the reception through the same slip ... system ... for physiotherapy there is a separate such book which is also numbered which is sequentially used ... the staff only ... collect the cash payment and note the UPI payments. The UPI payments are directly received by the physiotherapist. In his own personal account, and we do not want to track whether that payment arrived or not. We will believe what he enters into the system."*
- *"I would like the reception not to be involved in this bookkeeping. They simply take the payment and issue the slip and physiotherapist then does this Parchi entry and his Parchi entry are then matched with the totals which the reception daily posts. And any differences are flagged."*
- The physiotherapist's name is **Bhati** (login `bhati`). Never "Bharti".

## 2 · Numbers, pins, ownership

- Live files, **FROM pins — read each first; a different byte = STOP that file and report:**
  - `/root/finance/finance_app.py` **0d713b14570384e0de07ac93a3b113db** — one guarded mount block, placed beside the S408 packs block (§3.5).
  - `/root/finance/clinic_money.py` **b0408f82ec104e2170ccc069d0ec6450** (S541's TO) — one link on the Physiotherapy page (§3.6).
  - NEW `/root/finance/physio_book.py` — everything else.
- **Read only:** `clinic_physio_day` (reception's daily physiotherapy cash / UPI, written by `clinic_register.py` from the counter sheet — **never written by this kit**), `clinic_day_line` (Docterz's lines: `clinic_id`, `patient`), `unit_role`, `tile_grants.json`.
- Before any edit, read the board's `_numbers` claims (the artifact named in `NUMBERS_PROTOCOL_v1.md`): if another chat has a newer PLANNED line on `finance_app.py` or `clinic_money.py`, STOP and report.
- Services: `clinic-finance` restarted once. No crontab change. The build lock. F-185: no phone number of any kind in the kit, the walk or the report (made-up numbers are built at run time, as `walk_s549.py` does with `P("98765", "43210")`). No `.json` in the kit.

## 3 · The build

### 3.1 Tables (in `finance.db`; `CREATE TABLE IF NOT EXISTS` at mount and in the installer; append-only — a correction is a void plus a new row, never an UPDATE of an amount)

- `physio_patient(id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL DEFAULT '', name TEXT NOT NULL, mobile TEXT NOT NULL DEFAULT '', created_by TEXT, created_at TEXT)` — one person. A clinic patient carries the Docterz `clinic_id`; a new patient carries name + mobile, and a `clinic_id` can be added later (*"Clinic ID jodo"*), never changed once set.
- `physio_course(id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('clinic','home')), rate_p INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','paused','closed')), started TEXT, changed_at TEXT, changed_by TEXT)` — one patient can have a clinic course and a home course.
- `physio_session(id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL, day TEXT NOT NULL, slip_no INTEGER, amount_p INTEGER NOT NULL, mode TEXT NOT NULL DEFAULT '' CHECK(mode IN ('','cash','upi')), by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT '')` — a clinic session carries `slip_no` and `mode` (paid at the slip); a home visit carries neither.
- `physio_payment(id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL, day TEXT NOT NULL, amount_p INTEGER NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('cash','upi')), by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT '')` — home visits only.
- A unique index on `physio_session(slip_no) WHERE slip_no IS NOT NULL AND voided_at=''` — one live entry per slip.
- Every write goes through the app's own audit helper as `clinic_money.py` does (`_audit_safe`).
- Settings (the `setting` table): `physio_book.on` (default `0`), `physio_book.clinic_rate_p` (`25000`), `physio_book.home_rate_p` (`50000`).

### 3.2 Bhati's page — `GET /finance/physio/book` (unit `physiobook`, maker or checker), **Roman Hinglish** like the other staff pages; the payment button reads **"Payment received"** in English (the owner's word). Large type, taps first, typing only for a new name and mobile. While `physio_book.on` is `0`, a maker sees one line: *"Yeh page abhi band hai — Dr Manoj ke kehne par khulega."*; a checker sees everything (the owner's preview).

Two tabs, **Clinic** and **Ghar (Home visit)**:

**Clinic tab** (a day picker, today by default; any of the last 7 days):
1. **Slip entry:** slip number pre-filled with the highest live `slip_no` + 1 (editable); patient search by Clinic ID or name across `clinic_day_line` (distinct `clinic_id`, `patient`, last 365 days) and `physio_patient`, or *"Naya patient"* (name, mobile); amount ₹250 pre-filled (editable); **Cash** / **UPI** as two big buttons that save. A slip number already entered is refused with its day and patient.
2. **The day's slips:** slip, patient, amount, mode; a *"Galat entry hatao"* on each (a void with a reason, chosen from three: *galat amount / galat patient / do baar entry*).
3. **The match card:** Bhati's cash and UPI for the day beside reception's (`clinic_physio_day` cash_p, upi_p): ✓ when both agree; otherwise *"Farq: Cash ₹X · UPI ₹Y"*; *"Reception ne abhi nahi likha"* when the day has no reception row. **Missing slip numbers** between the day's lowest and highest, and between the previous entered day's highest and this day's lowest, are named.

**Home tab:** the active and paused home patients — name, last visit, visits, charged, received, **due** (charged − received). *"+ Naya ghar patient"* (search or new, rate ₹500 pre-filled). On a patient: **"Aaj visit hua ✓"** (date today, editable within 7 days; amount the course rate, editable), **"Payment received"** (amount, Cash / UPI, date), **Rok do / Phir shuru / Band karo**. Closed patients under a folded *"Band"* list. Full mobile shown here (he visits them).

### 3.3 The owner's report — `GET /finance/physio/book/report` (checker), **English**
- A month picker (current by default). **Day-wise:** clinic sessions, cash, UPI, reception's cash and UPI, the match (✓ / the difference), home visits and their charges, home payments received. **Patient-wise**, clinic and home separately: sessions, charged, received, due, last visit. **Month totals** and the year. Mobile numbers masked to the last four here.
- **The switch:** *"Open the register for Bhati"* / *"Close it"* (checker only; writes `physio_book.on`; audited).
- A line at the top when any day of the month differs: *"N days differ — reception and Bhati"*, each listed.
- Home visits appear only here and on Bhati's page — **nothing is added to `packs.py`, the income sheet, the day revenue or the morning match.**

### 3.4 Unit `physiobook`
The installer inserts, only if absent: `bhati` maker; `manoj` checker; `bhawna` checker (`INSERT OR IGNORE`, the pattern of `finance_app.py` L9350 / `seed_desk_roles.py`). No other login. **No tile is granted or withdrawn** — the page is reached from the existing Physiotherapy tile (§3.6).

### 3.5 Mount
In `finance_app.py`, one block beside S408's, the same guarded shape (`try: import physio_book; physio_book.init(app, db, require, audit?, unit="physiobook") except: _MOUNT_FAILED.append(...)`). Read how `clinic_money.init` receives `audit` and do the same.

### 3.6 The link
On `/finance/physio` (`clinic_money._physio_html`), at the top: for a login with any role in unit `physiobook`, one button — Hindi page: *"Patient-wise register ›"*; English page: *"Physio register ›"* → `/finance/physio/book` (checkers also see *"Report ›"* → `/finance/physio/book/report`). One counted edit; nothing else on that page changes.

## 4 · The walk (made-up database; no person, no number) and the norm (`BUILD_NORM_v1.md`, binding)
Made-up rows for: a clinic slip of a Docterz patient; a new patient with a mobile; a duplicate slip refused; a void; a day where reception and Bhati agree (✓) and one where they differ (the difference named); a missing slip number named; a home course with three visits and two payments (due correct); pause / restart / close; the switch off (maker refused, checker sees) and on; unit gate (a login outside `physiobook` refused); **the old `clinic_money.py` has no link (negative control)**; and the accountants' income sheet for the month **unchanged** by any physio row (`packs.build_income` before and after). Then the installer's order, rehearsed on a made-up root (green, ALREADY INSTALLED, red-after-placing restores), SUMS, `.gitignore` (last match wins), the number gate as PUBLISH runs it.

## 5 · Install, publish, report
Gates → the two FROM pins → compile → rebuild the two edited files from the live bytes (counted edits) → walk (DRY stops here) → `.bak_S552_<from8>` → place → tables and unit rows → restart `clinic-finance` → health 200 and the three new routes answer without a login as the gate says → as `manoj` (checker): the report and Bhati's page load; `physio_book.on` = 0 → the undo line. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` when the kit is final (CLAUDE.md); write `claude_code_briefs/REPORT_S552.md` — 3–5 plain lines on top for the owner, then the proof; append the install line to the board's `_numbers` claims (DONE / RELEASED for the two files).

**Later, not in this kit (name in the report only):** sessions in the patient's 360° record; *"physiotherapy advised"* entered by the doctor or Shavez reaching Bhati's page with a notification (name, clinic ID, full mobile); Bhati's absence tap sending a WhatsApp to his running clinic patients; a command-console line.

**NEVER:** write `clinic_physio_day`; add any physio money to the accountants' pack, the day revenue or the morning match; grant or withdraw a tile; print a mobile number in the report, a log or the kit; spell the name "Bharti".
