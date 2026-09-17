# S260 — THE SANJEEVNI / MARG SPLIT — plan, measured sizes, rehearsal (D528 part 2)

*Written 17-Sep-2026, S260. The assistant's; nothing here needed the owner except the last line.*

## 1 · Why now

The cap is not solved by tranches: S260 took project knowledge from **1,852,499 → 1,588,011** (the manifest
duplicate out, 21 superseded documents out), and the store still grows every close. The rescue (F-504)
also showed the real cost of one store: **184 of 314 documents lived only there.** Two projects, each
under half the cap and each mirrored to the PC at every close, is the durable shape. It has been the stated
answer since S206.

## 2 · What moves, what stays — by the document list, not by feel

**315 project documents at S260 were classified by name into two sides** (lists on the PC beside the
staging folder: `_MOVE_TO_PROJECT_KNOWLEDGE.txt`, `_EVIDENCE_ONLY_CLAUDECOWORK.txt`, and the parent's
`split_core` list in the evidence folder):

| side | documents | raw bytes (measured on disk) | goes to |
|---|---:|---:|---|
| **Sanjeevni / Marg — current references, rulings, plans, specs** | **35** | **389,234** | the NEW project's knowledge |
| **Sanjeevni / Marg — built/measured/finding papers** | **75** | **467,099** | `ClaudeCowork\03_WORKING_PAPERS\S###\` only (evidence; already there or rescued at S260) |
| **Clinic core** — canon, portal, staff, salary, attendance, WABA, callback tracker, Docterz, AI verdict, UNATTENDED/AUDIT runs, incidents, specs | **205** | — | stays in the parent |

**The 35 that move** are the System Book, the four SANJEEVNI_* registers and records, the Rung and
Consolidation plans, the five MARG_* references, the D350 transport contract, six rulings documents, and
fourteen current plans, specs and designs (S210 money page · S212 system map · S220 returns intent · S221
stock-audit finding · S224 purchase-order flow · S226 finding-report spec · S227 loss triage · S228 final
plan, navigation · S229 rectification, DB consolidation · S235 orthotic stock cycle · S240 machine map,
medical-to-VPS route, Amir's day flow).

**Raw bytes are not indexed bytes** (the S206 lesson: the store's measure has differed from file size by
3×). The parent side is measured by `project_info` before and after the 35 leave; the new project's side is
measured by `project_info` from its own first session. Both numbers go into the build brief of the session
that performs the move.

## 3 · One canon, two projects — the decisions (mine, recorded so they can be overturned)

1. **One repository, one `KB_canon_all\`, one `CANONICAL_MANIFEST.md`, one `MD5SUMS_ALL.txt`.** A
   Sanjeevni close appends its canon rows to the same manifest; either project's Phase 0 verifies the whole
   folder. Nothing is split that would need reconciling.
2. **One number series** — D, F, kits, sessions — reserved from the parent's `START_HERE_SESSION_###`,
   which both projects read **from the clone**, never from project knowledge (there is no copy there).
3. **One Fault Register, one KB Register, one Archive**, in the parent's canon; a Sanjeevni session mints
   into them exactly as the parent does.
4. **Each project's knowledge holds only its own Tier 0/1 documents**; every build paper of either project
   is written to `ClaudeCowork\03_WORKING_PAPERS\S###\` in the same close (the F-504 rule).
5. **Phase 0 is the same ritual in both** — connections, the three nightly reports, the clone and the gate,
   the parent's entry point, the board, the maintenance pass — written into
   `SANJEEVNI_START_HERE_PROMPT_v1.md` (staged) and `START_HERE_PROMPT_v10.md` (parent).

## 4 · The rehearsal — done, on the PC

`D:\Downloads\ClaudeCowork\05_DELIVERABLES\SANJEEVNI_PROJECT_STAGING\` holds **all 110 Sanjeevni-side
documents as bytes** — 65 from the S260 rescue, 3 from the repository canon folder, 38 from
`ClaudeCowork\03_WORKING_PAPERS` (each verified against its `MANIFEST.md5` row: 38 of 38), 4 recovered from
repository history (`deploy_kits\MARG_MEDICAL\`, `deploy_kits\S203_MARG_CANON\`) — plus
`SANJEEVNI_STAGING_SUMS.md5` (110 rows), the two lists, and `SANJEEVNI_START_HERE_PROMPT_v1.md`.
**The move itself is therefore a copy of already-proven bytes**, and the only step that is not the
assistant's is creating the project.

## 5 · The move, when the project exists — in order, each step proven

1. The owner creates the project **"Sanjeevni — Pharmacy & Marg"** in claude.ai and pastes
   `SANJEEVNI_START_HERE_PROMPT_v1.md` as its custom instructions; connects the same three folders,
   GitHub, Drive, Gmail.
2. In a session of the NEW project: upload the 35 from the staging folder; `project_info` → the new side's
   first measurement; read back three documents and hash them against `SANJEEVNI_STAGING_SUMS.md5`.
3. In a session of the PARENT: delete the same 35 from project knowledge — **only after step 2's
   read-back** — and `project_info` before and after; record both numbers in the build brief.
4. Manifest rows: each of the 35 gains a `project: sanjeevni` note; D528 part 2 recorded in the Register.
5. The 75 evidence papers are deleted from the parent's knowledge in tranches over the next closes, each
   only after its `ClaudeCowork` row is confirmed in `MANIFEST.md5` (75 of 75 are there or rescued today).

**What is HIS, in one line:** create the project and paste the prompt. Everything else is the assistant's.
