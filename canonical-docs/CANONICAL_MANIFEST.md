# CANONICAL MANIFEST — Dr. Manoj Agarwal Clinic (Tier 0 · linchpin)

**Bareilly · maintained with Claude · governs the canonical document set (D247).**

**STATUS: prepared at S149 close — becomes fully canonical when the owner installs this set (project-knowledge swaps + GitHub push, per the S149 install/push runbook).** **The S150–S158 EOS deltas (through Register v3.1, Archive v1.10, Runbook v96, START_HERE_SESSION_159, Fault Register v2.4, the four S157 docs, this manifest, plus live VPS code: the six S158 SSO files `portal.py`/`clinic_sso.py`/`clinic_users.py`/`att_dashboard.py`/`asset_register.py`/`staff_ledger.py`, and earlier staff_ledger v3.1 + watchdog) fold into the same pending doc install/GitHub push — install/commit them together.** The restructure (D247 + KB split) is live: `KB_Register` + `KB_History_Archive` replaced the retired monolith `Clinic_Master_KB_SystemsRegister_v1.72` (md5 `27b72639…`) in the session loop, alongside EOS prompt v4 and the four frozen-product dossiers. This manifest is the linchpin Phase 0 verifies. *(The whole S149 set installs together — until it does, project knowledge still holds the pre-S149 copies.)* **S159 UPDATE:** the S150–S158 install has LANDED (Phase 0 verified all rows). This EOS folds S159 on top — swap in `KB_Register` v3.2, `KB_History_Archive` v1.11, `HANDOFF_RUNBOOK` v97, `START_HERE_SESSION_160`, `Fault_Action_Register` v2.5, this manifest; and commit live `portal.py` `679a00874c039ecabc533f9ddd0f5e67`.

> **Phase 0 read rule (every session).** Verify **every** row below by md5 (cheap — hash compare only). **Read into context only Tier 0.** Tier 1 is opened on demand when the session's task touches it. Tier 2 is hash-verified but never read in the loop and never edited without an explicit waiver (D34 discipline). *A row whose md5 does not match halts work until reconciled (D172/D188). If a "pending" item looks done, verify it against reality first.*

---

## Tier 0 — session loop (read at start · rewritten at end)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `CANONICAL_MANIFEST.md` | S160 | *(self — recomputed last, each EOS)* | this file; the linchpin |
| `START_HERE_SESSION_161` | S160 | `66efd49ca82360db393ef0993c7f637a` | entry point; regenerated every close-out (was `START_HERE_SESSION_160`) |
| `KB_Register` | v3.3 | `89d060bf371773a46859e0c6c1ad0afa` | current state; from v1.72 (`27b72639…`). **v2.8→v2.9 (S156):** D259 indexed; F-51/F-52/F-53 minted; salary system v3.1 + watchdog live-state recorded; Archive pointer → v1.8. **S158 → v3.1:** SSO portal live end-to-end; §S158 state block added; D264–266, F-57/58; Archive ptr → v1.10. **S159 → v3.2:** portal Group D + personal tiles + GMB VPS-hosted (`portal.py` `679a0087…`); §S159 state block; D267–269, F-59/60/61; Archive ptr → v1.11; Fault ptr → v2.5. |
| `HANDOFF_RUNBOOK` | v98 (S160) | `8cbff4c481a62980fa634c3ebb59172a` | §0 what happened · §2 live backlog (was v97); file `HANDOFF_RUNBOOK_2026-08-09_Session160_v98.md` |
| active incident | — | — | **only while open**; none open (F-44 closed) |

