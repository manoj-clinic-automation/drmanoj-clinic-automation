> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — `SYSTEM_DOC_COVERAGE_MAP` ADDENDUM · SIX ROWS TO FOLD IN AT THE CLOSE

**DRAFT — nothing here has been applied.**

`SYSTEM_DOC_COVERAGE_MAP_S147.md` is **manifest-pinned at `50085e7564cb83476a6f587782143048`**
(verified today against `deploy_kits/KB_canon_all/SYSTEM_DOC_COVERAGE_MAP_S147.md`). **It was not
touched.** Editing it outside a close would change its hash and **halt Phase 0 on the next session**
(D172/D188). These rows are staged here for the owner to fold in deliberately, at a close, with the
manifest row updated in the same pass.

**Why they are owed.** The map is the project's designated answer to *"where is the reference for
tool X"*. It has **23 rows and not one** for clinic-finance, Marg capture, the medical PC, manojz,
the Lab PC or backup/DR — verified. It is dated **S147**; the entire estate below was built from
**S179 onward**.

**Format:** the map's own `| System | Repo | Authoritative doc | Status |`, with its own legend —
✅ wholesome single reference · 🟢 well-covered by a living spec · 🟡 operational-only ·
⚠ scattered, consolidation candidate · 🔴 *(added here)* under-protected, action owed.

**Section to fold into:** *Active systems (Tier 1 — spec/SOP + code is the reference)*, except the
Lab PC row, which belongs under *Forward (not yet a system)*.

**Every md5 below was computed with `md5sum` on this machine on 26-Aug-2026.**

---

