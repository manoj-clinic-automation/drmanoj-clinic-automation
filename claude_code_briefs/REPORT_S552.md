# REPORT S552_PHYSIO_REGISTER — kit S552 · D646 · installed 14-Oct-2026 05:29 IST

**For Dr Manoj**
- Bhati now has his own **Physio register** page, reached from his existing *Physiotherapy* tile (a new button at the top: *Patient-wise register ›*). It is installed **switched off for him** — he sees only *"Yeh page abhi band hai — Dr Manoj ke kehne par khulega."* You and Dr Bhawna can already see and try everything.
- **Clinic:** he enters each numbered Physio slip (slip number filled in, patient by Clinic ID or name or a new name + mobile, ₹250, a Cash or UPI button). His day's cash and UPI are set beside what reception wrote on the counter sheet: ✓ when they agree, *Farq: Cash ₹X · UPI ₹Y* when not; skipped slip numbers are named.
- **Home visits:** one tap per visit (₹500), *Payment received* any time, due worked out, *Rok do / Phir shuru / Band karo*. This is his own money — it is **not** in the accountants' income, the day revenue or the morning match (proved unchanged).
- **Your report:** https://followup.dr-manoj.in/finance/physio/book/report — day-wise, patient-wise, month and year, the days that differ, and the button **"Open the register for Bhati"** when you are happy with it.
- Tested on a copy of the live data before it went in, and checked again on the live server after: it works.

---

## For the chat

