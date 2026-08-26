# START HERE — SESSION 203

Hi Claude. Continuing my clinic-automation project (**Session 203**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**

- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → `py_compile` (I use `python`, not `python3`) → then I install.
- For VPS python, always use `/root/wa/venv/bin/python3`.
- **ALWAYS give me the COMPLETE path, and say which machine it is on.** I said this twice at S202 and
  was given bare commands and a bare `/finance/approvals` link. Full URLs. Full paths. Every time.
- **Prefer ONE file I double-click over a sequence of GUI steps or a long console paste.**
- **ALWAYS give me VPS commands as a copy block** — one block per machine, never mixed.

---

## PHASE 0 — DO THIS FIRST. Verification before work.

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin) — current at the **S202 close**.
2. **Verify every row by md5**, all tiers. A row whose hash does not match **halts work until
   reconciled** (D172/D188). A filename is not provenance (D188).
3. **Read into context only Tier 0:** the manifest, this START_HERE, **KB Register v5.54**,
   **HANDOFF_RUNBOOK v136**, and any open incident. Tier 1 on demand; Tier 2 never in the loop.
4. Standing checks: **F-88** · **F-107 inverse** · **F-119** (`md5sum -c` must exit 0) · **F-123** ·
   **A8** · **and NEW at S202: F-190** — confirm `.gitattributes` still pins `*.md text eol=lf`,
   because without it 192 of 208 canon files change hash on a default Windows checkout and Phase 0
   fails on all of them at once. **Also report project-knowledge headroom** — it was at 98% at the
   S202 close and nothing was watching it.
5. **`verify_live_pins.py`** — expect **GREEN against `live_pins_S202close.txt`**. If I have not yet
   copied it to `/root/deploy/live_pins.txt`, **that is the first thing to tell me.**
6. Then confirm, and start on ⭐1 below.

---

## WHERE THE TRUTH LIVES

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers and hashes. WINS on "what is canonical / current."
- **KB Register v5.54** (Tier 0) · **KB History Archive v1.49** (Tier 1, §S202 last) ·
  **HANDOFF_RUNBOOK v136** (Tier 0) · **Fault_Action_Register v2.41** (F-0 … F-193).
- **`OWNER_TODO_LIVE.md`** — the always-current owner list, deliberately un-manifested.
- **`S202_Marg_Transport_Resilience_D350_CONTRACT.md`** — written, and **scoped by me at the S202
  close to §2/§3/§4/§5. The Drive fallback is PARKED.**
- Marg references (Tier 1): `MARG_PIPELINE_REFERENCE_v1` · `MARG_INGESTION_REFERENCE_v1` ·
  `MARG_PIPELINE_MAINTENANCE_FLOW_v1` — **the last two were corrected at S202**; D347's claim that
  Tailscale is "NOT load-bearing" is wrong and is corrected in both.

---

## WHAT S202 DID (one paragraph)

Opened as housekeeping, became an incident. **The pharmacy revenue feed was dark for 8h40m and
nothing said so** — found only because I asked why a report had not arrived. Every component was
healthy; Windows had blocked unauthenticated guest access to the share. **F-187:** the Rs 20,000 that
left Darpan's drawer on 17-Aug existed only as prose, settled by **physical count** after a plausible
wrong theory was disproved. **I overruled the assistant on applying the 12-June report and was
right.** **D349 minted and both halves built** (one rule in one place). **D350 written and scoped by
me.** Seven kits live; **F-184 repaired**; **F-190** found and fixed. **F-185 CORRECTED — the claim
that patient diagnoses were public was false.** F-187…F-193 minted; **six of the nine findings were
the assistant's own.** Close: **GREEN, match 47, drift 0.**

---

## ⭐1 — WHAT I ASKED FOR NEXT, AND HOW

**Start with the pen-drive backup and the D350 Marg transport work. Work MAX ON YOUR OWN** — my
instruction at the S202 close. Do the survey, the design and the offline build without walking me
through each step; bring me decisions and installs, not keystrokes.

