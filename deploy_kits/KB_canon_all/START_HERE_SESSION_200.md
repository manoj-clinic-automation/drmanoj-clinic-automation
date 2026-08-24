# START HERE — Session 200

Hi Claude. Continuing the clinic-automation project (**Session 200**). I'm Dr. Manoj Agarwal,
orthopaedic surgeon, Advanced Orthopaedic Surgery Centre / Sanjeevni Medicos, Bareilly. Working
protocol unchanged (plain language; ONE step at a time, wait for my OK; full-file replacements or
fail-loud in-place patches; mask patient numbers to last-4 and all tokens; nothing live rebuilt
without my OK; manual workflow stays as fallback; build/test offline → py_compile → pyflakes → I
install; VPS python `/root/wa/venv/bin/python3` for the ledger).

## Phase 0 — verification before work (D247)

1. Open `CANONICAL_MANIFEST.md` and verify every row by md5. Current canon after the S199 close:
   Register **v5.44** (`4513138d…`) · Archive **v1.46** (`d0cee37d…`) · Fault Register **v2.36**
   (`37229a31…`) · Runbook **v133** · this file. A clean Phase 0 is expected — a mismatch is an
   incident.
2. Read Tier 0 only: this file · KB Register v5.44 · HANDOFF_RUNBOOK v133 · any open incident.
   Open Tier 1 on demand (the **D336/D337 contracts are Tier 1 — open them for any salary-flow
   work**).
3. `verify_live_pins.py`: expect GREEN against `live_pins_S199close.txt` (generated from v5.44 —
   A8). The S198 list would show RED drift on `staff_register.py` / `salary_engine.py` and miss
   the two NEW files — the stale-list condition (F-134), fixed by copying the new list.

## The live pins to trust (the S199 close set — the salary family)

- `staff_register.py` **`124c6eb2c5dc03055c70ac427c8347bb`** (v0.7 — flow + lock desk)
- `salary_policy.py` **`7f86cc8702b9fa48940e31a5ed2869d4`** (v1.3 — the D336 engine)
- `salary_engine.py` **`bedd468ee7b89b8f0c130d215a42b6d1`** (dormant fallback)
- `att_scenario.py` **`4dcd19bc02675a07cf0a77fadff6605b`** (v2)
- Unchanged from S198: `portal.py ab019dda…` · `finance_app.py 2c99b2c6…` · `portal_gist.py
  ef3ad196…` · `finance_entry.html 92477b06…` · `staff_ledger.py acd7b538…` ·
  `att_month_report.py 9ab98313…` · `email_agent.py e535c4f8…` · `signatures.json 1b21f3bf…`.

## Next-free numbers

**D338 · F-178 · A-D25 · Session 200.**

## The month-end flow is LIVE (D336/D337) — PREVIEW until `enforce_from` is set

Portal → Salary = the Lock Desk (readiness checklist; lock refuses non-enforced months).
Month-end flow = Sheet 1/2 pack + approvals + FINAL sheets. Settings page = every policy number.
Staff: own month view + remarks. **Nothing touches pay until the owner sets the enforcement month.**

## The backlog (HANDOFF_RUNBOOK v133 §2 is authoritative)

⭐0 owner: **token rotation (aging since 21-Aug)** · Shivani's July row (≈₹4,575) · August
advances + Darpan's ₹20,000 SPECIAL → the final working · notice serving + enforce_from.
⭐1 builder: desk columns/legend · the Arjun fine-threshold ruling · owner-advances entry ·
printable Sheet 2 · the selfie punch (mint a decision first) · hold-waiver UI.
⭐2 the August close = the first real run. ⭐3 carried: the Purchase Portal flagship + S198 list.

**Close-out routine:** `END_OF_SESSION_PROMPT_v6.md`.

## Connected sources

Google Drive (`drmka.ortho`) · Gmail · Notion (Clinic HQ) · GitHub (`drmanoj-clinic-automation`)
· the manojz/medical device bridge. ClickUp parked (D17).

*START_HERE_SESSION_200 — generated at the S199 close, 24-Aug-2026.*
