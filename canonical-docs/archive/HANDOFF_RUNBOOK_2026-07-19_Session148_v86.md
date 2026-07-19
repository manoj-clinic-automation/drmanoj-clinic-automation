# HANDOFF RUNBOOK — Session 148 (v86)

**Dr. Manoj Agarwal Clinic · Bareilly · 19 Jul 2026 · Owner: Dr. Manoj Agarwal · with Claude.**
**Type: documentation + repo-hygiene session (FULL EOS). One GitHub commit (repo trim). No live/VPS code touched.**

---

## §0 — What happened this session

A cleanup session that finished off the S147 restructure's loose ends and trimmed the repo.

- **S147 install verified** — all twelve restructure files present in project knowledge; retired v1.72 + EOS v3 absent.
- **START-HERE template v4 → v5** — the evergreen paste-in / custom-instructions template was rebuilt. It now carries Phase 0 + the tier model and **defers to the manifest for document versions**, so it can no longer go stale on a version bump (the fault that retired v4). Installed to project knowledge + custom instructions. v4 archived in the trim.
- **Manifest reconciled** — `Fault_Action_Register_v2.1` hash pinned (`fde74c…`) after confirming the project-knowledge copy and GitHub mirror are byte-for-byte identical; STATUS line flipped from "proposed" to "installed / canonical." The FAR is now inside the Phase 0 verified set.
- **Repo trim** — `Repo_Trim_S148.ps1` moved **105** superseded docs into `canonical-docs/archive/` and **rescued** the current Maintenance SOP out of `docs/`. Commit `0db5c01`, **106 renames, 0 content changes**, pushed and externally verified from GitHub (raw-file probes: old paths 404, new paths 200).
- **git-PATH permanent fix** — a PowerShell-profile snippet now auto-finds GitHub Desktop's git in every new window (survives GHD updates). Confirmed working. This fixes the "git is not recognized" failure that stopped the first `-Execute` run.

**Flags raised (no code):**
- **F-45** — `Fault_Action_Register` is titled v2.1 but its changelog stops at v2.0 (missing changelog row). Fix parked to S149.
- **Archive §S147 gap** — the S147 restructure narrative was never appended to `KB_History_Archive` (its story is in this runbook family + the D247 doc). Counter corrected in Archive v1.1; full backfill parked to S149.

**No live-system change · no incident · no new fault code · no SOP/surveillance change · Gmail health-note skipped (no manual health check).**

---

## §1 — Mental models (carry these)

- **Phase 0 is the gate.** Verify every manifest row by md5 (all tiers); read Tier 0 only; open Tier 1 on demand; Tier 2 is waiver-only. A mismatch halts work.
- **The repo is a mirror; live/project-knowledge is canonical (D160).** Trim and reorganise the repo freely — git history + the Archive preserve everything. But the repo can lag project knowledge (this session found two current docs missing from GitHub).
- **A doc titled vX with no vX changelog row is the stale-record family** — the same failure caught at v1.71, §S131, §S143, and now F-45. When a version marker and its changelog disagree, distrust and check.
- **A naive "sweep everything" instruction can bury a current file** — the Maintenance SOP was mislocated in `docs/`; verifying its hash before the sweep is what saved it. Classify, then move; don't wildcard-move.
- **Provenance = cross-store agreement, not a filename (D188).** The FAR hash was pinned only after PK==GitHub byte-for-byte.

---

## §2 — Open backlog (the live one)

**Repo-side (all "produce-then-push" — need a keyboard session; git now works in any window):**
1. **Push `API_QUICK_REFERENCE_CARD.md`** into the repo — current Tier-1 doc, absent from GitHub.
2. **Push `WABA_Approved_Templates_v1_S137.md`** into `canonical-docs/dossiers/` — current dossier, absent.
3. **Refresh `README_CANONICAL_SET.md`** to describe the post-restructure set, then push.
4. **`Fault_Action_Register` (F-45)** — add the missing v2.1 changelog row; bump + re-pin its hash in the manifest.
5. **Phase-2 repo tidy** — fold the remaining historical `docs/` files into `canonical-docs/archive/` (a second PowerShell pass).

**Documentation:**
6. **Backfill §S147** into `KB_History_Archive` from HANDOFF_RUNBOOK v85 §0 + `D247_Canonical_Data_Management_S147.md` (done deliberately, not from memory).

**Carried (unchanged):**
7. Insight Harvest items (best calling time · retry-value curve · min talk duration · said-vs-actually-came).
8. D223 doctor-portal gist tile (feeds live, build deferred).

**Next free: D248 · F-46 · Session 149.**