## Tier 1 — reference (hash-verified · read only if touched · rewrite only if changed)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `KB_History_Archive` | v1.12 | `5c3cfd294184b175723db852172894df` | all history, verbatim; from v1.72 (`27b72639…`). **§S156 appended (S156)** → re-pinned (was `3cd2d940…`); pure-append proven by prefix hash (+10,709 chars). **§S158 appended (S158)** → re-pinned (was `f885596a…`); pure-append proven by prefix hash (+11,025 chars). **§S159 appended (S159)** → re-pinned; stale top header fixed v1.9→v1.11; pure-append proven by reconstruction-diff to the pristine v1.10 (all 4,466 prior lines byte-identical). |
| `Dr_Manoj_Clinic_Umbrella_Architecture` | v1.58 | `728cc64950502011ff220e1249e488ce` | strategy + decisions log |
| `Call_Console_Evolution_Spec` | v2.4 | `63978d982d1f8037f728023d15a01328` | dashboard-as-dialer (active) |
| `Frontend_Dashboard_Documentation` | v4 (S140) | `02ef929b75aa77ec071c903705335375` | dashboard still evolving |
| `Diagnostics_Surveillance_System_Spec` | v2.3 | `bdd5fa5479a57dfb73fa653054a3f329` | fault codes / detection |
| `Maintenance_SOP_System_Spec` | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` | forward-looking (project not live) |
| `API_QUICK_REFERENCE_CARD` | — | `68c4fc344bf74caaea706149cd22e64c` | small + stable. **In the repo since S148** (`canonical-docs/`, byte-identical to project knowledge — verified S149). |
| `AI_Verdict_Layer_Master` | v1 (S145) | `bd4b67f6810cd2316eb58dfe6bf180cd` | Product B analytics |
| `Clinic_Callback_Tracker_AppsScript_Audit` | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` | **unfinished audit** (Pass 4 not started); reference only — NOT the frozen dossier |
| `Fault_Action_Register` | v2.6 | `6e90861ef72b86536cff5b3b9f9a210b` | **v2.2 (S156):** §7 Later-Findings index added (F-45..F-53; full text in the Archive); F-51/F-52/F-53 recorded; no lane/procedure changed; re-pinned (was `3bfeac72…`). Push refreshed file to the GitHub mirror. **v2.4 (S158):** F-57, F-58 recorded (SSO session); §0–§6 unchanged. **v2.5 (S159):** F-59/F-60/F-61 recorded; stale end-marker v2.3→v2.5 fixed; §0–§6 unchanged. |
| `Clinic_Estate_Master_Inventory` | v1.7 (S157) | `3668a9150d1c88017e46861c615aab3e` | **NEW S157.** Complete reconciled cross-project app+service estate; supersedes S63-era App_Service_Register for the automation core (D260). |
| `Clinic_Portal_SSO_Architecture` | v1 (S157) | `0c843bb64d579205d8c64946721c10f6` | **NEW S157.** SSO broker + shared verify-shim; `.dr-manoj.in` cookie; app logins as fallback (D261). |
| `Clinic_Portal_Build_Plan` | v1 (S157) | `3d6468cb4927d5d77d7a7d687ffabfe7` | **NEW S157.** Doctor/manager tile rosters + per-app selection; local apps = PC-only group (D262). |
| `Salary_System_KB` | v1 (S157) | `71bb915dff0dac26fe20192b91cd3940` | **NEW S157.** Staff Ledger + backend salary automation reference (D263); system only, F-31. |
| `Staff_Daily_Register_Dossier` | v1.0 (S160) **DRAFT** | `84fe26dd39baafb4305e803e28ed8608` | **NEW S160.** Staff Daily Register subsystem design (**D271**) — daily maker-checker capture + yearly balances + history-aware staff record + uniform/i-card issuance + salary-engine changes. Sign-off pending; becomes non-draft on owner approval. |
| `END_OF_SESSION_PROMPT` | v4 | `9fa2be50c527865982f195d347ab0283` | the close-out routine |
| `INCIDENT_2026-07-14_…_F44` (closed) | — | `774898e80fac3e006d80e8c2f77488e6` | history; consult on demand |

## Tier 2 — frozen products (hash-verified only · never in the loop · waiver to change)

Each frozen product has one canonical **dossier**; this is the FROZEN ledger. **Four** products (was five — Consent HTML reclassified, see below).

