# END OF SESSION — full session close-out (v8)

**You don't need to paste this.** Just say one of:
- **"EOS"** — full close-out (a build session: code/config changed this session)
- **"EOS-light"** — light close-out (a fold-in / documentation / planning session: no live code touched)

I'll run the routine below from what's already in project knowledge. Re-paste this file only if you want to *change* the routine itself.

**What EOS-light skips that EOS does:** the GitHub commit message (C) and the Gmail health digest (B) — both assume code or a live-system check happened. Everything else runs the same in both modes. If I'm not sure which mode fits, I'll ask once rather than guess.

**v7 in one line (S201, owner directive):** the owner's living to-do — the list he actually opens between sessions — was maintained *"during the session"* and named only inside §2 of the Runbook. **v7 promotes it to a hard numbered step, A10**, refreshed and confirmed before the close is called done. Same lesson as A8 and A9, for the third time: *narrative is not procedure; only a numbered step survives.* Everything else is v6 unchanged.

**v6 in one line (S194):** Notion kept getting skipped at close (188–193 all missed — it was buried in section B as a passive "during the session" action, and a passive action is not a checkpoint). **v6 promotes it to a hard numbered step, A9** — the page-per-session log in Clinic HQ is written and its URL confirmed before the close is called done, exactly like the manifest and pin list. Same lesson as F-134.

**v5 in one line (S188, F-134):** v4's routine ended at A7 — the manifest, "always updated last". It was not last. **`live_pins.txt` is generated FROM the Register**, so every Register bump makes it stale by definition. **v5 adds step A8.**

**v4 in one line:** the monolithic KB is retired (D247). The KB is now a small **Register** (current state) + an append-only **History Archive**, and every canonical doc is tiered in **CANONICAL_MANIFEST.md**.

---

## A0. THE EVIDENCE RULE — **read before any comparison in this close (added at v8 — F-208)**

**RE-KEYED TEXT MAY CORROBORATE. IT MAY NEVER CONVICT.**

Any claim that two copies of a document differ — a drift, a stale store, a dropped block, a fork
— must rest on **either**:

- **bytes handled as bytes**: hashed, diffed, or delivered as a file; **or**
- **two independent transcriptions that agree.** One careful pass is not evidence, however
  careful it looked.

**Why this is at the top and not in a footnote.** At S204 the cross-store audit reported
`Diagnostics_Surveillance_System_Spec_v2_3` as drifted between the two stores. **The stores were
identical.** The audit's own transcription had dropped a four-line block — the D114 paragraph
naming the Fault Register as the authority — and it convicted on its own error. The remedy that
followed worked: transcribe twice, independently, compare — **42 of 44 converged byte-for-byte**,
and the two that did not were the ones worth looking at.

**And the rule already existed.** `S181_postclose_addendum` §3 forbade exactly this, and the
audit broke it anyway. **A rule that lives only in a document nobody re-reads is not a rule** —
which is why it is now step zero of the close, where it cannot be walked past.

**Its corollaries, each earned:**

- **A filename is not provenance (D188).** Hash it.
- **The newer store is not automatically the right store.** At S204 the repo's S190 policy was
  newer than project knowledge's **and still wrong against the deployed code**. Check against
  what runs.
- **A green check must be asked what question it answers.** `md5sum -c` on a kit, a live pin, a
  passing selftest: each is true about something, and it is rarely the thing being claimed
  (F-195, F-209, F-215).

---

## A. DOCUMENT UPDATES (always) — tier-aware

**A0. Session summary** for the runbook §0. Flag separately: any new fault codes, SOP changes, or surveillance-scope changes.

**A1. KB History Archive (Tier 1) — APPEND ONLY.** Append this session's `§S###` narrative and any full-text decision blocks. **Never rewrite earlier history; never re-open the whole file to edit it — the header line is carried forward verbatim and is NOT bumped**, because bumping it would break the pure-append property the next close has to prove. Prove the append mechanically: everything before the previous END marker must be byte-identical. Bump the Archive's minor version in the END marker only. Hand me the file **only on a session that added history**.

**A2. KB Register (Tier 0) — UPDATE current state only.** Refresh CURRENT LIVE FILE VERSIONS (the md5 line), add a one-line index entry for each **new** decision (authored from the Archive text, never from memory — D172), note any state change, add a changelog/lineage line. **Check the four self-referential lines every time — the H1, the END marker, the How-to-use pointers, and the reserved-next-free numbers.** They are the **F-45 family's** favourite home and have gone stale at three separate closes; a correction is made **visibly**, never silently. Prove zero loss by **reverse application** onto the manifest's pin. Hand me the file.

