# THE PAPER POLICY v1.1 — one brief, one shelf, three fates

**Adopted S257, 14-Sep-2026 · v1.1 carries the ruling on the existing 193.** Written because the owner said, plainly: *"Each session you put some
papers in some folders in my PC and inform me here. It is very difficult for me to keep track."*
He is right, and the cause is on the assistant's side of the screen.

## What was measured first

**375 working papers across 44 sessions** in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\`.
Every filename was tested against `00_INDEX.md`, `CANONICAL_MANIFEST.md` and the current KB Register.

> **193 of them — 51 % — appear in none of the three.** Written once, never referred to again.
> **Ten of S256's eleven papers were already in that state the next morning**, because the S256 brief
> says so itself: *"Read this instead of the papers. One brief is a handover; ten papers are a record."*
> The doctrine was right and the practice never followed it.

Only **51 of 375** are the two kinds written to be read later — a build brief or a close report.

## Rule 1 — One document per session is written to be read

The **build brief**. One per session, and it is the handover. The **close report** is the proof record
and is written for the next assistant, not the owner. Everything else produced in a session is
**evidence** — it exists to be checked, not read, and is filed without ever being announced.

## Rule 2 — A file is named in chat only when the owner must act on it

Open it, print it, sign it, run it, hand it to someone. That is the whole list. Otherwise the chat
says **what happened**, in a few lines, and the document sits on the shelf. *"I wrote a paper at
`D:\...\S257\S257_THING.md`"* is not information — it is homework.

## Rule 3 — Staleness is read, not guessed

Every paper carries four lines at the top, so no future session has to infer anything:

```
status:       LIVE | SETTLED | SUPERSEDED
session:      S257
needs_owner:  yes | no
review_after: 2026-10-14
```

## Rule 4 — There is one shelf, and it is a screen

```
D:\Downloads\_kbtools\PAPERS.html
```

Built by `build_papers_index.py`, **rebuilt nightly at 03:10** alongside the manifest, and openable
any time by double-clicking:

```
D:\Downloads\_kbtools\PAPERS.bat
```

It reads only — it moves, renames and deletes nothing. It answers one question: *is there anything
here that still needs me?* Four shelves: **Needs you** (the ⭐0 items, not files) · **This session** ·
**The last three sessions** · **Archive**, a per-session ledger with a bar showing how much of each
session's paperwork has never been cited since. A copy is published as an artifact for the phone —
the first phone-readable route this project has had.

## Rule 5 — Three fates, decided at the close, never later

| fate | what | where it goes |
|---|---|---|
| **KEEP** | the build brief, the close report | stays in `03_WORKING_PAPERS\S###\` for ever |
| **FOLD** | evidence, per-kit "built/live" notes, pin readbacks, append chunks | its claims land in the close report; the file moves to `03_WORKING_PAPERS\_EVIDENCE\S###\` |
| **COLD** | anything FOLDed and older than 90 days | the SSD, `F:\ClinicBackup\DrManojClinic_Automation\` |

**Nothing is ever deleted by this policy.** COLD means *moved to the cold store after a verified
copy exists*, which is the same copy-verify-then-move discipline the closes already use.

## The 193 already in the tree — RULED, S257: move nothing

The owner gave a free hand. **The ruling is to leave every one of them exactly where it is**, under
his standing rule *do what is best, and does not destabilise the system*.

1. **The shelf already solved the problem he raised.** They are invisible to him now — archive
   ledger, asking nothing. A move buys him nothing he can see.
2. **A move is a copy plus a deletion**, and deletion on his PC costs his approval. Spending that on
   193 files nobody reads is a poor use of the one thing only he can give.
3. **The fix belongs upstream.** From S258, evidence is written straight into
   `03_WORKING_PAPERS\_EVIDENCE\S###\`. The tree stops growing this way **without one existing file
   being touched**, and the history stays where every past close left it.

The full list is written out once, by session, in `S257_NEVER_CITED_193.md` — a proven candidate set
for the reduction tranche or a future cold sweep, so the measurement never has to be repeated and the
decision stays reversible by anyone.

## What this costs the assistant, which is the point

Fewer papers, written later, and a close that has to decide each one's fate rather than writing
everything down and moving on. **The 51 % figure is the measure to watch: if the next close does not
move it down, this policy did not take.**