| Product | Dossier | Dossier md5 | Artefact (the live thing) | Artefact md5 | Frozen | Waiver |
|---|---|---|---|---|---|---|
| WABA templates | `WABA_Approved_Templates_v1_S137.md` **(adopted)** | `63dd1883ed6677bc96620c087fc1d154` | MyOperator panel — 14 approved | compute at freeze | S147 / D247 | Meta re-approval + bump |
| Attendance system | `Attendance_System_Dossier_v1_2_S153.md` **✓ built** (v1.2 folded the S153 report layer at close-out) | `bf19179181c553777e4cc8e3834bc754` | `attendance/` folder + VPS deploy + `att_month_report.py` (additive report layer: **v2.5 `e64cad19…` INSTALLED + July-verified S154**; v2.4 `608f2a90…`, S151 v1 `c9251988…` superseded). Companion (non-core) files S154: `build_staff_master.py` v2 `9fe81d7b…` (owner PC), Staff Ledger app `staff_ledger.py` **v2.4 `74dac84eb15f5172478a97066f56c99d` (S155, selftest 123 — D258 single home for all staff money incl. Darpan loan)** (VPS, own systemd — a separate live system tracked in the Register, not part of this frozen product) | 10-file frozen-core digest `dc12f4a0…` byte-unchanged; **full-folder re-pin DONE S155: `c4c9c83f44fbbbb39609047671e77d60`** (11 files; recipe `md5sum attendance/* \| sort \| md5sum`, rediscovered+proven S155) | S151 / D251 | frozen core: explicit waiver + bump; additive report layer sanctioned S151, extended S153 (owner-directed) |
| Nutrition/Diet (`clinic_writer`) | `Nutrition_Diet_clinic_writer_Dossier_v1_1_S150.md` **✓ built** | `6900ff40d43da0013f6ea81c3c31a0e4` | `clinic_writer/` folder + PC `D:\clinic_writer\` | `fcedae30…` (`vitals_page.html` v28; **folder digest re-pinned S155: `1b4f0f2299cd6c9e72b6d04f45847556`**, repo confirmed at v28, was `df0b0c34…`) | S147 / D247; **waiver exercised S150 / D248** | explicit waiver + bump |
| Callback Tracker **core** | `Callback_Tracker_Core_Dossier_v1_S147.md` **✓ built** *(scope pending confirm)* | `7e445ff04f086af0fdce656b1eae5dc1` | live Apps Script project (`WebApp.gs` D34 + core `.gs`) + Sheet `1USj…klo0` | `e4fd4512522c2e2723cb50690b92c5e8` (live project digest) | S147 / D247 | explicit waiver (D34) + bump |

**Deferred — NOT frozen (future Tier 2 candidate):**
- **Consent HTML** — reclassified S147: folded into the still-in-development **Surgical Estimate tool** (clinic-growth workstream; not yet in GitHub). It is dossiered + frozen only when that tool completes development and ships to the repo. Until then it is neither frozen nor in the session loop.

*Note: the Callback Tracker **Console/Dashboard** (`Callconsole.gs`, `Dashboard.html`) is NOT frozen — it stays active under Tier 1 (`Call_Console_Evolution_Spec`, `Frontend_Dashboard_Documentation`). Only the tracker **core** freezes (confirmed S147).*

---

## Companion

- `SYSTEM_DOC_COVERAGE_MAP_S147.md` (md5 `50085e7564cb83476a6f587782143048`) — every subsystem → its authoritative doc; answers "where's the wholesome reference for tool X". Read on demand.
- `README_CANONICAL_SET.md` (repo `canonical-docs/`) — **refreshed S149** to the post-restructure tiered model. A repo-navigation doc that carries no version numbers and defers to this manifest; it is not a Phase-0-verified canonical row.

---

## Governance

- **D247** (the tiering + Register/Archive split + this manifest) lives in the KB Register's decisions index/changelog — **added to the index at v2.2 (S149); housekeeping closed.**
- **Provenance rule:** every md5 here is computed from the live artefact; none is assumed (D172/D188). "compute at freeze" = a real hash still owed, not a placeholder to skip.
- **Install:** the whole S149 set installs together (project-knowledge swaps + one GitHub push). Until then, project knowledge holds the pre-S149 copies and this STATUS reads "prepared."

### S149 changelog (this close-out)
- **Tier-0 loop rows corrected** to the live set — they had drifted to the S148-*open* set (`START_HERE_148`, `KB_Register` v2.0, `HANDOFF_RUNBOOK` v85) because the S148-*close* manifest update was missed. Now: `START_HERE_SESSION_150`, `KB_Register` v2.1, `HANDOFF_RUNBOOK` v87.
- **F-45 fixed:** `Fault_Action_Register` v2.1 gained its missing CHANGELOG row (§0.35 / D204, S132); re-pinned `fde74c…`→`3bfeac72…`.
- **Archive:** **§S147 backfilled** (from Runbook v85 §0 + `D247_Canonical_Data_Management_S147.md`) and **§S149 appended**; re-pinned `44681d05…`→`b369f88d…`.
- **Repo-mirror backlog resolved / verified:** `API_QUICK_REFERENCE_CARD.md` + `WABA_Approved_Templates_v1_S137.md` were already in the mirror and byte-identical (md5s match these pins) — struck, not re-pushed. `README_CANONICAL_SET.md` refreshed.
- **Repo tidy (Phase 2):** `Repo_Trim_Phase2_S149.ps1` produced — archives 38 superseded docs (3 canonical-docs stragglers + 35 historical `docs/`); **12 live/uncertain clinic + reference docs held** for owner confirmation.
- **Register v2.1 → v2.2 (housekeeping closed):** findings line advanced (F-45 RESOLVED → next free F-46); D247 added to its decisions index. **§S149 appended to the Archive; runbook v87 + `START_HERE_SESSION_150` generated.** No decision minted.
- **Next free: D249 · F-46 · Session 151.**

---

### S150 changelog (this close-out)
- **Tier-2 waiver exercised (D248):** `clinic_writer` unfrozen for one owner-approved batch, then re-frozen. `vitals_page.html` **v26 → v28** (md5 `fcedae303b620f3e5199f4b1e4766510`), installed live on `D:\clinic_writer\`: Hindi spelling tidy (closes the dossier caveat) · exercise library 126 → 128 · PIVD stop-rule · bottle-roll dose · Excel `Diet_Chart` ported as an optional printable **diet-aware** diet sheet (no shopping list) · a **screen-only** comfort theme (print byte-identical). Engine/app/ledger schemas untouched.
- **Nutrition dossier → v1.1** (`6900ff40d43da0013f6ea81c3c31a0e4`): caveat closed, v28 recorded, folder-digest recompute owed at install.
- **Tier-0 rows bumped:** `KB_Register` v2.2 → **v2.3** (`63440a8114403e66eeb7af5f08746586`, D248 indexed); `HANDOFF_RUNBOOK` v87 → **v88** (`6eba948c13b7c23d76741a5c4e91f09b`); `START_HERE_SESSION_150` → **`START_HERE_SESSION_151`** (`830cb5c4bc151ec96e60ba4410347f2a`).
- **Archive:** **§S150 appended** → **v1.2** (`68b2f52b8aa766a82da80cecf0fb6c4b`); re-pinned (was `15196ec3…`).
- **No new finding** (the `cond`-scope slip was self-introduced during the build and fixed before delivery — a lesson, not a fault). **No architectural decision beyond the waiver D248.**
- **Owed at install (S151):** recompute the `clinic_writer/` folder digest on the installed folder and re-pin it here + in the dossier (one file changed; the specific `vitals_page.html` md5 is the pinned truth meanwhile). The S149-owed doc install/push + the 12 held `docs/` files still stand.
- **Next free: D249 · F-46 · Session 151.**

---

**END OF CANONICAL_MANIFEST — S150.**

### S151 EOS (05 Aug 2026, FULL — one new live VPS file)
**S151 canonical filenames (Phase-0 mapping):** `KB_Register_v2_4_S151.md` · `KB_History_Archive_v1_3_S151.md` · `HANDOFF_RUNBOOK_2026-08-05_Session151_v89.md` · `START_HERE_SESSION_152.md` · `Attendance_System_Dossier_v1_1_S151.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.3 → **v2.4** (`a8fee1a4ff7c4219f1d8182cefa84785`, D249–D251 indexed; F-46); `HANDOFF_RUNBOOK` v88 → **v89** (`1d21546ba845899c1bec562c162ed905`); `START_HERE_SESSION_151` → **`START_HERE_SESSION_152`** (`199d39a438b9b4447421ee21c23f1883`).
- **Archive:** **§S151 appended** → **v1.3** (`68109ea651c91060fd0e0ba68a9a889d`); re-pinned (was `68b2f52b…`).
- **Tier-1:** Attendance dossier v1 → **v1.1** (`6525e2c8298db2ea02000245ebd498e7`) — `att_month_report.py` (`c925198895ea146b37a0c69b0ef85b6b`) pinned as an ADDITIVE salary-report layer; frozen 10-file core byte-unchanged; folder-digest re-pin owed at the repo commit. All other Tier-1 unchanged.
- **Live additions:** VPS `att_month_report.py` (`c9251988…`) · `staff_master.csv` rebuilt (`f8f3a23908d2007ccdc1bd9af5e87725`, 12 salaried staff).
- Notion catch-up owed (connector absent S151). **Next free: D252 · F-47 · Session 152.**

