# START HERE — Session 151 · Dr. Manoj Agarwal Clinic automation

Hi Claude. Continuing the clinic-automation project — **Session 151**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Working protocol (strict):** plain language, no assumed coding knowledge · **ONE step at a time**, wait for my explicit confirmation · full-file replacements, never diffs · **ALL-CAPS from me = urgent** · mask patient numbers (last-4) + all secrets/tokens · nothing live is rebuilt without my OK, manual fallback always stays · build offline → `py_compile` (I use `python`) → I install · VPS python is `/root/wa/venv/bin/python3`. End a session with **EOS** or **EOS-light** (routine is canonical in `END_OF_SESSION_PROMPT_v4.md`).

---

## Phase 0 — verify the canonical set FIRST

Verify **every** doc in `CANONICAL_MANIFEST.md` by md5 (all tiers). **Read into context only Tier 0.** Open Tier 1 on demand; Tier 2 is hash-verified only. A mismatch halts work until reconciled (D172/D188). *If a "pending" item looks done, verify it against reality before acting.*

**Tier 0 (read at start):** `CANONICAL_MANIFEST.md` · this file · `KB_Register` (current state, **v2.3**) · `HANDOFF_RUNBOOK_2026-07-22_Session150_v88` (§0 what happened · §2 backlog) · open incident: **none**.

Everything else (KB History Archive **v1.2**, the specs, dossiers, Fault Register **v2.1**) is Tier 1/2 — verified by hash, read only when a task touches it.

---

## §0 — What happened in S150 (short)

A **FULL EOS** — the **frozen** `clinic_writer` (Nutrition/Diet write-path, Tier 2) was changed under an explicit **waiver (D248)** and re-frozen. `vitals_page.html` **v26 → v28** (md5 `fcedae303b620f3e5199f4b1e4766510`), **installed live** on `D:\clinic_writer\`: Hindi spelling tidy (closes the dossier caveat) · exercise library 126 → **128** · PIVD stop-rule · bottle-roll dose · the Excel `Diet_Chart` **ported** as an optional printable **diet-aware** diet sheet (no shopping list) · a **screen-only** comfort theme (print byte-identical). Engine/app/schemas untouched; a build-time `cond`-scope error was caught by the node smoke test before delivery and fixed (lesson, not a fault). **Dossier → v1.1 · Register → v2.3 · Archive §S150 → v1.2.** No new finding.

---

## §2 — Backlog for S151

**Owed (doc install/push — my keyboard; the S150 deltas fold into the same pending set):**
1. Install the pending doc set into project knowledge + push to GitHub — **Register v2.3, Archive v1.2, Nutrition dossier v1.1, Runbook v88, this START-HERE, regenerated manifest**, plus the still-owed S149 items (corrected FAR, refreshed README); then run `Repo_Trim_Phase2_S149.ps1`.
2. Rule on the **12 held `docs/` files** (current vs superseded).
3. **Recompute the `clinic_writer/` folder digest** on the installed folder and re-pin it (dossier + manifest Tier-2 row) — one file (`vitals_page.html`) changed, so the old folder digest `df0b0c34…` is stale; the specific file md5 `fcedae30…` is the pinned truth meanwhile.

**Carried (real work):** Insight Harvest items · D223 doctor-portal gist tile.

**Live-systems Track 2 (when you turn to live work):** WABA sends blocked on D120 (Lokesh) · `wa_approve` still nohup-not-systemd · key rotations overdue.

---

## Numbers & sources

Next free: **D249 · F-46 · Session 151.**
Connected: Google Drive · Gmail · Notion ("Clinic HQ") · GitHub (`drmanoj-clinic-automation`). ClickUp parked (D17).

**Read the manifest + Register + Runbook, confirm, then pick a backlog item.**