**A3. Runbook (Tier 0)** — write `HANDOFF_RUNBOOK_<date>_Session<N>_v<N>.md` with §0 (what happened), §1 (mental models), §2 (open backlog — the live one), §3 (install discipline), §4 (the boundary). Hand me the file.

**A4. START_HERE (Tier 0)** — write `START_HERE_SESSION_<N+1>.md` whose Phase 0 **verifies `CANONICAL_MANIFEST.md` by md5 (all tiers) but instructs reading only Tier 0**. It carries next-free D/F numbers and the backlog pointer. Hand me the file.

**A5. Tier-1 reference docs — only the ones that actually changed.** For each: update + hand me the file. For the rest: one combined line — *"Tier-1 unchanged this session: [list]"*.

**A6. Tier-2 frozen products — do NOT touch** without an explicit owner **waiver** (D34) + version bump + note.

**A7. CANONICAL_MANIFEST.md (Tier 0) — the linchpin, updated after every document above is final.** Recompute each md5 and update its row. Hand me the file.

**A8. THE LIVE-PIN LIST (Tier 0 discipline · added at v5 — F-134) — regenerate AFTER A7.**

```
python gen_live_pins.py <KB_Register_vX.md> --manifest CANONICAL_MANIFEST.md \
       --session "S### close" -o live_pins_S###close.txt
```

Confirm the header reads **`register_pin_verified: yes`**, ship it beside the canon, and note that the owner must copy it to `/root/deploy/live_pins.txt`. **A close that rebuilds the manifest and not the pin list is not finished.**

**A8b — REFRESH `deploy_kits/KB_canon_all/` IN THE SAME STEP (added at v7, S201).** `verify_live_pins.py` proves the pin list's source by looking in **exactly one folder** — `repo/deploy_kits/KB_canon_all/` — for a file that hashes to `source_md5`, and for the `CANONICAL_MANIFEST.md` **beside it** pinning that same hash as CURRENT. So the close must copy this session's **Register, manifest** (and, by convention, the rest of the canon set) into that folder. **A per-close `KB_canon_S###close/` folder does not satisfy the checker** — it never looks there.

*Why this is a numbered sub-step: the S200 close rebuilt the manifest and the pin list but left `KB_canon_all/` at Register **v5.44**, so its run could only ever return **AMBER (`register_not_in_repo`)** — every pinned file matching, but the source unprovable. Discovered at S201 by reading the checker rather than trusting the word GREEN in a header. This is the F-134 shape one folder over: a derived artefact must be rebuilt in the same routine that changes its source.*

**A9. NOTION SESSION LOG (Tier 0 discipline · added at v6) — a hard checkpoint.** Create the page-per-session entry in **Clinic HQ — Dr. Manoj** (page id `38618b9d-8f91-813e-9773-c20f567fd32f`), titled `Session <N> — <date> — <one-line summary>`, carrying what went live, the final live pins, the open backlog and the next-free numbers. **Confirm the page URL** in the close report. If the connector is absent this session, **say so explicitly** and carry it into the next START_HERE — never let it pass silently.

**A10. THE OWNER'S LIVING TO-DO (Tier 0 discipline · added at v7 — S201 owner directive) — a hard numbered step.** Refresh **`OWNER_TODO_LIVE.md`** in project knowledge so it is current **as at this close**, and confirm in the close report that it was written.