### S152 EOS (06 Aug 2026, FULL — no VPS/live code; owner-side salary-workbook product change; three policies locked, one drafted)
**S152 canonical filenames (Phase-0 mapping):** `KB_Register_v2_5_S152.md` · `KB_History_Archive_v1_4_S152.md` · `HANDOFF_RUNBOOK_2026-08-06_Session152_v90.md` · `START_HERE_SESSION_153.md` · this `CANONICAL_MANIFEST.md`.
- **Numbering correction recorded (D172):** the S152 chat labelled its decisions D251–D254; canonical mints are **D252–D255** (D249–D251 were spent at S151). Notice filenames carry the wrong D-prefixes — cosmetic (D188).
- **Tier-0 rows bumped:** `KB_Register` v2.4 → **v2.5** (`c61d25d28288c6016527428c6b8fd266`, D252–D255 indexed); `HANDOFF_RUNBOOK` v89 → **v90** (`f6d2fb50afa6608c11766ad410b492cb`); `START_HERE_SESSION_152` → **`START_HERE_SESSION_153`** (`9996a15592378ee9bd1358af3589eef8`).
- **Archive:** **§S152 appended** → **v1.4** (`fbe348a4d9ddf6962df3a7741872016f`); re-pinned (was `68109ea6…`).
- **Tier-1/Tier-2 documentation unchanged** (no spec touched; no waiver exercised). **Owner-side product change, F-31 non-repo, pinned in the Register only:** `Salary_System_2026.xlsx` v3 (Darpan-integrated, as-delivered `3dfe5bea7a559740fc239323ecc85319`, owner-installed); `Darpan_Loan_System_v2_3.xlsx` RETIRED; attendance notice v5 FINAL `f2de5527385800c3122cd0209d32fb67` (print artefact, posting pending).
- **Carried:** attendance-dossier folder-digest re-pin (report script now in the repo, owner-done) · clinic_writer digest re-pin · `wa_approve` systemd **verify-first** (record conflict logged S152) · Notion catch-up **S151+S152**.
- **Next free: D256 · F-47 · Session 153.**

