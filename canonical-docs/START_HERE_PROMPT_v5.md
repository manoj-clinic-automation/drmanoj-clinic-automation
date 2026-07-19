# START-HERE PROMPT — v5 — paste to begin a new session

> **The canonical set lives in this Project's knowledge** (no zip to upload). Code lives in
> **GitHub** (`drmanoj-clinic-automation`, connected, read-only). Cold-backup zip is on the PC only.
> This block is also saved as the project's **custom instructions**, so it applies automatically.
>
> **v5 change (S147 restructure, D247):** the KB is now **split** into a small **KB Register**
> (current state) + an append-only **KB History Archive** (all history), and every canonical
> document is listed with its md5 in **`CANONICAL_MANIFEST.md`**. This prompt no longer names
> document *versions* — the manifest is the single source of truth for what is canonical and
> current, so this prompt cannot go stale on a version bump again (the fault that retired v4).

---

Hi Claude. Continuing my clinic-automation project (**Session __ — use the next number**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**
- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → py_compile (I use `python`, not `python3`) → then I install.
- For VPS python, always use `/root/wa/venv/bin/python3` (system python3 lacks gspread).

**Ending a session:** say **"EOS"** (full close-out, code changed) or **"EOS-light"**
(fold-in/documentation session, no code touched). The close-out routine is canonical in project
knowledge as **`END_OF_SESSION_PROMPT_v4.md`** (tier-aware: appends to the History Archive,
updates the small Register, maintains the manifest — no more whole-KB rewrites).

---

**Phase 0 — do this FIRST, every session (D247). Verification before work.**

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin). It lists every canonical doc, its
   tier, and its md5.
2. **Verify every row by md5** — hash-compare only, cheap, all tiers. *A row whose hash does not
   match halts work until reconciled* (D172/D188). A filename is not provenance (D188).
3. **Read into context only Tier 0:** the manifest, this START-HERE, the **KB Register**, the
   **HANDOFF_RUNBOOK**, and any **open incident**. Open **Tier 1** (Archive, specs, dossiers, API
   card, Fault Register…) **only when the task touches it**. **Tier 2** (frozen products) is
   hash-verified but never read in the loop and never edited without an explicit waiver (D34).
4. Then confirm, and ask which backlog item to start (**HANDOFF_RUNBOOK §2** = the live backlog).

---

**Where the truth lives — read the manifest for the doc set + current versions; don't hard-code them here:**

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers, and hashes. WINS on "what is canonical / current."
- **KB Register** (Tier 0) — authority on what is true **NOW**: systems register, decisions index,
  live-file versions, backlog pointer.
- **KB History Archive** (Tier 1) — every session narrative + full decision text, **verbatim**.
  History only; opened on demand.
- **HANDOFF_RUNBOOK** (Tier 0) — §0 what happened last · §2 live backlog.
- **Fault_Action_Register** (Tier 1) — the findings/faults register (F-##).
- **SYSTEM_DOC_COVERAGE_MAP** — every subsystem → its authoritative doc ("where is the reference
  for tool X").
- Specs are Tier 1, opened on demand: Umbrella Architecture · Call Console Evolution ·
  Diagnostics & Surveillance · Frontend Dashboard · Maintenance-SOP · API Quick Reference ·
  AI Verdict Layer Master.

> **No canonical document is a delta (D202, clarified by D247).** Canonical docs are fully
> consolidated single files. The KB is *split* into Register + Archive — two complete files,
> neither a delta chain. If a document arrives claiming to "carry forward vX unchanged," distrust
> it and verify against the manifest: that failure has bitten this project before (`Diagnostics_v1_7`
> silently dropped sixteen lines — F-23; two other docs were stumps, rebuilt at S131 from cold
> backups because git and Drive did not have them).

Code lives in **GitHub** (`drmanoj-clinic-automation`). Patient data is **NOT** in this project.

---

**Connected sources available this session:**
- Google Drive (`drmka.ortho@gmail.com`) — read/write docs, incident reports, SOPs
- Gmail — draft/send alerts, read MyOperator notification emails
- Notion ("Clinic HQ") — update register, decisions, active projects
- GitHub (`drmanoj-clinic-automation`) — read any code file directly
- ClickUp — **parked (D17), not in active use.** Listed only so it isn't forgotten if it's ever
  revived; don't check it or suggest it otherwise.

**Maintenance & SOP project:** does not exist yet (created after `Diagnostics.gs` is live ≥1 real
clinic day). Anything in the specs that references it is forward-looking, not a current gap to
flag each session.

---
*START_HERE_PROMPT — v5 · supersedes v4 · adopted S148. Session-specific entry points (e.g.
`START_HERE_SESSION_###`) are regenerated at each close-out; THIS evergreen prompt is the
custom-instructions template and should change only when the session-start procedure itself changes.*
