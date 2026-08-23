# START HERE — Session 197

Hi Claude. Continuing the clinic-automation project (**Session 197**). I'm Dr. Manoj
Agarwal, orthopaedic surgeon, Bareilly. Working protocol unchanged (plain language; one
step at a time; full-file replacements; mask patient numbers to last-4 and all tokens;
nothing live rebuilt without my OK; build/test offline → py_compile → pyflakes → I install).

## Phase 0 — verification before work (D247), WITH THE STANDING CAVEAT

1. Open `CANONICAL_MANIFEST.md`, verify rows by md5 — **the canon is folded only to S192.**
   S193–S196 live as standalone `claude/S19x_*` docs; manifest mismatches/missing rows for
   those FOUR sessions are EXPECTED, not incidents. `live_pins.txt` is stale (generated
   from Register v5.40) — **`verify_live_pins.py` has been unprotecting since S193.**
2. Read Tier 0: this file · `S196_Close_Summary_FINAL.md` (the anchor — carries THE live
   pins to trust) · `HANDOFF_RUNBOOK_2026-08-23_Session196close_v130.md` · KB Register
   v5.40 · the two S196 build-state docs as needed.

## The live pins to trust (S196 close — the authoritative list)

- `staff_register.py` **`9087954c8a4a891e8cdd848d6a9d48b2`** (v0.4)
- `att_month_report.py` **`9ab98313bbda7ae5555fb4b5a5a82c4b`** (v2.6)
- `finance_app.py` **`388c8ac0fdfecdee6029c0033b9b0ef8`** (smoke 668)
- `portal.py` **`ee749cd9f3ac1294aab0d13ce069efc1`**
- unchanged from S195: `staff_ledger.py acd7b538…` · `email_agent.py e535c4f8…` · Marg `signatures.json 1b21f3bf…`

## ⭐0 — THIS SESSION'S FIRST TASK: THE FOLD-IN (EOS-light, S185 precedent)

**Step 1, before anything: reconcile the F-SERIES FORK.** Canonical Fault Register v2.32
says next-free F-155; S193 standalone docs used F-155–F-159; S196 candidates were written
as F-160–F-162 assuming S193's usage. Rule on the final numbering, then:
Archive §S193…§S196 pure appends → Register bump (all moved pins + D333 + **mint D334**,
the present-request policy + findings) → Fault Register extend (S193's five + S196's
three: delivery-outside-git-tree · headline-never-wired · A4-dead-via-shadowed-today) →
manifest rebuild → `live_pins.txt` regen + owner one-copy + verify GREEN →
**cold kit TAKE (due — 4 of 3–5 since S192)** → knowledge re-compaction (62%).

## Then / owner-side (from the S196 pending block)

1. **Token rotation** — FINANCE_MARG_TOKEN + FINANCE_CRON_TOKEN (exposed 21-Aug; cron
   token also in GAS "UPI Reconciliation"). **Highest-severity open item, aging.**
2. Darpan's signed application scan → approve `0cc0b26b38c5` **before the August close**.
3. 17-Aug ₹20,000 → Staff Ledger. 4. File 21-Aug (auto-replay then loads its pending
   Marg push — 37 bills staged, F-155 behaviour, not a fault). 5. 18-Aug 8-bill
   attribution. 6. Correction-checklist day + 4 UPI/bank disagreement days.
7. July salary sheet. 8. Staff-phone PWA installs. 9. Drive-for-Desktop on the medical
   PC. 10. Labmate sample export.

## Watch

- **The Auditor's FIRST report** — scheduled task fired Mon 24-Aug ~07:05 IST
  (`trig_01XBRt7dcsXcjtmgdmemnR3x`, weekly): slice 1 cash-trail CALIBRATION;
  report lands as `claude/AUDIT_RUN_*` with AF-# findings + push/email summary.
  Triage its ≤3 recommendations. An auditor finding nothing on slice 1 is broken.
- **August month-end** — first full run on SL5–SL7 + F6 + the v2.6 present-request fold
  + D331/D332 rules. Watch, don't assume.
- Minor UX noted, no kit owed: the Marg Apply refusal message ("applied: — still not
  filed, skipped") reads thin (F-146 cousin, cosmetic).

## Next-free numbers

**Frozen until the ⭐0 reconcile** — do not mint bare F-numbers or D-numbers before it
(D334 reserved for the present-request policy). The Auditor mints AF-# only.

## Connected sources

Google Drive (`drmka.ortho`) · Gmail · Notion (Clinic HQ) · GitHub
(`drmanoj-clinic-automation`) · manojz device bridge. ClickUp parked (D17).

*START_HERE_SESSION_197 — generated at the S196 close, 23-Aug-2026.*