### S153 EOS (07 Aug 2026, FULL — attendance report layer v2→v2.5; notice v6; staff_master v2 installed; frozen core untouched)
**S153 canonical filenames (Phase-0 mapping):** `KB_Register_v2_6_S153.md` · `KB_History_Archive_v1_5_S153.md` · `HANDOFF_RUNBOOK_2026-08-07_Session153_v91.md` · `START_HERE_SESSION_154.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.5 → **v2.6** (`5cab7efcd268c25469f0970d52273804`, D256 indexed, F-47/F-48 minted); `HANDOFF_RUNBOOK` v90 → **v91** (`c7758ec4468e76622074470d7056baee`); `START_HERE_SESSION_153` → **`START_HERE_SESSION_154`** (`e08ef431fb99fea2947385ae2fd6b6ae`).
- **Archive:** **§S153 appended** → **v1.5** (`591fd4bbd2797103865e6cfc733bbe57`); re-pinned (was `fbe348a4…`); pure append proven by prefix-hash equality.
- **Tier-2 Attendance row updated (no waiver needed — additive layer sanctioned S151, owner-directed S153):** `att_month_report.py` **v2.4 `608f2a90bf9ff65f196ac4f2f13c00bb` INSTALLED on VPS + July-verified; v2.5 `e64cad19d135618dec1413553e6bdc80` delivered, INSTALL PENDING** (first backlog item). `staff_master.csv` v2 **`3b1ebcb1e339fdcdb8b47389ee206108` INSTALLED** (+sunday_group/+minutes_exempt; workbook + `build_staff_master.py` columns owed). Frozen 10-file core byte-unchanged. **Dossier → v1.2 `bf19179181c553777e4cc8e3834bc754` (folded at close-out; supersedes v1.1 `6525e2c8…`).**
- **Owner print artefacts (Register-pinned, non-repo):** attendance notice **v6 FINAL `b29dfa1317024d1d622d79d6de6f5c17`** (PDF `ca8216b3…`) supersedes v5; `Staff_Rate_Card_v2_S153.xlsx` `8e9cf6462d63b9d229bcbf973d25f88c` (F-31 home `D:\clinic_salary\`).
- **D256** consolidated attendance computation rules (full text Archive §S153); **F-47** double-punch artefact; **F-48** shadow-write / diff-audit rule.
- **Carried:** folder-digest re-pins (attendance at repo commit; clinic_writer) · Phase-2 trim ruling · wa_approve verify-first · key rotations · WABA/Lokesh · **Notion catch-up S151–S153** · **cold kit DUE**.
- **Next free: D257 · F-49 · Session 154.**

### S154 EOS (07 Aug 2026, FULL — Staff Ledger maker-checker LIVE (D257); workbook v4; builder v2; v2.5 install verified; F-49 gitignore gate)
**S154 canonical filenames (Phase-0 mapping):** `KB_Register_v2_7_S154.md` · `KB_History_Archive_v1_6_S154.md` · `HANDOFF_RUNBOOK_2026-08-07_Session154_v92.md` · `START_HERE_SESSION_155.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.6 → **v2.7** (`284ee8c8f5c4f8e768f964d846ec32b2`, D257 indexed, F-49 minted); `HANDOFF_RUNBOOK` v91 → **v92** (`19f3b385a456c8002911a12713140953`); `START_HERE_SESSION_154` → **`START_HERE_SESSION_155`** (`d776bfd45b3c5a7b82533d0d219e9c3d`).
- **Archive:** **§S154 appended** → **v1.6** (`2eaf4f9b072bf7159cb899e9762a9b64`); re-pinned (was `591fd4bb…`); pure append proven by prefix-hash equality.
- **Tier-2 Attendance row updated (no waiver — frozen 10-file core byte-untouched):** `att_month_report.py` **v2.5 `e64cad19…` INSTALLED S154** (md5 + selftest + July rerun + browser verified). Companion files noted: `build_staff_master.py` v2, `staff_ledger.py` v1.2 (separate live system, Register-tracked).
- **New live VPS system (D257, Register-pinned, NOT a manifest row):** Staff Ledger — `staff_ledger.py` v1.2 `478c02984dbb30a330375e3f5899ff97`, `staff-ledger.service`, OpenLiteSpeed `/ledger` context (vhost backup `/root/vhost.conf.BACKUP_S154`), live at `attendance.dr-manoj.in/ledger`; data `/root/staff_ledger/` F-31.
- **Owner-side pins (F-31, Register only):** `Salary_System_2026.xlsx` v4 as-delivered `a8625fd810477765dd9b6dd2678e7d86` (+2 roster columns, installed); round-trip proof: builder v2 output byte-identical to installed `staff_master.csv` `3b1ebcb1…` on sandbox AND owner PC. Docs shipped: `Staff_Master_Update_SOP_v1_S154.docx` `36352247…`, `Staff_Ledger_Briefing_v1_S154.docx` `cf07e468…`.
- **F-49 (gate on the owed repo commit):** `.gitignore attendance/staff_master.csv` BEFORE committing; then commit att_month_report v2.5 + build_staff_master v2 + staff_ledger v1.2.
- **Cold kit REBUILT this EOS** (`DrManoj_Clinic_FULL_Handoff_Session154_2026-08-07.zip`). Notion catch-up owed S151–S154 (connector absent again).
- **Next free: D258 · F-50 · Session 155.**
### S155 EOS (07 Aug 2026, FULL — Staff Ledger v2.4; D258 minted+EXECUTED; Darpan loan migrated live; repo trim pushed; digest recipe documented)
**S155 canonical filenames (Phase-0 mapping):** `KB_Register_v2_8_S155.md` · `KB_History_Archive_v1_7_S155.md` · `HANDOFF_RUNBOOK_2026-08-07_Session155_v93.md` · `START_HERE_SESSION_156.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.7 → **v2.8** (`c96ab2b7735f0b54735d78438d6095c3`, D258 indexed, F-50 minted+fixed, F-49 closed-by-ruling); `HANDOFF_RUNBOOK` v92 → **v93** (`a34795223903c4516e4a24069f667a0e`); `START_HERE_SESSION_155` → **`START_HERE_SESSION_156`** (`541e0f6eab406336be72ab65c078a5c5`).
- **Archive:** **§S155 appended** → **v1.7** (`3cd2d9408aba2bfe90f0c5515495dfd2`); re-pinned (was `2eaf4f9b…`); pure append proven by prefix-hash equality (+10,029 chars).
- **Digest re-pins DONE (recipe documented S155):** attendance full-folder **`c4c9c83f…`** (11 files) · clinic_writer **`1b4f0f22…`** (v28 confirmed in repo). Frozen cores byte-untouched.
- **Live system:** `staff_ledger.py` v1.2 → **v2.4 `74dac84e…`** (five verified installs, selftest 123). **D258 executed:** Darpan loan migrated + rupee-verified; `close 2026-07` run (loan 179,000); workbook Darpan sheets RETIRED; workbook canonical home → VPS `/root/clinic_salary/` (`a0e3b038…`, test perk removed).
- **Repo:** Phase-2 trim commit pushed + HEAD-verified (docs/ → 6 kept, 4 archived, 2 dupes removed). Owed: staff_ledger v2.4 + canonical-docs mirror refresh (this S155 set + ~15 root strays).
- Notion absent 5th session (catch-up S151–S155). Cold kit rebuilt this EOS.
- **Next free: D259 · F-51 · Session 156.** **S156 TOP (owner mandate): full backend salary automation.**

### S156 EOS (07 Aug 2026, FULL — backend salary automation built + live D259; F-51 UI safety; watchdog guards staff-ledger; F-52/F-53 delivery-gate findings)
**S156 canonical filenames (Phase-0 mapping):** `KB_Register_v2_9_S156.md` · `KB_History_Archive_v1_8_S156.md` · `HANDOFF_RUNBOOK_2026-08-07_Session156_v94.md` · `START_HERE_SESSION_157.md` · `Fault_Action_Register_v2_2.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.8 → **v2.9** (`a5b38555f42aa4f2556ee1a1550b6c20`, D259 indexed; F-51/F-52/F-53); `HANDOFF_RUNBOOK` v93 → **v94** (`66b8735e36a3c0749535ee592b65a8d1`); `START_HERE_SESSION_156` → **`START_HERE_SESSION_157`** (`ad3ab2a8797671dc5a8c5bea680edb46`).
- **Archive:** **§S156 appended** → **v1.8** (`5fad707422c3ce46ad655d3ad149f14b`); re-pinned (was `3cd2d940…`); pure append proven by prefix-hash equality (+10,709 chars).
- **Tier-1:** `Fault_Action_Register` v2.1 → **v2.2** (`9b969149a4559d44d92c29eff64f9633`) — §7 Later-Findings index (F-45..F-53). All other Tier-1 unchanged this session: Umbrella, Call Console Spec, Frontend Dashboard, Diagnostics Spec, Maintenance-SOP, API Quick-Ref, AI Verdict Master, Callback Tracker Audit.
- **Live VPS code (D259/F-51 — Register-pinned, NOT manifest rows; F-31 keeps DATA out):** `staff_ledger.py` **v2.4 → v3.1 `8bcf1b2d296786717437db672fb29b05`** (selftest 184; `/salary` engine + F-51 batch + salary report = vetted attendance HTML + spliced layer; proven on Python 3.11); `clinic_watchdog.py` **`01ca6591a74ec8009bf9748fb7f480c2`** (11 services incl. staff-ledger + gutlog).
- **D259** minted + executed (full backend salary automation). **F-51** (one-tap append — fixed), **F-52** (repo op-script stale vs live), **F-53** (wrong-Python compile). No incident report (install syntax error caught pre-service).
- **Owner carry:** July salary reconciliation OPEN (no APPROVE press — paid via workbook; a clean verdict demotes the workbook to read-only). First real approval August.
- **Owed at commit:** ledger v3.1 + watchdog `01ca6591…` + canonical-docs mirror (S155 **and** S156 sets). `gutlog.service` = owner's separate Health project (guarded, not managed). Notion catch-up S151–S156 (sixth absence). Cold kit rebuilt this EOS.
- **Next free: D260 · F-54 · Session 157.**

