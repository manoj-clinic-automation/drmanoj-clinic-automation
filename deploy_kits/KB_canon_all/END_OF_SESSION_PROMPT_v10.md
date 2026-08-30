# END OF SESSION — full session close-out (v10)

**You don't need to paste this.** Just say one of:
- **"EOS"** — full close-out (a build session: code/config changed this session)
- **"EOS-light"** — light close-out (a fold-in / documentation / planning session: no live code touched)

I'll run the routine below from what's already in project knowledge. Re-paste this file only if you
want to *change* the routine itself.

**What EOS-light skips that EOS does:** the GitHub commit message (C) and the Gmail health digest
(B) — both assume code or a live-system check happened. Everything else runs the same in both modes.
If I'm not sure which mode fits, I'll ask once rather than guess.

**v10 in one line (S207, owner directive):** v9's step A12 named the fourth store as
**`D:\ClaudeCowork\`**. **It is `D:\Downloads\ClaudeCowork\`** — and so did the index inside the
folder and `COWORK_FOLDER_INDEX.md` in project knowledge, all three written at the same close from
the same assumption. A session that trusted the routine **recorded A12 as un-runnable while the
folder sat, connected, one level down.** v10 corrects the path in the routine, adds the **external
1 TB SSD** to the store table, and promotes the standing reduction of project knowledge to a hard
numbered step, **A13** — because the plan to reduce it has existed since S206 and, being narrative
rather than a step, has moved exactly one document since. *Narrative is not procedure; only a
numbered step survives* — for the fifth time.

**v9 in one line (S206):** the knowledge base outgrew its container; the fourth store was created
and its refresh became step **A12**.
**v7 (S201):** the owner's living to-do became step **A10**.
**v6 (S194):** the Notion session log became step **A9**.
**v5 (S188, F-134):** the live-pin list became step **A8**.
**v4 (D247):** the monolithic KB retired; Register + Archive + `CANONICAL_MANIFEST.md`.

---

## A0. THE EVIDENCE RULE — **read before any comparison in this close**

**RE-KEYED TEXT MAY CORROBORATE. IT MAY NEVER CONVICT.**

Any claim that two copies of a document differ must rest on **either** bytes handled as bytes —
hashed, diffed, or delivered as a file — **or** two independent transcriptions that agree. One
careful pass is not evidence, however careful it looked.

**Why this is at the top.** At S204 a cross-store audit reported a spec as drifted. **The stores
were identical**; the audit's own transcription had dropped four lines and convicted on its own
error. And the rule already existed in `S181_postclose_addendum` §3, and was broken anyway — which
is why it is step zero, where it cannot be walked past.

**Its corollaries, each earned:**

- **A filename is not provenance (D188).** Hash it.
- **A PATH IN A DOCUMENT IS NOT PROVENANCE EITHER (added at v10).** `D:\ClaudeCowork\` was written
  into three canonical places and was wrong in all three. **Look for the folder before reporting it
  missing.**
- **The newer store is not automatically the right store.** Check against what runs.
- **A green check must be asked what question it answers.** `md5sum -c` on a kit, a live pin, a
  passing selftest: each is true about something, and it is rarely the thing being claimed.
- **AN EMPTY OR SMALL RESULT IS NOT GOOD NEWS (added at v10).** At S207 an expiry list that should
  have had rows came back with none, and the bug that produced it read as a clean shop. **A result
  that would be pleasant if true gets checked harder, not less.**

---

## A. DOCUMENT UPDATES (always) — tier-aware

**A0. Session summary** for the runbook §0. Flag separately: new fault codes, SOP changes,
surveillance-scope changes.

**A1. KB History Archive (Tier 1) — APPEND ONLY.** It lives in
`deploy_kits/KB_canon_all/`, **not in project knowledge** — it was moved out at S206. Append this
session's `§S###` narrative and any full-text decision blocks. **Never rewrite earlier history; the
header line is carried forward verbatim and is NOT bumped**, because bumping it would break the
pure-append property the next close has to prove. **Prove the append mechanically: hash the previous
file, then hash the same number of leading bytes of the new one and show they match.** Bump the
Archive's minor version in the END marker only.

