# START HERE — Session 148 · Dr. Manoj Agarwal Clinic automation

Hi Claude. Continuing the clinic-automation project — **Session 148**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Working protocol (strict):** plain language, no assumed coding knowledge · **ONE step at a time**, wait for my explicit confirmation · full-file replacements, never diffs · **ALL-CAPS from me = urgent** · mask all secrets/tokens · nothing live is rebuilt without my OK, manual fallback always stays · build offline → `py_compile` (I use `python`) → I install · VPS python is `/root/wa/venv/bin/python3`. End a session with **EOS** or **EOS-light** (routine is canonical in `END_OF_SESSION_PROMPT_v4.md`).

---

## Phase 0 — verify the canonical set FIRST

Verify **every** doc in `CANONICAL_MANIFEST.md` by md5 (all tiers). **Read into context only Tier 0.** Open Tier 1 on demand; Tier 2 is hash-verified only. A mismatch halts work until reconciled (D172/D188).

**Tier 0 (read at start):**

| Doc | Version |
|---|---|
| `CANONICAL_MANIFEST.md` | S147 |
| `START_HERE_SESSION_148.md` | this file |
| `KB_Register_v2.0` | current state — authority on what's true NOW |
| `HANDOFF_RUNBOOK_2026-07-19_Session147_v85` | §0 what happened · §2 backlog |
| open incident | none (F-44 closed) |

Everything else (KB History Archive, the specs, dossiers) is Tier 1/2 — verified by hash, read only when a task touches it.

---

## §0 — What happened in S147 (the KB restructure)

- **D247** — three-tier canonical system (0 loop · 1 reference · 2 frozen) + the KB split.
- **KB split:** `KB_Register_v2.0` (current state, ~490 lines) + `KB_History_Archive_v1.0` (all history, verbatim). Proven: **0 of 3,500 content lines dropped**. Monolithic KB v1.72 retired.
- **Decisions index completed D121→D246** (45 undefined decisions authored from the Archive, not memory).
- **`CANONICAL_MANIFEST.md`** — the linchpin Phase 0 verifies.
- **`END_OF_SESSION_PROMPT_v4`** — tier-aware close-out (appends to Archive, updates the small Register; never rewrites the whole KB).
- **4 frozen-product dossiers** built/adopted: Attendance · Nutrition/Diet (`clinic_writer`) · Callback Tracker **core** · WABA templates. Plus `SYSTEM_DOC_COVERAGE_MAP_S147`.
- **Consent HTML** reclassified OUT of the frozen set → deferred (folded into the in-development Surgical Estimate tool; not yet in GitHub).
- **Callback freeze split confirmed:** write-path core frozen; console/dashboard/health/outcome stay active Tier 1.
- **Repo hygiene:** the live `Main.gs` (D206 trigger-ownership fix) was pushed over the stale repo copy.

---

## §2 — Backlog for S148

1. **Repo trim (PowerShell/cmd, LOCAL git repo).** Generate a PowerShell/cmd script that moves every superseded doc in `canonical-docs/` (and the historical `docs/`) into `canonical-docs/archive/`, leaving only the current manifest set in the active folder. Git history + the KB History Archive already preserve content, so this is safe. Then adopt the standing rule: on any version bump, old file → `archive/`.
2. **`Fault_Action_Register_v2.1` hash** — reconcile into Phase 0 (it was drifting outside the verified set).
3. **Gap consolidations** (only when the system next needs sustained attention — see the coverage map): (1) Follow-up Tracker → (2) Call-hook capture family → (3) WhatsApp API family.
4. **Surgical Estimate tool + Consent HTML** — dossier + freeze when it ships to GitHub.
5. **Carried:** Insight Harvest items (best calling time, retry-value curve, min talk duration, said-vs-actually-came); D223 doctor-portal gist tile (feeds live, build deferred).

---

## Numbers & sources

Next free: **D248 · F-45 · Session 148.**
Connected: Google Drive · Gmail · Notion ("Clinic HQ") · GitHub (`drmanoj-clinic-automation`). ClickUp parked (D17).

**Read the manifest + Register + Runbook, confirm, then pick a backlog item.**