---

- **Post-close amendment (same evening, owner-directed):** `START_HERE_SESSION_155` re-issued with the Darpan money-routing ruling (D258 candidate: loan machinery = workbook; day-to-day entries incl. Darpan = Staff Ledger via doctor DIRECT login; per-staff backend ledger) + a per-staff statement-view build task; re-pinned `d776bfd4…` → `a537565e7475f63c5d6fc74114c0e0aa`. Sunday roster print artefact shipped: `Sunday_Roster_SepDec2026_v1_S154.docx` `b06fac335b6a195e3dce76e40a5bb541` (D253 dates Sep–Dec computed; 29-Nov = 5th Sunday). Manifest self-hash recomputed.

---

### S157 EOS delta (07 Aug 2026 · documentation & design only — NO live code; no GitHub commit)
**S157 canonical filenames (Phase-0 mapping):** `KB_Register_v3_0_S157.md` · `KB_History_Archive_v1_9_S157.md` · `HANDOFF_RUNBOOK_2026-08-07_Session157_v95.md` · `START_HERE_SESSION_158.md` · `Fault_Action_Register_v2_3.md` · `Clinic_Estate_Master_Inventory_v1.md` · `Clinic_Portal_SSO_Architecture_v1.md` · `Clinic_Portal_Build_Plan_v1_S157.md` · `Salary_System_KB_v1_S157.md` · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v2.9 → **v3.0** (`f7f1c985b2263e2acaba299bed885573`, §S157 block; D260–D263 minted, D259 backfilled; F-54/55/56); `HANDOFF_RUNBOOK` v94 → **v95** (`d64417525b6cf5389e57487213fa669d`); `START_HERE_SESSION_157` → **`START_HERE_SESSION_158`** (`0051adb72f07562b42eeacc5febbd5a5`).