**A2. KB Register (Tier 0) — UPDATE current state only.** Refresh CURRENT LIVE FILE VERSIONS, add a
one-line index entry for each **new** decision (authored from the Archive text, never from memory —
D172), note any state change, add a changelog/lineage line. **Check the four self-referential lines
every time — the H1, the END marker, the How-to-use pointers, and the reserved-next-free numbers.**
They are the **F-45 family's** favourite home; **at the S207 close three of the four were stale at
once.** A correction is made **visibly**, never silently.

**A3. Runbook (Tier 0)** — `HANDOFF_RUNBOOK_<date>_Session<N>_v<N>.md` with §0 (what happened),
§1 (mental models), §2 (open backlog — the live one), §3 (install discipline), §4 (the boundary).

**A4. START_HERE (Tier 0)** — `START_HERE_SESSION_<N+1>.md` whose Phase 0 **connects `Downloads`
and `dr-manoj-git`**, verifies `CANONICAL_MANIFEST.md` by md5 (all tiers) but instructs reading only
Tier 0, and **opens `D:\Downloads\ClaudeCowork\00_INDEX.md`**. It carries next-free D/F numbers and
the backlog pointer.

**A5. Tier-1 reference docs — only the ones that actually changed.** For the rest, one combined
line: *"Tier-1 unchanged this session: [list]"*.

**A6. Tier-2 frozen products — do NOT touch** without an explicit owner **waiver** (D34) + version
bump + note.

**A7. CANONICAL_MANIFEST.md (Tier 0) — the linchpin, updated after every document above is final.**
Recompute each md5 and update its row. **A row whose file is absent from project knowledge is not a
failed row — halt on a HASH MISMATCH, never on absence from one particular store.**

**A8. THE LIVE-PIN LIST (Tier 0 discipline) — regenerate AFTER A7.**

```
python gen_live_pins.py <KB_Register_vX.md> --manifest CANONICAL_MANIFEST.md \
       --session "S### close" -o live_pins_S###close.txt
```

Confirm the header reads **`register_pin_verified: yes`**, and note that the owner must copy it to
`/root/deploy/live_pins.txt`. **A close that rebuilds the manifest and not the pin list is not
finished.**

**A8b — REFRESH `deploy_kits/KB_canon_all/` IN THE SAME STEP.** `verify_live_pins.py` proves the pin
list's source by looking in **exactly one folder** for a file that hashes to `source_md5`, and for
the `CANONICAL_MANIFEST.md` **beside it**. A per-close `KB_canon_S###close/` folder **does not
satisfy the checker** — it never looks there.

**A9. NOTION SESSION LOG — a hard checkpoint.** Page-per-session entry in **Clinic HQ — Dr. Manoj**
(`38618b9d-8f91-813e-9773-c20f567fd32f`), titled `Session <N> — <date> — <one-line summary>`.
**Confirm the page URL** in the close report. If the connector is absent, **say so explicitly** and
carry it into the next START_HERE.

**A10. THE OWNER'S LIVING TO-DO — a hard numbered step.** Refresh **`OWNER_TODO_LIVE.md`** so it is
current as at this close. It is **deliberately UN-MANIFESTED** — it edits continuously, and hashing
it would make Phase 0 fail by design; that is exactly why it needs a numbered step. Every ⭐0 item
completed is **struck through and moved to DONE with its session number**, never deleted. **Nothing
gets left out** — the owner's words when he asked for this.

**A11. RE-CAPTURE THE LIVE PC TOOLS — AND VERIFY AGAINST THE LIVE SOURCE.** On any session that
changed a file on **manojz** or the **medical PC**, capture current bytes into
`deploy_kits/S###_LIVE_TOOLS/` with a `SUMS.md5`, **then compare every captured file against its
LIVE SOURCE — not against the kit's own `SUMS.md5`.** Report both ways: *"N files checked against
the live source: X drift, Y identical."* **A kit verified against its own copy proves nothing about
what is running.** Also capture what the kit needs to be USED: install order, destinations, which
credentials are required (**never their values**), scheduled tasks and the account each runs as, and
the checks that prove it worked.

---

