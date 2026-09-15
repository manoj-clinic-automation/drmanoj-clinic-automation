# HANDOFF RUNBOOK — v180 · S259 close · 15-Sep-2026

*Tier 0. Read with `CANONICAL_MANIFEST.md`, `KB_Register_v5_99_S259close.md` and
`START_HERE_SESSION_260.md`. Supersedes v179 whole.*

---

## §0 · WHAT HAPPENED

**One long attended day, four kits, and one question the estate had never been able to answer.**

**S277_SHELF_CORPUS** repaired **F-491**. `build_papers_index.py` built its citation corpus from
`00_INDEX.md` *plus* `MANIFEST.md5`, and since S268 the manifest is rebuilt nightly over the whole
tree — so every paper's name was in the corpus by construction and the never-cited figure could only
ever read zero. v1.1 drops the manifest and adds the durable part: **a share gate refusing any source
that names 90 % or more of the papers**, and an outright refusal of any file named `NEVER_CITED`.
Proven on the real 380 names: **v1.0 reads 0, v1.1 reads 196 (51.6 %)**, against S257's 193 of 375.
Force-feeding the manifest back leaves 196 unchanged. **Applied through the file tools to both
`_kbtools` and the repository; no step reached the owner.**

**S278_BOARD_TILE** gave the owner's System Board a home: one tile, first on his portal,
`roles ["doctor"]` only, two additive insertions in `portal.py` and nothing else.
**`dc8f363e…` → `4974209b…`**, the offline-computed pin and the live pin identical, and the tile then
**read back off the rendered page** rather than off a return code.

**S279_JOB_PULSE and S280_JOB_PULSE_FIX** are the session's spine. Four of the day's six open faults
were one shape — a check built correctly, wired correctly, then never switched on or never looked at.
**A job that is quiet looks exactly like a job that is passing.** Counted: of **38 clinic jobs**,
**8** left a run record anyone could read back, and **all five nightly backups were among the thirty
that could not** (**F-495**). The collector reads each log path **out of the crontab at run time**,
asks systemd for the four timers, and measures each schedule's widest legitimate silence over a real
16-day window. **It modifies no job and opens no database.** First reading: **35 alive · 1 quiet ·
2 no trace · 1 late** — and **the certificate watch ran at 06:40**, so **F-500**: its eleven days of
silence were what a healthy watch does, and recording that as a fault was the assistant's error.

**The tool then found two faults in itself on its first live run** — **F-497**, systemd timestamps
forced to UTC and shifted again, so two timers reported a run in the future at −329 minutes and v1.0
still called it healthy; and **F-498**, a job that runs every five minutes read as dead because it
prints nothing on a quiet pass. S280 fixed both within the hour and **now reads the run table for the
seven jobs that keep one**, with each line naming which it read.

**Findings that came out of the day's ordinary work:**

- **F-493** — S258's two-surface disagreement explained. The hub compares expected against Marg's
  export; the shadow compares the server's re-run against the PC's push. Both say "compared / agree /
  differ", and canon copied one into the other's row. **Item 3f's entry condition must name
  `sh_run.differ = 0`, not the hub card**, which can never reach zero while two spellings of one
  product exist.
- **F-494** — bill 160 of 1-Sep exists twice, two suppliers on one day, so **5 lines worth ₹17,777**
  belong to no vendor. Once in 1,551 lines; August untouched.
- **F-496** — the nightly bundle carries what a scheduled job *is* but not whether it is *switched on*.
- **F-499**, retracted — fourteen vendors needing bank details were **three**; thirteen were the same
  firms under a second spelling, already aliased at S263. Caught because the owner asked for the list
  rather than the number.

**The owner's rulings:** **D524** Shavez becomes a maker on the cheque register · **D525** the UPI
check matches the **total** sale, never the split, because Darpan marks it in the end-of-day rush and
nothing may be added to his night · **D526** his board carries only what needs him and what he should
know · **D527** liveness is measured from evidence jobs already leave.

**And the day's honest summary:** four published numbers were wrong within one day, every one from
reporting a figure before naming what would falsify it.

---

## §1 · MENTAL MODELS — what to hold in your head next session

1. **Liveness and verdict are different questions.** *Did it run?* and *did it find anything?* were
   one number in this estate until today. Keep them apart on every surface.
2. **A number carries the question it answers, or it carries nothing.** Two surfaces measuring
   different things may not share a vocabulary (F-493), and a plan condition written on a number must
   name the surface it is read from.
3. **Silence from an alarm built to speak only on change is not evidence** (F-500). The question is
   never "why is it quiet" but "is it switched on" — and until F-496 is fixed no backup can answer it.
