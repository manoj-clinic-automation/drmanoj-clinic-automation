# canonical-docs/ — current governing set

These are the fully-consolidated single-file masters. **The Master KB wins on any conflict.**

- `Clinic_Master_KB_SystemsRegister_v1_48.md` — Master KB / Systems Register (decisions through D161; next free **D166**).
- `Dr_Manoj_Clinic_Umbrella_Architecture_v1_36.md` — Umbrella Architecture.
- `HANDOFF_RUNBOOK_2026-07-08_Session125_v59.md` — latest Handoff Runbook.
- `Diagnostics_Surveillance_System_Spec_v1_7.md` — latest Diagnostics & Surveillance Spec.
- `Call_Console_Evolution_Spec_v1_6.md` — Call Console design spec.
- `INCIDENT_2026-07-08_CALLHOOK_403_RECURRENCE.md` — incident report, **v2**. Rewritten in place at S125; v1 is in git history and its errors are quoted before they are corrected.

Policy (owner directive, S100): canonical docs are single consolidated files — never delta chains.

Older delta/base versions (KB v1.7–v1.41, Umbrella v1.2–v1.30) remain in `docs/` as historical archive.

---

## ⚠️ Pending, as of Session 125 — the KB is one version behind its own decisions

`KB_APPEND_Session125.md` is an **append block**, not a canonical doc. It holds the §S125 section, decisions **D162–D165**, three §12 state replacements, and a changelog row for **v1.49**.

Why an append block and not a full file: the Master KB is 107 KB, and re-emitting it from a summary risks silently dropping material that has no other home. That is a worse failure than a paste, and an invisible one. The reasoning is in the block's own §0.

**To close this out:** paste the four sections into `Clinic_Master_KB_SystemsRegister_v1_48.md`, save as `_v1_49.md`, delete `KB_APPEND_Session125.md`, and update the first line of this README. Until then, **`v1_48.md` plus `KB_APPEND_Session125.md` together are the KB**, and D162–D165 are live decisions that the KB file does not yet mention.

---

## Version history of this set

| Doc | Was (S124) | Now (S125) |
|---|---|---|
| Master KB | v1.48 | v1.48 **+ append block** (v1.49 pending) |
| Umbrella Architecture | v1.36 | v1.36 — unchanged |
| Handoff Runbook | v58 (Session 124) | **v59 (Session 125)** |
| Diagnostics & Surveillance Spec | v1.6 | **v1.7** |
| Call Console Evolution Spec | v1.6 | v1.6 — unchanged |
| Incident, 08-Jul callhook 403 | v1 | **v2 (rewritten in place)** |
