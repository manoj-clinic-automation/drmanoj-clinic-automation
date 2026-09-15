# S258 CLOSE REPORT — 15-Sep-2026

*Written against `END_OF_SESSION_PROMPT_v14.md`. **Every A17 row is answered. Silence is never DONE.***

**Mode: EOS** (code changed on two machines). **Folders connected this session:** `D:\Downloads` ·
`D:\dr-manoj-git` · `F:\ClinicBackup` — all three, the whole session.
**Session:** one Cowork chat, 15-Sep-2026, ~05:30 → close.
**Harness URL:** `https://claude.ai/code/session_01TqYiRJYufrZpjsx5Lvvq8L`

---

## A17 · THE CHECKLIST

| # | step | verdict | evidence |
|---|---|---|---|
| **0** | the three nightly reports read FIRST | **DONE** | `REBUILD_REPORT_LATEST.txt` and `MAINTENANCE_REPORT_LATEST.txt` present and current. **`CANON_SUMS_LATEST.txt` did not exist** — S275 shipped after the 03:10 run, so tonight's is its first. Stated as expected, not as green. |
| **1** | Archive (A1), append proven | **DONE** | `KB_History_Archive_v1_95_S258close.md` — **first 1,439,590 bytes byte-identical to v1.94 (`2669e946…`)**, +18,992 → **1,458,582 B**, md5 `bb209277ca360cc059be3c679496395e`. Ten sections; §9 is F-491, §10 is F-492. |
| **2** | Fault Register | **DONE** | `Fault_Action_Register_v2_80.md` — **F-485 … F-492**, six of the eight the assistant's. **First 631,365 bytes byte-identical to v2.79 (`cf494367…`)**, +14,246 → **645,611 B**, md5 `33e700e291f0182512bbe374aba2ed14`. |
| **3** | KB Register (A2) + the four self-referential lines | **DONE — and two were stale** | `KB_Register_v5_98_S258close.md`, md5 `f0d59a9cdc4cacc14ab5276988546ce1`. **The how-to-use line was stale in TWO clauses at once**: the Runbook pointer read v176 while v178 was current, and the second Fault pointer read v2.77 while the first on the same line read v2.79. Both corrected visibly. **And the changelog section had stopped being written at v5.95** — no v5.96 or v5.97 bullet exists. Recorded, not back-filled. |
| **4** | Manifest (A7), written LAST | **DONE** | `CANONICAL_MANIFEST.md`. **Its own md5 is deliberately NOT quoted here**: the manifest rows this report, so stating the manifest's hash inside a document the manifest describes has no fixed point — **`MD5SUMS_ALL.txt` is the authority for it (F-120), and the gate is what proves it.** Every row of a file this close touched was rewritten from the bytes, not from the plan; rows were twice found carrying hashes from a previous pass and corrected. |
| **4b** | **A7b — the manifest's four self-referential surfaces** | **DONE, the first close to own them** | narrative · STATUS line · Tier-0 rows · footer. **The STATUS line had read S240 for eight consecutive closes** and the footer had been frozen at S255 for two, because no close step owned them. v14 A7b now does. |
| **5** | Runbook + START_HERE (A3/A4) | **DONE** | `HANDOFF_RUNBOOK_2026-09-15_Session258close_v179.md` (`e83fc7e7…`, §1 now **nine** mental models) · `START_HERE_SESSION_259.md` (`678f76da…`). |
| **6** | `OWNER_TODO_LIVE` (A10) | **DONE** | `3d742462…`. **A10b honoured: nothing was added that I could have done myself.** The one item that was about to be — `INSTALL_S275.bat` — was withdrawn as an invented step. |
| **7** | Live pins (A8/A8a/A8b) | **DONE** | `live_pins_S258close.txt`, md5 `3212d06ccb8a2f111ca586a05021b746` — **381 rows (VPS 327 · SHORT 20 · BLIND 34), `register_pin_verified: yes`**. **Regenerated a second time** after the F-491 edits changed the Register's bytes: a pin list generated from a superseded Register is not a pin list. **A8a: its manifest row was written in the same breath.** |
| **7b** | **A8c — the VPS deploy clone pulled** | **DONE** | carried by this session's two install lines (S273, S274), each of which included its own `git pull` (F-464). |
| **8** | **NOTION (A9)** | **DONE — URL quoted** | `https://app.notion.com/p/3dc18b9d8f91812da8acf8e53fae3451?pvs=204` — created first try, no 403. *(Its title was written as "three retractions", corrected to "two" so Notion and canon do not disagree.)* |
| **9** | **KB EXTENSION (A13)** | **DONE** — eight steps answered below | see §A13. |
| **9b** | the S258 canon snapshot | **DONE — and it had been frozen on superseded bytes** | the snapshot written earlier in the session held the **pre-F-491** Register, Archive, Fault Register, Runbook, entry point, brief and sums. **A frozen snapshot of the wrong bytes is worse than no snapshot**, because it claims to be this close's canon. All eleven files rewritten from the final bytes, plus `KIT_ID.txt` and this report. |
| **10** | **SSD (A14)** | **DONE** | mirror **now nightly, not at closes** (S272) — `KB_mirror_ClaudeCowork_nightly_2026-09-15.zip`, **90,893,382 B, 2,815 files, every CRC tested, verified by listing back.** Cold kit: see §E. Housekeeping list refreshed. |
| **11** | Cleanup (A13.5) | **NONE NEEDED, stated** | nothing was written to either drive root outside `ClaudeCowork\`, `_kbtools\` and `KB_canon_all\`. **No `_to_delete_S258\` was created, and that is the finding, not an omission.** The pre-existing loose files at both roots are ⭐0 item 17 and are the owner's. |
| **12** | Reduction tranche (A15), measured | **DONE — and it did NOT pay for the growth** | **before 1,892,654 (94.63 %)** → **after 1,893,431 / 2,000,000 (94.67 %). Net +777 bytes: the cap went UP across a close whose whole job included bringing it down.** Seven documents moved, each proven by hash in `KB_canon_all` first, and the canon they were making room for grew by more. **TWO WERE REFUSED**: `END_OF_SESSION_PROMPT_v13.md` and `START_HERE_PROMPT_v8.md` are **not in canon**, so project knowledge is their only copy — *no document moves that is its own only copy*. |
| **13** | Publish (A16) | **OWED — the owner's double-click** | `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` |
| **14** | **A16b — verify the publish landed** | **OWED, and it is mine** | commit hash + `md5sum -c` from **inside `KB_canon_all\`**, after he runs it. v14 forbids taking the word "published" for it. |
| **15** | **the never-cited percentage (PAPER_POLICY_v1.1)** | **UNKNOWN — and that is a finding, F-491** | the shelf reads **0 of 380**. **It is an artefact and is not to be quoted.** See below. |

---

## THE ONE NUMBER THE POLICY ASKS FOR — AND WHY IT IS NOT A NUMBER

`PAPER_POLICY_v1.1`: *"Report the never-cited percentage at every close. If it does not fall, the
policy did not take — say so."* At S257 it was **51 % (193 of 375)**. The shelf now reads **0**.

**That is not success. It is F-491.** `build_papers_index.py`'s `load_haystack()` builds the corpus
a paper is searched for in from `00_INDEX.md` **plus `MANIFEST.md5`** — and since S268 the manifest
is rebuilt nightly over the whole ClaudeCowork tree, 2,802 rows, every working paper included. **So
every paper's name is in the haystack by construction and nothing can ever be never-cited again.**

Both tools are correct. Put together one night later, one destroyed the other's meaning — **and the
destruction reports itself as good news.** 193 → 0 on a dashboard, no error anywhere. It was checked
only because A0 says *a result that would be pleasant if true gets checked harder.*

**Reported as UNKNOWN, not as 0. The last trustworthy reading is S257's 51 %.** The repair is named
in `START_HERE_SESSION_259` §7: drop `MANIFEST.md5` from the corpus, and count only a name appearing
in a document somebody *wrote*. It must also survive `S257_NEVER_CITED_193.md`, which lists all 193
— **a list of the unread is not a reading of them.**

---

## §A13 · THE KB EXTENSION CLOSE — eight steps

1. **`00_CANON_SNAPSHOT_S258\`** — frozen: manifest · Archive · Fault Register · Register · Runbook · entry point · brief · pins · `MD5SUMS_ALL.txt` · `KIT_ID.txt`. **DONE**
2. **`02_SESSION_KITS\S258\`** — S272 · S273 · S274 · S275 · S276, as published. **DONE**
3. **`03_WORKING_PAPERS\S258\`** — the build brief and this report. **DONE**
4. **Copy → verify → only then delete.** **DONE** — every tranche document was hashed in `KB_canon_all` before it left project knowledge, and two were refused for having no second copy.
5. **Sweep the bloat.** **NONE FOUND** — nothing written outside the three managed folders.
6. **`MANIFEST.md5` rebuilt after the sweep.** **DONE, by the 03:10 nightly (S268)** — 2,802 rows. *This is also the mechanism behind F-491: the rebuild is correct and it is what broke the shelf's metric.*
7. **`00_INDEX.md`** — S258 row added. **DONE**
8. **`knowledge_size` MEASURED — and the honest reading is that the tranche lost.** before
   **1,892,654 (94.63 %)** → after **1,893,431 / 2,000,000 (94.67 %)**. **Net +777 bytes.**
   *Measured with `project_info`, never projected — a projection from file size was once wrong by
   more than three times.*

   **Seven documents left and the number still rose**, because the Register, the manifest, the
   Runbook and this report all grew, and this close wrote F-491 and F-492 into every one of them.
   **A tranche that does not cover the close's own growth is not a reduction, and calling it DONE
   without the arithmetic would have hidden that.** *(Measured after the canon swaps; this report's
   own final revision moves it again by a few KB, which is the same self-reference the canon gate
   has — the direction and the margin are the signal, not the digit.)*

   **The margin is now 106,569 bytes — about five closes at this session's rate.** The durable answer
   has not changed since S206: **branch Sanjeevni/Marg into its own project.** Until that happens the
   tranche has to move more than the close adds, and at this close it did not.

---

## §E · THE COLD KIT

**DUE — the Register and the Archive both bumped.** Taken at this close: the canon set (16 documents),
the five kits, the pin file, `SUMS.md5` over all of it, and `00_READ_FIRST.md` written to restart
from this folder alone. **No patient data, no phone numbers, no tokens**, with `NO_PHONE_NUMBERS.py`
at the kit root so a restored copy still enforces F-185.

**Gated from inside the folder, and the count reconciled both ways: files = rows, none missing,
none orphaned.** `INSTALL_S275.bat` is deliberately absent (D523 — it was an invented step).

**Assembling it is what found F-492.** The per-kit file count did not match the source for one of
the five, and the kit with no `SUMS.md5` was the one that could not have told anybody.

---

## THE CANON GATE — measured, not assumed

**Reconciled both ways, which is the part that matters: zero files in canon without a row, and zero
rows without a file.** At the gate run that sealed this close: **550 files · 550 rows · `md5sum -c`
550 OK from inside the folder · zero unrowed · zero orphaned.**

**The absolute number is not a fixed target, and pretending otherwise would be the F-485 mistake in
reverse.** `canon_sums.py` leaves a dated backup of the previous sums file each time it runs, and
that backup is itself canon and is rowed on the next run — so the count rises by one per run, by
design. *A count is only meaningful against the count it ought to be*, and the two-way
reconciliation is what establishes that; the headline figure alone never could.

**Eight rows were force-rewritten** because their files legitimately changed at this close.
`canon_sums.py` **refuses** to rewrite a changed file's row without `--force-changed` — that refusal
is the whole point of it, and it is what stops a gate from quietly re-blessing a file nobody looked
at.

**This report is itself inside the gate**, so writing it changes what the gate covers. It is rowed,
and the sums are written last (F-479).

**Every one of the twelve files written to manojz was read back and hashed: 12 of 12 MATCH.**
A tool saying "written" is not a delivery (F-481).

---

## WHAT THIS CLOSE OWES THE NEXT ONE

1. **The publish, and then A16b** — the verification is mine, not his.
2. **`END_OF_SESSION_PROMPT_v13.md` and `START_HERE_PROMPT_v8.md` have ONE copy each**, in project
   knowledge. They are superseded, so nothing is at risk today, but a single copy is not a store.
   **They were not transcribed into canon at this close on purpose**: F-473 — exact bytes never pass
   through the assistant's own output, and 15 KB of canonical text retyped is exactly that risk.
   *(`END_OF_SESSION_PROMPT_v12.md` is fine — it is in `ClaudeCowork\01_RESCUED_FROM_PROJECT_KNOWLEDGE\`.)*
3. **F-491's repair**, before the shelf's figure is quoted again.
3b. **The cap.** 94.67 % and rising, ~106 KB of margin. **The next close cannot report a tranche as
   DONE unless the measured number falls** — the arithmetic, not the gesture.
3c. **A close step that derives every append-proof figure from the files** and fails the close when a
   stated figure disagrees with the file it describes. The stale-figure correction above is the
   fourth time the F-45 family has been caught by eye at a close this week; `canon_sums.py` proved
   the fix works for hash rows, and the same idea covers the prose.
4. **F-489 first** — item 3f cannot start until the hub and `sh_run` agree.
5. **`CANON_SUMS_LATEST.txt` should exist for the first time** on the morning of 16-Sep.

---

## AND ONE NOTE ON HOW THIS CLOSE WENT

**Four times this close, a thing that looked finished was not**, and not one of them was reported by
a gate:

- the pin list was generated, then the Register changed, so **it was generated again** — the first
  one was already stale on the day it was written;
- four manifest rows carried hashes from before the F-491 edits and **read as perfectly plausible**;
- the shelf's headline number had improved by 51 points and was wrong (**F-491**);
- **a kit shipped with no gate on itself**, and was found only by counting each kit's files against
  its source instead of trusting that five kits built the same way were built the same way
  (**F-492**).

- **and a fifth, found AFTER the publish, during A16b**: the Archive's byte count and `+N` figure
  were left at their pre-F-492 values — **`+17,588 → 1,457,178` where the truth is
  `+18,992 → 1,458,582`** — in the manifest, the Register's how-to-use line, `KIT_ID.txt` and **this
  report's own row 1**, together with the Archive's superseded md5. **Corrected visibly here, not
  silently.**

**All five were found by asking what a good-looking result was actually measuring.** That is A0, and
it is the only part of this routine that no automation replaces.

**The fifth deserves its own sentence, because it is this session's own lesson landing on this
session.** The canon gate passed 550 of 550 on the published commit **while four documents stated
the wrong size for a file the gate had just certified** — because *the gate hashes files and does
not read prose*. Exactly F-485's shape: **green is not the same as complete, and a gate answers only
the question it was built to ask.** The figures went stale because F-492 was minted after they were
written, and the re-flow updated the hash rows — which are mechanical — and not the sentences, which
are not.

**Nothing was wrong with the Archive.** Its append proof is sound and was re-derived from the
published bytes during A16b: the first **1,439,590** bytes of v1.95 are byte-identical to v1.94
(`2669e946…`). Only the description of it was stale. *A correct file described by a wrong number is
still a fault — it is how a later session gets told the wrong thing by canon.*

**It was not four figures, it was eleven.** The A16b sweep, run properly, found the Archive's size
and delta stale in four documents, **the Fault Register's size and delta stale in two**, and **five
superseded hashes quoted in this report's own checklist** — the Register, the Runbook, the entry
point, the pin list and the manifest. Each was correct when written and each was overtaken by the
next pass. **The count is the point: hand-written figures do not go stale one at a time, they go
stale in a wave, every time a document upstream of them is rewritten.**

**And the durable answer is not "check harder" — it is that these figures should never have
been typed.** The byte count, the delta and the md5 are all derivable from the two files. **S259
owes a close step that computes every append-proof figure from the files and refuses a close where a
stated figure and the file disagree** — the same move `canon_sums.py` made for the hash rows, applied
to the prose that quotes them.

**The last one is the sharpest, because it was found while doing the close rather than while doing
the work.** S276 had been built, walked, installed, and proven live by reading the machine's own
state back off the disk — the strongest proof in the session — and it still could not say whether
its own four files were the four it was built from. **A kit that proves what it does is not the same
as a kit that can prove what it is.**

---
*S258_CLOSE_REPORT · 15-Sep-2026 · in project knowledge, in `ClaudeCowork\03_WORKING_PAPERS\S258\`,
and in the cold kit. **Next free: D524 · F-493 · Session 259 · kit S277.***
