# KB CONSOLIDATION — plan for S203+

**Written at the S202 close, at the owner's direction: *"project kb and repo totally uptodate and
without the unnecessary flab, we can park the old retired kb somewhere."***

**NOT YET APPROVED. Nothing is deleted until the owner signs §5.**

---

## 0 · WHY NOW, AND WHY IT IS DANGEROUS

**Why now.** At the S202 close, project knowledge hit **1,958,788 of 2,000,000 tokens — 98%** — and
eight superseded documents had to be deleted mid-close to finish the routine. **Nothing was watching
that limit.** It is the same shape as F-191: a constraint with no watchdog, discovered by hitting it.

**Why it is dangerous.** Deletion is precisely the operation this project has been hurt by:

- **F-89** — a nine-session backup lapse **permanently lost three canonical documents.**
- **The S131 stumps** — two documents survived only because a cold backup had them; git and Drive
  did not.
- **F-23** — `Diagnostics_v1_7` silently dropped sixteen lines while claiming to carry forward.

**So the governing rule: nothing is retired until it is provably recoverable from TWO independent
places.** Not "we think it's in git" — proved, by hash, in two stores, before anything moves.

---

## 1 · THE ORGANISING PRINCIPLE, WHICH ALREADY EXISTS

`README_VERIFY.md` states it: **project knowledge is the READING copy; git is the VERIFICATION copy.**

That gives a criterion that is not arbitrary taste:

> **Project knowledge should hold what a session needs IN CONTEXT — Tier 0, plus the Tier-1
> documents actually consulted. The repository carries everything, including history.**

Measured against that, the flab is visible: superseded Registers, old Runbooks, and ~60 one-off
`S###_*.md` session records whose content should already live in the Archive's `§S###` narrative.

**"Should already" is a claim, not a fact — and §3 tests it.**

---

## 2 · PHASE 1 — CENSUS. NOTHING IS DELETED.

The deliverable of phase 1 is an inventory, and only an inventory. For every document in project
knowledge, every file in `deploy_kits/KB_canon_all/`, and every hash row in the manifest:

| classification | meaning |
|---|---|
| **CURRENT** | a live Tier-0/1 row in the manifest |
| **SUPERSEDED** | an earlier version of something CURRENT |
| **SESSION RECORD** | `S###_*.md` — a working note from one session |
| **ORPHAN** | present in one store and in no register — **F-107's shape, and the most interesting category** |

**Orphans are the finding, not the flab.** A document nobody registered is one nobody is checking.
Expect some, and expect at least one that should have been Tier 1 all along.

---

## 3 · PHASE 2 — THE TEST THAT MUST PASS BEFORE ANY SESSION RECORD IS RETIRED

The claim is *"its content is in the Archive."* **Verify it per document**, mechanically where
possible and by reading where not:

- does `§S###` in the Archive exist, and does it carry the record's substance — the decisions, the
  figures, the reasoning — or only a one-line mention?
- does it contain anything that appears **nowhere else**: a hash, a figure, a design rationale, a
  ruling?

**If a session record holds something unique, it is not flab — it is an unregistered canonical
document, and it gets promoted to Tier 1 rather than retired.** That inversion is the whole reason
this phase exists.

---

## 4 · PHASE 3 — RETIREMENT IS A MOVE, NEVER A DELETE

**`deploy_kits/_retired_S203/`** in the repository, with its own `MD5SUMS.txt`, listed in the
manifest as a single Tier-2 folder digest — hash-verified, never read in the session loop.

**The gate every document passes before it moves:**

1. its md5 is present in the **cold kit** — an independent store; and
2. its md5 is present in **git history**; and
3. the manifest is updated **in the same pass** (F-134: a derived artefact is rebuilt in the routine
   that changes its source); and
4. **Phase 0 passes afterwards** — `md5sum -c` exit 0, the inverse check clean, F-88 accounted for.

**Any document failing 1 or 2 does not move.** It gets copied INTO both stores first, and only then
becomes eligible.

---

## 5 · WHAT THE OWNER MUST APPROVE BEFORE ANYTHING IS REMOVED

A single list: **every document proposed for retirement, with its classification and the evidence it
is recoverable.** No removal happens on the assistant's judgement alone.

**Recommended default, for discussion:** retire superseded versions and verified-redundant session
records from **project knowledge only** — leaving them in the repository — before considering any
move to `_retired/`. That alone reclaims most of the headroom and touches nothing irreversibly.

---

## 6 · PHASE 4 — STOP IT RECURRING

**A size check at every close.** Report project-knowledge headroom in the close report, and warn
below 15% remaining. The 98% was discovered by hitting it; that is exactly the class of fault this
session spent the day eliminating.

**And a standing question in Phase 0**, in the spirit of F-107 and F-190: *what is in one store and
not the other?* Asked routinely, an orphan cannot accumulate for a year.

---

## 7 · SEQUENCE, AND THE HONEST COST

1. Census (read-only) — safe, and useful on its own.
2. Redundancy tests on session records — the slow part, and the part that must not be rushed.
3. The approval list to the owner.
4. Retire, in one pass, with Phase 0 run before and after.
5. The size check added to the close routine.

**This should not be done in the same pass as feature work.** Documents are the one thing here that
cannot be rebuilt from a backup of themselves, and the project has lost three already. **Steps 1 and
2 are most of the value and carry none of the risk** — if the session runs short, stopping after the
census is a good outcome, not a failure.

---

## 8 · A COUNTER-ARGUMENT, RECORDED

**Flab is cheap; lost documents are not.** Project knowledge at 98% is inconvenient, and the
inconvenience is real — but the failure mode of doing nothing is *"I had to delete eight files
during a close"*, while the failure mode of doing this badly is *"the S184 rationale exists
nowhere."*

If the owner prefers, **the minimum viable version is §6 alone**: add the size check, remove
superseded versions from project knowledge only, and leave the session records entirely. That
reclaims headroom, needs no judgement calls, and risks nothing.

*S203_KB_CONSOLIDATION_PLAN · written at the S202 close · awaiting approval at §5.*