**S158 canonical filenames (Phase-0 mapping):** `KB_Register_v3_1_S158.md` · `KB_History_Archive_v1_10_S158.md` · `HANDOFF_RUNBOOK_2026-08-08_Session158_v96.md` · `START_HERE_SESSION_159.md` · `Fault_Action_Register_v2_4.md` · (S157 reference docs unchanged) · this `CANONICAL_MANIFEST.md`.
- **Tier-0/1 rows bumped (S158):** `KB_Register` v3.0 → **v3.1** (`e24230e0c498417536115cc66239df87`, §S158 block; D264–266; F-57/58); `KB_History_Archive` v1.9 → **v1.10** (`050798976be9b064fff877d9d5c6c70c`, §S158 pure-append, +11,025 chars); `HANDOFF_RUNBOOK` v95 → **v96** (`cab18f3dba5e2ad5ab8f4ae6a2256506`); `Fault_Action_Register` v2.3 → **v2.4** (`d46a1751441482bc70b28d430338de81`, F-57/58); `START_HERE_SESSION_158` → **`START_HERE_SESSION_159`** (`0d1b192c11be47d1215dc78c50622c97`). Live VPS code (the six SSO files) is committed to the repo separately — not doc-canon.
- **Tier-1:** `KB_History_Archive` v1.8 → **v1.9** (`f885596a8c8455d11fc39ef505ed93b7`, §S157 appended); `Fault_Action_Register` v2.2 → **v2.3** (`c45d5a55b0330a1144eaae5ac99d75ee`, F-54/55/56). **Four new Tier-1 docs registered:** Estate Inventory v1.7 (`3668a915…`), Portal SSO Architecture v1 (`0c843bb6…`), Portal Build Plan v1 (`3d6468cb…`), Salary System KB v1 (`71bb915d…`). All other Tier-1 unchanged: Umbrella, Call Console Spec, Frontend Dashboard, Diagnostics Spec, Maintenance-SOP, API Quick-Ref, AI Verdict Master, Callback Tracker Audit. Tier-2 untouched (no waiver).
- **No live code, no incident.** Cold kit `DrManoj_Estate_ColdKit_S157.zip` built (sanitized: patient files + F-31 + keys removed; service-account key to rotate). Next free: **D264 · F-57.**