**1. The backup — this is the crown jewels.** Everything we have built is downstream of Marg; Marg
holds the actual pharmacy. Established at S202: backups are **manual**, every 2–4 days, to `E:\`
(an HP USB 2.0 stick permanently attached to the medical PC). **`E:\auto` and `E:\MARGBCKUP\auto`
have been EMPTY since October 2025** — automatic backup was configured and has never once run
(F-191c). Last backup **22-Aug**. What is needed: find why the automatic backup produces nothing;
get it to daily; add an **offsite leg** (Drive is installed on that PC and proved itself through the
S202 outage); and **test one restore**, because an untested backup is a hope.

**2. D350, at the scope I set:** §2 verification at both ends (measured, never inferred) · §3 the B2
states · §4 the reinstall kits, **Marg and its data first** · §5 the document corrections (already
done at S202 — verify, don't redo). **§1 the Drive fallback is PARKED.**

**3. The expectations file** — what report is due, by when, for every type. Useful whether Marg is
automated or I keep clicking.

**4. THE KB CONSOLIDATION — I want the project KB and the repo totally up to date and without the
unnecessary flab, and the retired KB parked somewhere.** The plan is written and waiting at
`S203_KB_CONSOLIDATION_PLAN.md`; **§5 needs my approval before ANYTHING is removed.**

*Why it is now urgent:* at the S202 close project knowledge hit **1,958,788 of 2,000,000 tokens —
98%** — and eight superseded documents had to be deleted mid-close to finish the routine. **Nothing
was watching that limit.** Same shape as F-191: a constraint with no watchdog, found by hitting it.

*Why it must not be rushed:* **deletion is the operation this project has been hurt by.** F-89 lost
three canonical documents permanently. Two more survived the S131 stumps only because a cold backup
had them when git and Drive did not. So the governing rule is **nothing is retired until it is
provably recoverable from TWO independent stores, by hash** — and retirement is a **MOVE to
`deploy_kits/_retired_S203/`, never a delete.**

*The inversion that matters:* the ~60 `S###_*.md` session records are assumed redundant because
"the Archive has it". **Test that per document.** Any record holding something unique — a hash, a
figure, a rationale, a ruling — **is not flab; it is an unregistered canonical document and gets
PROMOTED to Tier 1.** That is F-107's shape, and it is the most likely real finding of the whole
exercise.

*Do this in its own pass, not alongside feature work.* **Phases 1–2 (census and redundancy testing)
carry most of the value and none of the risk** — if the session runs short, stopping after the
census is a good outcome, not a failure. And §8 records the minimum viable version if I would rather
take that: add the size check, drop superseded versions from project knowledge only, leave the
session records entirely.

Then: F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 · Staff Console
Phase 0 (my four rulings owed) · **Purchase Portal (D335)** as the other flagship.

---

## ⭐0 — MY ACTIONS

1. **TOKEN ROTATION** — still the oldest and highest-severity item, aging since 21-Aug.
2. **Copy `live_pins_S202close.txt` → `/root/deploy/live_pins.txt`** and run the checker.
3. **Pravesh exits 31-Aug** · July top-ups Rs 4,519 · Surendra Rs 516 · Arjun · Shivani ·
   **AF-3's scan before the August close**.
4. **F-173** — the April-2025 NEFT advice file. Money may already have gone to wrong accounts.
5. **Generate 25-Aug's Marg sale report** (the picture correctly reports it missing).
6. **F-185** — the repo visibility ruling is mine, on the corrected figures: 62 mobile-shaped
   numbers, **no diagnoses, ever**.
7. Marg support: the report-scheduling question **and** why automatic backup produces nothing.

---

## ⚠ WHAT S202 GOT WRONG, SO IT IS NOT REPEATED

**Six of nine findings were the assistant's.** A gate matching the bare word `OK`. A preflight
demanding a binary the kit never uses. A generator's correct refusal silenced with `2>/dev/null`. A
monitor wired so it could only report success — built the same morning as the witness designed to
catch exactly that. A dead machine's heartbeat read as proof it was alive. And **a false claim that
patient diagnoses were public**, pressed on me twice before it was checked properly.

**The rule that came out of it: a monitor is proven against the thing it monitors, running, in its
real state — never against a fixture.** Every one of those surfaced from live data or from my own
questions, not from any test.

**Next free: D351 · F-194 · A-D25 · Session 203.**
**Cold kit: taken at the S202 close.**

*START_HERE_SESSION_203 · written at the S202 close · supersedes 202.*
