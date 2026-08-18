# END OF SESSION — full session close-out (v5)

**You don't need to paste this.** Just say one of:
- **"EOS"** — full close-out (a build session: code/config changed this session)
- **"EOS-light"** — light close-out (a fold-in / documentation / planning session: no live code touched)

I'll run the routine below from what's already in project knowledge. Re-paste this file only if you want to *change* the routine itself.

**What EOS-light skips that EOS does:** the GitHub commit message (C) and the Gmail health digest (B) — both assume code or a live-system check happened. Everything else runs the same in both modes. If I'm not sure which mode fits, I'll ask once rather than guess.

**v5 in one line (S188, F-134):** v4's routine ended at A7 — the manifest, "always updated last". It was not last. **`live_pins.txt` is generated FROM the Register**, so every Register bump makes it stale by definition; S187 regenerated it by hand and recorded the fact as narrative, v4 never gained a step, and the S188 close skipped it — sending the owner's own close-out check RED on two files the box had right. **v5 adds step A8.** Everything else is v4 unchanged.

**v4 in one line:** the monolithic KB is retired (D247). The KB is now a small **Register** (current state) + an append-only **History Archive**, and every canonical doc is tiered in **CANONICAL_MANIFEST.md**. The routine below writes only what a session actually touched — it never rewrites the whole history again.

---

## A. DOCUMENT UPDATES (always) — tier-aware

**A0. Session summary** for the runbook §0. Flag separately: any new fault codes, SOP changes, or surveillance-scope changes.

**A1. KB History Archive (Tier 1) — APPEND ONLY.** Append this session's `§S###` narrative and any full-text decision blocks to `KB_History_Archive_vX.md`. Never rewrite earlier history; never re-open the whole file to edit it. Bump the Archive's minor version. Hand me the file **only on a session that added history** (i.e. almost every EOS; rarely an EOS-light).

**A2. KB Register (Tier 0) — UPDATE current state only.** In `KB_Register_vX.md`: refresh CURRENT LIVE FILE VERSIONS (the md5 line), add a one-line index entry for each **new** decision (authored from the Archive text, never from memory — D172), note any state change in §12A, add a changelog line. This file stays small and roughly flat. Hand me the file (Tier 0 → always in the swap list).

**A3. Runbook (Tier 0)** — write `HANDOFF_RUNBOOK_<date>_Session<N>_v<N>.md` with §0 (what happened), §1 (mental models), §2 (open backlog — the live one). Hand me the file.

**A4. START_HERE (Tier 0)** — write `START_HERE_SESSION_<N+1>.md` whose Phase 0 **verifies `CANONICAL_MANIFEST.md` by md5 (all tiers) but instructs reading only Tier 0** (START_HERE, Register, Runbook, any open incident). It carries next-free D/F numbers and the backlog pointer. Hand me the file.

**A5. Tier-1 reference docs — only the ones that actually changed:** Umbrella Architecture · API Quick-Ref Card · Call Console Spec · Diagnostics & Surveillance Spec · Maintenance & SOP Spec · AI Verdict Layer Master · Frontend Dashboard doc · Fault→Action Register · Callback Tracker Audit. For each that changed: update + hand me the file. For the rest: one combined line — *"Tier-1 unchanged this session: [list]"* — not a confirmation each.

**A6. Tier-2 frozen products — do NOT touch** (Callback Tracker core, Attendance, Nutrition/Diet HTML, Consent HTML, WABA templates). Changing one needs an explicit owner **waiver** (D34 discipline) + a version bump + a note; absent that, they are hash-verified only and never edited here.

**A7. CANONICAL_MANIFEST.md (Tier 0) — the linchpin, ALWAYS updated last.** After every file above is final, recompute its md5 and update its row (version · md5 · tier · last-changed session). This is the file the next session's Phase 0 checks against. Hand me the file.