## The six rows

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **Clinic-finance** (Sanjeevni + clinic daily money: entry · approvals · day page · health · month close) | `finance/` — *working tree is S180/S182-stale; the LIVE bytes are recovered by md5 from `deploy_kits/` per the pin list* | **Split, and no single document answers "how does clinic-finance work".** **STATE:** `KB_Register` live-file table — `KB_Register_v5_54_S202.md` `8fede84d7126e13fca17418e449f9d0a` + `live_pins_S202close.txt` `374bf3c547a08b19b5fba0e79c14819e` · **MECHANISM (ingest only):** `MARG_INGESTION_REFERENCE_v1.md` `4d603b727a91a7c782992f092fc949e3` · **DESIGN + RULINGS:** `S179_Finance_LIVE_State.md` `54cb25a88adc5692360341113a87a43e` (D313 and the invariants) | ⚠ **Split ownership — and the manifest names only the design document.** `S179_Finance_LIVE_State` is S179-era and **describes the Marg adapter as something that *"needs its own adapter"***, i.e. unbuilt — it is **authoritative on design and out of date on state**. The row must name both and say which answers which. **No consolidated reference exists for the non-Marg half** (entry, approvals, day page, month close); that is a real gap, not a filing error |
| **Marg capture & transport** (capture → route → archive → send) | `margpull/` — ***mirror is STALE**: `marg_watch.py` = `25126388e6841ab38202811d2b940d6a`, the PDF-blind old watcher* · `deploy_kits/S195_MARG` · `deploy_kits/S202_PICTURE` · `deploy_kits/S202_B2B` · **`deploy_kits/S203_MARG_CANON`** | **Read first:** `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` `579ea885e440e76af73de3ecc4542d71` (**§0.1 decides which document wins when two disagree**) · then `MARG_PIPELINE_REFERENCE_v1.md` `97b3cf73f7f83c0860bde2d911596ff7` (how it works) and `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` `c2b5251f55762490ad219b8855a18dd8` (faults by symptom). **Retired documents → `S203_MARG_DOC_POINTERS.md`** in `deploy_kits/S203_MARG_CANON/` | ✅ **wholesome set.** Two conditions attach: **(a)** strike the *"SOLE reference"* label on `S195_Medical_Watcher_LIVE_Reference` (`885090ab946b61e7b5a990a14a190a15`) **when this row lands** — two pinned documents each claiming to be *the* reference is the confusion this map exists to end (C5 / N3, both open); **(b)** `deploy_kits/S203_MARG_CANON` is **not yet manifest-pinned**, so Phase 0 does not verify it — pin it in the same pass (F-184) |
| **The MEDICAL PC** (`MEDICAL` — the Marg host: `medical_agent.py` · `marg_watch.py` · `SEND_TO_CLINIC.bat` · **two output trees**, one on `D:` and one at `C:\Users\Public\MARG\`) | `deploy_kits/S203_MARG_CANON/S195_medical_kit` — **and `medical_agent.py`, `xlsx_stdlib.py` and `medical_census.py` are in NO repo path at all** | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` **§1.1 and §3** `579ea885e440e76af73de3ecc4542d71` · `S203_MEDICAL_PC_PINS.md` `976a6f0ccc22318a603d055f81541f71` in `deploy_kits/S203_CENSUS_BACKUP/` (**the first live pins ever taken on this machine**) · **D347** for the architecture — *with its "Tailscale is not load-bearing" clause **known-wrong**, master §1.5 / §9 #6* | 🟡 **operational, with a recovery gap.** **Until S203 no pin of any kind covered this machine**, and **three live files still have no off-box copy**. The mirror on manojz never purges, so it shows files the machine does not have — master §3.1 lists six things it wrongly implies. **Take pins from `FromMedical\CENSUS.txt`, not from this row**; §3.2's values are a dated snapshot and every kit install invalidates them |
| **manojz** (Dr Manoj's PC — publisher + 10-minute puller + mirror + offsite, **all in one box**) | `margpull/` · `deploy_kits/S202_PICTURE` · `deploy_kits/S202_B2B` · `PUBLISH_ALL.bat` (D328) | `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` **§1** `c2b5251f55762490ad219b8855a18dd8` — **the 60-second check: three files, none needs a login** · `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` **§1.2** · `S203_MARG_CODE_TRUTH_MAP.md` `4a7ff0a62eff51ed2c61e3aab3aa2e8b` for what the code actually does | 🟡 **Named single point of failure.** The Auditor's Surface B records manojz as *"publisher + puller + mirror + offsite in one box"* — **audit slice 4, never run**. Also: the operational copy of the maintenance flow sitting at `D:\Downloads\margsync\` is the **S201** version and **does not contain the fix for the outage that produced it** (master §9). **Until `PUBLISH_ALL.bat` runs, the repo is committed locally only — the "second store" is one disk** |
| **Lab PC / Labmate** (pathology) | — **none** | **NONE. There is no authoritative document, and this row exists to say so.** The only canonical document that names Labmate at all is `Clinic_Source_Data_Retention_Policy_v1.md` `90831162f985359b69725b1dc874e679`, and only for export retention — **it does not describe the system** | ⚠ **NOT A SYSTEM YET — survey before any build.** Standing warning, from S181: **the revenue arithmetic is INVERTED between medical and clinic/lab** — *"the single most dangerous copy-paste in the build."* Attach a source as **a profile + signatures, never a copied script**, and **ask where Labmate writes** — Marg had two output trees on two different drives and one of them went unnoticed for ten days |
| **Backup & disaster recovery** | `deploy_kits/S203_MARG_CANON` (documents only) · `finance/finance_backup.sh` `efe6f1b527bffafc21062bc352a063ee` (the VPS books — **a different subject**) | `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` **§5** `579ea885e440e76af73de3ecc4542d71` — ***this section did not exist anywhere before S203*** · **STATE:** `FromMedical\BACKUP.txt` on the machine and the heartbeat's `BACKUP` line · **exports only, and still a DRAFT awaiting approval:** `Clinic_Source_Data_Retention_Policy_v1.md` `90831162f985359b69725b1dc874e679` | 🔴 **The least-protected part of the estate.** `D:\MARGERP\Data` **cannot be copied consistently while Marg is running** — no copier can. The only unattended-safe artefacts are `serverbackup\` and a human-made `.mbk`. **No restore has ever been tested.** Ownership is split by design: the **master owns the database**, the **retention policy owns the exports** — keep them apart. **`Fault_Action_Register_v2_41.md` `4883e3bdf08cba92da7597448e00f2da` F-191(c) is wrong on the diagnosis** — it says the backup *"was configured … and has never once run"*; the machine says **nothing in Task Scheduler and nothing at startup runs a backup at all**. Amend F-191(c)'s wording at the close, or the vendor question built on it wastes the call |

---

## Fold-in notes for whoever applies these

1. **Do not apply this file by copy-paste alone.** Re-hash every md5 above at the moment of folding
   — `S203_MARG_CANON` gained a `S203_MARG_DOC_POINTERS.md` and sixteen banners this session, and
   the master will move again when §4.3's pointer work and the D1–D10 pointer pass land.
2. **Update the manifest row for `SYSTEM_DOC_COVERAGE_MAP` in the same commit as the edit.** The
   pinned hash `50085e7564cb83476a6f587782143048` becomes wrong the instant the map changes, and a
   mismatched row **halts the next session's Phase 0** (D172/D188).
3. **Three rows carry a condition that must land with them**, not after: the *"SOLE reference"*
   label (Marg capture), F-191(c)'s wording (backup/DR), and D347's Tailscale clause (medical PC).
   **A ruling is amended only by a ruling** — D347's fix is a decisions-index correction, not a
   reference edit.
4. **Honest gaps, stated as gaps and not filled with a plausible pointer:** the Lab PC has **no**
   document · clinic-finance has **no** consolidated reference for its non-Marg half · three live
   medical-PC files have **no** repo path.

---

*S203 · 26-Aug-2026 · DRAFT, nothing applied · `SYSTEM_DOC_COVERAGE_MAP_S147.md` was **not** read
into an edit and **not** modified; its pinned hash was verified only · every md5 computed with
`md5sum` this session · no `git` command run (F-131) · no token value read or printed · no patient
identifier reproduced.*

---

> **VERSION NOTE, added 26-Aug-2026.** This was built against master **v3**.
> The current master is **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v4.md`**
> (md5 `df290c6f5cbb870af6c232db21bc2219`). Every section reference still resolves
> — v4 only ADDED section 2.1 and refreshed the section 2 chain table; it
> renumbered nothing. v3 is retained as `...v3.md.superseded_by_v4`.
