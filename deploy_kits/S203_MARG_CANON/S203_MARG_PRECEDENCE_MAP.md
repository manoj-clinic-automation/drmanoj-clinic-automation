> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG / MEDICAL PC: OVERLAP AND PRECEDENCE MAP

**Session 203 · 26-Aug-2026 · READ-ONLY.** Nothing edited, moved or removed. No `git` command run
(F-131). No token value read or printed.

**Why this exists — the owner's words:** *"your documents match our other kb which also might be
having related data, so as to avoid any conflicts and confusions later on."*

He is right, and the project has already paid for this failure mode twice: **F-23** (a document
silently dropping sixteen lines while claiming to carry them forward) and the **S201 ruling** that
*an uploaded copy is a second source of truth with no hash and no owner*. A master reference that
restates what other documents own does not remove the conflict — **it adds a second place to go
stale.**

---

## 0 · VERIFICATION DONE FIRST

| what | result |
|---|---|
| `deploy_kits/S203_MARG_CANON/` · `md5sum -c SUMS.md5` | **exit 0 · 55 rows · all OK** |
| `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v2.md` | `fc3058d92570fd12bbdb1d472270b7c9` — **matches the value I was given** |
| v1, retained | renamed `…_v1.md.superseded_by_v2`, `57d12c8c46dd633a318f096344d02709`, still hash-covered |
| `S203_MARG_RETIREMENT_LIST.md` (repo) | `afb0c984e455aa4bdc3dda1954d25bbb` — **byte-identical to the copy I staged** |

**A naming discrepancy, recorded not fixed.** The repo file is `…_MASTER_REFERENCE_v2.md`; the
Project path is still `claude/MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md` carrying v2 content.
**A document's filename is a claim about itself (D188, F-45 family).** Rename the Project copy to
`_v2` at the close, or the next session hashes "v1" and gets v2's bytes.

**v2 closed all three gaps I reported against v1** — §4.3 encryption, §4.4 the money rule + V7,
§4.5 the ingestion half — **and** corrected the token list to five distinct stores and the §10
counts. Verified by reading v2 in full.

