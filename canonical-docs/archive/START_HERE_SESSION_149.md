# START HERE — Session 149 · Dr. Manoj Agarwal Clinic automation

Hi Claude. Continuing the clinic-automation project — **Session 149**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Working protocol (strict):** plain language, no assumed coding knowledge · **ONE step at a time**, wait for my explicit confirmation · full-file replacements, never diffs · **ALL-CAPS from me = urgent** · mask patient numbers (last-4) + all secrets/tokens · nothing live is rebuilt without my OK, manual fallback always stays · build offline → `py_compile` (I use `python`) → I install · VPS python is `/root/wa/venv/bin/python3`. End a session with **EOS** or **EOS-light** (routine is canonical in `END_OF_SESSION_PROMPT_v4.md`).

---

## Phase 0 — verify the canonical set FIRST

Verify **every** doc in `CANONICAL_MANIFEST.md` by md5 (all tiers). **Read into context only Tier 0.** Open Tier 1 on demand; Tier 2 is hash-verified only. A mismatch halts work until reconciled (D172/D188).

**Tier 0 (read at start):** `CANONICAL_MANIFEST.md` · this file · `KB_Register` (current state, now **v2.1**) · `HANDOFF_RUNBOOK_2026-07-19_Session148_v86` (§0 what happened · §2 backlog) · open incident: **none**.

Everything else (KB History Archive **v1.1**, the specs, dossiers, Fault Register) is Tier 1/2 — verified by hash, read only when a task touches it.

---

## §0 — What happened in S148 (short)

A cleanup + repo-hygiene session, no live code. Verified the S147 install; rebuilt the START-HERE evergreen template v4→v5 (now defers to the manifest for versions); reconciled the manifest (pinned the `Fault_Action_Register` hash after PK==GitHub provenance, flipped STATUS to installed); ran the **repo trim** (105 superseded docs → `archive/`, Maintenance SOP rescued; commit `0db5c01`, pushed + verified); installed a permanent git-PATH fix. Raised **F-45** (FAR titled v2.1 with no v2.1 changelog row) and flagged that **§S147 was missing from the Archive** (counter fixed; full backfill parked). No decision minted.

---

## §2 — Backlog for S149

**Repo-side (produce-then-push; git works in any PowerShell window now):**
1. Push `API_QUICK_REFERENCE_CARD.md` — current doc, absent from the repo.
2. Push `WABA_Approved_Templates_v1_S137.md` → `canonical-docs/dossiers/` — current dossier, absent.
3. Refresh `README_CANONICAL_SET.md`, then push.
4. **F-45:** add the missing `Fault_Action_Register` v2.1 changelog row; bump + re-pin its manifest hash.
5. Phase-2 repo tidy: fold remaining historical `docs/` into `canonical-docs/archive/`.

**Documentation:**
6. Backfill **§S147** into `KB_History_Archive` from runbook v85 §0 + the D247 doc (deliberately, not from memory).

**Carried:** Insight Harvest items; D223 doctor-portal gist tile.

---

## Numbers & sources

Next free: **D248 · F-46 · Session 149.**
Connected: Google Drive · Gmail · Notion ("Clinic HQ") · GitHub (`drmanoj-clinic-automation`). ClickUp parked (D17).

**Read the manifest + Register + Runbook, confirm, then pick a backlog item.**
