# S552_PHYSIO_REGISTER — kit S552 (session 313, 14-Oct-2026) · D646

**The owner, 13-Oct 14:16–14:42 IST and 14-Oct 04:32:** *"Physiotherapist also wants to log his home visits … He keeps the money with himself. And it should not count in the monthly income for the accountants and stay as a separate report … instead of paisa mila, payment received is a better word. And for the clinic physiotherapy … expand it similarly to patient-wise."* · *"I would like the reception not to be involved in this bookkeeping. They simply take the payment and issue the slip and physiotherapist then does this Parchi entry and his Parchi entry are then matched with the totals which the reception daily posts. And any differences are flagged."*

## What it does

- **Bhati's page** `/finance/physio/book` (unit `physiobook`; Roman Hinglish). **Clinic** tab: a day picker (today and the six days before); slip number filled in with the highest live slip + 1, patient by Clinic ID or name (Docterz's last year and the register's own) or *Naya patient* (name, mobile), ₹250 filled in, **Cash** / **UPI** as two big buttons that save. A slip already entered is refused with its day and patient. The day's slips, each with *Galat entry hatao* (a void with one of three reasons; the row stays). The **match card**: his cash and UPI beside reception's (`clinic_physio_day`, read only) — ✓, or *Farq: Cash ₹X · UPI ₹Y*, or *Reception ne abhi nahi likha*; missing slip numbers named. **Ghar (Home visit)** tab: running and paused patients with last visit, visits, charged, received, due; *+ Naya ghar patient* (₹500 filled in); on a patient *Aaj visit hua ✓*, **Payment received** (Cash / UPI, any date), *Rok do / Phir shuru / Band karo*, *Clinic ID jodo* (once, never changed); closed patients under a folded *Band* list; the full mobile shown (he visits them).
- **The owner's report** `/finance/physio/book/report` (checker; English): month picker; *N days differ — reception and Bhati* with each day; day-wise (clinic sessions, cash, UPI, reception's cash and UPI, the match, home visits, home charges, home received); patient-wise, clinic and home apart (sessions, charged, received, due, last visit); month totals and the year; mobiles masked to the last four. **The switch** *Open the register for Bhati* / *Close it* (audited).
- **The door**: the existing Physiotherapy tile → `/finance/physio`; at its top, for a login with any role in `physiobook`: *Patient-wise register ›* (Hindi page) / *Physio register ›* (English page), and *Report ›* for checkers. No tile granted or withdrawn.
- Installed **switched off** for Bhati (`physio_book.on = 0`): he sees one line, *"Yeh page abhi band hai — Dr Manoj ke kehne par khulega."*; the doctors see everything.
- Money is append-only: a correction is a void plus a new row. Every write goes through the app's audit helper. **Home-visit money is never in `packs.py`, the income sheet, the day revenue or the morning match**; `clinic_physio_day` is never written.

## Files

| live file | from → to | what |
|---|---|---|
| `/root/finance/finance_app.py` | 0d713b14 → 87cc4266 | 1 counted edit: one guarded mount block right after S408's (`physio_book.init(app, db, require, audit, unit="physiobook")`) |
| `/root/finance/clinic_money.py` | b0408f82 → 0a2085ca | 1 counted edit: the link at the top of the Physiotherapy page |
| `/root/finance/physio_book.py` | NEW | the register, the home visits, the report, the switch |

Both edited files are rebuilt on the box from the live bytes by `make_s552.py`; the installer refuses unless the result is byte for byte the TO pin.
**Data step** (`seed_s552.py`, idempotent): `physio_patient`, `physio_course`, `physio_session`, `physio_payment` + the unique index (one live entry per slip) — the SCHEMA read out of `physio_book.py`; settings `physio_book.on = 0`, `physio_book.clinic_rate_p = 25000`, `physio_book.home_rate_p = 50000` (INSERT OR IGNORE); `business_unit` `physiobook`; `unit_role` bhati maker, manoj checker, bhawna checker (only where absent). Restarts `clinic-finance` only. No crontab, no tile, no other login.

Note: `/finance/physio/...` is gated first by the front gate on unit `physio` (bhati holds a viewer row there since S249), then by the module on `physiobook`.

## Proof (the walk, on the box, scratch copies only)

`walk_s552.py` loads the REAL finance app from a scratch copy, on a backup-API copy of the database, header sign-in for that process only; made-up rows dated March 2031, made-up mobiles built at run time. 52 checks: the data step (and a second run adds nothing); no login → 302; a login with no `physio` row → 302; a `physio` login outside `physiobook` → 403; switch off (bhati one line, his tap writes nothing; manoj and bhawna see the preview); the switch on (audited); slip filled in with highest + 1; search by Clinic ID and name; a Docterz patient's slip; a new patient with a mobile (a short mobile refused); the duplicate refused naming day and patient; a void (reason required; row kept, amount unchanged); a day that agrees (✓), one that differs (*Farq: Cash ₹ 250 · UPI ₹ 0*), one with no reception row; missing slip numbers inside a day and after the previous day; a day outside the window refused; a home course with three visits and two payments (due ₹400), pause / restart / close, a payment after closing, a voided payment, *Clinic ID jodo* once; the report (the differing day listed, day-wise and patient-wise figures, mobiles masked, month and year totals) for manoj and bhawna; **the staff-eye walk** (bhati's portal tiles from the real `portal.py` + the grants file show *Physiotherapy → /finance/physio*; his door shows *Patient-wise register ›*; manoj's shows *Physio register ›* and *Report ›*; an outsider's shows no link; bhati's register shows the slip entry while open); `packs.build_income` byte-identical before and after every physio row (March 2031 with a made-up revenue day, and the current month); the morning match unchanged; `clinic_physio_day` untouched; every write audited; the switch closed again.
**Negative controls:** the same walk on the old files goes red (the link among the failures), and with only `clinic_money.py` old exactly the two link checks go red.
`rehearse_s552.sh` runs the installer on a made-up root in /tmp with a stand-in service (the real app on port 18552): red after placing restores every file, a green run installs, a second run says ALREADY INSTALLED.

## Install — one line on the VPS

`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S552_PHYSIO_REGISTER/install_S552_PHYSIO_REGISTER.sh`

`DRY=1` before `bash` runs every gate and the walk and writes nothing.

## Undo

`\cp -p /root/finance/finance_app.py.bak_S552_0d713b14 /root/finance/finance_app.py && \cp -p /root/finance/clinic_money.py.bak_S552_b0408f82 /root/finance/clinic_money.py && rm -f /root/finance/physio_book.py && systemctl restart clinic-finance`

(The physio_* tables, settings and physiobook rows are additive and unused without the module; the database backup `finance.db.bak_S552_<stamp>` is only for reversing data, and is not needed for the undo.)
