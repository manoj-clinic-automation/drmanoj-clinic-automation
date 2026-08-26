# OWNER TO-DO — LIVE (refreshed at EVERY close · step A10 of `END_OF_SESSION_PROMPT_v7`)

> **This is the always-current truth.** `HANDOFF_RUNBOOK §2` carries the close-time *snapshot*; this
> file edits continuously, which is why it is **deliberately UN-MANIFESTED** — hashing it would make
> Phase 0 fail by design. Nothing else checks it, so **A10 is a numbered step**.
> **Refreshed at the S202 CLOSE — 26-Aug-2026.** Tick = struck through, moved to DONE with its
> session number, never deleted.

---

## ⭐0 — MY ACTIONS

1. **TOKEN ROTATION** — `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`. Aging since 21-Aug; **still the
   oldest and highest-severity item in the project.** Three copies of the Marg token: the systemd
   unit, `D:\SendToClinic\token.txt` on the medical PC, and the manojz cache. Never hand-copy between
   machines. The cron token also lives in the "UPI Reconciliation" GAS Script Properties.

2. **COPY THE PIN LIST** — on the VPS:
   `cp /root/deploy/repo/deploy_kits/KB_canon_all/live_pins_S202close.txt /root/deploy/live_pins.txt`
   then `python3 /root/deploy/verify_live_pins.py`. Publish first.

