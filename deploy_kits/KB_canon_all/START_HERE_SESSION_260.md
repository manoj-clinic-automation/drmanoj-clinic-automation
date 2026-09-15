# START HERE — SESSION 260

Hi Claude. Continuing Dr. Manoj Agarwal's clinic-automation project. **This is Session 260.**
The evergreen rules are in **`START_HERE_PROMPT_v9.md`** (the project's custom instructions). This
file is the entry point for *this* session only.

## ⭐⭐ §0.0 — THE TOP JOB OF THIS SESSION — HIS INSTRUCTION, 15-Sep-2026

**He asked at the S259 close how the 2 MB project-knowledge cap had been handled and whether
anything was incomplete, then said: "Add these task to next session top job."** So these two come
**before** the ⭐1 backlog, and before any Sanjeevni build work. They come **after** Phase 0 and the
two owed faults, because Phase 0 is what proves the stores are sound in the first place.

**The measured position at the S259 close: 1,850,657 of 2,000,000 — 92.5 %, headroom 149,343 bytes,
and `CANONICAL_MANIFEST.md` alone costs about 139,825 to write.** That is room for ONE more close,
not two. Three times during the S259 close the store refused the manifest outright and documents had
to be deleted mid-close to make it fit (F-501).

### JOB 1 — take the manifest's copy OUT of project knowledge. Do this FIRST; it is one action.

`deploy_kits\KB_canon_all\CANONICAL_MANIFEST.md` in the repository is the byte-authoritative copy,
and **Phase 0 step 4 clones the repository and verifies it by md5 every session anyway.** The
project-knowledge copy is a convenience duplicate that costs ~140 KB of a 2 MB cap at every single
close, and it is also the one document that keeps being refused.

**Do it in this order and prove each step:**

1. Confirm the repository copy is present and its `md5sum -c` gate is green **from inside
   `KB_canon_all\`** — never delete the convenience copy before the authoritative one is proven.
2. Delete `claude/CANONICAL_MANIFEST.md` from project knowledge.
3. Measure `knowledge_size` immediately before and after, and state both.
4. Write the change into `START_HERE_PROMPT` (the evergreen prompt) so Phase 0 step 3 reads the
   manifest **from the clone**, not from project knowledge, and so no future session reports it
   missing as a fault.
5. Record it as a decision (**D528 is free**) with the measured before/after.

**Expected recovery ~140 KB, which roughly doubles the headroom.** Measure it; do not project it —
`knowledge_size` is an indexed measure and has been wrong by 3× when projected from file size
(the S206 lesson).

### JOB 2 — prepare the Sanjeevni/Marg split, which is the durable answer

Branching Sanjeevni/Marg into its own project has been the stated durable answer since S206 and is
now **overdue rather than optional**: JOB 1 buys one or two closes, not a year.

**What is the assistant's, and is to be done without asking him anything:**

- A written split plan: which documents move, which stay, what the new project's custom
  instructions say, how the manifest and the canon gate are split or shared, and what a session's
  Phase 0 looks like across two projects.
- The measured size of each side, so he can see the cap problem is actually solved and not moved.
- A rehearsal: everything staged and verified in `D:\Downloads\ClaudeCowork\` first, so the move
  itself is a copy of already-proven bytes.

**What is HIS, and it is the only thing:** creating the new project in claude.ai. Ask for that in
**one line**, when the plan and the rehearsal are done — not before.

> ⚠ **The rule that governs both jobs: nothing is deleted from any store until its surviving copy
> has been proven present.** At S259 all 35 documents removed from project knowledge were checked
> one by one — 12 survive in the repository, 30 in `ClaudeCowork`, **0 in neither**. Hold the same
> standard here. And note the open method fault: **a project-knowledge document still cannot be
> hashed by the tools**, so provenance for a moved document is by construction, not by byte
> comparison. Say so plainly wherever it applies.

## §0 — THE STANDING OWNER RULINGS (restated every close)

1. **Publishing is HIS double-click.** Name one file, full path.
2. **Full paths ALWAYS — including URLs**, each in its own copy block.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **Do not hand him a step that is not his.** If the assistant can do it, the assistant does it —
    or the nightly does.
12. **⭐ NEW AT S259 — HIS BOARD CARRIES ONLY TWO KINDS OF THING** (D526). His words:
    *"your format is very much time consuming for me… I see only the actionables and the important
    things you want me to see."* Something he must do, or something he should know. Everything else
    belongs in the work list on his PC, never on the board.

## §1 — PHASE 0, IN ORDER

**⭐ 0. READ THE OWNER'S BOARD FIRST — NEW AT S259, and it comes before everything.**
The System Board is a published artifact with its own store. He writes on it between sessions and
nothing tells you he has. Read `board` and `messages`; answer on the lines themselves; set
`read: true` on each message and update `board/_claude_status.lastRead` so he can see it was picked
up. **At S259 he left twelve notes and one Hold, and three of them changed the plan.**

1. **Connect and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`.
2. **Read the three nightly reports.** For each: **does it exist · what is its clock time · what is
   its verdict.**

```
D:\Downloads\_kbtools\REBUILD_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\MAINTENANCE_REPORT_LATEST.txt
```

```
D:\Downloads\_kbtools\CANON_SUMS_LATEST.txt
```

**`CANON_SUMS_LATEST.txt` should exist for the first time on the morning of 16-Sep** — S275 shipped
after the 03:10 run on the 15th, so the S259 close performed that check by hand instead (553 files,
553 rows, 553 OK, 0 uncovered). **If it is still absent, the nightly did not run: that is a RED.**

3. **⭐ AND READ THE JOB PULSE — NEW AT S259.** It is the first surface in this estate that can tell
   a job that is working from one that has quietly stopped.

```
D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz
```

The live report is on the box at `/root/finance/JOB_PULSE_LATEST.txt`, rewritten hourly at 17 past,
and the same figures are in `/root/finance/job_pulse.json`. **S259's first reading: 35 alive · 1
quiet · 2 no trace · 1 late, of 38.** Read the verdict line and name anything that has changed.

4. Open `CANONICAL_MANIFEST.md` and **verify every row by md5** — clone the repository and run
   `md5sum -c MD5SUMS_ALL.txt` **from inside `KB_canon_all\`**. Halt on a mismatch, never on absence
   from one store.
5. **Read Tier 0 only:** the manifest · the evergreen prompt · `KB_Register_v5_99_S259close.md` ·
   `HANDOFF_RUNBOOK_2026-09-15_Session259close_v180.md` · `OWNER_TODO_LIVE.md` · any open incident.
6. Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read
   `03_WORKING_PAPERS\S259\S259_BUILD_BRIEF.md`.
7. **Run §1.5**, then confirm, and only then ask which ⭐1 item to start.

## §1.5 — THE MAINTENANCE PASS

**Verify, do not perform:** the VPS code bundle in reach, the SSD mirror, the folder counts — all in
`MAINTENANCE_REPORT_LATEST.txt`. If missing or stale, that is the pass's first finding.

**⭐ TOMORROW'S BUNDLE HAS THREE THINGS OWED TO IT.** The 01:35 bundle of **16-Sep** is the first
that should:

- carry **241 files, not 217** (S273's widening, and the proof that six live files with no off-box
  copy are finally carried);
- contain **`/root/finance/freshness_legs.json`**, which has never been off the server — it defines
  the **seven checks that have never fired** and the **UPI evidence leg** that D525 replaces;
- contain the **live `salts_refresh.py`**, which S259 could not read.

A cloud-only scheduled check runs at 03:30 on 16-Sep and writes the file count onto the board.

**Measure the four numbers.** At the S259 close: **drift 0 · dead 1 · stale 1 · folders** as the
nightly measured them at 05:52 on 15-Sep — `D:\Downloads` 72 loose / 9,472 · `D:\dr-manoj-git` 7 /
7,193 · `F:\ClinicBackup` 7 / 554. **This session added four kit folders under `deploy_kits\` and six
files under `_kbtools\`; they land in tonight's count.**

**Hold the live pins against the bundle** whenever the VPS was touched, and state the three counts.
At S259: **107 matched · 5 mismatched · rest not carried**, the five being exactly the files S273 and
S274 installed after that bundle was built.

## ⚠ ONE FAULT IS OWED, AND F-501 IS RESERVED FOR IT — MINT IT FIRST

**Found at the very end of the S259 close, after the Fault Register had been sealed and its prefix
proven.** Project knowledge refused the manifest with *"this write would exceed the project's
maximum size"* — at **1,886,887 of 2,000,000** the linchpin no longer fits.

**The thing that is actually wrong is the model, not the cap.** Every close has assumed a canon
*swap* is roughly size-neutral: delete v(n−1), write v(n). **It is not. A replace is charged as an
addition** — the manifest alone is ~139,581 tokens of the 2,000,000 — so at 94 % full the store can
refuse to take the one document Phase 0 opens on. **A second tranche of 14 documents had to be
deleted mid-close to make the manifest fit**, which is not a tranche; it is the cap making the
decision.

**Mint this as F-501 at the S260 open** and bump the Fault Register accordingly. It was not minted at
S259 because the Fault Register v2.81 was already sealed and prefix-proven, and re-opening it would
have dragged the Register's four self-referential clauses with it — **recorded as OWED, which the
routine allows, rather than minted quietly into a file that says it is closed.**

**The durable answer is the one already on the table and now overdue: branch Sanjeevni/Marg into its
own project.** Trimming build briefs buys tens of kilobytes against a manifest that grows every
close.

## ⚠ A SECOND FAULT IS OWED — F-502, ALSO TO BE MINTED FIRST

**A file write reported success and left the old bytes on disk.** At the S259 close
`deploy_kits\S280_JOB_PULSE_FIX\SUMS.md5` was rewritten from three rows to four so the kit's own
gate would cover the README it had been shipped without. The commit returned that path in its
`written` list. **The file on disk was still the three-row version**, and it was the publish — which
carried the README but not the sums — that exposed it.

**The README beside it, committed in the same call, landed byte-perfect.** So this is not "the tool
was down"; it is a single write that silently did nothing while reporting that it had. Every other
`.md5` written that close (five kit sums under `ClaudeCowork\02_SESSION_KITS\S259\`) was checked
afterwards and all five were correct, **so it is not a pattern in the extension either — which makes
it worse, not better: there is no rule that would have predicted which write to distrust.**

**The lesson is already a project rule and was not applied to this file: a write to a store is not
done until it is read back and hashed.** The fourteen canon documents were read back; this one was
not, because it was a two-line housekeeping file. **Read back everything, or the exception is where
the fault lives.** This is the F-383 family (a tidy script that moved 218 items and reported
`MOVED 0`) and the S258 rule that a gate must be asked what it is guarding.

## §2 — RESERVED NUMBERS

**Next free: D528 · F-501 · A-D25 · kit S281 · Session 260.** ⚠ **F-501 AND F-502 ARE BOTH SPOKEN FOR** by the two owed faults above — mint them first, then take F-503 onward. Take them from this line, never from
memory (F-463).

## §3 — THE CURRENT CANON

| | |
|---|---|
| KB Register | `KB_Register_v5_99_S259close.md` |
| History Archive | `KB_History_Archive_v1_96_S259close.md` |
| Fault Register | `Fault_Action_Register_v2_81.md` |
| Runbook | `HANDOFF_RUNBOOK_2026-09-15_Session259close_v180.md` |
| Live pins | `live_pins_S259close.txt` |
| Build brief | `S259_BUILD_BRIEF.md` |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_2_S258.md` — **§7.2 is wrong, see F-493** |
| Close-out routine | `END_OF_SESSION_PROMPT_v14.md` |
| Evergreen prompt | `START_HERE_PROMPT_v9.md` |
| Paper policy | `PAPER_POLICY_v1.1` |

## §4 — THE PINS THAT MOVED AT S259

`/root/portal/portal.py` is **`4974209bfd2a66510294d8adf8712523`** (was `dc8f363e…`; S278, two
additive insertions, rollback `portal.py.bak_S278_dc8f363e`).
`/root/finance/job_pulse.py` is **`917713f5269bb6af46ea355fc212ad2c`** (S279 → S280; rollback
`job_pulse.py.bak_S280_cbeb6d72`). The root crontab carries **one** new line, `# S279_JOB_PULSE`,
backed up to `/root/finance/crontab.bak_S279_20260915_134021`.
manojz: `build_papers_index.py` **`dfcf659cb4a82a940d0f861aa6b88a33`**, `SUMS.md5`
**`6af7f601d074e7570e04f95f2eb1c6b0`**.
`/root/finance/purchase_app.py` is unchanged at **`3535dc978d4ec53846368c8772347a50`**.

## §5 — WHAT IS WAITING ON HIM

`OWNER_TODO_LIVE.md` is the list and **nothing is in it that the assistant could have done.** The
head of it: **close August** · **bank details for three suppliers** — AGARWAL SURGICALS AND MEDICALS,
RAMA MEDICOSE and **KUSHAGRA MEDICAL AGENCY**, the last on no earlier list · **his three stock
corrections**, which hold the 6-Sep count and Darpan's whole day flow behind them · **the first
cheque, ₹400**.

## §6 — WHAT THIS CLOSE OWES THE NEXT ONE

- **F-498's second half** — an empty log and an old log are different facts; the tool still treats
  them alike, and that conflation cost an hour on a healthy job.
- **F-496** — one line so the backup carries whether each job is switched on.
- **The asset-register nightly backup** names no log and throws its errors away: the one genuinely
  blind job of the thirty-eight.
- **F-493's correction to the Sanjeevni Book §7.2**, and to item 3f's entry condition.
- **F-494** — five purchase lines, ₹17,777, belonging to no vendor.
- **D524** — Shavez to maker on the cheque register, its own kit, one line.
- **The tile's caption** still reads *"What is done · what is running · what needs you"*, which
  described the board before it was rebuilt. Fix it with the next portal change, not on its own.
- **A16b was run:** the publish is verified by reading the repository back, not by the word
  "published".

## §7 — THE SWITCHES

```
bash /root/finance/sanjeevni_switch.sh status
```

VPS `/root/finance/_off/` · VPS `/root/marg_ingest/OFF` · manojz `D:\Downloads\margsync\_off\` ·
medical `D:\SendToClinic\_off\`. **⚠ `ALL_OFF` on the medical PC does not stop capture, by design.**

---
*START_HERE_SESSION_260 · written at the S259 close, 15-Sep-2026. The manifest wins on what is
current.*
