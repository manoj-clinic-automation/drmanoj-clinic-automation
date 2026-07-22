# CANONICAL MANIFEST — Dr. Manoj Agarwal Clinic (Tier 0 · linchpin)

**Bareilly · maintained with Claude · governs the canonical document set (D247).**

**STATUS: prepared at S149 close — becomes fully canonical when the owner installs this set (project-knowledge swaps + GitHub push, per the S149 install/push runbook).** **The S150 EOS deltas (Register v2.3, Archive v1.2, Nutrition dossier v1.1, Runbook v88, START_HERE_SESSION_151, this manifest) fold into that same pending install — install them together.** The restructure (D247 + KB split) is live: `KB_Register` + `KB_History_Archive` replaced the retired monolith `Clinic_Master_KB_SystemsRegister_v1.72` (md5 `27b72639…`) in the session loop, alongside EOS prompt v4 and the four frozen-product dossiers. This manifest is the linchpin Phase 0 verifies. *(The whole S149 set installs together — until it does, project knowledge still holds the pre-S149 copies.)*

> **Phase 0 read rule (every session).** Verify **every** row below by md5 (cheap — hash compare only). **Read into context only Tier 0.** Tier 1 is opened on demand when the session's task touches it. Tier 2 is hash-verified but never read in the loop and never edited without an explicit waiver (D34 discipline). *A row whose md5 does not match halts work until reconciled (D172/D188). If a "pending" item looks done, verify it against reality first.*

---

## Tier 0 — session loop (read at start · rewritten at end)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `CANONICAL_MANIFEST.md` | S149 | *(self — recomputed last, each EOS)* | this file; the linchpin |
| `START_HERE_SESSION_151` | S151 | `830cb5c4bc151ec96e60ba4410347f2a` | entry point; regenerated every close-out (was `START_HERE_SESSION_150`) |
| `KB_Register` | v2.3 | `63440a8114403e66eeb7af5f08746586` | current state; from v1.72 (`27b72639…`). **v2.2→v2.3 (S150):** D248 indexed (clinic_writer waiver); Tier-2 state note added; findings line at F-46. |
| `HANDOFF_RUNBOOK` | v88 (S150) | `6eba948c13b7c23d76741a5c4e91f09b` | §0 what happened · §2 live backlog (was v87); file `HANDOFF_RUNBOOK_2026-07-22_Session150_v88.md` |
| active incident | — | — | **only while open**; none open (F-44 closed) |

## Tier 1 — reference (hash-verified · read only if touched · rewrite only if changed)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `KB_History_Archive` | v1.2 | `68b2f52b8aa766a82da80cecf0fb6c4b` | all history, verbatim; from v1.72 (`27b72639…`). **§S150 appended (S150)** → re-pinned (was `15196ec3…`). |
| `Dr_Manoj_Clinic_Umbrella_Architecture` | v1.58 | `728cc64950502011ff220e1249e488ce` | strategy + decisions log |
| `Call_Console_Evolution_Spec` | v2.4 | `63978d982d1f8037f728023d15a01328` | dashboard-as-dialer (active) |
| `Frontend_Dashboard_Documentation` | v4 (S140) | `02ef929b75aa77ec071c903705335375` | dashboard still evolving |
| `Diagnostics_Surveillance_System_Spec` | v2.3 | `bdd5fa5479a57dfb73fa653054a3f329` | fault codes / detection |
| `Maintenance_SOP_System_Spec` | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` | forward-looking (project not live) |
| `API_QUICK_REFERENCE_CARD` | — | `68c4fc344bf74caaea706149cd22e64c` | small + stable. **In the repo since S148** (`canonical-docs/`, byte-identical to project knowledge — verified S149). |
| `AI_Verdict_Layer_Master` | v1 (S145) | `bd4b67f6810cd2316eb58dfe6bf180cd` | Product B analytics |
| `Clinic_Callback_Tracker_AppsScript_Audit` | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` | **unfinished audit** (Pass 4 not started); reference only — NOT the frozen dossier |
| `Fault_Action_Register` | v2.1 | `3bfeac72fe82c14aa2feb0d44a43ae2e` | **F-45 fixed S149** — the missing v2.1 CHANGELOG row was added (the v2.1 bump had left none); no lane/procedure changed; re-pinned (was `fde74c…`). Push the corrected file to the GitHub mirror `canonical-docs/Fault_Action_Register_v2_1.md` so the two stores stay byte-identical. |
| `END_OF_SESSION_PROMPT` | v4 | `9fa2be50c527865982f195d347ab0283` | the close-out routine |
| `INCIDENT_2026-07-14_…_F44` (closed) | — | `774898e80fac3e006d80e8c2f77488e6` | history; consult on demand |

## Tier 2 — frozen products (hash-verified only · never in the loop · waiver to change)

Each frozen product has one canonical **dossier**; this is the FROZEN ledger. **Four** products (was five — Consent HTML reclassified, see below).

| Product | Dossier | Dossier md5 | Artefact (the live thing) | Artefact md5 | Frozen | Waiver |
|---|---|---|---|---|---|---|
| WABA templates | `WABA_Approved_Templates_v1_S137.md` **(adopted)** | `63dd1883ed6677bc96620c087fc1d154` | MyOperator panel — 14 approved | compute at freeze | S147 / D247 | Meta re-approval + bump |
| Attendance system | `Attendance_System_Dossier_v1_S147.md` **✓ built** | `efc17e190b980d3c678d1f634060052e` | `attendance/` folder + VPS deploy | `dc12f4a0f9cb921b4cf2ce7c579aae16` (folder digest) | S147 / D247 | explicit waiver + bump |
| Nutrition/Diet (`clinic_writer`) | `Nutrition_Diet_clinic_writer_Dossier_v1_1_S150.md` **✓ built** | `6900ff40d43da0013f6ea81c3c31a0e4` | `clinic_writer/` folder + PC `D:\clinic_writer\` | `fcedae30…` (`vitals_page.html` v28; **folder digest `df0b0c34…` recompute owed at install**) | S147 / D247; **waiver exercised S150 / D248** | explicit waiver + bump |
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
