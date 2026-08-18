# EOS / EOS-light — the portable definition (v1 · born S189, Dr Manoj clinic project)

**Purpose: replicate this project's session-close discipline in ANY project.** This file is
project-agnostic; the clinic's own canonical routine (`END_OF_SESSION_PROMPT` v5) is the reference
implementation. Copy this file into a new project and adapt the bracketed parts.

## The two modes

**EOS (full)** — anything changed outside documents this session: code, config, live data, a
service, a schema. **EOS-light** — a documentation / planning / fold-in session; no live system
touched. *Everything below runs in both modes except steps marked (full only). When unsure which
mode fits, the assistant asks once rather than guesses.*

## The invariants that make a close a close

1. **History is append-only.** The session narrative is APPENDED to the history archive; the bytes
   before the previous end-marker are proven byte-identical (a hash, not a promise). An append-only
   file cannot be repaired by a later append — order is forever.
2. **Current-state is rewritten, small, and additive.** The register of what-is-true-now gains this
   session's pins, decisions and findings; nothing is cut; zero loss is PROVEN by reverse
   application — strip exactly what the session inserted, undo exactly what it edited, and the
   result must hash to the previous version's pin.
3. **Every claim of change carries a hash, transcribed from the file it names** — never retyped
   from memory, never computed from intent. A footer is a claim about the file, checked like any
   other.
4. **The manifest is updated LAST among documents** — it pins everything else, so it cannot be
   final until they are.
5. **Derived artefacts are rebuilt in the same routine that changes their source** (the clinic's
   F-134: a pin list generated from the register went stale the one close that skipped it).
   Enumerate every derived artefact; give each a numbered step AFTER its source's step.
6. **Findings raised this session are appended THIS session** — a close with an owed append is not
   clean. The next-free counters (decision #, finding #, session #) advance visibly.
7. **The next session's entry point is written now**, carrying: the verification-first Phase 0, the
   live backlog pointer, the next-free counters, and the lessons that must not be re-learned.
8. **A cold backup on a cadence** (every 3–5 sessions or on any major version bump), counted at
   every close, taken BEFORE the count says overdue. Everything the project would need to restart
   from nothing, in one archive, on a second medium.

## The automation boundary (the owner's S189 directive, generalised)

**The assistant executes the entire close.** Document set, knowledge-base swap, connector updates
(Notion/Drive/etc.), the commit staged into the owner's working copy, the cold backup when due, the
derived artefacts last. **The owner's residual work is enumerated at the end of every close as an
explicit, numbered, minimal list — ideally: (1) one credentialed publish action the assistant
cannot perform without holding the owner's credentials, and (2) any on-box copy the assistant has
no shell on.** Anything else appearing on the owner's list is a defect in the close, to be
automated next session. Credentials never transit chat; retiring the publish click requires an
explicit scoped-credential ruling recorded as a decision.

## The close-out sequence (adapt names, keep order)

```
A0  session summary (what happened, new findings, scope changes)
A1  HISTORY ARCHIVE   append §S<N>, prove prefix byte-identical, bump minor
A2  REGISTER          pins as-they-moved verified, decisions index, findings index,
                      lineage row, end-marker; prove zero-loss by reverse application
A3  RUNBOOK           §0 narrative · §1 mental models · §2 live backlog · discipline notes
A4  START_HERE <N+1>  verification-first, Tier-0-only reading, next-free counters
A5  changed reference docs only (never "confirm each unchanged" — one combined line)
A6  frozen artefacts: hash-verified, NEVER edited without explicit waiver
A7  MANIFEST          recompute every changed row's md5, update CURRENT/superseded labels,
                      append the session's EOS block — updated LAST of the documents
A8  DERIVED ARTEFACTS regenerate everything generated FROM the above (pin lists, indexes),
                      AFTER A7, with their own generated-from attestations
B   connectors        Notion/Drive/etc. updated by the assistant, live
C   commit            staged into the owner's working copy by the assistant (full only)
D   knowledge swap    executed by the assistant
E   cold backup       when the cadence says due — taken, not offered
F   the owner's list  printed explicitly, minimal, numbered
```

## What EOS-light skips

The commit message/publish (C) and any live-system health check — nothing else. A light session
still appends history, still proves zero-loss, still updates the manifest last, still regenerates
derived artefacts, still ends with the owner's (usually empty) list.

## The three failure patterns this definition exists to prevent

- **The owed append** (clinic F-108): findings recorded in one document and never applied to their
  register — four sessions behind and saying so nowhere.
- **The narrative step** (clinic F-134): a close step performed once, recorded as prose, never
  numbered — skipped the next time by an operator following the numbered steps faithfully.
- **The unverifiable document** (clinic F-107): a file the next session must READ that no manifest
  row pins — read on trust, because nothing looks for a missing row.

*v1 · S189 · portable. The reference implementation and its scars: END_OF_SESSION_PROMPT_v5 and
Fault_Action_Register (F-45, F-107, F-108, F-110, F-116, F-119, F-122, F-134) in the clinic project.*