> **BLOCKER, unchanged:** the `Projects` tool remains disabled ("disabled for this session, in
> subagents as well"); `ToolSearch` finds no replacement. **This document is staged at
> `/home/claude/S203_MARG_PRECEDENCE_MAP.md`** and must be published to
> `claude/S203_MARG_PRECEDENCE_MAP.md` by a session that has the tool. I read master v2 and the
> retirement list from their **repo** copies, whose md5s I verified above.

---

## 1 · THE GENERAL RULE — worth more than the table

### 1.1 The three-way risk, named

One fact can legitimately appear in three different documents at once:

- the **Register**, because it is the current state;
- the **Archive**, because it happened;
- a **reference**, because it explains how the thing works.

None of those is wrong. The failure is that **nothing says which of the three a reader should
believe when they diverge** — and they diverge silently, because only one of them is ever updated.

### 1.2 The rule

> **Every fact is OWNED by exactly one document class, decided by the question the fact answers.
> It may be RESTATED elsewhere only as a citation that names its owner. When a restatement and its
> owner disagree, the owner wins — and when either disagrees with a measurement, the measurement
> wins.**

**The four classes, and the question each owns:**

| class | the question it owns | authoritative document |
|---|---|---|
| **STATE** | *What is true right now?* | `KB_Register` live-file table (VPS + manojz pins) · **master §3.2** (medical-PC pins) · the live state files (`MARG_PICTURE.txt`, `heartbeat.txt`, `index.csv`, `_outbox_state.json`) |
| **MECHANISM** | *How does it work? What do I do?* | **the master** · `MARG_PIPELINE_REFERENCE_v1` · `..._MAINTENANCE_FLOW_v1` · `MARG_INGESTION_REFERENCE_v1` |
| **RULING** | *What was decided?* | `KB_Register` decisions index (D-numbers) · the signed contracts |
| **FAULT** | *What is wrong, and is it closed?* | `Fault_Action_Register` (F-numbers) · `AUDIT_RUN_*` (AF-numbers, until bridged) |
| **HISTORY** | *What happened, and why?* | `KB_History_Archive` — **append-only, never corrected** |

### 1.3 The four corollaries that do the actual work

1. **HISTORY is never in conflict.** An Archive sentence that is false today is a dated record, not
   an error — F-23 forbids editing it. **A conflict exists only when a STATE, MECHANISM or RULING
   document repeats a stale fact.** This single distinction dissolves most of the apparent
   three-way collisions below: §S201 saying the C: tree was "found 25-Aug" is history; the
   *manifest* saying it is the problem.

2. **The measurement outranks every document, including the master** — D321(d), F-169: *the box
   wins*, and the record is corrected **from** the box. The master's own governing line says the
   same: *"When something contradicts what you see, believe the machine and tell me."*

3. **A RULING is superseded only by another RULING.** D348 retires the min_confidence question;
   a reference cannot. Conversely a reference cannot keep a retired question alive — but it does,
   and that is conflict **C4**.

4. **A restatement with no owner named is a defect, not a convenience.** It is `marg_net_sql`'s
   lesson generalised: *"never write a second way of summing Marg rows."* The same applies to
   prose. **Duplication is how the 18-Aug ₹23,879 phantom happened.**

### 1.4 The one-line test to apply to any sentence in the master

> *If this becomes false next Tuesday, which document does someone edit?*
> **If the answer is not "this one", the master must point instead of state.**

---

## 2 · THE SUBJECT MATRIX

`OWNS` = the document to change when the fact changes. Everything in *also mentions* should read as
a citation.

| # | Subject | OWNS it | Also mentions it | Agree? | If conflict — who wins, and why | What the master must say |
|---|---|---|---|---|---|---|
| 1 | **The machines, paths, drive letters** | **master §1** (MECHANISM+STATE, measured 25/26-Aug) | `MARG_PIPELINE_REFERENCE_v1` §1 · `S195_Medical_Watcher_LIVE_Reference` · `S203_MARG_CODE_TRUTH_MAP` §1 · `S203_MARG_MEDICAL_SYSTEM_MAP` §1 · `Clinic_Estate_Master_Inventory_v1_1` (**zero Marg mentions — verified by grep**) · `Dr_Manoj_Clinic_Umbrella_Architecture_v1_58` (**zero**) | **AGREE**, except the roots (row 3) | — | Already does. **But the estate inventory and the umbrella architecture have no row for any of this** — a gap, not a conflict; §3 below. |
| 2 | **The transport — Tailscale / the `DDrive` share** | **master §1.5** | **D347** in `KB_Register_v5_54` **line 738** · `CANONICAL_MANIFEST` §S201 · Archive §S201 · `MARG_PIPELINE_REFERENCE_v1` §1 · `..._MAINTENANCE_FLOW_v1` §2a · `S202_..._D350_CONTRACT` §5 | **CONFLICT — C1** | **The master and the S202 references win.** D347 is a RULING and only a ruling can amend it — so this needs a *correction entered in the decisions index*, not a reference edit. It is the sole transport; 26-Aug proved it over 8h40m. | Says it (§1.5). Add: *"the Register's D347 entry is the document to correct; until it is, the ruling text is known-wrong."* |
| 3 | **Capture and the watcher (how many roots)** | **master §2** (three roots, measured from the live heartbeat) | `MARG_PIPELINE_REFERENCE_v1` §1 ("BOTH folders") · `S195_Medical_Watcher_LIVE_Reference` (two) · `S203_MARG_CODE_TRUTH_MAP` §6.3 | **CONFLICT — C8** | **Master wins — measured.** `medical_agent.py:51-52` and the live heartbeat both say three. | Says it. Add the pointer: the third root is on `C:`, so `MEDICAL_RECENT.bat` cannot list "every file". |
| 4 | **Routing, signatures, the archive** | **`MARG_PIPELINE_REFERENCE_v1` §6/§7** (MECHANISM) | master §2 step 5 · `..._MAINTENANCE_FLOW_v1` §3/§4 · `S195_Marg_Report_Router_Design` (design rationale) · `S201_Part0/Parts2_3_4` (the derivations) · `S203_MARG_CODE_TRUTH_MAP` §1/§3 | **AGREE**, with two code-level corrections | `marg_router.py` is called **in-process**, not as a batch step; and `--learn` emits no `end_marker` (master §9 #5). Code wins. | **Point, do not restate.** The master should carry only the two corrections and defer §7's procedure. |
| 5 | **The outbox and sending** | **`MARG_PIPELINE_REFERENCE_v1` §3** (the upload contract) | master §2 step 6 · `..._MAINTENANCE_FLOW_v1` §2 · `S202_PICTURE/README_PICTURE.md` · `S202_B2B/README_B2B.md` · Archive §S201 (F-179) | **CONFLICT — C7 and C9** | **C9 (filename): the code wins** — `marg_gate.py:506` sends the archive name. **C7 (dedupe): UNRESOLVED — nobody wins yet.** `marg_gate.py:31-32` says the server dedupes; both references say it does not. | Master §9 #11 already flags C7 as unresolved. **Keep it flagged and do not pick a side until the VPS answers** — a wrong guess stages duplicates. |
| 6 | **Server-side ingestion and D313** | **`MARG_INGESTION_REFERENCE_v1`** (MECHANISM) + **D313/D314/D348** in the Register (RULING) | master §4.5 · `S201_Month_vs_Marg_Explained` · `S179_Finance_LIVE_State` | **CONFLICT — C4** | **D348 wins.** A ruling is superseded only by a ruling; `MARG_INGESTION_REFERENCE_v1` §9 item 5 still calls min_confidence *"an owner decision"* and was written hours before D348 retired it. | Master §4.5 already names the contradiction. **Fix belongs in the reference**, as a struck line (F-23), not by deleting it. |
| 7 | **The money rule** | **`S179_Marg_Sale_Report_Analysis`** (the derivation: `277,083 − 193,412 = 83,671 = 88,777 − 5,106`) | master §4.4 · `S180_Marg_Feed_Transport_Design` §3.3 · `S180_Marg_Feed_Request_and_Flow` §1 · `S180_Marg_Daily_Sale_Button_Settings` | **AGREE** — all four state it identically | — | v2 now carries the rule. **It must cite `S179_Marg_Sale_Report_Analysis` as the evidence**, because the master carries the rule and not the proof. |
| 8 | **Report variants and V7's silent truncation** | **`S180_Marg_Action_Register` V7** + **`Marg_Report_Requirement_Sanjeevni` §6** (the vendor-facing defect) | master §4.4 · `S180_Marg_Sample_Findings` (the 3-vs-9 column discovery) · `S201_Parts2_3_4_Record` (the per-type `end_marker` derivations) | **AGREE** | — | v2 carries it. **Point at `Marg_Report_Requirement_Sanjeevni` for the vendor question** — "is there a page/line cap?" is still unanswered and lives there with its acceptance test. |
| 9 | **Encryption of the `.c18` tables** | **`S180_Marg_Folder_Recon`** (the format analysis) + **`S195_Marg_decrypt_partial_key`** (the thorough negative) | master §4.3 · `S195_Marg_dbf_Encryption_Finding` (**the superseded optimistic note**) | **CONFLICT — C16, internal to the S195 pair** | **`S195_Marg_decrypt_partial_key` wins by its own declaration**: *"it supersedes the earlier optimistic 'crackable via crib-drag' note."* | ⚠ **v2 §4.3 sides with the SUPERSEDED note.** See §4 — this is the one place v2 has introduced a new conflict. |
| 10 | **Backup and DR** | **master §5** (it did not exist anywhere before) + **`BACKUP.txt`** on the machine (STATE) | `Clinic_Source_Data_Retention_Policy_v1` §6 · **F-191(c)** in `Fault_Action_Register_v2_41` · `OWNER_TODO_LIVE` ⭐0a · `S203_MEDICAL_PC_PINS` | **CONFLICT — C3** | **The master wins — measured.** F-191(c) and the Register say the auto-backup *"was configured … and has never once run"*; the machine says **nothing in Task Scheduler or at startup runs a backup at all.** *(Verified: "never once run" appears in `Fault_Action_Register_v2_41` ×1 and `KB_Register_v5_54` ×1.)* | Says it. Add: **F-191(c)'s wording must be amended at the close** — the finding stands, the diagnosis in it does not, and the wording is what a future session would act on. |
| 11 | **Live pins — VPS and manojz** | **`KB_Register` live-file table** (STATE, and `gen_live_pins.py` generates from it) | master §3.2 (PC only) · `S201_*` pin records · `live_pins_S202close.txt` | **CONFLICT — C6** | **The box wins** (D321(d), F-169). Register pins `PULL_FROM_MEDICAL.bat 3c5389d5…`; the box holds `92f03999…`. A live, unrecorded F-186 instance. | **The master must NOT restate VPS pins.** It correctly does not. It should say: *"for anything on the VPS or manojz, the Register's live-file table is the owner; this document owns only the medical-PC pins."* |
| 12 | **Live pins — the MEDICAL PC** | **`S203_MEDICAL_PC_PINS`** (the measurement record) — master §3.2 is a *copy* | master §3.2 | **AGREE today** | — | **This is duplication, not conflict — see §3 D1.** The master should point; the pins move whenever a kit installs. |
| 13 | **Faults — the F-series** | **`Fault_Action_Register_v2_41`** | master §7/§9 · `KB_Register` findings index · Archive · `S201_PARKED_BACKLOG` C1–C8 · `S202_PENDENCY_AUDIT` §5 · `S203_PENDENCY_RECONCILIATION` | **AGREE**, but **incomplete** | Four of C3–C8 are recommended for numbers and none is minted; F-191(c) needs amending (row 10). | Master should state: **the Fault Register is the only register of record; anything numbered elsewhere is a candidate, not a finding.** |
| 14 | **Faults — the AF-series** | **`AUDIT_RUN_2026-08-24_slice1`** — and **nothing bridges it to the F-series** | master §3.1 (AF-1) · `S201_PARKED_BACKLOG` §E · `S202_PENDENCY_AUDIT` N2 · `S203_PENDENCY_RECONCILIATION` Thread 2 · `AUDITOR_SEED_v1` | **CONFLICT — C2, and a structural gap** | **Master wins on AF-1**: it is recorded in **seven canon places** (verified: manifest ×1, Register ×2, Archive ×2, Runbook v136 ×1, `MARG_PIPELINE_REFERENCE_v1` ×1) against `GUARD_AND_SEND.bat`, **which is not on the machine**. | Says it (§3.1). Add: **`AUDITOR_SEED_v1` still instructs the live weekly Auditor to continue the F-series**, which S196 overrode — an F-23 situation for the owner's ruling, not a silent edit. |
| 15 | **The owner's task list** | **`OWNER_TODO_LIVE`** (A10 keeps it current; **un-manifested by design**) | master §11 · `HANDOFF_RUNBOOK v136` §2 (a close-time *snapshot*) · `S202_PENDENCY_AUDIT` §1 | **AGREE today, guaranteed to diverge** | `OWNER_TODO_LIVE` wins by construction — it is the only one with a numbered step keeping it current. | **§11 must become a pointer.** See §3 D8. |
| 16 | **Retention of source exports** | **`Clinic_Source_Data_Retention_Policy_v1`** (RULING-in-draft) | master §5 (database backup, a different subject) · `MARG_PIPELINE_REFERENCE_v1` §6 | **CONFLICT — C13** | **The pipeline references win on paths.** The policy is wrong three ways: working copy `D:\MargArchive\` (live: `D:\Downloads\margsync\MargArchive\`); its "single highest-value step" (a Drive-*synced* folder) was built as `robocopy`, **which excludes `_spool`/`_outbox`**; and medical origin `Sent\` vs the live `_captured\`. | **Keep the two subjects apart.** The policy owns *exports*; the master owns *the database*. The master should say so in one line — the policy's own §6 already gestures at it. **And the policy is still a draft awaiting approval.** |
| 17 | **The D350 scope** | **`S202_Marg_Transport_Resilience_D350_CONTRACT`** (RULING, as scoped by the owner) | master §11 · `OWNER_TODO_LIVE` ⭐1 · `S203_MARG_MEDICAL_SYSTEM_MAP` §5 (the item-by-item gap tables) | **AGREE** | — | Master must record **§1 the Drive fallback is PARKED at the owner's ruling**, with his reasoning — otherwise a future session rebuilds a transport he declined. |
| 18 | **Session history** | **`KB_History_Archive_v1_49`** | manifest §S-blocks · `KB_Register` version lineage · every `S###_*` record | **AGREE by construction** | **History is never in conflict** (§1.3 #1). | The master should say: *"for why anything is the way it is, read Archive §S195/§S201/§S202 — and never take a current fact from it."* |
| 19 | **Decisions** | **`KB_Register` decisions index** + the signed contracts | manifest §S-blocks · Archive (full texts) · master §1.5/§4.5 | **CONFLICT — C1, C4** (both above) | A ruling is amended only by a ruling. | **D327 is minted and was never built** (`S203_PENDENCY_RECONCILIATION` Thread 4) — the decisions index records that a decision was *made*, never whether it was *done*. **A built/not-built column is the one structural fix that would catch this class unaided.** |
| 20 | **The document set itself** | **`CANONICAL_MANIFEST`** (what is canonical) + **`SYSTEM_DOC_COVERAGE_MAP_S147`** (where the reference for X is) | master §10 · `S203_MARG_DOC_INVENTORY` · `S203_MARG_RETIREMENT_LIST` | **CONFLICT — C5, and a total gap** | **C5:** the manifest still labels `S195_Medical_Watcher_LIVE_Reference` *"SOLE reference for the Marg capture pipeline"* (verified, manifest line 191) while `MARG_PIPELINE_REFERENCE_v1` opens *"Supersedes…"*. **The reference wins; the manifest label must change.** | **The coverage map has 23 rows and not one for clinic-finance, Marg, the medical PC, manojz, the Lab PC or backup/DR** — verified. §5 drafts them. |

---

## 3 · WHERE THE MASTER DUPLICATES A FACT ANOTHER DOCUMENT OWNS

Each of these will go stale silently. **The fix is a pointer, not a deletion** — the master should
say what the fact *means* and name who owns the *value*.

| # | Master § | What it restates | Owner | Why it will go stale |
|---|---|---|---|---|
| **D1** | §3.2 — the six medical-PC pins | `S203_MEDICAL_PC_PINS` | that record + `CENSUS.txt` | **`medical_agent.py` already moved once today** (`69e60d77…` → `7b9a76f2…`). Every kit install invalidates this table. Say *"the current values are in `FromMedical\CENSUS.txt`; these were true on 26-Aug"*. |
| **D2** | §4.5 — the `marg_net_sql` expression, written out | `MARG_INGESTION_REFERENCE_v1` §6 | **This is the exact fault it exists to prevent** — *"never write a second way of summing Marg rows."* Two copies of an expression is how the ₹23,879 phantom happened. **Name it and point; do not transcribe it.** |
| **D3** | §1.1, §3.1 — `77 files`, `_captured` 35, `Sent\` 16, all four disk free figures | `medical_census.py` → `CENSUS.txt` | Counts change daily. The master's own rule says a statement about a running system has an expiry date; these carry `[MEASURED 26-Aug]` and should carry *"re-read with `MEDICAL_CENSUS.bat`"*. |
| **D4** | §4.2 — backup ages (`4.1 days old`, `12-day gap`, `newest 22-Aug`) | the heartbeat's `BACKUP` line (built at S203.3 for exactly this) | **Stale within 48 hours by design.** Point at the heartbeat, which the master itself says now carries it. |
| **D5** | §5.1 — `38 file(s), 0.07 GB … 145 still to copy` | the heartbeat | A first-run figure. Keep it as *evidence the leg works*, labelled as first-run, not as state. |
| **D6** | §9 — twelve corrections | `S203_MARG_DOC_VERIFICATION` (82 claims: 42/17/12/11) | The master reproduces 12 of 82. When a 13th is found, two documents need editing. **Keep the twelve as the headline and point at the verification for the rest** — §9 already does this in its lead line; make it binding. |
| **D7** | §11 — thirteen open items | `OWNER_TODO_LIVE` (A10) | The only list with a numbered step keeping it current. Two task lists is how an item gets done twice or never. |
| **D8** | §8 #5 — the five token paths | **nobody — and that is the real problem** | `MARG_PIPELINE_REFERENCE_v1` §4 owns the token inventory and lists **three**. **Correct §4 to five and have the master point at it.** On the oldest open item, two lists of different lengths is worse than one wrong list. |
| **D9** | §10 — the document counts (69/8/17/5/39) | `S203_MARG_DOC_INVENTORY` | v2 already corrected the "30 in one store" clause. **Point for the numbers; keep the sentence that matters** — that the folder is not yet manifest-pinned. |
| **D10** | §7 — failure modes by symptom | `..._MAINTENANCE_FLOW_v1` §2 (the decision trees) + the Fault Register (the F-numbers) | The master's table is a good index. It should say *"the decision tree for each is in the maintenance flow §2"* rather than growing into a second runbook. |

---

## 4 · WHERE THE MASTER CONTRADICTS A CURRENT KB DOCUMENT

### 4.1 The master is right — the other document must change

| # | Both sides | Who wins | What must change |
|---|---|---|---|
| **C1** | **D347**, `KB_Register_v5_54` line 738: *"**Tailscale is a read-only D:-only view and is NOT load-bearing**"* — vs **master §1.5**: *"`\\100.119.151.40\DDrive` is the **sole transport** … the feed went dark for **8 hours 40 minutes**"* | **Master** (measured; 26-Aug) | **The Register's D347 entry.** A ruling is amended only by a ruling, so this is a decisions-index correction at the close — not a reference edit. `S202_..._D350_CONTRACT` §5 has listed it as owed since 26-Aug and it is **still not done**. |
| **C2** | **Seven canon places** (manifest ×1, Register ×2, Archive ×2, Runbook v136 ×1, `MARG_PIPELINE_REFERENCE_v1` ×1): *"AF-1 remains armed on it — deliberately, and recorded"* — vs **master §3.1**: *"`GUARD_AND_SEND.bat` … **That file is not on the machine.** … the fault attached to it cannot fire"* | **Master** (measured from the machine, not the mirror) | **Strike AF-1** at the close. Amend the two STATE/MECHANISM places (`MARG_PIPELINE_REFERENCE_v1`, Runbook §2, `OWNER_TODO_LIVE` ⭐3). **Leave the Archive and manifest §S201 alone** — they are history (§1.3 #1). D347's clause preserving `SEND_TO_CLINIC.bat` as the fallback **stands and is unaffected**. |
| **C3** | **F-191(c)** + `KB_Register_v5_54`: *"automatic Marg backups were **configured** around 02-Oct-2025 and **have never once run**"* — vs **master §4.2**: *"**Nothing in Task Scheduler and nothing at startup runs a backup.** It was never scheduled."* | **Master** (measured) | **Amend F-191(c)'s wording.** The finding is right (no working automatic backup); the diagnosis is wrong, and the diagnosis is what the vendor question in `OWNER_TODO_LIVE` ⭐0 #9 is built on. Asking Marg *"why does the configured backup produce nothing"* invites the answer *"it isn't configured"* and wastes the call. |
| **C5** | **manifest line 191**: `S195_Medical_Watcher_LIVE_Reference` … *"**SOLE reference for the Marg capture pipeline**"* — vs **`MARG_PIPELINE_REFERENCE_v1`** opening: *"**Supersedes** `S195_Medical_Watcher_LIVE_Reference.md` as the authoritative description"* | **The reference, and now the master** | **Strike the "SOLE reference" label** on the manifest row. Raised as `S202_PENDENCY_AUDIT` **N3** and still open. **Both rows are Tier-1 CURRENT** — two canonical documents each claiming to be the reference is precisely the confusion the owner asked about. |
| **C6** | `KB_Register` live-file table: `PULL_FROM_MEDICAL.bat` = `3c5389d5…` — vs the box: `92f03999d0a14d00b7f552dbb4d44c05` | **The box** (D321(d), F-169) | Correct the Register row **from the box** at the close, citing the `.bak_before_diag` beside it. A live, unrecorded **F-186** instance. |
| **C8** | `MARG_PIPELINE_REFERENCE_v1` §1 *"BOTH folders"* / `S195_Medical_Watcher_LIVE_Reference` (two) — vs **three**, from `medical_agent.py:51-52` and the live heartbeat | **Master** (measured) | Correct §1 of the reference. A reader of the canonical reference alone does not know a whole output tree is captured. |
| **C13** | `Clinic_Source_Data_Retention_Policy_v1` §2/§3 paths — vs the live archive layout | **The pipeline references** | The policy is **still a draft awaiting the owner's approval**; correct the three path/mechanism errors *before* it is approved, not after. |

### 4.2 The master is WRONG — and this one is new in v2

> **C16 · §4.3 sides with a superseded document.**
>
> **Master v2 §4.3:** *"**So it is genuinely breakable.** … The way in, when it is resumed:
> known-plaintext crib-dragging … Status: **PARKED by the owner on 21-Aug** … not abandoned, and
> **not because it failed**."*
>
> **`S195_Marg_decrypt_partial_key.md`** (repo `3f83f1594fcb22e29b6aba0458e6574b`, verified today) —
> written *after* the note v2 is quoting, and explicitly superseding it:
> *"Corrected verdict below — **it supersedes the earlier optimistic 'crackable via crib-drag'
> note**. … **All failed on the record fields.** … **0** occurrences of bill numbers … **0**
> occurrences of "2026" … Field descriptors do NOT decode to valid VFP types … **All 7 files share
> an identical 19-byte header prefix despite sizes 809 B … 13 MB.** Under simple XOR of a standard
> DBF the prefixes would differ. **Identical prefixes falsify "XOR-of-standard-DBF".** … Only byte0
> (0x30) and rec_len (256) ever "verify", and those are consistent with **coincidence/wrapper, not
> a real decrypt**. **Remote decryption from the files alone is not tractable.** … **Decision
> (recommended): RETIRE remote decryption.**"*
>
> **The later document wins.** v2 §4.3 reproduces `S195_Marg_dbf_Encryption_Finding` — the note the
> retirement list classifies **RETIRE precisely because it is superseded** — including its two
> "confirmations" (`0x30`, rec_len 256) which the later analysis names as *the coincidences that
> made it look breakable*.
>
> **Why this matters more than a wording fix:** §4.3's stated purpose is *"the standing answer to
> 'why don't we just read Marg's database?'"* As written, the standing answer is **"it's breakable,
> we just parked it"** — an open invitation to spend a session on a road already surveyed and
> closed. The true answer is: *four independent attacks over 27,246 records failed; the plaintext
> under the 256-byte period is not a standard DBF; the only remaining route is a one-time debugger
> dump on the Marg PC.*
>
> **Required change to v2 §4.3:** replace "genuinely breakable / parked, not because it failed"
> with the thorough negative, keep the crib-drag paragraph **only** as the historical first
> hypothesis marked superseded (F-23), and cite **both** S195 documents so the supersession is
> visible. **§11 item 12 needs the same correction** — it currently reads *"parked, proven
> crackable"*.
>
> **Consequence for the retirement list:** `S195_Marg_dbf_Encryption_Finding` stays **RETIRE**, but
> **`S195_Marg_decrypt_partial_key` must be promoted into `S203_MARG_CANON` and pinned** — it is
> the winning document, it is repo-only in `KB_canon_S197fold/filed/`, and the master currently
> contradicts it.

### 4.3 Unresolved — neither side wins yet

> **C7 · Does the server dedupe by content?**
> `marg_gate.py:31-32` (live on manojz): *"**A repeat send is free — the server dedupes by
> content.**"* — vs `MARG_PIPELINE_REFERENCE_v1` §3 and `MARG_INGESTION_REFERENCE_v1` §2:
> *"**The endpoint does NOT dedupe by content.** Sending the same bytes twice stages twice."*
>
> Master §9 #11 flags it as unresolved, which is correct. **Resolve it against the VPS before
> anything else on the code list** — if the references are right, `marg_gate`'s stated safety
> margin does not exist, and any path that loses `_outbox_state.json` stages a dozen duplicates
> into the approvals queue.

---

## 5 · DRAFT `SYSTEM_DOC_COVERAGE_MAP` ROWS

The map is the project's own designated answer to *"where is the reference for X"*. **Verified: 23
rows, none for any system below.** It is dated S147; the entire estate was built from S179 onward.

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| **Clinic-finance** — Sanjeevni + clinic daily money: entry · approvals · day page · health · month close | `finance/` *(working tree S180/S182-stale; the LIVE bytes are recovered by md5 from `deploy_kits/` per the pin list)* | **STATE:** `KB_Register` live-file table + `live_pins_S202close.txt` · **MECHANISM:** `MARG_INGESTION_REFERENCE_v1` (`4d603b72…`) for ingest · **DESIGN/RULINGS:** `S179_Finance_LIVE_State` (`54cb25a8…`) for D313 and the invariants | ⚠ **Split ownership, and the manifest names only the third.** `S179_Finance_LIVE_State` is S179-era — **verified: it describes the Marg adapter as something that *"needs its own adapter"***, i.e. unbuilt. It is authoritative on design and **out of date on state**. The row must name both and say which answers which. |
| **Marg capture & transport** — capture → route → archive → send | `margpull/` *(mirror STALE — `marg_watch.py 25126388…` is the PDF-blind old watcher)* · `deploy_kits/S195_MARG` · `S202_PICTURE` · `S202_B2B` · **`deploy_kits/S203_MARG_CANON`** | **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v2` (`fc3058d9…`) — read first** · then `MARG_PIPELINE_REFERENCE_v1` (`97b3cf73…`, how it works) and `..._MAINTENANCE_FLOW_v1` (`c2b5251f…`, faults by symptom) | ✅ wholesome set. **Strike the "SOLE reference" label on `S195_Medical_Watcher_LIVE_Reference` when this row lands** (= C5 / N3). |
| **The MEDICAL PC** — Marg host: `medical_agent.py` · `marg_watch.py` · `SEND_TO_CLINIC.bat` · two output trees (`D:` and `C:\Users\Public\MARG\`) | `deploy_kits/S203_MARG_CANON/S195_medical_kit` · **`medical_agent.py`, `xlsx_stdlib.py`, `medical_census.py` are in NO repo path** | **master §1.1/§3** · `S203_MEDICAL_PC_PINS` (`976a6f0c…`, the first live pins) · **D347** for the architecture *(with its Tailscale clause known-wrong — C1)* | 🟡 **operational, with a recovery gap.** Until S203 no pin of any kind covered this machine. **Three live files still have no off-box copy.** |
| **manojz** — publisher + 10-minute puller + mirror + offsite, one box | `margpull/` · `deploy_kits/S202_PICTURE` · `S202_B2B` · `PUBLISH_ALL.bat` (D328) | **`..._MAINTENANCE_FLOW_v1` §1** — the 60-second check's three files all live here, none needs a login · master §1.2 · `S203_MARG_CODE_TRUTH_MAP` (`4a7ff0a6…`) for what the code actually does | 🟡 **Named single point of failure**: the Auditor's Surface B records manojz as *"publisher + puller + mirror + offsite in one box"* — audit **slice 4**, never run. |
| **Lab PC / Labmate** (pathology) | — none | **NONE.** The only canonical document naming Labmate is `Clinic_Source_Data_Retention_Policy_v1` (`90831162…`), and only for export retention | ⚠ **NOT A SYSTEM YET — survey before any build.** Standing warning: **S181 records the revenue arithmetic is INVERTED between medical and clinic/lab** — *"the single most dangerous copy-paste in the build."* Attach a source as a **profile + signatures, never a copied script**, and **ask where Labmate writes** — Marg had two output trees on two drives. |
| **Backup & disaster recovery** | `deploy_kits/S203_MARG_CANON` (docs) · `finance/finance_backup.sh` (the VPS books) | **master §5** — *the section did not exist anywhere before S203* · **STATE:** `FromMedical\BACKUP.txt` + the heartbeat's `BACKUP` line · **exports only:** `Clinic_Source_Data_Retention_Policy_v1` (still a **draft**) | 🔴 **The least-protected part of the estate.** `D:\MARGERP\Data` **cannot be copied consistently while Marg runs** — no copier can. The only unattended-safe artefacts are `serverbackup\` and a human's `.mbk`. **No restore has ever been tested.** |

---

## 6 · WHAT TO DO, IN ORDER

1. **Correct master v2 §4.3 and §11 item 12** (C16) — it is the only place the master is wrong, and
   it points a future session at a closed dead end.
2. **Add `S195_Marg_decrypt_partial_key` to `S203_MARG_CANON`** and pin it; it is the winning
   document on encryption and is repo-only today.
3. **Rename the Project copy to `…_v2`** so its name stops being a false claim (D188).
4. **Turn D1–D10 into pointers** — one editing pass, and it is what stops the master becoming the
   next stale document.
5. **At the close:** correct D347's Tailscale clause · strike AF-1 in the STATE/MECHANISM places
   only · amend F-191(c)'s wording · correct the `PULL_FROM_MEDICAL.bat` pin from the box · strike
   the "SOLE reference" label · correct the reference's watch-root count and its three-copy token
   list.
6. **Pin `deploy_kits\S203_MARG_CANON\`** in the manifest **before** anything is retired (F-184).
7. **Add the six coverage-map rows.**
8. **Resolve C7 against the VPS.**

---

*S203 · read-only · every md5 quoted was computed by `md5sum` in this session or transcribed from
the file that carries it · master v2, the retirement list and the canon documents were read from
their repo copies, whose hashes are recorded in §0 · no document edited, moved or removed · no git
command run · no token value read or printed · no patient identifier reproduced.*