4. **The right check often already exists and is not being used.** `darpan_kal_day` went live on
   13-Sep and holds zero rows; it is the day-close that makes the money provably right.
5. **Before publishing a number, name what would falsify it and go and look at that.** Four
   retractions in one day; the rules already existed, so another rule was not the answer.
6. **The owner's board is not a planning surface.** Two kinds of thing only: what needs him, what he
   should know (D526).

---

## §2 · THE LIVE BACKLOG

### ⭐0 — waiting on the owner

The list is `OWNER_TODO_LIVE.md` and it is short by design (A10b). In order: **close August** ·
**bank details for three suppliers** (AGARWAL SURGICALS AND MEDICALS, RAMA MEDICOSE, KUSHAGRA MEDICAL
AGENCY) · **his three stock corrections**, which are what hold the 6-Sep count and Darpan's whole day
flow · **the first cheque, ₹400** · then KEDAR PHARMA's July ₹310, Amir's name-check sheet, the ₹650
flag, two parked logins, and the key rotation.

### ⭐1 — what to build next, in this order

1. **Finish F-498's second half** — an **empty** log and an **old** log are different facts; the
   empty one means the job has never once spoken. It cost this session an hour on `salts_refresh`.
2. **F-496** — one line in `code_bundle.py` so the backup carries each job's enabled state.
3. **The asset-register nightly backup names no log** and sends its errors to `/dev/null` — the one
   genuinely blind job of the thirty-eight.
4. **D524** — Shavez to maker on the cheque register; its own small kit, one line for the owner.
5. **F-494** — attribute a purchase line by supplier as well as bill and date.
6. **The seven health legs and the UPI leg** (D525) — `freshness_legs.json` comes off the box in
   tonight's bundle for the first time; G0, G4 and the UPI replacement are one pass, not three.
7. **`darpan_kal_day` needs a place in the portal** — the highest value per unit of work in the
   system, and it waits on the owner's three stock corrections, not on code.
8. Then the structural chain: **one store for sale lines → retire the manojz senders → Sanjeevni in
   its own process.** All of it behind **F-493's corrected witness**.

**Parked by the owner, deliberately:** the per-person PWA banner and its download-fill-upload
worksheet — *"we can develop it when the flow comes to that point"*.

---

## §3 · INSTALL DISCIPLINE

Unchanged, plus what S259 confirmed:

- **Read the real file before patching it.** `portal.py` was patched from the box's own nightly
  bundle, pin-verified first. No inferred anchor.
- **Every installer refuses on a fingerprint, backs up before writing, compiles before replacing, and
  restores byte-identically if the service will not start.** S278 was walked through all four paths
  in a sandbox before it went near the box.
- **An installer that edits the crontab proves it by reading the crontab back** — S279: 66 → 67
  lines, exactly one added, verified from `crontab -l`.
- **A kit that ships a tool runs that tool's own selftest ON THE BOX and refuses to install if it
  fails there.** S279 and S280 both do.
- **Write the test for the fault you just found, in the same hour.** S280 carries one assertion per
  fault; the selftest had already caught three defects before shipping, including one where the
  failing assertion was the assistant's and the code was right.

---

## §4 · THE BOUNDARY — what the assistant may not do

Unchanged. The VPS needs the owner because he holds every credential by design; publishing is his
double-click; nothing live is rebuilt without his OK and the manual path stays as fallback.

**And what the assistant must stop doing:** handing him a step it could take itself (A10b), and
publishing a figure it has not tried to falsify.

---

## §5 · ONE FAULT OWED — F-501 RESERVED

Project knowledge refused `CANONICAL_MANIFEST.md` at the end of this close: **1,886,887 of
2,000,000, and a replace is charged as an addition, not as a swap.** Fourteen more documents were
deleted to make the linchpin fit. **The assumption that a canon swap is size-neutral is wrong, and
every close from here is closer to the wall.** Mint it as F-501 at the S260 open; it is not in
v2.81 because that file was sealed and prefix-proven before the refusal happened, and OWED is an
answer the routine allows while a quiet append to a closed file is not.

## §6 · A SECOND FAULT OWED — F-502 RESERVED

`deploy_kits\S280_JOB_PULSE_FIX\SUMS.md5` was rewritten to four rows; the commit reported it
written; **the disk kept the three-row file.** The README committed in the same call landed
byte-perfect, and the five other kit sums written that close were all correct, so nothing would have
told you which write to distrust. **The only defence is the rule that was skipped for this one file:
read the write back and hash it.** Mint as F-502 at the S260 open, with F-501.

---
*v180 · S259 close · 15-Sep-2026 · supersedes v179 whole.*