- It is the list the owner actually opens between sessions, in the product he reads (project knowledge), so it is the one artefact whose staleness he feels directly.
- **It is deliberately UN-MANIFESTED** — it edits continuously, and hashing it would make Phase 0 fail by design. That is exactly why it needs a numbered step: nothing else checks it. *(This is F-107's shape inverted — a document deliberately outside the register still needs an owner, and the routine is that owner.)*
- Every ⭐0 item completed this session is **struck through and moved to DONE with its session number**, never deleted; every new owner action, every finding that needs his ruling, and every parked item goes in. **Nothing gets left out** — the owner's words when he asked for this.
- Runbook §2 remains the close-time *snapshot*; **this file is the always-current truth**, and each must point at the other.

---

**A11. RE-CAPTURE THE LIVE PC TOOLS — AND VERIFY AGAINST THE LIVE SOURCE (added at v8 — F-215).**
On any session that changed a file on **manojz** or the **medical PC**, capture the current bytes
into `deploy_kits/S###_LIVE_TOOLS/` with a `SUMS.md5`, **and then perform the check that actually
matters:**

> **Compare every captured file against its LIVE SOURCE — not against the kit's own `SUMS.md5`.**
> Report the count both ways: *"N files checked against the live source: X drift, Y identical."*

**Why this is a numbered step and not a habit.** `S203_LIVE_TOOLS` was captured at 12:42 on
26-Aug; the three S203 repair kits landed at 12:53, 13:04 and 14:47 — *after* it — and nothing
re-captured at that close or the next. Three of its ten files held the **pre-fix** bytes,
including a `PULL_FROM_MEDICAL.bat` that writes `-- ok` unconditionally (**F-196**). **A rebuild
from that kit would have restored the exact fault that let the feed run dark for 8h40m while
reporting itself healthy.** It was also missing `PULL_HIDDEN.vbs`, the file the scheduled task
launches.

**And `md5sum -c` on it exited 0 the entire time**, because it hashes the kit against *itself*.
**A kit verified against its own copy proves nothing about whether it matches what is running.**
Never report that check as evidence the kit is current; it answers a different question.

**Also capture what the kit needs to be USED, not only its bytes:** install order, where each
file goes, which credentials are required (**never their values**), the scheduled tasks and the
account each must run as, and **the checks that prove it worked** (D350 §4). A kit whose
recovery procedure is not written is a set of files, not a rebuild.

---

## B. LIVE SYSTEM ACTIONS (connectors — executed live during the session)

- **Notion (the session log is A9):** additionally, update any Tech & Systems Register status that changed, move any Active Projects card, add new D-series decisions to the decisions log.
- **Drive:** upload any new/updated Tier-0/Tier-1 files (version-named) to Generated Documents.
- **Drive incident report:** only if an incident actually occurred.
- **Gmail (EOS only):** if `Diagnostics.gs` isn't live yet and a manual health check was actually done, draft a brief health note to `drmkaortho@gmail.com`.

**ClickUp is parked (D17)** — dropped from this routine entirely.

---

## C. GITHUB COMMIT (EOS only, skip on EOS-light)

```
Session <N>: <one-line summary>

- <file or change 1>
- <file or change 2>
- Docs: Register/Archive/manifest updated as needed
- Diagnostics: <any fault code or check changes>
```

---

## D. PROJECT KNOWLEDGE SWAPS — tier-driven

- **Tier 0 — almost always:** KB Register, Runbook, START_HERE, CANONICAL_MANIFEST (+ the Archive on any session that added history). **Plus `OWNER_TODO_LIVE.md` per A10** — updated in place, never version-swapped.
- **Tier 1 — only if §A5 flagged it changed.** **Tier 2 — never, unless a waiver was exercised.**

```
DELETE: KB_Register_v2.0.md
UPLOAD: KB_Register_v2.1.md
```

---

## E. COLD BACKUP — periodic, not every session

Skip by default; generate `DrManoj_Clinic_FULL_Handoff_Session<N>_<date>.zip` when ~3–5 sessions have passed, **or** the Register/Archive/Umbrella just bumped, **or** you ask. Flag at close if one's overdue rather than build it unasked.

---

## F. MAINTENANCE PROJECT CHECK — dormant until the project exists

---

*v8 changes from v7 (S205): **A0 — the evidence rule** promoted to step zero: re-keyed text
may corroborate, never convict (F-208, and the rule already existed in `S181_postclose_addendum`
§3 and was broken anyway). **A11 — re-capture the live PC tools and verify them against the
LIVE SOURCE**, never against the kit's own `SUMS.md5` (F-215: a kit that verified green held
the pre-fix bytes and would have restored the 8h40m fault).*

*v7 changes from v6 (S201): step **A10** added — the owner's living `OWNER_TODO_LIVE.md` is refreshed and confirmed as a numbered step, because a document deliberately kept outside the manifest has no other guardian. A2 also gains the explicit four-line self-reference check, after the F-45 family went stale at three separate closes in the same document.*

*v6 changes from v5 (S194): step **A9** added — the Notion page-per-session log is a hard, URL-confirmed numbered step.*

*v5 changes from v4 (S188, F-134): step **A8** added — the live-pin list is regenerated after the manifest.*

*v4 changes from v3 (D247): the KB split into Register + History Archive; A7 maintains CANONICAL_MANIFEST.md; START_HERE reads Tier 0 only; swaps are tier-driven; Tier-2 is edit-by-waiver.*
