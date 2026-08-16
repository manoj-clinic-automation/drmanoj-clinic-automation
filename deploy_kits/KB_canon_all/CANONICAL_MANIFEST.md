# CANONICAL MANIFEST — Dr. Manoj Agarwal Clinic (Tier 0 · linchpin)

**Bareilly · maintained with Claude · governs the canonical document set (D247).**

**STATUS: canonical — current at S183** (FULL code session, three threads: (1) the **F-97 structural fix shipped** — `verify_live_pins.py` at `/root/deploy/` checks every live-code pin against the box (D321); its first run corrected NINE Register rows (F-101 eight wrong paths + F-102 one stale md5); F-100 fixed `push_kit.bat` silently dropping a `.gitignore`-excluded file. (2) The **Marg pharmacy feed went LIVE and backfilled** — `marg_report.py` reads `.xlsx` too (kit S183_M2a), migration `S183_marg_map`, `marg_backfill.py` v2 backfilled **119 days / 15,574 drug lines / 982 attributed bills**, money byte-identical (D313 proven at scale). (3) The **Sanjeevni cash chain was reconciled from bank records and found whole** — the −₹30,056 was 16 unrecorded Yes Bank cash deposits (₹16,45,600), not missing money; ICICI holds card/UPI only (Darpan's UPI confirmed T+1), Yes Bank holds all cash; F-103/F-104 minted; **no live finance write made** — booking is S184. Register v5.4 → **v5.5**. **Archive stays v1.30 and Fault Register stays v2.18 this close — the formal §S183 append + F-100–F-104 append are OWED as S184 opening housekeeping** (precedent: the S181 owed-appends); the S183 narrative + findings are fully captured in the Register, the Runbook §0, and three dedicated S183 docs. Below, the historical S182 status block is retained.)

**(S182 status, retained:)** FULL code session: the **Marg pharmacy feed** was established offline end-to-end and **sale returns were made to reach the books**, across FOUR separate live installs on `clinic-finance`. `finance_ingest.py` and `finance_app.py` were both replaced; four new modules landed at `/root/finance/` (`marg_report.py`, `finance_returns.py`, `finance_returns.sql`, `finance_identity.py`); the database gained one **redefined view** (`v_day_attribution`, netting `*_return`) and one **new table** (`sale_line_item`), both non-destructive; `xlrd 2.0.2` was added. **D314–D315 minted** (a return is a magnitude with its direction in the row's type; a patient-identity match is graded and only the top grade may feed an audit). **F-85–F-88 raised** — two of them about this session's own process: F-87, a change shipped twice to a test suite that could not be run offline (F-84's own lesson repeated, remedied by `dev_seed_smoke_db.py` + differential verification), and F-88, a passing `md5sum -c` proving a kit internally consistent rather than current. A vendor-facing requirement document was written. Archive §S180 appended v1.27 → **v1.28** (pure append, prefix byte-identical). Register v5.1 → **v5.2** (additive). Live finance code is Register-pinned, NOT a manifest row — F-31 keeps the DB + patient CSVs out of repo and manifest.) (S179 was the clinic-finance medical go-live; S178 an EOS-light KB compaction; S173–S177 the Asset-Register sub-project.) **Rows changed this session are pinned from a live md5 recomputed at the S180 EOS.** **Seven rows were unreachable at Phase 0: FOUR RECOVERED by hash-search, THREE CLOSED AS LOST under D316 — see the section below. A closed row does not halt Phase 0.**

> **Phase 0 read rule (every session).** Verify **every** row below by md5 (cheap — hash compare only). **Read into context only Tier 0.** Tier 1 is opened on demand when the session's task touches it. Tier 2 is hash-verified but never read in the loop and never edited without an explicit waiver (D34 discipline). *A row whose md5 does not match halts work until reconciled (D172/D188). If a "pending" item looks done, verify it against reality first.*

---

## RESOLVED AT THE S180 CLOSE — four recovered, three CLOSED AS LOST (D316 · F-89)

At the S180 Phase 0, **33 of 33 reachable rows verified clean** and seven could not be reached. A
hash-based recovery tool then searched the owner's `D:` and `C:` drives — **by md5, not by filename**
(D188), opening `.zip` archives because the cold backup is one, and re-hashing LF-normalised copies
of near-misses. **26,745 files hashed.**

### Recovered — each matched its pinned md5 exactly

| Row | Tier | md5 | Found in |
|---|---|---|---|
| `Fault_Action_Register` v2.16 | **Tier 1 CURRENT** | `1702b5a8e0663847eaa097919aea94d3` | the S171 cold kit |
| `Staff_Daily_Register_Dossier` v1.1 | historical | `7969deadcbf062fccae302e1f8ae07f0` | the S165 cold kit |
| `KB_Asset_Register` v1.10.3 | historical | `07d01e80a1d6a49884650d2e542205df` | git `canonical-docs/` |
| `KB_Register` v4.6 | historical | `0503f255da0ab9a98dc6f092ddff2ef6` | git `canonical-docs/` |

### CLOSED AS LOST — under D316. **These do NOT halt Phase 0.**

| Row | md5 (kept for provenance) | Closure |
|---|---|---|
| `KB_Register` v5.0 (S178) | `ee12a63d4b87b1359f2d0954945457b2` | **LOST-SUPERSEDED** — v5.1 (`1c86b83a…`) verified present on disk. Nothing current depends on it. No action. |
| `KB_History_Archive` v1.26 (S178) | `30dc00b300a491105577b8c58b2c47e0` | **LOST-SUPERSEDED** — v1.27 (`adb85c35…`) verified present on disk. No action. |
| `KB_Asset_Register` v1.11.0 | `1c147beb44ad4413d3b147ad70e43ea7` | **LOST-RECONSTRUCTABLE** — Tier-1 CURRENT. Rebuild from the recovered v1.10.3 + Archive §S173–§S177. **Backlog item, not a blocker.** |

**Why exactly these three (F-89).** All are **S177–S178 outputs**. The newest full cold kit on the
machine is **`DrManoj_Clinic_FULL_Handoff_Session171`** — so they were created **nine sessions after
the last cold backup**. Everything up to S171 was comfortably recoverable; everything after depended
on whatever happened to be downloaded loose. Every document that *was* recovered came from a backup
mechanism that had actually run: the S171 kit, the S165 kit, or the git repo.

**D316 — a closed row is not drift.** Its md5 stays listed for provenance, but Phase 0 does not halt
on it. Only a row listed as *present* that fails its hash does that. A halt that fires every session
is a halt that gets waved through, and then it protects nothing.

---

## Tier 0 — session loop (read at start · rewritten at end)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `CANONICAL_MANIFEST.md` | S179 | *(self — recomputed last, each EOS)* | this file; the linchpin |
| `START_HERE_SESSION_184` | S183 | `18c2bf463ad53bd075683aebfba8f373` | entry point; regenerated every close-out (S162–S183 entry files superseded). Carries the git-clone Phase 0 **and** the NEW `python3 /root/deploy/verify_live_pins.py` live-code check (D321) |
| `KB_Register` | v5.5 | `3cad79e6361c6e1777f3bc9db983770d` | current state; **S183 → v5.5** (additive: 9 live pins corrected to the box + the Marg feed live entries (`marg_report.py 829f4344…`, `marg_backfill.py fa33ec8a…`, migration `S183_marg_map`, `/root/deploy/verify_live_pins.py`), **D321** into the decisions index, **F-100–F-104** into the findings index, finance/cash reconciliation state, v5.5 lineage row; nothing in v5.4 cut). **S182 → v5.4** (additive: the `portal.py` pin CORRECTED after F-97 found it two sessions stale, `marg_backfill.py` added, D320, F-96–F-99, v5.4 lineage row; nothing in v5.3 cut). **S181 → v5.3** (additive: the clinic-module live entries, D317–D319, F-90–F-95, v2.17/v1.11.0-R promotions, v5.3 lineage row; nothing in v5.2 cut). **S180 → v5.2** (additive: six finance live-file entries changed/added, D314–D316 into the decisions index, F-85–F-89 into the findings index, v5.2 lineage row; nothing in v5.1 cut). **S179 → v5.1** (`1c86b83a…`) (additive over the v5.0 compaction: the clinic-finance live-file block added to the consolidated table; **D313** folded into the decisions index; **F-84** into the findings index; v5.1 row added to the lineage; nothing in v5.0 cut). **S178 → v5.0** (`ee12a63d…`; COMPACTION — the three duplicated history forms removed zero-loss, decisions index completed through D312, truncation-proof END-marker; Archive UNCHANGED v1.25). Earlier lineage in the §S… blocks below. |
| `HANDOFF_RUNBOOK` | v117 (S183) | `cc523169dbcd0e2fb50a96ab132e215b` | §0 what happened (S183 — F-97 fix live; Marg feed live + backfilled; Sanjeevni cash reconciled, whole) · §1 mental models · §2 live backlog — ⭐S184 = book the Sanjeevni cash correction (gated) · §3 install discipline; file `HANDOFF_RUNBOOK_2026-08-16_Session183close_v117.md` |
| active incident | — | — | **only while open**; none open |

## Tier 1 — reference (hash-verified · read only if touched · rewrite only if changed)

| Doc | Version | md5 | Notes |
|---|---|---|---|
| `KB_History_Archive` | v1.30 | `7a673ac6e09abeb60642aa58367bf860` | all history, verbatim; §S182 is last (appended at the S182 EOS; pure-append, **content before the v1.29 END marker byte-identical**, +18,638 chars); END-marker present. Previously §S181 was last (appended at the S181 EOS; pure-append, **content before the v1.28 END marker byte-identical to the `0e8b4bd6…` pin**, +15,747 chars); END-marker present. |
| `S179_Finance_LIVE_State` | S179 | `54cb25a88adc5692360341113a87a43e` | **NEW S179 · SOLE live-state reference** for the clinic-finance subsystem (D313 · F-84). Live URLs/paths/service, final live md5s (UPI + browse folded), the three security faults + fixes, the B1 data findings, design invariants, and what is still open. Companions in project knowledge: build contract v2, migration analysis, B1 reconciliation, `S179_Marg_Sale_Report_Analysis`, `S180_Marg_Folder_Recon`, delivery notes. Opened on demand at any finance task. |

| `Dr_Manoj_Clinic_Umbrella_Architecture` | v1.58 | `728cc64950502011ff220e1249e488ce` | strategy + decisions log |
| `Call_Console_Evolution_Spec` | v2.4 | `63978d982d1f8037f728023d15a01328` | dashboard-as-dialer (active) |
| `Frontend_Dashboard_Documentation` | v4 (S140) | `02ef929b75aa77ec071c903705335375` | dashboard still evolving |
| `Diagnostics_Surveillance_System_Spec` | v2.3 | `bdd5fa5479a57dfb73fa653054a3f329` | fault codes / detection |
| `Maintenance_SOP_System_Spec` | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` | forward-looking (project not live) |
| `API_QUICK_REFERENCE_CARD` | — | `68c4fc344bf74caaea706149cd22e64c` | small + stable; in the repo `canonical-docs/` (byte-identical) |
| `AI_Verdict_Layer_Master` | v1 (S145) | `bd4b67f6810cd2316eb58dfe6bf180cd` | Product B analytics |
| `Clinic_Callback_Tracker_AppsScript_Audit` | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` | unfinished audit (Pass 4 not started); reference only — NOT the frozen dossier |
| `Fault_Action_Register` | **v2.18** | `ff0f020a3b645cbfa65400a51448cf0f` | findings register (F-##). **S182: F-96–F-99 appended to §7.1**, pure append — everything above the new block byte-identical to v2.17. |
| `Fault_Action_Register` (pre-S182) | v2.17 | `7bcde8c98d62e6570f9995b7bbbd5166` | findings register (F-##). **BUILT at S181**: the three owed appends APPLIED (F-82+F-83 · F-84 · F-85–F-89); NEW §7.1 carries their full text; zero-loss proven mechanically against the v2.16 pin; source-of-truth line corrected; seven changelog rows reconstructed from evidence (v2.9→v2.7 relabel on two independent Archive proofs). §0–§6 lanes unchanged. The three append artefacts are provenance only. |
| `GAS_Outcome_Vocabularies_v1_S171` | v1 | `71140b7b2259d8e6e04f04691b777fff` | verbatim K/FU/IN/L outcome sets + K_CODE_MAP + Hindi coaching map; seeds `console_options` + `HI_OUTCOME`; code wins over doc summaries (D172) |
| `Portal_WhatsApp_Casepack_Dossier_v1_S172` | v1 | `3d97ec8040c81fb4812d04f209ca46b2` | **SOLE reference** for the in-portal Surgical Case Pack (D309), the shared canonical WhatsApp sender (D310), and the follow-up batch (D311) + UI-served-from-disk (D312). All live-file md5s/paths/config + the F-82 vendor outage + go-live steps. Opened on demand. |

| `D297_Call_Console_Contract_v4_FINAL` | S166 | `42991579f3c20cbd4f512131e58c22f9` | **signed, build-ready** Call-Intelligence Console contract + Appendix A verified ground truth. Tier 1 — opened at the D297 build. |
| `D297_Console_Portal_Build_Dossier` | v1 (S168) | `7429a696f4f1f7186c12d66a4a39ac75` | **self-contained build reference** for the console/portal work: console.db schema · staff-attribution mechanism + roster · dedup/query rules (F-74) · display contract · install state · staged roadmap. Opened alongside the contract at any console build. |
| `Console_Rev5_Punchlist` | v1 (S169) | `e8f707d7be1fb20b20e360ba9453df9a` | the autonomous console build plan (D302) — ordered items each with source·file·function·change·gate·install·acceptance. |
| `Clinic_Estate_Master_Inventory` | v1.1 (S177; lineage v1.7 S157) | `a8450fd44a0d69cc5dd97da8f7b1f6eb` | reconciled cross-project app+service estate (D260); S177: Asset-Register row → v1.11.0 + NEW `/root/shared/` shared-libs row. *(Forward: a clinic-finance row is owed when the estate is next reconciled.)* |
| `KB_Asset_Register` | **v1.11.0-R** (S181 reconstruction) | `631a2ba7ff907b98aadee89ac97d0412` | **the D316 rebuild of the LOST v1.11.0** (lost pin `1c147beb…` kept for provenance; this is NOT those bytes — the -R suffix says so in the version string). Built from the hash-verified v1.10.3 + Archive §S177 (the recipe §S178 records); adversarially verified. Opened on demand at any asset-app work. Next free A-D25. |
| `Clinic_Portal_SSO_Architecture` | v1 (S157) | `0c843bb64d579205d8c64946721c10f6` | SSO broker + shared verify-shim (D261) |
| `Clinic_Portal_Build_Plan` | v1 (S157) | `3d6468cb4927d5d77d7a7d687ffabfe7` | tile rosters + per-app selection (D262) |
| `Salary_Attendance_Master_Dossier` | v1 (S164) | `669917fcaca3fece3a3f6caa1899edbf` | **SOLE reference** for the salary + attendance + staff-daily-register machine. Supersedes `Attendance_System_Dossier_v1.2` (Tier-2 frozen row retained as integrity anchor), `Salary_System_KB_v1`, `Staff_Daily_Register_Dossier_v1.1` — all retained historical. |
| `END_OF_SESSION_PROMPT` | v4 | `9fa2be50c527865982f195d347ab0283` | the close-out routine |


## Tier 1 — HISTORICAL / superseded (retained · **still hash-verified at Phase 0** · never read in the loop)

*Kept for lineage + integrity anchoring, not as current references. Their content is superseded; do not open them for current work — use the doc named in the "superseded by" note.*

| Doc | Version | md5 | Superseded by / status |
|---|---|---|---|
| `Salary_System_KB` | v1 (S157) | `71bb915dff0dac26fe20192b91cd3940` | → `Salary_Attendance_Master_Dossier` (S164) |
| `Staff_Daily_Register_Dossier` | v1.1 (S161) | `7969deadcbf062fccae302e1f8ae07f0` | → `Salary_Attendance_Master_Dossier` (S164); §5 also superseded by the C-model (D279/D280) |
| `INCIDENT_2026-07-14_…_F44` | — (closed) | `774898e80fac3e006d80e8c2f77488e6` | closed incident; consult on demand only |
| `KB_Asset_Register_v1_10_3` | v1.10.3 (S176) | `07d01e80a1d6a49884650d2e542205df` | → v1.11.0 (LOST, D316) → **v1.11.0-R (S181 reconstruction)** |
| `KB_Register` (pre-compaction) | v4.6 (S177) | `0503f255da0ab9a98dc6f092ddff2ef6` | → `KB_Register` v5.0 (compacted S178) → v5.1 (S179) |
| `KB_Register` (compaction base) | v5.0 (S178) | `ee12a63d4b87b1359f2d0954945457b2` | → `KB_Register` v5.1 (S179, additive finance fold) |
| `KB_History_Archive` (pre-S179) | v1.26 (S178) | `30dc00b300a491105577b8c58b2c47e0` | → `KB_History_Archive` v1.27 (S179, §S179 pure-append) |
| `KB_Register` (pre-S180) | v5.1 (S179) | `1c86b83acefcf9bce8c00f1b39bcb111` | → `KB_Register` v5.2 (S180, additive) |
| `KB_History_Archive` (pre-S180) | v1.27 (S179) | `adb85c35cabfc4a826738e491554ec27` | → `KB_History_Archive` v1.28 (S180, §S180 pure-append) |
| `START_HERE_SESSION_180` | S179 | `b2f89f18af10f110cc26e11d7ab03b7b` | → `START_HERE_SESSION_181` (S180) |
| `START_HERE_SESSION_181` | S180 | `d4de1df35c72f364e77b395534c4ac3e` | → `START_HERE_SESSION_182` (S181) |
| `KB_Register` (pre-S181) | v5.2 (S180) | `fb6c3e40221250d1c6c5848bb8f7c231` | → `KB_Register` v5.3 (S181, additive) |
| `KB_History_Archive` (pre-S181) | v1.28 (S180) | `0e8b4bd6b4e09fd2dcb6ce7fbf2c14ad` | → `KB_History_Archive` v1.29 (S181, §S181 pure-append) |
| `HANDOFF_RUNBOOK` | v114 (S180) | `aab96fc8c83d11ad8ab6ec4c8d750408` | → `HANDOFF_RUNBOOK` v115 (S181) |
| `Fault_Action_Register` (pre-append) | v2.16 (S171/recovered S180) | `1702b5a8e0663847eaa097919aea94d3` | → **v2.17 (S181, appends applied)** |
| `HANDOFF_RUNBOOK` | v113 (S179) | `f743a639d8750122ec3be17be752094a` | → `HANDOFF_RUNBOOK` v114 (S180) |
| `KB_Register` (pre-S182) | v5.3 (S181) | `df00d5c253c1f1cd6b2c0387d6b7dbe6` | → `KB_Register` v5.4 (S182, additive) |
| `KB_History_Archive` (pre-S182) | v1.29 (S181) | `8ef9bc8bdce233c03de60bdb75969dfd` | → `KB_History_Archive` v1.30 (S182, §S182 pure-append) |
| `HANDOFF_RUNBOOK` | v115 (S181) | `61b2216107f38798287c258013475904` | → `HANDOFF_RUNBOOK` v116 (S182) |
| `START_HERE_SESSION_182` | S181 | `3fad5ed45c0a98cb63a9cf0a070e0396` | → `START_HERE_SESSION_183` (S182) |

## Tier 2 — frozen products (hash-verified only · never in the loop · waiver to change)

Each frozen product has one canonical **dossier**; this is the FROZEN ledger. **Four** products.

| Product | Dossier | Dossier md5 | Artefact (the live thing) | Artefact md5 | Frozen | Waiver |
|---|---|---|---|---|---|---|
| WABA templates | `WABA_Approved_Templates_v1_S137.md` **(adopted)** | `63dd1883ed6677bc96620c087fc1d154` | MyOperator panel — 14 approved | compute at freeze | S147 / D247 | Meta re-approval + bump |
| Attendance system | `Attendance_System_Dossier_v1_2_S153.md` **✓ built** | `bf19179181c553777e4cc8e3834bc754` | `attendance/` folder + VPS deploy + `att_month_report.py` (**v2.5 `e64cad19…` INSTALLED + July-verified**); Staff Ledger app `staff_ledger.py` **v2.4 `74dac84eb15f5172478a97066f56c99d`** (separate live system, Register-tracked) | 10-file frozen-core digest `dc12f4a0…` byte-unchanged; **full-folder re-pin `c4c9c83f44fbbbb39609047671e77d60`** (11 files) | S151 / D251 | frozen core: explicit waiver + bump; additive report layer sanctioned |
| Nutrition/Diet (`clinic_writer`) | `Nutrition_Diet_clinic_writer_Dossier_v1_1_S150.md` **✓ built** | `6900ff40d43da0013f6ea81c3c31a0e4` | `clinic_writer/` folder + PC `D:\clinic_writer\` | `fcedae30…` (`vitals_page.html` v28; folder digest `1b4f0f2299cd6c9e72b6d04f45847556`) | S147 / D247; **waiver exercised S150 / D248** | explicit waiver + bump |
| Callback Tracker **core** | `Callback_Tracker_Core_Dossier_v1_S147.md` **✓ built** *(scope pending confirm)* | `7e445ff04f086af0fdce656b1eae5dc1` | live Apps Script project (`WebApp.gs` D34 + core `.gs`) + Sheet `1USj…klo0` | `e4fd4512522c2e2723cb50690b92c5e8` (live project digest) | S147 / D247 | explicit waiver (D34) + bump |

**Deferred — NOT frozen (future Tier 2 candidate):**
- **Consent HTML** — folded into the still-in-development Surgical Estimate tool; dossiered + frozen only when that tool ships to the repo.

*Note: the Callback Tracker **Console/Dashboard** is NOT frozen — it stays active under Tier 1. Only the tracker **core** freezes.*

---

## Companion

- `SYSTEM_DOC_COVERAGE_MAP_S147.md` (md5 `50085e7564cb83476a6f587782143048`) — every subsystem → its authoritative doc. Read on demand. *(The clinic-finance subsystem's authoritative doc is `S179_Finance_LIVE_State`; add its row when the coverage map is next rebuilt.)*
- `README_CANONICAL_SET.md` (repo `canonical-docs/`) — a repo-navigation doc that carries no version numbers and defers to this manifest; not a Phase-0-verified canonical row.

---

## Governance

- **D247** (the tiering + Register/Archive split + this manifest) lives in the KB Register's decisions index.
- **Provenance rule:** every md5 here is computed from the live artefact; none is assumed (D172/D188). "compute at freeze" = a real hash still owed, not a placeholder to skip.
- **Install:** project-knowledge swaps + one GitHub push travel together per EOS.

---

*(**S179 consolidation note — flagged for owner review, reversible.** The manifest's pre-S178 per-session changelog blocks (§S149–§S177) were consolidated OUT this EOS: each is duplicated verbatim in **KB History Archive §S…** and its per-version md5 lineage is in the **KB Register version-lineage table**, so keeping a third copy here only re-grew the linchpin. Only the current-state tables above (the sole Phase-0-verified rows) plus the S178 and §S179 blocks are kept. **This is a size reduction of the manifest, not a loss of provenance** — every dropped hash still lives in the Archive/Register. If you'd rather the manifest carry the full changelog history again, say so and I'll restore §S149–§S177 verbatim at the next EOS. This mirrors the S178 Register compaction philosophy applied to the manifest.)*

### S178 documentation close (14 Aug 2026, EOS-light — NO live code · NO new decision/finding)
Owner directive: *"organize the KB docs thoroughly · cut bloat · compact without any loss of context."* Phase 0 green.
- **KB Register compacted v4.6 → v5.0** (`ee12a63d4b87b1359f2d0954945457b2`; 752 → 500 lines). Cut the three duplicated history forms (verbatim in the untouched Archive); kept current-state + indexes; folded D283–D312 into the index; added a consolidated live-file table + a truncation-proof END-marker. Zero-loss proven mechanically.
- **KB Asset Register refreshed v1.10.3 → v1.11.0** (`1c147beb44ad4413d3b147ad70e43ea7`) — A-D24 wave.
- **De-clutter:** `Salary_System_KB`, `Staff_Daily_Register_Dossier`, the closed F-44 incident, and the two pre-refresh docs → new **Tier 1 — HISTORICAL** subsection.
- **Session-loop close:** Archive §S178 → **v1.26** (`30dc00b300a491105577b8c58b2c47e0`); Runbook v111 → **v112** (`a6c4f218db8d9fc4e324eb1124eae3f5`); `START_HERE_SESSION_179` (`00d100191922aff5e69c25a170d9e390`). **Next free: D313 · F-84 · A-D25 · Session 179.**

**END OF CANONICAL_MANIFEST — S178.**

---

### §S179 EOS (15 Aug 2026, FULL — the Sanjeevni (medical) daily-revenue system LIVE on the VPS off Google Forms; D313; F-84 (three self-found security faults) fixed)
**S179 canonical filenames (Phase-0 mapping):** `KB_Register_v5_1_S179.md` · `KB_History_Archive_v1_27_S179.md` · `HANDOFF_RUNBOOK_2026-08-15_Session179close_v113.md` · `START_HERE_SESSION_180.md` · `S179_Finance_LIVE_State.md` (NEW Tier-1) · `Fault_Register_append_F84_S179.md` (append artefact, not a canonical row) · this `CANONICAL_MANIFEST.md`. (All other Tier-1/Tier-2 rows UNCHANGED — re-hashed clean.)
- **Tier-0 bumps (md5s pinned this EOS):** `KB_Register` v5.0 → **v5.1** (`1c86b83acefcf9bce8c00f1b39bcb111`; additive finance fold — live-file block + D313 + F-84); `HANDOFF_RUNBOOK` v112 → **v113** (`f743a639d8750122ec3be17be752094a`); `START_HERE_SESSION_179` → **`START_HERE_SESSION_180`** (`b2f89f18af10f110cc26e11d7ab03b7b`).
- **Tier-1 bumps:** `KB_History_Archive` v1.26 → **v1.27** (`adb85c35cabfc4a826738e491554ec27`; §S179 **pure-append**, prefix byte-identical to the v1.26 pin `30dc00b3…`, +13,540 chars, END-marker present); **NEW Tier-1 doc** `S179_Finance_LIVE_State` (`54cb25a88adc5692360341113a87a43e`) — the clinic-finance sole live-state reference. `Fault_Action_Register` stays **v2.16 pinned** (`1702b5a8…`) with the F-82+F-83 append (`3393d527…`) **and** the new F-84 append (`Fault_Register_append_F84_S179.md`, md5 `cce4009f373971fdadf8ed1f9b031d03`) owed → v2.17 on owner apply. All other Tier-1/Tier-2 rows UNCHANGED (re-hash clean); two pre-S179 doc versions added to the HISTORICAL subsection.
- **Live VPS code (Register-pinned, NOT manifest rows; F-31 keeps the DB + patient CSVs out):** **NEW subsystem** `clinic-finance` at `/root/finance/` (system `python3`, port 8106, `/finance` on the portal origin — F-68): `finance_app.py 61e36d5522e4e99e1e65e159ef50c85e` (smoke 176/176) · `finance_ingest.py 872ec33ef7c628cd474224b0c6c78ba5` (30/30) · `finance_import_medical.py 7cfde93ef…` (12/12) · `finance_upi.py 3f5016f0c64f12b91ab55c18252705c1` (14/14) · `finance_schema.sql bef0d8100…` · `finance_ui/finance_entry.html 8ec6ad49…` · `finance_ui/finance_review.html ddd3d5f6…` · `finance_backup.sh efe6f1b5…` · `clinic-finance.service 59c03bfa…` · clinic-Gmail GAS `VPS_Push_UPI.gs 955b291c…`. PHI/data gitignored (`finance.db*`, `scans/`, `exports/`, `medical_*.csv`). All other clinic live files UNCHANGED from S177/S178.
- **D313 minted** (clinic-finance subsystem architecture — medical live; clinic + lab a replication). **F-84 minted + FIXED** (three self-found security faults — ungated reads · spoofable header identity · unchecked epoch; "the offline-testing shortcut was the vulnerability"). **No incident** (all three found on self-review, fixed before close; installer auto-rolls-back on `sso_epoch_ok:false`). Git kit `gitkit_S179.zip` prepared (`finance/` + `gas/` + `.gitignore.additions` + commit message) — **owner action: `.gitignore` the PHI paths in the SAME commit before `git add` (F-31/F-49).**
- ⭐ **Next-session top task: CLINIC + LAB finance modules (a replication of medical).** Next free: **D314 · F-85 · A-D25 · Session 180.** This was Session 179.

**END OF CANONICAL_MANIFEST — S179.**

---

### §S180 EOS (15 Aug 2026, FULL — the Marg pharmacy feed built offline end-to-end; sale returns made to reach the books; four live installs; D314–D315; F-85–F-88)
**S180 canonical filenames (Phase-0 mapping):** `KB_Register_v5_2_S180.md` · `KB_History_Archive_v1_28_S180.md` · `HANDOFF_RUNBOOK_2026-08-15_Session180close_v114.md` · `START_HERE_SESSION_181.md` · `Fault_Register_append_F85_F89_S180.md` (append artefact, not a canonical row) · this `CANONICAL_MANIFEST.md`. (All other Tier-1/Tier-2 rows UNCHANGED — the 33 reachable ones re-hashed clean. Of the seven unreachable: four recovered and back in the set, three closed as LOST — see the resolution section above.)
- **Tier-0 bumps (md5s pinned this EOS):** `KB_Register` v5.1 → **v5.2** (`fb6c3e40221250d1c6c5848bb8f7c231`; additive — six finance live-file entries changed/added, D314–D315, F-85–F-88, v5.2 lineage row); `HANDOFF_RUNBOOK` v113 → **v114** (`aab96fc8c83d11ad8ab6ec4c8d750408`; gains a §1 mental-models section); `START_HERE_SESSION_180` → **`START_HERE_SESSION_181`** (`d4de1df35c72f364e77b395534c4ac3e`).
- **Tier-1 bumps:** `KB_History_Archive` v1.27 → **v1.28** (`0e8b4bd6b4e09fd2dcb6ce7fbf2c14ad`; §S180 **pure-append**, prefix byte-identical to the v1.27 pin `adb85c35…`, +25,910 chars, END-marker present). `Fault_Action_Register` **v2.16 RECOVERED** (hash verified from the S171 cold kit), with THREE appends owed → v2.17.
- **Live VPS code (Register-pinned, NOT manifest rows; F-31 keeps patient DATA out):** `finance_ingest.py` `872ec33e…` → **`2cd0f264fb1a091f3e3ec7c3f4a17438`** (smoke 50/50) · `finance_app.py` `61e36d55…` → **`7b62b7ae661914505c864d71cc6c9abc`** (smoke 179/179) · **NEW** `marg_report.py` `28b47d447cfd966411742055717a5c56` · **NEW** `finance_returns.py` `a46a87e65d951d59baeb9d86c9d8fe59` · **NEW** `finance_returns.sql` `9cec4e317590f845beda87881721cf69` · **NEW** `finance_identity.py` `81092e3ca18c9a85f1de06cc8055d967`. Database: `v_day_attribution` redefined; `sale_line_item` + 4 indexes + 3 settings added; both non-destructive. VPS python gained `xlrd 2.0.2`.
- **D314–D316 minted. F-85–F-89 raised**, two about the session's own process. **No incident** — every failure was caught by an install gate or by self-review before reaching live use. **Git kits COMMITTED at this close**, clearing the two-session lag. **The seven unreachable rows were resolved: four recovered by hash-search, three closed as LOST under D316 (F-89 — the cold-kit cadence had lapsed nine sessions).** Cold-backup discipline restarted: `KB_S180_close.zip`; **next kit due within 3–5 sessions, and the count is checked at every close.**
- ⭐ **Next-session top task: owner's choice — the CLINIC + LAB finance modules (the carried S180 star), or finishing the Marg chain (U5·U7·U8·U9·U12).** Next free: **D317 · F-90 · A-D25 · Session 181.** This was Session 180.

**END OF CANONICAL_MANIFEST — S180.**

---

### §S181 EOS (16 Aug 2026, FULL — the CLINIC finance module LIVE via the NEW D317 deploy chain; housekeeping cleared; D317–D319; F-90–F-95)
**S181 canonical filenames (Phase-0 mapping):** `KB_Register_v5_3_S181.md` · `KB_History_Archive_v1_29_S181.md` · `HANDOFF_RUNBOOK_2026-08-16_Session181close_v115.md` · `START_HERE_SESSION_182.md` · `Fault_Action_Register_v2_17.md` (**promoted CURRENT**) · `KB_Asset_Register_v1_11_0_R_S181.md` (**promoted CURRENT**, D316 reconstruction) · this `CANONICAL_MANIFEST.md`. All other rows unchanged, re-hash owed at the S182 Phase 0 as usual.
- **Tier-0 bumps:** Register v5.2 → **v5.3** · Runbook v114 → **v115** · START_HERE 181 → **182**. **Tier-1:** Archive v1.28 → **v1.29** (§S181 pure append; content before the v1.28 END marker byte-identical to `0e8b4bd6…`, +15,747 chars) · Fault Register **v2.17** CURRENT (`7bcde8c9…`) · Asset Register **v1.11.0-R** CURRENT (`631a2ba7…`).
- **Live VPS (Register-pinned):** `finance_app.py` → `86382f62907b65cf17fded2ee914328e` (clinic unit + owner redesign; live smoke **316/316**) · NEW `finance_ui/finance_entry_clinic.html` `0c64fda2…` · migrations `S182_clinic` + `S182_c2` applied · new tables `clinic_verification` / `clinic_line_side` / `tracker_day` · clinic roles seeded real (makers shavez/alisha/shivani; checkers manoj/bhawna; `clinic.final_checker`=manoj). Kits S182_C1a…C2a in the repo's `deploy_kits/` (anticipatory labels — F-85 note); GAS `VPS_Push_TrackerDay.gs` + PC-side `docterz_report.py` delivered, wiring pending.
- **D317–D319 minted · F-90–F-95 raised** (F-90 repo PUBLIC — owner ruling owed). **No incident** — three installer reds were caught by gates with nothing half-installed; one red was the bank arbiter working. **KB swap executed per D319 for the first time**: the assistant wrote this canonical set into project knowledge directly; owner actions at this close = one KB-kit double-click + one cold-kit download. ⚠ the S181 FULL cold kit is **PHI-bearing** (six unmasked numbers pre-existing in the canonical set) — keep private; owner ruling owed.
- ⭐ **S182 top task: portal tiles · GAS tracker-feed wiring · first parallel-run checks.** Cold-kit count **1 of 3–5** (F-89). Next free: **D320 · F-96 · A-D25 · Session 182.** This was Session 181.

**END OF CANONICAL_MANIFEST — S181.**

---

### §S182 EOS (16 Aug 2026, FULL — Phase 0 proved against git bytes; the clinic PORTAL TILES live; a fail-open identity default closed; D320; F-96–F-99)
**S182 canonical filenames (Phase-0 mapping):** `KB_Register_v5_4_S182.md` · `KB_History_Archive_v1_30_S182.md` · `HANDOFF_RUNBOOK_2026-08-16_Session182close_v116.md` · `START_HERE_SESSION_183.md` · `Fault_Action_Register_v2_18.md` · this `CANONICAL_MANIFEST.md`. All other rows unchanged.
- **Tier-0 bumps:** Register v5.3 → **v5.4** (`9506a0fe…`) · Runbook v115 → **v116** (`5b871ab7…`) · START_HERE 182 → **183** (`076e301b…`). **Tier-1:** Archive v1.29 → **v1.30** (`7a673ac6…`; §S182 pure append, prefix byte-identical, +18,638 chars) · Fault Register v2.17 → **v2.18** (`ff0f020a…`; F-96–F-99 appended to §7.1, prefix byte-identical).
- **Phase 0 was verified independently this session:** the repo was cloned anonymously and the **45 manifest pins hashed against the git bytes**, separately from the kit's own `MD5SUMS_ALL.txt` (48 = 45 rows + 3 append artefacts). Both passed. The rule adopted: **a hash verdict is only pronounced on bytes delivered as a FILE**; re-keyed inline text may corroborate, never convict — a re-keyed Phase 0 had produced a false red on `KB_Register` v4.6 earlier the same day (104 bytes of transcription drift, proven not assumed).
- **Live VPS (Register-pinned, NOT manifest rows):** `/root/portal/portal.py` `da417709…` → `410388da…` (S182_P1a, clinic tiles, gate 42/42) → **`2784b1cb76abfb9dbe2407c38da5bd83`** (S182_P2a, F-98 fixed, gate 48/48). **NEW** `/root/finance/marg_backfill.py` `e101c595619dc39a19397abb040d64c9` (placed, dry-run by default). Kits `S182_P1a` · `S182_P2a` · `S182_M1a` in `deploy_kits/`.
- **D320 minted** (the repo stays PUBLIC, owner ruling — with the binding corollary that no PHI-bearing artefact enters it). **F-96–F-99 raised**, F-98 fixed the same session. **No incident** — every failure was caught by a gate, by an offline rehearsal, or by reading the code before writing it. ⚠ **F-97 is the one to carry:** Phase 0 verifies documents; **nothing verifies the Register's live-code pins**, and one was stale by two sessions. Mitigated per-kit by a new **live-file currency gate**; the structural fix is owed.
- ⭐ **S183 top task: the Marg April→August backfill** (v2 driver writing `sale_item` AND `sale_line_item`; the `marg_export` column map + activation; the fortnight chunks). Reachable and zero-risk: filed days run 1 Apr → 13 Aug and both target tables are empty. Cold-kit count **2 of 3–5**. Next free: **D321 · F-100 · A-D25 · Session 183.** This was Session 182.

**END OF CANONICAL_MANIFEST — S182.**

---

### §S183 EOS (16 Aug 2026, FULL — the F-97 fix shipped; the Marg feed went live + backfilled 5 months; the Sanjeevni cash chain reconciled from bank records and found whole)
**S183 canonical filenames (Phase-0 mapping):** `KB_Register_v5_5_S183.md` (`3cad79e6…`) · `HANDOFF_RUNBOOK_2026-08-16_Session183close_v117.md` (`cc523169…`) · `START_HERE_SESSION_184.md` (`18c2bf46…`) · this `CANONICAL_MANIFEST.md`. **Two NEW Tier-1 finance docs** in project knowledge: `S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md` (`de4f88b3a48e71c19e708f6a1d274f41`) · `S183_Sanjeevni_Cash_Reconciliation_YesBank.md` (`ca49c4113b3cbd658fd2986b1aa7bb89`). (Also created this session: `S183_Marg_backfill` analysis is folded into the design doc.)
- **Tier-0 bumps:** Register v5.4 → **v5.5** · Runbook v116 → **v117** · START_HERE 183 → **184**.
- **Tier-1 this close:** `KB_History_Archive` STAYS **v1.30** and `Fault_Action_Register` STAYS **v2.18** — the formal **§S183 Archive append + F-100–F-104 Fault-Register append are OWED as S184 opening housekeeping** (precedent: S181 applied owed appends). The S183 narrative and findings are captured verbatim in Register v5.5, Runbook §0, and the two S183 finance docs, so nothing is lost; only the formal into-Archive fold is deferred. All other Tier-1/Tier-2 rows UNCHANGED (re-hash owed at S184 Phase 0 as usual).
- **Live VPS code (Register-pinned, NOT manifest rows; F-31 keeps PHI out):** `marg_report.py` `28b47d44…` → **`829f4344df6e086510bb0fb6112ecb77`** (reads `.xlsx` too; `.xls` path byte-identical) · `marg_backfill.py` `e101c595…` → **`fa33ec8a6dfa0ee0b6af5613160f3394`** (v2, ran to completion) · **NEW** migration `S183_marg_map` `9340675c9105f9d5e78cc37980494999` (applied) · **NEW** `/root/deploy/verify_live_pins.py` `ce36dbf10e7d5bbd5310507add41f3cb` + `gen_live_pins.py` + generated `live_pins.txt`. The 9 corrected call-hook/verdict pins are in the Register live-file table. finance.db gained 15,574 `sale_line_item` + 982 `sale_item` rows via the backfill; `day_line` (the money) untouched.
- **D321 minted. F-100–F-104 raised.** No incident — every failure was caught by a gate or by read-only analysis. **The Sanjeevni cash reconciliation was read-only; no live finance write was made** (the 16 Yes Bank deposit bookings + opening anchor + Yes Bank reconciliation are the S184 ⭐ top task, gated). Cold kit `KB_S183_close` taken (count **3 of 3–5**, F-89 met).
- ⭐ **S184 top task: book the Sanjeevni cash correction (16 Yes Bank deposits + ₹40k drawer advances + opening anchor + Yes Bank reconciliation), then WALK-IN reclass (F-104), then the daily Marg live flow.** Next free: **D322 · F-105 · A-D25 · Session 184.** This was Session 183.

**END OF CANONICAL_MANIFEST — S183.**