---

### S160 EOS (09 Aug 2026, FULL — one live VPS file `portal.py`; two design decisions D270/D271; new Tier-1 dossier DRAFT)
**S160 canonical filenames (Phase-0 mapping):** `KB_Register_v3_3_S160.md` · `KB_History_Archive_v1_12_S160.md` · `HANDOFF_RUNBOOK_2026-08-09_Session160_v98.md` · `START_HERE_SESSION_161.md` · `Fault_Action_Register_v2_6.md` · `Staff_Daily_Register_Dossier_v1_0.md` (DRAFT) · this `CANONICAL_MANIFEST.md`.
- **Tier-0 rows bumped:** `KB_Register` v3.2 → **v3.3** (`89d060bf371773a46859e0c6c1ad0afa`; §S160 block; D270–D271 indexed; F-62/F-63); `HANDOFF_RUNBOOK` v97 → **v98** (`8cbff4c481a62980fa634c3ebb59172a`); `START_HERE_SESSION_160` → **`START_HERE_SESSION_161`** (`66efd49ca82360db393ef0993c7f637a`).
- **Tier-1 rows:** `KB_History_Archive` v1.11 → **v1.12** (`5c3cfd294184b175723db852172894df`; §S160 pure-append **proven** by prefix-hash, +6,294 chars); `Fault_Action_Register` v2.5 → **v2.6** (`6e90861ef72b86536cff5b3b9f9a210b`; F-62/F-63). **New Tier-1 doc (DRAFT):** `Staff_Daily_Register_Dossier_v1_0` (`84fe26dd39baafb4305e803e28ed8608`) — D271 subsystem design, sign-off pending. All other Tier-1/Tier-2 unchanged (no waiver).
- **Live VPS code (Register-pinned, NOT a manifest row):** `portal.py` **`679a00874c039ecabc533f9ddd0f5e67` → `81c2baef638f0d2d59d438c6370522cb`** (health tiles + sectioned mobile layout); backups on VPS; **repo commit owed → `launcher/portal.py`**.
- **D270** Case Pack → VPS off-Drive (reverses D262 / re-amends D137); **D271** Staff Daily Register subsystem. **F-62** audit-the-artefact-not-the-label; **F-63** Flask test-client route gate (a `pc`-NameError reached prod, rolled + fixed live). WABA "blocked" record corrected to "operationalise". SSO-passthrough (3 health apps) + F-56 rotation **parked**. `portal_config.py` entered the transcript → rotate `CLINIC_SSO_SECRET` at convenience.
- Cold kit + Notion catch-up owed (Notion S151–S160). **Next free: D272 · F-64 · Session 161.**

---

**END OF CANONICAL_MANIFEST — S160.**
