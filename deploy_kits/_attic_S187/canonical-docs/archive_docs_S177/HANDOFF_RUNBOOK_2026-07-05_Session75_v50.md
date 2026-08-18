# HANDOFF RUNBOOK — Session 75 · v50 · 2026-07-05

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · with: Claude**
**EOS — CODE CHANGED.** Baseline in: KB v1.38, Umbrella v1.28, Runbook v49 (S74).
Baseline out: **KB v1.39 (delta), Umbrella v1.29 (delta), Runbook v50 (S75).**
**KB wins on any conflict.**

---

## §0 — WHAT HAPPENED THIS SESSION (S75)

> **KIT CORRECTION (same session, re-issued):** the first S75 EOS kit filed
> `clinic_writer.py` under `followup-tracker/`. That was wrong — the PC writer is a
> distinct system. It now lives in its OWN top-level repo folder **`clinic_writer/`**
> (with a README documenting the split), matching `C:\clinic_writer\` on the PC. Code
> is byte-identical (md5 unchanged); only the repo path moved. Session number NOT
> advanced. This runbook + docs are the superseding versions.


Track 1, Step 4 BUILT, INSTALLED, VERIFIED. Plus three architecture pivots that
simplify the whole Track-1 hosting model. Four decisions: **D135–D138.**

1. **Step 1 closed** — owner confirmed v26 Plan-record panel passed a real-Chrome check
   ("all good in v26"). No fixes.

2. **Step 2 closed** — verified the v26 embedded vitals section matches the locked
   `vitals_ledger` 20-column schema (§67.3) field-for-field, in order. No change needed.

3. **THREE PIVOTS (the important part of this session):**
   - **PC-LOCAL, not VPS.** The write-path tool runs on the CLINIC PC, not the VPS.
     Reason chain: the two source CSVs already live on the clinic PC (tracker writes
     them) and sync to Drive; hosting the writer where the data already is avoids
     spreading patient data to a second place, and honours the earlier no-VPS-hosting
     lean. (**D136** — amends D121/D122/D133.)
   - **STAFF BP-ONLY PAGE RETIRED.** Owner clarified the decisive fact: *"I only enter
     the vitals in my PC; staff hand me a physical vitals record."* The second front
     door (D124/D127) has no user — only the doctor enters vitals. Page dropped from
     the Track-1 build entirely. (**D135**.)
   - **PDF STORAGE HOME moves VPS → clinic PC**, then syncs to Drive. Archive STRUCTURE
     (yearly / Patient_UID / Plan_ID naming) UNCHANGED and still locked. (**D137** —
     amends D133.)

4. **Step 4 BUILT — `clinic_writer.py`** (the PC-side single writer). Three jobs:
   write_vitals, write_plan, archive_pdf; plus read-only lookup_uid_by_clinic_id.
   - Computes BMI / category (Indian cut-offs) / waist:height for EVERY vitals row,
     mirroring the plan-tool's compute() exactly. Assigns running IDs
     `V-YYYY-NNNNNN` / `P-YYYY-NNNNNN` (per-year 6-pad). Links Vitals_ID_Used.
   - Append-only; one-writer-per-file; NEVER writes the two read-only source CSVs;
     no network. IST timestamps explicit.
   - **PDF engine = reportlab** (**D138**) — pure-Python, one-command install, no
     Windows system-library fragility; text-faithful archive PDF (fit for a record,
     not a pixel photocopy). Chosen over HTML-render (playwright/weasyprint) which
     needs heavier, fragile Windows setup.
   - `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`;
     new patients → `plan_archive/pending/<Clinic_Id>_<mobile>/…` (D132 paths, exact).

5. **Verified end-to-end on BOTH machines:**
   - Build sandbox (Python 3.12.3): `py_compile` clean; built-in `--selftest` **20/20
     PASS**; real PDF produced (valid `%PDF-` header, ~2 KB) filed to correct folder.
   - **Clinic PC (Python 3.14.5): owner ran `--selftest` → 20/20 PASS; `certutil`
     md5 = `d4e20a51ead1aada8c07bead2b504100` — MATCHES.** Installed and confirmed.

6. **Step 4 closed.** Steps 3 (folder rule) resolved to PC-local; Step 6 (staff page)
   retired. Remaining: Step 5 (front-end), Step 7 (reconciliation).

---

## §1 — STATE

Track-2 live systems: **unchanged** (identical to S64–S74 close — see KB §12). WABA
bridge BUILT+LIVE, sends still BLOCKED vendor-side (D120); `wa_approve` still nohup
(not systemd); key rotation still overdue; health report / watchman / attendance /
follow-up push all live as before.

Track-1 new state:
- **`clinic_writer.py` — INSTALLED on the clinic PC at `C:\clinic_writer\`, verified
  (md5 `d4e20a51ead1aada8c07bead2b504100`), self-test 20/20 on Python 3.14.5.** This is
  the WRITE-PATH LIBRARY — not yet a screen; no front-end wired to it yet.
- reportlab installed on the clinic PC (`pip install reportlab`).
- The plan-tool front-end is still **v26** (offline Thread-A artifact, md5
  `6212ad8fe5072521cadb36b21f190ffa`) — not hosted, not committed to live repo.
- **NOT yet done:** Step 5 (local front-end that imports the three writer functions);
  Step 7 (new-patient reconciliation). Living Clinic Data Map (§66.6) still standing.

---

## §2 — BACKLOG (what to pick up next)

### Track 1 — PC-local plan+vitals writer  ← **NEXT SESSION STARTS HERE**
Engine done and installed. Remaining sequence:

1. **Step 5 — the local front-end (NEXT).** A page on the clinic PC where the owner
   types a patient's Clinic_Specific_Id → it resolves the real Patient_UID from the
   local CSVs (shared-mobile pick-list, D123) → owner enters vitals + plan choices →
   it calls `write_vitals`, `write_plan`, `archive_pdf` to write the two ledgers and
   file the PDFs on the real UID folder + real Plan_ID.
   - **OPEN QUESTION owner was mid-answer on:** how to reach the front-end — a local
     browser page (small local Flask app, key-gated, clinic-Wi-Fi bound), OR folded
     into the existing plan-tool HTML as one combined screen. **Resolve this first
     next session.** (Claude lean: small local Flask app that imports clinic_writer —
     keeps the write-path in Python where it's proven, browser page just collects
     input and posts to it.)
   - Front-end resolves real UID folder + real Plan_ID at write time (offline the tool
     only previews `pending/` + `<Plan_ID>` placeholder — D129).

2. **Step 7 — new-patient reconciliation** (D131). Stitch UID-blank vitals/plan rows +
   `pending/` PDFs to the real Docterz UID once the tracker ingests them (match Clinic
   ID + mobile). Runs on the PC over the local ledgers + archive.

**RETIRED:** Step 6 (staff BP-only page) — D135.
**RESOLVED:** Step 3 (canonical CSV folder) — it's the clinic PC local `data/` folder
the tracker already writes; no VPS folder to find (D136).

### STANDING (surfaces every session until done)
- **📘 Living "Clinic Data Map"** (KB §66.6) — one exhaustive pass of the ENTIRE data
  structure incl. the verified Docterz headwater + the `plan_archive/` PDF store +
  the two PC-local ledgers. Update on every file/column/writer change.

### Track 2 — live-systems backlog (unchanged)
1. **🔴 WABA authorizer fault (D120)** — Lokesh must fix MyOperator publicapi AWS
   gateway; blocks ALL WABA sends; re-fire TEST when it clears. AWS request-id
   `eb82db53-47b2-48f1-b744-027a754be56c`.
2. **Make `wa_approve` a systemd service** (`wa-approver.service`) — nohup dies on SSH
   close; add to watchman.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** — true-identical rows; `inspect_dupes.py`; sender
   unchanged (D119).
5. Arm timer-freshness checker + maintenance jobs; verify & close "Agent shows as
   Staff"; `call_transcription.py` GitHub commit; Stage-3 AI verdict layer;
   clinic_health_report UTC→IST fix; v12.xlsm audit fixes; GitHub commit S59–S64;
   data pass; P1–P10 lock; D78 sticky counter.

---

## §3 — DECISIONS THIS SESSION (D135–D138)

- **D135** — **Staff BP-only page RETIRED** from the Track-1 build. Only the doctor
  enters vitals (staff hand him a physical vitals record); the second front door
  (D124/D127) has no user. Supersedes the staff-page portions of D124/D127/D131.
- **D136** — **Track-1 write-path hosting = PC-LOCAL**, not VPS. The writer runs on the
  clinic PC, reads the tracker's local `data/` CSVs, writes local ledgers + PDF archive;
  Google Drive sync carries the outputs to Drive. Amends **D121** (no Flask+OLS/VPS for
  this tool) and resolves **D122** (canonical source = clinic-PC local `data/` folder,
  newest-by-date rule still applies).
- **D137** — **PDF + ledger storage home = clinic PC** (then Drive sync), not VPS.
  Amends **D133**. Archive STRUCTURE (D132) unchanged.
- **D138** — **PDF engine = reportlab** (pure-Python, text-faithful archive). Chosen for
  durability + one-command Windows install over HTML-render engines (playwright/
  weasyprint) which need fragile Windows system libraries.

Reserved: D83–D92 for P1–P10. **Next free decision number: D139.**

---

## §4 — FILES / CANONICAL SET AFTER THIS SESSION

- **KB:** `Clinic_Master_KB_SystemsRegister_v1_39.md` (delta over v1.38).
- **Umbrella:** `Dr_Manoj_Clinic_Umbrella_Architecture_v1_29.md` (delta over v1.28).
- **Runbook:** this file (v50).
- **NEW CODE:** `clinic_writer.py` (md5 `d4e20a51ead1aada8c07bead2b504100`) — PC-local
  write-path; committed to Git under its OWN top-level folder `clinic_writer/`
  (deliberately separate from `followup-tracker/` — two distinct systems; a README
  in the folder documents the split). Code md5 unchanged.
- **Plan-tool artifact:** `rehab_nutrition_plan_v26.html` (md5
  `6212ad8fe5072521cadb36b21f190ffa`) — offline, unchanged.
- Git commit zip + cold-kit zip produced this session.

---

## §5 — INSTALL RECORD (for audit)

`clinic_writer.py` placed at `C:\clinic_writer\` on the clinic PC. `pip install reportlab`
run. `python clinic_writer.py --selftest` → **20/20 checks passed** (Python 3.14.5).
`certutil -hashfile clinic_writer.py MD5` → `d4e20a51ead1aada8c07bead2b504100` (matches).
Confirmed by owner 2026-07-05. Manual fallback (print from browser, no archive) remains
available and unchanged until the front-end is live.
