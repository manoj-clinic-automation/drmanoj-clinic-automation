# HANDOFF RUNBOOK — Session 149 (v87)

**Dr. Manoj Agarwal Clinic · Bareilly · 19 Jul 2026 · Owner: Dr. Manoj Agarwal · with Claude.**
**Type: documentation + repo-hygiene session (EOS-light). No live/VPS code touched. GitHub pushes owed (produce-then-push).**

---

## §0 — What happened this session

The S148/S149 sanitization arc's last loose ends were cleared, and the canonical set was made internally consistent again.

- **Two "pending" repo pushes were already done.** `API_QUICK_REFERENCE_CARD.md` and `WABA_Approved_Templates_v1_S137.md` were found in the GitHub mirror, **byte-for-byte identical** to project knowledge and their manifest pins. The backlog that called them "absent" was stale — struck, not re-pushed.
- **F-45 RESOLVED.** `Fault_Action_Register` (titled v2.1, changelog stopped at v2.0) gained its missing v2.1 row — documents §0.35 / **D204 (S132)**: the Lane-1 auto-responder does not exist and is not scheduled. No lane/procedure changed. `fde74c…` → `3bfeac72…`.
- **§S147 backfilled** into `KB_History_Archive` from Runbook **v85** §0 (pulled back from `canonical-docs/archive/`) + `D247_Canonical_Data_Management_S147.md` — from the artefacts, not memory; every md5 cross-checked. Re-pinned.
- **README refreshed.** The repo `README_CANONICAL_SET.md` was stuck at Session 125; rewritten to the tiered model, now defers to the manifest (can't go stale on a bump).
- **Phase-2 repo tidy produced** — `Repo_Trim_Phase2_S149.ps1` archives **38** superseded docs (3 `canonical-docs/` stragglers + 35 historical `docs/`), and **holds 12** live/uncertain clinic + reference docs for an owner ruling (no wildcard sweep — the S148 "don't bury a live file" rule).
- **Register housekeeping finished (v2.1 → v2.2)** — findings line advanced (F-45 RESOLVED, next free F-46); **D247 added to its decisions index** (was header-only). Nothing else in the Register changed.
- **Manifest reconciled** — the stale Tier-0 rows (they described the S148-*open* set because the S148-*close* update was missed) corrected to the live set; FAR + Archive re-pinned. Then this Archive got its own **§S149** entry, and this runbook + `START_HERE_SESSION_150` were generated.

**F-45 resolved · no new finding · no decision minted (D248 stays free) · no live-system change · no incident · Gmail health-note skipped (no manual health check).**

---

## §1 — Mental models (carry these)

- **Phase 0 is the gate.** Verify every manifest row by md5 (all tiers); read Tier 0 only; open Tier 1 on demand; Tier 2 is waiver-only. A mismatch halts work.
- **A stale backlog is the same fault as a stale record.** Twice this arc, "pending" items were already done (the two repo pushes; the manifest itself described a prior session's state). **Verify "pending" against reality before acting** — a check that cannot fail is not a check.
- **The repo is a mirror; live/project-knowledge is canonical (D160).** Reorganise the repo freely; git history + the Archive preserve everything. But the repo can lag — verify cross-store agreement (PK == GitHub) before pinning a hash (D188).
- **A doc titled vX with no vX changelog row is the stale-record family** — caught at v1.71, §S131, §S143, and F-45. When a version marker and its changelog disagree, distrust and check.
- **Don't wildcard-sweep a folder — classify, then move.** The Phase-2 tidy moves only the 38 it is certain about and holds the 12 it isn't; the S148 Maintenance-SOP near-miss is why.
- **Produce-then-push.** The assistant is read-only on GitHub; every repo change is built + verified offline and pushed at the owner's keyboard.

---

## §2 — Open backlog (the live one)

**Owed from this session (owner's keyboard — the S149 install/push runbook has the exact steps):**
1. **Install the S149 set** into project knowledge (replace `CANONICAL_MANIFEST.md`, `Fault_Action_Register_v2_1.md`, `KB_History_Archive_v1_1_S148.md`; add `START_HERE_SESSION_150`, this runbook v87; retire `START_HERE_SESSION_149`, runbook v86).
2. **Push to GitHub** — overwrite the corrected FAR, updated Archive, refreshed README, regenerated manifest, the new runbook + START_HERE; then run `Repo_Trim_Phase2_S149.ps1` (dry-run → `-Execute`); commit + push.
3. **Rule on the 12 held `docs/` files** (current vs superseded), then I extend the tidy.

**Carried (unchanged — REAL work, not housekeeping; housekeeping ended at S149):**
4. Insight Harvest items (best calling time · retry-value curve · min talk duration · said-vs-actually-came).
5. D223 doctor-portal gist tile (feeds live, build deferred).

**Live-systems Track 2 (separate from the doc arc — pick up when you turn to live work):**
6. WABA sends blocked on the MyOperator authorizer fault (**D120**, Lokesh's fix).
7. `wa_approve` still `nohup`, not a systemd unit.
8. Service-account + key rotations overdue (standing high-priority security item).

**Next free: D248 · F-46 · Session 150.**
