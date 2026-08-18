# PROJECT KNOWLEDGE — FILE SWAP MANIFEST (end of Session 126)

What to change in the Claude.ai project knowledge, and in what order.
**Verify every file by opening it and confirming its last line. Never by size or hash.**

---

## 1. REMOVE (quarantine, do not delete from disk)

| File | Why |
|---|---|
| `KB_APPEND_Session125.md` | **TRUNCATED.** Ends mid-sentence inside §3. Missing the third §12 replacement, the §12 addition, and the changelog line. **Never paste it.** Its intact content is re-carried in `KB_APPEND_Session126.md` §1A and §2A. |
| `HANDOFF_RUNBOOK_2026-07-08_Session125_v59.md` | Superseded by v60. Intact — archive it, do not destroy it. |

Move both into `_QUARANTINE_TRUNCATED_S125\` (the v59 runbook into an `_ARCHIVE\` subfolder, since it is intact and merely superseded).

---

## 2. ADD to project knowledge

| File | Last line must read |
|---|---|
| `HANDOFF_RUNBOOK_2026-07-08_Session126_v60.md` | `**END OF RUNBOOK v60 — §7 is the last section. If §7 is absent, this file is truncated.**` |
| `KB_APPEND_Session126.md` | `**END OF KB APPEND BLOCK — Session 126. §6 is the last section. If §6 is absent, this file is truncated and must not be pasted.**` |
| `INCIDENT_2026-07-08_CALLHOOK_403_RECURRENCE_v3_S126_ADDENDUM.md` | `**END OF INCIDENT ADDENDUM v3 (S126). §14 is the last section. If §14 is absent, this file is truncated.**` |

---

## 3. UPDATE the canonical KB — by paste, not by rewrite

`Clinic_Master_KB_SystemsRegister_v1.48.md` → **v1.49**.

Open `KB_APPEND_Session126.md` and perform its six paste operations in order:

1. **§1A** — append `§S125` at the end of the session-sections series *(re-carried; the S125 block is truncated)*
2. **§1B** — append `§S126` immediately after `§S125`
3. **§2A** — append D162–D165 to the decisions index *(re-carried)*
4. **§2B** — append D166–D169, plus the numbering note (**D161 unaccounted; next free is D170**)
5. **§3** — append the new mental models to the running list
6. **§4** — three §12 replacements and two §12 additions (the only deletions in the whole block)
7. **§5** — add the v1.49 changelog line to the header block

Then rename the file to `Clinic_Master_KB_SystemsRegister_v1.49.md`.

**Do not ask the assistant to re-emit the KB as a full file unless you first place `v1.48` in the uploads folder** where the shell can read it. Otherwise it can only be retyped from a read, cannot be mechanically diffed or byte-counted, and that is exactly how S125 produced five truncated documents. See Runbook v60 §6.

---

## 4. KEEP UNCHANGED

`Umbrella Architecture` · `API_QUICK_REFERENCE_CARD` · `Call_Console_Evolution_Spec` · `Maintenance_SOP_Spec` · `END_OF_SESSION_PROMPT_v3.md` · `START_HERE_PROMPT_v3.md`

`Diagnostics_Surveillance_System_Spec_v1_7.md` — unchanged this session. The watchdog's two defects are described accurately there and in Runbook v60 §2 item 3.

---

## 5. SESSION-START PROMPT

Replace whatever you currently paste at session start with `NEXT_SESSION_PROMPT_Session127.md`.

Its three integrity checks are calibrated to *these* files. If the assistant reports **D166** as the next free decision number, the S126 append block did not load. If it cannot find **§1A**, the block is truncated. Both are STOP conditions.

---

**END OF SWAP MANIFEST. §5 is the last section.**
