# CANONICAL MANIFEST — Dr. Manoj Agarwal Clinic (Tier 0 · linchpin)

**Bareilly · maintained with Claude · governs the canonical document set (D247).**

**STATUS: proposed S147 — becomes canonical on install.** This manifest describes the *target* state of the restructure (D247 + KB split). Until the owner installs it, the live canonical file is still `Clinic_Master_KB_SystemsRegister_v1.72` (md5 `27b72639…`).

> **Phase 0 read rule (every session).** Verify **every** row below by md5 (cheap — hash compare only). **Read into context only Tier 0.** Tier 1 is opened on demand when the session's task touches it. Tier 2 is hash-verified but never read in the loop and never edited without an explicit waiver (D34 discipline). *A row whose md5 does not match halts work until reconciled (D172/D188).*

---

## Tier 0 — session loop (read at start · rewritten at end)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `CANONICAL_MANIFEST.md` | S147 | *(self — recomputed last, each EOS)* | this file; the linchpin |
| `START_HERE_SESSION_148` | S148 | `5f979a8c84e2177236fed16940805502` | entry point; regenerated every close-out |
| `KB_Register` | v2.0 | `651c254b11666b45553602fff88a05aa` | current state; from v1.72 (`27b72639…`) |
| `HANDOFF_RUNBOOK` | v85 (S147) | `4fe05c660c1dd3d96322060eaffcb72d` | §0 what happened · §2 live backlog |
| active incident | — | — | **only while open**; none open (F-44 closed) |

## Tier 1 — reference (hash-verified · read only if touched · rewrite only if changed)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `KB_History_Archive` | v1.0 | `44681d05144a1bc20f475125e3eae9dc` | all history, verbatim; from v1.72 (`27b72639…`) |
| `Dr_Manoj_Clinic_Umbrella_Architecture` | v1.58 | `728cc64950502011ff220e1249e488ce` | strategy + decisions log |
| `Call_Console_Evolution_Spec` | v2.4 | `63978d982d1f8037f728023d15a01328` | dashboard-as-dialer (active) |
| `Frontend_Dashboard_Documentation` | v4 (S140) | `02ef929b75aa77ec071c903705335375` | dashboard still evolving |
| `Diagnostics_Surveillance_System_Spec` | v2.3 | `bdd5fa5479a57dfb73fa653054a3f329` | fault codes / detection |
| `Maintenance_SOP_System_Spec` | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` | forward-looking (project not live) |
| `API_QUICK_REFERENCE_CARD` | — | `68c4fc344bf74caaea706149cd22e64c` | small + stable |
| `AI_Verdict_Layer_Master` | v1 (S145) | `bd4b67f6810cd2316eb58dfe6bf180cd` | Product B analytics |
| `Clinic_Callback_Tracker_AppsScript_Audit` | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` | **unfinished audit** (Pass 4 not started); reference only — NOT the frozen dossier |
| `Fault_Action_Register` | v2.1 | **compute at EOS** | ⚠ was outside the S147 Phase 0 set — reconcile its hash in |
| `END_OF_SESSION_PROMPT` | v4 | `9fa2be50c527865982f195d347ab0283` | the close-out routine |
| `INCIDENT_2026-07-14_…_F44` (closed) | — | `774898e80fac3e006d80e8c2f77488e6` | history; consult on demand |

## Tier 2 — frozen products (hash-verified only · never in the loop · waiver to change)

Each frozen product has one canonical **dossier**; this is the FROZEN ledger. **Four** products (was five — Consent HTML reclassified, see below).

| Product | Dossier | Dossier md5 | Artefact (the live thing) | Artefact md5 | Frozen | Waiver |
|---|---|---|---|---|---|---|
| WABA templates | `WABA_Approved_Templates_v1_S137.md` **(adopted)** | `63dd1883ed6677bc96620c087fc1d154` | MyOperator panel — 14 approved | compute at freeze | S147 / D247 | Meta re-approval + bump |
| Attendance system | `Attendance_System_Dossier_v1_S147.md` **✓ built** | `efc17e190b980d3c678d1f634060052e` | `attendance/` folder + VPS deploy | `dc12f4a0f9cb921b4cf2ce7c579aae16` (folder digest) | S147 / D247 | explicit waiver + bump |
| Nutrition/Diet (`clinic_writer`) | `Nutrition_Diet_clinic_writer_Dossier_v1_S147.md` **✓ built** | `3b869d0e110b9539349716141e499c35` | `clinic_writer/` folder + PC `D:\clinic_writer\` | `df0b0c340fd0930c49bbc7437437262f` (folder digest) | S147 / D247 (as-is; Hindi-spelling tidy = waiver) | explicit waiver + bump |
| Callback Tracker **core** | `Callback_Tracker_Core_Dossier_v1_S147.md` **✓ built** *(scope pending confirm)* | `7e445ff04f086af0fdce656b1eae5dc1` | live Apps Script project (`WebApp.gs` D34 + core `.gs`) + Sheet `1USj…klo0` | `e4fd4512522c2e2723cb50690b92c5e8` (live project digest) | S147 / D247 | explicit waiver (D34) + bump |

**Deferred — NOT frozen (future Tier 2 candidate):**
- **Consent HTML** — reclassified S147: folded into the still-in-development **Surgical Estimate tool** (clinic-growth workstream; not yet in GitHub). It is dossiered + frozen only when that tool completes development and ships to the repo. Until then it is neither frozen nor in the session loop.

*Note: the Callback Tracker **Console/Dashboard** (`Callconsole.gs`, `Dashboard.html`) is NOT frozen — it stays active under Tier 1 (`Call_Console_Evolution_Spec`, `Frontend_Dashboard_Documentation`). Only the tracker **core** freezes (confirmed S147).*

---

## Companion

- `SYSTEM_DOC_COVERAGE_MAP_S147.md` (md5 `50085e7564cb83476a6f587782143048`) — every subsystem → its authoritative doc; answers "where's the wholesome reference for tool X". Read on demand.

---

## Governance

- **D247** (the tiering + Register/Archive split + this manifest) lives in the KB Register's decisions index/changelog once installed.
- **Provenance rule:** every md5 here is computed from the live artefact; none is assumed (D172/D188). "compute at freeze / at EOS" = a real hash still owed, not a placeholder to skip.
- **Install:** this manifest + KB Register v2.0 + KB History Archive v1.0 + EOS prompt v4 + the D247 decision install together at one EOS, replacing `Clinic_Master_KB_SystemsRegister_v1.72` in the loop.

---

**END OF CANONICAL_MANIFEST — S147.**
