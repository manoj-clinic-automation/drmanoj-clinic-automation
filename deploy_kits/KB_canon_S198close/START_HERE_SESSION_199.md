# START HERE — Session 199

Hi Claude. Continuing the clinic-automation project (**Session 199**). I'm Dr. Manoj
Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre / Sanjeevni Medicos,
Bareilly. Solo practice, older Hindi-first semi-urban patients. Working protocol unchanged
(plain language; ONE step at a time, wait for my OK; full-file replacements or fail-loud
in-place patches; mask patient numbers to last-4 and all tokens; nothing live rebuilt
without my OK; manual workflow stays as fallback; build/test offline → py_compile →
pyflakes → I install; VPS python `/root/wa/venv/bin/python3` for the ledger).

## Phase 0 — verification before work (D247)

1. Open `CANONICAL_MANIFEST.md` (Tier 0 · linchpin) and verify every row by md5. Current
   canon after the S198 close: Register **v5.43** · History Archive **v1.45** · Fault
   Register **v2.35** · Runbook **v132** · this file. A clean Phase 0 is expected — a
   mismatch is an incident, not a known debt.
2. Read Tier 0 only: this file · KB Register v5.43 · HANDOFF_RUNBOOK v132 · any open
   incident. Open Tier 1 on demand (the **D335 signed contract is Tier 1 and THIS
   session's task touches it — open it**).
3. **The `verify_live_pins.py` expectation:** GREEN, `source: VERIFIED`, against
   `live_pins_S198close.txt` (generated from v5.43 — A8). If the box still carries the
   S197 list, it will show RED drift 3 on `portal.py`/`finance_app.py`/`portal_gist.py` —
   files the box has right; that is the stale-list condition (F-134), fixed by copying the
   new list, not an incident.

## The live pins to trust (the S198 close set)

- `portal.py` **`ab019dda3ac68e566de017c5ae536a6b`** (S198_G1 — the eight-kit chain)
- `finance_app.py` **`2c99b2c6c719091deada5603fc295c90`** (S198_H2; smoke 680)
- `portal_gist.py` **`ef3ad196a00c2df44a7770553237a0e6`** (S198_G1; selftest 27)
- `finance_ui/finance_entry.html` **`92477b068c67e28661b049b7f3385708`** (S193_UX / F-169)
- `staff_ledger.py` **`acd7b538ec9476f86e243c73eec3d3fd`**
- `staff_register.py` **`9087954c8a4a891e8cdd848d6a9d48b2`** (v0.4)
- `att_month_report.py` **`9ab98313bbda7ae5555fb4b5a5a82c4b`** (v2.6)
- `email_agent.py` **`e535c4f8116abd2fe60b7fda334f33ec`**
- Marg `margpull/signatures.json` **`1b21f3bf582d9f19fb8959a5336b0ba0`** (5 types — the
  item-wise purchase export is NOT among them yet; adding it is this session's Club-3 step)

## Next-free numbers

**D336 · F-174 · A-D25 · Session 199.** (The Auditor mints AF-# only, in its own chat.)

## THE FLAGSHIP — the Purchase Portal build (D335, SIGNED at S198)

`S198_Purchase_Portal_Design_CONTRACT.md` (v8 final) is the spec — **the 14-state workflow
table IS the spec**; nothing in it is re-litigated at build time. Stages PP0 → PP4;
Phase 2 (two-witness item layer) after the core loop proves. First step: the owner's
item-wise Marg purchase export from 01-08-2026 should be sitting in MargArchive under
`_UNKNOWN` — read its real shape (F-106: never assert an unprinted shape), mint its router
signature, THEN design PP0 ingestion against the artefact (D172).

## The backlog (HANDOFF_RUNBOOK v132 §2 is authoritative)

**Owner actions (⭐0):** token rotation (highest severity, aging since 21-Aug) · the
item-wise export from 01-08 (D335 prerequisite) · Darpan's Club 0 before the Aug close
(application scan → approve `0cc0b26b38c5` → 17-Aug ₹20,000 → drawer ≈ ₹175,201 + the
₹20,003 surplus) · 18-Aug 8-bill attribution · correction-checklist days · July salary ·
staff-phone PWA installs (live since S198_P4) · verify ToMedical on the medical PC (closes
F-168) · upload forms to the Forms tile · `pip install openpyxl xlrd` on manojz ·
`Neft_Guard.gs` paste + Drive API + `ng_setup()` · **F-173: check the April-2025 bank
statement against the vendor master** · triage the Auditor's Monday report.

**⭐2 the August month-end** — watch, don't assume. **⭐3 carried:** Club C (WABA works ·
call-pop · free-text replies) · B2 accountant email pack (awaiting owner answers) · Club 4 ·
expense-scan viewer · vehicle module · local-PC migration roadmap · casepack saved-cases ·
refresh the stale repo mirrors of the live finance/portal trees.

**Close-out routine:** `END_OF_SESSION_PROMPT_v6.md` (CURRENT; A9 = the Notion page). The
evergreen START-HERE custom-instructions still name `_v4` — a one-line owner edit.

## Connected sources

Google Drive (`drmka.ortho`) · Gmail · Notion (Clinic HQ) · GitHub
(`drmanoj-clinic-automation`) · the manojz/medical device bridge. ClickUp parked (D17).

*START_HERE_SESSION_199 — generated at the S198 close, 23-Aug-2026.*