**A12. THE COWORK FOLDER AND ITS MIRRORS — `D:\Downloads\ClaudeCowork\`**

⚠ **The path.** v9 said `D:\ClaudeCowork\`. **It is `D:\Downloads\ClaudeCowork\`**, reachable
whenever the **Downloads** folder is connected — which is how this project is normally worked.

**Five stores now hold this project's material, and one rule keeps them honest:**

| store | authoritative for | must never hold |
|---|---|---|
| **project knowledge** | canon — Tier 0/1, everything the manifest names | bulk data, backups, superseded working papers |
| **GitHub** | code + `deploy_kits/KB_canon_all/` | patient data, secrets, **phone numbers (F-185)** |
| **`D:\Downloads\ClaudeCowork\`** | everything canon excludes + dated frozen snapshots + session kits | **any live, editable copy of a canonical document** |
| **external 1 TB SSD** — `F:\ClinicBackup\` | dated frozen mirrors of that folder + the cold kits | nothing originates there |
| **Google Drive** | **not set up.** Never ruled out — what was ruled out (measured) was the GitHub sync filter. Still the only route to a phone or browser | — |

**NO DOCUMENT MAY BE LIVE AND EDITABLE IN TWO STORES** (D202 · F-201). Frozen snapshots are exempt.

**At every close:**

1. **File this session's working papers** into `03_WORKING_PAPERS\S###\`, and its kits into
   `02_SESSION_KITS\`. **Copy → verify → only then delete from project knowledge. Never the other
   way round.**
2. **Refresh `00_INDEX.md`** and **rebuild `MANIFEST.md5`**, then verify it.
3. **Report project-knowledge usage** in the close report — bytes and percent of the 2 MB cap.
   **A close that does not say how full the container is cannot see the wall coming.**
4. **Mirror to the SSD, or say in the close report that it was not connected.**
   **A mirror nobody refreshes is a copy that lies.**

**THE SSD — `F:\ClinicBackup\`, one folder per project**

⚠ **It does not mount in the device shell.** Reachable only by `device_list_dir` /
`device_stage_files` / `device_commit_files`, so it takes **archives, never a file-by-file sync** —
which is also the right shape, because an archive cannot drift into a second live copy.

```
F:\ClinicBackup\<ProjectName>\
   01_KB_MIRRORS\    a dated zip of the Cowork folder     -- EVERY close
   02_COLD_KITS\     dated full handoff kits              -- see §E
   03_BUILD_BRIEFS\  the loose brief                      -- EVERY close
   99_SUPERSEDED\    older copies awaiting deletion
