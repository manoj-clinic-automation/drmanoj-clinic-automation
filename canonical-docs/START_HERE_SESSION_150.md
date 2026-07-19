# START HERE — Session 150 · Dr. Manoj Agarwal Clinic automation

Hi Claude. Continuing the clinic-automation project — **Session 150**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Working protocol (strict):** plain language, no assumed coding knowledge · **ONE step at a time**, wait for my explicit confirmation · full-file replacements, never diffs · **ALL-CAPS from me = urgent** · mask patient numbers (last-4) + all secrets/tokens · nothing live is rebuilt without my OK, manual fallback always stays · build offline → `py_compile` (I use `python`) → I install · VPS python is `/root/wa/venv/bin/python3`. End a session with **EOS** or **EOS-light** (routine is canonical in `END_OF_SESSION_PROMPT_v4.md`).

---

## Phase 0 — verify the canonical set FIRST

Verify **every** doc in `CANONICAL_MANIFEST.md` by md5 (all tiers). **Read into context only Tier 0.** Open Tier 1 on demand; Tier 2 is hash-verified only. A mismatch halts work until reconciled (D172/D188). *If a "pending" item looks done, verify it against reality before acting — twice last arc a backlog item was already complete.*

**Tier 0 (read at start):** `CANONICAL_MANIFEST.md` · this file · `KB_Register` (current state, **v2.2**) · `HANDOFF_RUNBOOK_2026-07-19_Session149_v87` (§0 what happened · §2 backlog) · open incident: **none**.

Everything else (KB History Archive **v1.1**, the specs, dossiers, Fault Register **v2.1**) is Tier 1/2 — verified by hash, read only when a task touches it.

---

## §0 — What happened in S149 (short)

An EOS-light close-out that **ended the housekeeping arc** — S150 starts on real work. **F-45 resolved** (FAR v2.1 changelog row added). **§S147 backfilled** + **§S149 appended** to the Archive. **Register v2.1 → v2.2** (findings line advanced to F-46; D247 added to its index). **README** refreshed; **manifest** reconciled (its Tier-0 rows had drifted). Backlog items 1–2 (repo pushes) found **already done** and struck. **Phase-2 repo tidy** produced (38 archived; 12 held for your ruling). No decision minted.

---

## §2 — Backlog for S150

**Owed from S149 (my keyboard — see the S149 install/push runbook):**
1. Install the S149 set into project knowledge + push to GitHub (corrected FAR, updated Archive, refreshed README, regenerated manifest, runbook v87, this START-HERE); run `Repo_Trim_Phase2_S149.ps1`.
2. Rule on the **12 held `docs/` files** (current vs superseded) so the tidy can finish.

**Housekeeping: NONE — closed at S149.**

**Carried (real work):** Insight Harvest items; D223 doctor-portal gist tile.

**Live-systems Track 2 (when you turn to live work):** WABA sends blocked on D120 (Lokesh) · `wa_approve` still nohup-not-systemd · key rotations overdue.

---

## Numbers & sources

Next free: **D248 · F-46 · Session 150.**
Connected: Google Drive · Gmail · Notion ("Clinic HQ") · GitHub (`drmanoj-clinic-automation`). ClickUp parked (D17).

**Read the manifest + Register + Runbook, confirm, then pick a backlog item.**
