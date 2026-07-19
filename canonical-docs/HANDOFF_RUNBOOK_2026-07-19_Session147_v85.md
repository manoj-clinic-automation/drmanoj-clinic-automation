# HANDOFF RUNBOOK — Session 147 (v85)

**Dr. Manoj Agarwal Clinic · Bareilly · 19 Jul 2026 · Owner: Dr. Manoj Agarwal · with Claude.**
**Type: documentation/restructure session (EOS). One repo code push (Main.gs).**

---

## §0 — What happened this session

S147 was a **knowledge-base restructure** — solving the problem that the canonical docs had grown huge and were read at the start and rewritten at the end of every session.

- **D247 minted** — a three-tier canonical system (**Tier 0** session loop · **Tier 1** reference · **Tier 2** frozen) and the KB split. Clarifies D202/S100 (still consolidated single files, no delta chain).
- **KB split** — the monolithic `Clinic_Master_KB_SystemsRegister_v1.72` (~4,300 lines) became:
  - `KB_Register_v2.0` (md5 `651c254b…`) — current state only (~490 lines): systems register, decisions index, live-file versions, backlog. Rides the loop.
  - `KB_History_Archive_v1.0` (md5 `44681d05…`) — every session narrative + full decision text, **verbatim**. Out of the loop.
  - **Proof:** every source line 1→4307 assigned to exactly one file; **0 of 3,500 content lines dropped**. Three self-checks tried to pass while wrong (a newline off-by-one that blinded its own check, plus two dedupe checks fooled by mis-computed sets) — each caught by an artefact-level second check. Live "a check that cannot fail is not a check."
- **Decisions index completed** — D121→D246 in the Register; the 45 previously-undefined decisions (D189–D218, D225–D239) authored from their full text in the Archive, never from memory.
- **`CANONICAL_MANIFEST.md`** created — the linchpin every Phase 0 verifies (all tiers by hash; read Tier 0 only).
- **`END_OF_SESSION_PROMPT_v4`** (md5 `9fa2be50…`) — tier-aware close-out: append to Archive, update Register, maintain the manifest; no more whole-KB rewrites.
- **Frozen-product dossiers (Tier 2):**
  - Attendance (`attendance/`) — dossier `efc17e19…`, folder digest `dc12f4a0…`.
  - Nutrition/Diet write-path (`clinic_writer/`) — dossier `3b869d0e…`, folder digest `df0b0c34…`, frozen **as-is** (Hindi-spelling tidy = waiver-gated).
  - Callback Tracker **core** (`dashboard/`) — dossier `7e445ff0…`, live project digest `e4fd4512…`. Freeze split **confirmed**: write-path core frozen (WebApp D34 + Config/MyOperator/Netting/Sheets/Main/manifest + the Sheet); console/dashboard/health/outcome active Tier 1.
  - WABA templates — adopted (`WABA_Approved_Templates_v1_S137`, `63dd1883…`).
  - `SYSTEM_DOC_COVERAGE_MAP_S147` — every subsystem → its authoritative doc + the three consolidation-candidate gaps.
- **Consent HTML reclassified** — out of the frozen set; it now lives inside the in-development **Surgical Estimate tool** (not in GitHub yet). Dossier/freeze deferred until it ships.
- **Repo code push** — the live `Main.gs` (D206: `removeTriggers()` scoped to Main's own three triggers) was pushed over the stale pre-D206 repo copy. Verified live-vs-repo: all other `dashboard/` files already matched.

---

## §1 — Mental models (carry these)

- **Tiers:** read Tier 0 every session; verify everything by hash; open Tier 1 on demand; never read/edit Tier 2 without a waiver.
- **Dossier = frozen-product artefact.** Active systems are documented by their living spec/SOP + the code you read when you touch them — don't dossier active churn.
- **Register = authority on NOW; Archive = authority on history.** They can't conflict.
- **Live is canonical (D160).** The Apps Script export / VPS wins over the repo; the repo is a mirror.
- **The manifest is the linchpin.** If a doc isn't a row in it, it doesn't carry forward.

---

## §2 — Open backlog

1. **INSTALL the restructure** (if not already done at S147 close): project-knowledge swaps — retire v1.72 + EOS v3; add Register v2.0, Archive v1.0, manifest, EOS v4, the 4 dossiers, coverage map, D247, START_HERE_148, this runbook.
2. **Repo trim — S148, via PowerShell/cmd on the local repo.** Move superseded `canonical-docs/` + historical `docs/` versions to `canonical-docs/archive/`; keep only the manifest set active. Standing rule thereafter: version bump → old file to `archive/`.
3. **`Fault_Action_Register_v2.1` hash** — reconcile into Phase 0.
4. **Gap consolidations** (only when next needed): Follow-up Tracker · Call-hook family · WhatsApp API family.
5. **Surgical Estimate tool + Consent HTML** — dossier/freeze on ship.
6. **Carried:** Insight Harvest items; D223 gist tile.

**Next free: D248 · F-45 · Session 148.**