```

**A file loose at the root has no owner.** In six months nobody knows which project it belonged to
or whether deleting it is safe. **A folder name is the cheapest provenance there is.**

5. **APPLY THE RETENTION RULE and say what was moved.** Keep the **3** most recent KB mirrors and the
   **5** most recent cold kits; everything older goes to `99_SUPERSEDED\`. Keep **every** build
   brief. Sweep `__pycache__`, `.pyc` and duplicate raw exports. **Moving is safe — the agent on
   manojz can do it. The final delete is the owner's, and never of the only copy.**

6. **WRITE ONE BUILD BRIEF** — the single document the next session reads *instead of* this
   session's working papers. Into project knowledge, the Cowork folder, and loose on the SSD.
   *Ten papers are a record; one brief is a handover.*

---

**A13. REDUCE PROJECT KNOWLEDGE BY ONE TRANCHE — a numbered step (added at v10, S207 owner directive)**

`KB_EXTENSION_PLAN` has existed since S206 with 112 classified candidates and an order to do them
in. **Being narrative rather than a step, it has moved exactly one document.** So:

**Every close moves ONE tranche**, in the plan's order, or states in the close report why it did
not. The tranches:

1. the **22 S206 papers** — six are superseded outright, and those are the most dangerous documents
   in the KB: a future session can read them as current and get wrong numbers
2. superseded runbooks (v113, v134, v138, v139) and the `Fault_Register_append_*` artefacts
3. **S179 – S184**, oldest first
4. **S194 – S202**, after confirming every D-number is indexed in the Register
5. **S205 — LAST**, and only after the §S205 gap is ruled on: those seven documents are the only
   surviving record of that session

**⛔ NEVER MOVE**, whatever the manifest says: the evergreen `START_HERE_PROMPT`, the current
`live_pins_*`, `OWNER_TODO_LIVE.md`, `UNATTENDED_QUEUE.md`, open work orders, and **any INCIDENT
document not confirmed closed** — Phase 0 reads "any open incident" as Tier 0.

**Measure, never project.** At S206 a projection from file SIZE said the Archive was 46.9 % of the
cap; the measured delta was **13.6 points** — wrong by more than three times, because
`knowledge_size` is an **indexed** measure, not a sum of bytes. **Report the measured
`knowledge_size` before and after every tranche.** It also means small documents may cost
proportionally more than their bytes suggest, so the ranking above is a hypothesis until a tranche
is measured.

**The durable answer is still branching Sanjeevni / Marg into its own project** once it is stable.
Tranches buy time; they are not the fix.

---

## B. LIVE SYSTEM ACTIONS (connectors)

- **Notion (the session log is A9):** additionally update any Tech & Systems Register status that
  changed, move any Active Projects card, add new D-series decisions.
- **Drive:** upload new/updated Tier-0/Tier-1 files (version-named) to Generated Documents, and
  refresh the ClaudeCowork mirror (A12 §4).
- **Drive incident report:** only if an incident actually occurred.
- **Gmail (EOS only):** if `Diagnostics.gs` isn't live and a manual health check was done, draft a
  brief health note to `drmkaortho@gmail.com`.

**ClickUp is parked (D17)** — dropped from this routine entirely.

## C. GITHUB COMMIT (EOS only)

```
Session <N>: <one-line summary>

- <file or change 1>
- Docs: Register/Archive/manifest updated as needed
- Diagnostics: <any fault code or check changes>
```

**Run `deploy_kits\NO_PHONE_NUMBERS.py` before proposing the commit (F-185).**

## D. PROJECT KNOWLEDGE SWAPS — tier-driven

- **Tier 0 — almost always:** KB Register, Runbook, START_HERE, CANONICAL_MANIFEST. **Plus
  `OWNER_TODO_LIVE.md` per A10** — updated in place, never version-swapped.
- **Tier 1 — only if §A5 flagged it changed.** **Tier 2 — never, unless a waiver was exercised.**

## E. COLD KIT — a cadence, and it is written down so it can be kept

**Take one when EITHER is true:** **three sessions** since the last, **or** the KB Register or
History Archive **just bumped**. Whichever comes first — on an active project the bump usually does.

**What goes in:** the canon set · this session's kits · the pin file · `SUMS.md5` over all of it ·
and a `00_READ_FIRST.md` saying how to restart from the kit alone. **No patient data, no phone
numbers, no tokens** — and put `NO_PHONE_NUMBERS.py` *inside* the kit so a restored copy still
enforces that.

**Where it goes:** `F:\ClinicBackup\<Project>\02_COLD_KITS\` **and** `D:\Downloads\`.

**RECORD, every time, in the close report AND in the evergreen prompt:** what was taken, **its
md5**, where it went, and **when the next one is due.** *A cadence nobody writes down is a cadence
nobody keeps — which is why this project went from S181 to S206 with two cold kits.*

| | |
|---|---|
| **last taken** | **S207, 28-Aug-2026** — `DrManoj_Clinic_FULL_Handoff_Session207_2026-08-28.zip`, 94 files, md5 `8989e0f1d59b09379ecf322b421b7db2` |
| **next due** | **S210, or the next Register/Archive bump — whichever is first** |

## F. MAINTENANCE PROJECT CHECK — dormant until the project exists

---
*v10 changes from v9 (S207): **A12's path corrected** to `D:\Downloads\ClaudeCowork\` and the
external SSD added to the store table; **A13 added** — one reduction tranche per close, measured not
projected; A0 gains two corollaries earned this session — *a path in a document is not provenance*,
and *an empty or small result is not good news*; A1 records that the Archive now lives in
`KB_canon_all/`; C requires the phone-number gate to run before a commit is proposed.*