**A8. THE LIVE-PIN LIST (Tier 0 discipline · added at v5 — F-134) — regenerate AFTER A7.** `live_pins.txt` is **generated from the KB Register**, so a Register bump makes it stale by definition, and `verify_live_pins.py` will report RED at the next open on files the box has perfectly right. It must run **after** the manifest, not before: the generator refuses unless the Register hashes to the manifest's CURRENT row (**F-110**).

```
python gen_live_pins.py <KB_Register_vX.md> --manifest CANONICAL_MANIFEST.md \
       --session "S### close" -o live_pins_S###close.txt
```

Confirm the header reads **`register_pin_verified: yes`**, ship it beside the canon (a
`KB_canon_S###close/` folder), and note that the owner must copy it to `/root/deploy/live_pins.txt`
on the box. **A close that rebuilds the manifest and not the pin list is not finished.**

*Why this is a numbered step and not a note: S187 did it, wrote about it in the manifest, and the
instruction did not survive to S188. Narrative is not procedure (F-134).*

---

## B. LIVE SYSTEM ACTIONS (connectors — executed live during the session, not a separate step)

- **Notion:** update any Tech & Systems Register status that changed; move any Active Projects card that completed/started; add new D-series decisions to the Clinic HQ decisions log; add a Clinic HQ page if a new spec doc was created.
- **Drive:** upload any new/updated Tier-0/Tier-1 files (version-named) to the Generated Documents folder.
- **Drive incident report:** only if an incident actually occurred — Google Doc in `Incident Reports/`, format from Diagnostics Spec §4.
- **Gmail (EOS only, skip on EOS-light):** if `Diagnostics.gs` isn't live yet and a manual health check was actually done, draft a brief health note to `drmkaortho@gmail.com`. No manual check → skip.

**ClickUp is parked (D17)** — dropped from this routine entirely.

---

## C. GITHUB COMMIT (EOS only, skip on EOS-light)

Ready-to-paste commit summary covering every file actually changed this session:

```
Session <N>: <one-line summary>

- <file or change 1>
- <file or change 2>
- Docs: Register/Archive/manifest updated as needed
- Diagnostics: <any fault code or check changes>
```

If nothing has a real GitHub home this session, I'll say so instead of forcing an entry.

---

## D. PROJECT KNOWLEDGE SWAPS — tier-driven

Only the files that actually changed. In practice:
- **Tier 0 — almost always in the list:** KB Register, Runbook, START_HERE, CANONICAL_MANIFEST. (KB History Archive too, on any session that added history.)
- **Tier 1 — only if §A5 flagged it changed.**
- **Tier 2 — never, unless a waiver was exercised.**

```
DELETE: KB_Register_v2.0.md
UPLOAD: KB_Register_v2.1.md
```

(repeat per changed file)

---

## E. COLD BACKUP — periodic, not every session

Skip by default. I'll generate `DrManoj_Clinic_FULL_Handoff_Session<N>_<date>.zip` (Register + Archive + all Tier-1 specs + manifest + START_HERE + EOS prompt) only when: ~3–5 sessions since the last one, **or** the Register/Archive/Umbrella just bumped a version, **or** you ask. I'll flag at close if one's overdue rather than build it unasked.

---

## F. MAINTENANCE PROJECT CHECK — dormant until the project exists

Skipped until the Maintenance & SOP project is created. When it goes live: project-knowledge sync (Register + changed SOPs) and confirming any newly-live module is in the surveillance register with a matching `Diagnostics.gs` check.

---

*v5 changes from v4 (S188, F-134): step **A8** added — the live-pin list is regenerated after the
manifest, because it is derived from the Register and the manifest pins the Register. A derived
artefact must be rebuilt in the same routine that changes its source.*

*v4 changes from v3 (D247): the KB split into Register (Tier 0, current state) + History Archive (Tier 1, append-only) replaces the "append a section + rewrite the KB" step; a new step A7 maintains CANONICAL_MANIFEST.md as the linchpin Phase 0 verifies; START_HERE now reads Tier 0 only and hash-verifies the rest; project-knowledge swaps are tier-driven; frozen Tier-2 products are edit-by-waiver only.*