3. **PUBLISH** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` on manojz. The whole
   S202 close is committed locally only until you do.

4. **GENERATE 25-AUG'S MARG SALE REPORT.** `MARG_PICTURE.txt` now correctly reports it as the one
   genuinely missing day. On the medical PC: Marg → BILL WISE SALES, *With Item Deta. = Yes*, for
   25-08-2026. The watcher captures it automatically.

5. **F-173 — THE APRIL-2025 NEFT ADVICE FILE.** Its account-number column is SHIFTED against its
   names, so **payments that month may have gone to the wrong accounts.** Still the only open item
   where money may already have left for the wrong party. Check that month's bank statement.

6. **PRAVESH EXITS 31-AUG** — check his advance position now; full & final at exit.

7. **BEFORE THE AUGUST CLOSE:** July cash top-ups ₹4,519 (Shavez 1068 · Sandip 797 · Awdhesh 707 ·
   Alisha 666 · Pravesh 569 · Ranjeet 449 · Vikki 170 · Sukhveer 93) · Surendra's ₹516 gap → settle
   his ₹855 · Arjun's July actual-paid figure · Shivani's ₹3,724.55 recovery + the parked ₹3,000 ·
   **AF-3's duplicate-advance scan** · the UPI correction-checklist day + the 4 disagreement days.

8. **F-185 — THE REPO VISIBILITY RULING IS YOURS**, and on corrected figures. I told you patient
   diagnoses were public. **That was false** — your `.gitignore` had always excluded them. The real
   measure: **62 mobile-shaped numbers in tracked files, no diagnoses, ever**, and the two biggest
   sources are synthetic test fixtures. Worth closing on the phone numbers alone, at your convenience.
   Not the emergency I made it.

9. **ASK MARG SUPPORT TWO THINGS**, in one message:
   (a) can `margwin.exe` be told to generate or export a specific report from the command line?
   (b) why does the configured automatic backup produce nothing? — see F-191(c) below.

---

## ⭐0a — THE BACKUP (F-191c) — the crown jewels, and the first job next session

Everything we have built is downstream of Marg. **Marg holds the actual pharmacy.**

- Backups are **manual**, every 2–4 days, to `E:\` (an HP USB 2.0 stick permanently attached to the
  medical PC). **Last: 22-Aug.**
- **`E:\auto` and `E:\MARGBCKUP\auto` have been EMPTY since October 2025.** Automatic backup was
  configured and **has never once run**, while a human quietly filled the gap by hand.
- The old financial year (`d1-sanjeevni-20250401-20260331`) was last backed up **17-July**.
- **All 308 MB sits on one drive attached to the machine it protects** — fine against a dead disk,
  useless against fire, theft or ransomware.
- **No restore has ever been tested.** Eleven months of files nobody has opened.

---

## ⭐0b — MARG PIPELINE — tidy when convenient (nothing deletes)

`D:\Downloads\margsync\MargPull\CLEANUP_DRIVE.bat` (manojz) ·
`F:\My Drive\Clinic Data Archive\ToMedical\CLEANUP_MEDICAL.bat` (medical) ·
empty `D:\Downloads\margsync\_to_delete\` · sync the repo's stale
`deploy_kits/S182_C1a/deploy/vps_deploy.sh` to the live one.

**The 60-second check:** `D:\Downloads\margsync\MargPull\_last_pull.txt` ·
`H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt` ·
`D:\Downloads\margsync\MARG_PICTURE.txt`. Full flow in `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md`,
**which now carries the 26-Aug guest-access fault by symptom.**

---

## ⭐1 — CLAUDE BUILDS NEXT (your stated order at the S202 close, "max on yr own")

1. **The pen-drive backup (⭐0a)** — find why the automatic backup produces nothing, get it to daily,
   add an offsite leg via Drive, and **test one restore**.
2. **D350 at the scope you set:** §2 verification at both ends · §3 the B2 states · §4 the reinstall
   kits (**Marg and its data first**) · §5 documents (done at S202 — verify, don't redo).
   **§1 the Drive fallback is PARKED at your ruling.**
3. **The expectations file** — what report is due, by when, for every type.
4. F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 ·
   **Staff Console Phase 0** (your four rulings owed) · **Purchase Portal D335** as the other flagship.

**Parked at your ruling:** the Drive fallback transport · the `/ops` runbook surface (B2 delivered
much of what it was for).

---

## ⭐2 — THE AUGUST CLOSE — the first fully live, ENFORCED run

Pravesh's exit · Darpan's SPECIAL + ₹3.55L schedules · 3 auto-recoveries · Shivani's two items · the
first suspended-charge cancel/collect cycle · AF-3's scan. **Watch, don't assume.**

---

## ⭐3 — BLOCKED, NOT FORGOTTEN

The no-clinic-ID bills (49, ₹51,868) → the **Docterz EMR migration** (match key
`bill_date + patient_name + phone_last4`, last-4 only per F-86; **a re-apply wipes that day's parked
list**) · **Lab PC / Labmate** (survey first; S181 warns the revenue arithmetic is INVERTED between
medical and clinic/lab) · **AF-1 still armed** on the medical sender, kept deliberately as the only
medical-side fallback.

**Also outstanding from the S202 sweep:** `C3`–`C8` from `S201_PARKED_BACKLOG` were never minted as
F-numbers · the **AF-# series has no bridge to the F-# register** (AF-5 unaccounted for anywhere) ·
`SYSTEM_DOC_COVERAGE_MAP` has no row for clinic-finance, Marg, the medical PC, manojz or the Lab PC ·
the later **Daily Flow v2 stages** (D-R returns · 360 · orthotics · D5 · D6) have no recorded status
since S189 — neither built nor cancelled. Full detail in `S202_PENDENCY_AUDIT.md`.

---

## HOUSEKEEPING

- ~~COLD KIT DUE~~ → **TAKEN at the S202 close** and, for the first time, **restore-tested**:
  extracted to a clean directory, `md5sum -c` exit 0, 214 OK.
  `D:\dr-manoj-git\cold_kits\DrManoj_Clinic_FULL_Handoff_Session202_2026-08-26.zip`
- ~~Three S201 docs owed their repo filing~~ → **DONE, S202.**
- ~~`END_OF_SESSION_PROMPT` v8 / A8b owed~~ → **not needed.** A8b already exists in v7 and was
  followed; F-184 was a failure to follow it, not a gap in it.
- **Owed at the S203 close:** file `S202_PENDENCY_AUDIT.md` and the D350 contract to the repo (F-107).

---

## DONE (recent)

- **S202:** ~~the pull dark for 8h40m~~ (guest-access block, fixed by authenticating) · ~~Darpan's
  drawer ₹20,000~~ (F-187, settled by your physical count) · ~~the statement page lying about his
  payroll~~ (D349B) · ~~the exceptions card still saying "variance"~~ (D349A) · ~~no visibility of
  your machines from the server~~ (B2, both halves) · ~~a stale heartbeat read as a live watcher~~
  (B2C) · ~~every report called REPORT_1.XLS~~ · ~~56 phantom missing days~~ (S202_PICTURE) ·
  ~~F-184, twelve canonical documents absent from the folder Phase 0 verifies~~ · ~~`.gitattributes`
  never pinned `*.md`~~ (F-190) · ~~the 12-June report~~ (arrived, ACCEPTED, **deliberately NOT
  applied** — you were right).
- **S201:** 11 stranded reports rescued · the outbox had no sender · D347 · D348.
- **S200:** July salary LOCKED ₹59,163 · Portal-PWA unification.