### Live files — FROM → TO, md5 read back on the box (05:29:29 IST, `after.sh`)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/finance_app.py` | 0d713b14570384e0de07ac93a3b113db (pin exact) | 87cc4266f9cd05f3633f23e1f36488a0 — 1 counted edit: guarded mount block after `# --- S408_MONTH_END_PACKS end ---` |
| `/root/finance/clinic_money.py` | b0408f82ec104e2170ccc069d0ec6450 (pin exact, S541's TO) | 0a2085ca5392646521fc9796485ae5f0 — 1 counted edit: the link at the top of `_physio_html` |
| `/root/finance/physio_book.py` | — (absent) | 745130164014ec8d6f90cda839f5521b (NEW) |

Both edited files were rebuilt on the box from the live bytes by `make_s552.py` (each anchor exactly once; FROM md5 checked inside the builder) and compiled on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.

### Data step (`seed_s552.py`, idempotent; read back)
- tables `physio_patient`, `physio_course`, `physio_session`, `physio_payment` + `ux_physio_session_slip` (unique `slip_no` WHERE `slip_no IS NOT NULL AND voided_at=''`) — 0 rows each;
- settings `physio_book.on = 0`, `physio_book.clinic_rate_p = 25000`, `physio_book.home_rate_p = 50000` (INSERT OR IGNORE);
- `business_unit` `physiobook` ('Physio register') — needed because `unit_role.unit` references `business_unit(code)` (the S400 seed's pattern);
- `unit_role` physiobook: bhati maker, bhawna checker, manoj checker (3 added; nobody else). **No tile granted or withdrawn.**

### Walk (on the box, inside the installer, scratch copies in /tmp; the real finance app loaded from a scratch folder on a backup-API copy of finance.db; header sign-in for that process only; made-up rows dated March 2031, made-up mobiles built at run time)
`WALK OK S552: 52 checks green` — data step + second run adds nothing; no login → 302 on the three new pages; no `physio` row → 302; `physio` row but no `physiobook` → 403 (register and report); switch off: bhati one line and his tap writes nothing, manoj/bhawna see the preview; switch on audited as manoj; slip filled with highest + 1, ₹250; search by Clinic ID and by name; Docterz patient's slip; new patient with mobile; short mobile refused; duplicate refused *"Slip 95520001 pehle hi likhi hai — 10-Mar-2031, W552 WALK ONE"*; void needs a reason, row kept, amount unchanged; day agrees ✓; day differs *"Farq: Cash ₹ 250 · UPI ₹ 0"*; no reception row *"Reception ne abhi nahi likha"*; missing numbers inside a day and after the previous day; day outside 7 refused; home course 3 visits / 2 payments, due ₹400; pause (no visit while paused) / restart / close (under *Band*); payment after close; voided payment not counted; *Clinic ID jodo* once, second refused; report (1 day differs listed; day-wise and patient-wise figures; mobiles masked; month/year) for manoj and bhawna; **staff-eye**: bhati's portal tiles from the real `portal.py` + grants file include *Physiotherapy → /finance/physio*; his door shows *Patient-wise register ›* (no *Report ›*); manoj's shows *Physio register ›* + *Report ›*; an outsider's shows no link; bhati's register shows the slip entry while open; **`packs.build_income` byte-identical** (sheet XML) before and after every physio row, for March 2031 (a made-up revenue day) and the current month; morning match (`match_day`) identical; `clinic_physio_day` not written; writes audited; switch closed again.

### Negative controls
- the same walk on the OLD files: `43 of 52 checks red`, the two link checks among them;
- only `clinic_money.py` old (everything else new): `2 of 52 checks red` — exactly the two link checks.

### Rehearsal (BUILD_NORM §3) — `rehearse_s552.sh` on a made-up root in /tmp, the real app under a stand-in systemctl on port 18552
`REHEARSAL OK`: run 1 red after placing → both files back byte-identical, physio_book.py removed, health 200, db backup kept, lock released; run 2 green → DONE, md5s at pin, `physio_book.on = 0`; run 3 → ALREADY INSTALLED.

### After placing (live)
- `clinic-finance` restarted once (ActiveEnterTimestamp 05:29:07 IST), active; `/finance/healthz` 200 (local and public); `/finance/physio/book`, `/report`, `/home/1`, `/finance/physio` → 302 without a login (the gate, expected); journal: 0 "NOT mounted".
- As manoj (`probe_s552.py`, real app from a copy of the PLACED files on a fresh copy of the live db): report 200, Bhati's page 200 (preview), Physiotherapy page carries both links; as bhati: the one *band hai* line. `physio_book.on = 0`.

### Backups
`/root/finance/finance.db.bak_S552_20261014_052858` (sqlite backup API, 36,757,504 bytes) · `/root/finance/finance_app.py.bak_S552_0d713b14` · `/root/finance/clinic_money.py.bak_S552_b0408f82` (md5s = the FROM pins).

### Undo
`\cp -p /root/finance/finance_app.py.bak_S552_0d713b14 /root/finance/finance_app.py && \cp -p /root/finance/clinic_money.py.bak_S552_b0408f82 /root/finance/clinic_money.py && rm -f /root/finance/physio_book.py && systemctl restart clinic-finance`

### Kit
`deploy_kits/S552_PHYSIO_REGISTER/`: physio_book.py, make_s552.py, seed_s552.py, walk_s552.py, probe_s552.py, install_S552_PHYSIO_REGISTER.sh, rehearse_s552.sh, README.md, KIT_ID.txt, SUMS.md5 (no .json; F-185 gate clean). The installer ran from a byte-identical copy (`SUMS.md5` md5 ce7a1108… on both sides). Lock `/root/deploy/.claude_code_build.lock` taken 05:28:58 IST, owner S552, removed after this report.

### Calls made (no one was asked)
- **Tables "at mount":** created on the first request (`_ensure`, the estate's F-303 rule: never at import) and by the installer's data step — not at import time.
- **"Differ" days** are counted from the register's first clinic entry on; reception days before it show *before the register* in the report (otherwise every past day would read as differing while the register is switched off). A day with Bhati's entries but no reception row is *reception not written*, not a difference.
- **Voids** are offered on home visits and home payments too (same three reasons), since the tables carry void columns and the rule is "a correction is a void plus a new row".
- **Visits** only on a running course (a paused one shows *Phir shuru* first); payments any time, any date up to a year back (never in the future).
- A checker (owner/Dr Bhawna) can also write while the switch is off (the preview is real).
- The new walk-only login `w552outsider` and the made-up rows exist only in scratch copies.

### Not done, and why
- **The board's `_numbers` claims** could not be read or appended from this runner (the board is a claude.ai artifact; no tool here reaches it). Read instead: the newest canon (S314 close, 05:15 IST 14-Oct) records `_numbers` v402 as this kit's own claim, with no other PLANNED line on `finance_app.py` or `clinic_money.py`; and both live pins were exact. **The chat should append the DONE / RELEASED line for S552 (finance_app.py, clinic_money.py) to `_numbers`.**
- **DUTY_MAP.md / .json not changed.** The register is installed switched off, so no staff duty is live yet. When the owner opens it, Bhati's duty ("enter the day's physio slips"; due while a `clinic_physio_day` row exists for a day on/after the register's first entry with no live slip of that day) needs its DUTY_MAP line and door (`/finance/physio` → *Patient-wise register ›*). Named here as a finding, not silence.

### Noticed outside the brief (not touched)
- `/finance/physio/...` is gated first by the front gate on unit `physio` (`_unit_for_path`): Bhati reaches the register only because he holds a `physio` viewer row (S249). Removing that row would also close his register.
- The health page's mount list (`finance_app.py`, the S425 row: a fixed tuple of module names and `_all = 30`) does not name `physio_book`; a mount failure still shows there through `_MOUNT_FAILED`, but the "all N parts loaded" count was not raised (outside the one block the brief allows).
- *Clinic ID jodo* is on the home-patient page; a clinic-only patient added as a new name has no such button yet.
- Port 8199 on the box is held by another local service (the rehearsal uses 18552).
- **Later, not in this kit** (from the brief): sessions in the patient's 360° record; "physiotherapy advised" reaching Bhati's page with a notification; Bhati's absence tap sending a WhatsApp to his running clinic patients; a command-console line.
