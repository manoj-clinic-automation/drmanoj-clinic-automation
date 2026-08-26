# HANDOFF RUNBOOK — v137 (Session 203 · THE SESSION THAT LOOKED AT THE MACHINES THEMSELVES · 26 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 203 — FULL build EOS)

Opened as documentation housekeeping. Became the first honest inventory of the two Windows PCs the
pharmacy revenue chain actually runs on.

1. **THE CHAIN — three faults, each visible only because the one before it was fixed, in one
   evening.**
   **18:38** — `S203_R2` gave the pull a log (**F-197**). Until then the leg was dark: `PULL_HIDDEN.vbs`
   had discarded stdout every ten minutes for a session and a half.
   **18:44** — its **first log ever kept** ended `pipeline_status: post failed (HTTP Error 401)`.
   That line had printed on **every pull since S202** and been thrown away every time (**F-194**).
   **18:51** — traced to `_gate()`, a `before_request` that fails closed and exempts exactly three
   literal paths (the cron token on any path · `MARG_TOKEN` for `/finance/api/marg-push` ·
   `RENEWALS_TOKEN` for `/finance/api/renewals-push`). **`/finance/api/pipeline-status` was added at
   S202 and never added to that list**, so every real post was refused **before**
   `api_pipeline_status()` ran and the route's own token check was unreachable dead code.
   **B2 — the pipeline heartbeat, the whole point of two S202 kits — had never once reported.**
   Proven both ways with the server's own token: **401 `not_signed_in` before**, **HTTP 200
   `{"ok":true,"received_at":"2026-08-26T18:52:00"}` after.**
   **19:17** — proven again **from the REAL caller, not a curl**: three consecutive
   `pipeline_status: 200 (token from medical PC (live))` in the pull's own console log, including the
   **scheduled** runs at 19:10 and 19:17.

2. **Why it shipped broken, and why the fix for it does not bite (F-195, OPEN, ours).** The smoke
   suite *does* post with the `X-Finance-Marg` header — but on `c`, a **signed-in** test client, so
   `_gate()` waved it through on the **session** and the token clause was never exercised. The check
   above it, *"an unauthenticated pipeline post is REFUSED"*, returned 401 from the **route's** check
   rather than from the gate. **Both checks passed for reasons other than the ones they name.** The
   two checks added at S203 to close that hole **do not bite either** — reverting the gate still
   gives **721/721**. Recorded green-and-meaningless rather than left looking like coverage.

3. **THE FIRST MEDICAL-PC PINS EVER TAKEN.** Seven hashed files plus `token.txt` (deliberately never
   hashed), read **from the machine** by `medical_census.py` S203.6 at 13:04 —
   `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md`, now rows in the Register. Drift there had
   been **undetectable by construction**: `verify_live_pins.py` runs on the VPS and cannot reach the
   machine, the Tailscale share is read-only and D:-only, and manojz's mirror is `robocopy /E` with
   **no `/PURGE`** — it still showed 340 `marg_watch.py.before_*` files, an AutoHotkey install and
   three tools the machine's own listing proves are gone (**F-199**).

4. **AF-1's PROPOSED STRIKE WAS REFUSED ON EVIDENCE (F-206) — AF-1 IS LIVE AND ARMED.** The close
   proposed to strike AF-1 because it is filed against `GUARD_AND_SEND.bat`, which the medical PC does
   not have. **Wrong.** `GUARD_AND_SEND.bat` is 88 lines and contains no `curl`, `last_response`,
   `sent_hashes`, `ACCEPTED-FOR-REVIEW` or `http_code` — **AF-1's mechanism was never in it.** It is in
   **`SEND_TO_CLINIC.bat`, live on the medical PC at `e19a8a777ac22fe75a242f1eb9762185`**: `%RESP%` is
   not deleted before `curl`, the `findstr /c:"ACCEPTED-FOR-REVIEW"` success test never consults
   `%HTTP%`, and a false accept appends the hash to `sent_hashes.txt`, blacklisting that report **for
   ever**. `SEND_TO_CLINIC.bat` is self-contained **and** AF-1 is live inside it — both true at once,
   and the strike confused them. **It is the only medical-side fallback D347 preserves.**

5. **THE BACKUP — measured, then fixed.** `E:` present, 28.5 GB free of 28.9 · 177 files, 0.4 GB ·
   newest **22-Aug** · `E:\auto` and `E:\MARGBCKUP\auto` **EMPTY**, `E:\MARGBCKUP` last written
   **09-Oct-2025** · **six non-Microsoft scheduled tasks, all Google and OneDrive** · 115 Marg config
   files, **none mentions backup** · `margwin.exe` running (pid 7172), so `D:\MARGERP\Data` is open
   FoxPro tables · previous FY last backed up **17-Jul**. **So F-191(c) was wrong (F-201): the
   automatic backup was never *scheduled*, not "configured and has never once run".** The empty `auto`
   folders were never going to fill. Marg's own `serverbackup` is no substitute — the real ~2.3 MB
   `*_c18_d_*` pair only on 26, 25, 22-Aug then a **12-day gap** to 10-Aug, and it sits on **D:, the
   same disk as the data**. **Fixed:** the agent now copies the stick offsite automatically —
   **proven at 19:37, `offsite: 182 file(s), 0.41 GB … offsite copy is COMPLETE`, newest backup
   0.2 days old**, unattended, within the hour of the owner taking a fresh backup.
   **Still open: no restore has ever been tested; the previous financial year is 40 days stale with
   one copy.**

6. **D351 MINTED — sixty-nine Marg/medical documents to three**, at the owner's own words. One
   `CURRENT`, one append-only `HISTORY`, one printed `WALL_CARD`, plus a report-expectations spec.
   **Preserved first, retired second:** 52 documents copied into `deploy_kits/S203_MARG_CANON/` and
   hash-verified (**67 files, `md5sum -c` exit 0**); only then were **18 removed from project
   knowledge**, each proven present in pushed commit `f94ff27a8b89f01363e62c9f800acd55ff4ff00d` first.

7. **Kits live, every pin recorded as it moved (F-97) and re-verified from the box at this close:**
   `S203_R1` `marg_router.py` (selftest **14 → 21**, +7 exactly) · `S203_R2` `PULL_FROM_MEDICAL.bat` +
   `PULL_HIDDEN.vbs` · `S203_R3` `pipeline_status.py` (**15 → 21**, +6 exactly; **installed by Claude
   directly**) · the VPS B2 gate then the B2 test (**719 → 721**, +2; the gate fix correctly adding
   none) · `medical_agent.py` **S203.3** · `medical_census.py` **S203.6**. **Every projection was
   written before measuring, and every one landed.**

8. **A stale record found by re-measuring:** the Register's S202 row for `PULL_FROM_MEDICAL.bat`
   recorded `3c5389d5…`; the box actually held **`92f03999…`** immediately before `S203_R2`, and
   `3c5389d5…` now sits beside it as `PULL_FROM_MEDICAL.bat.bak_before_diag`. The owner's own edits
   moved the file after the S202 close — exactly as that row had warned they might. Corrected in the
   Register, struck rather than overwritten.

**Thirteen findings — F-194 … F-206. Five are the assistant's own, and a sixth (F-206) was found at
this close.** F-195 checks that do not bite · F-200 the stale store · F-204 a `NameError` shipped
twice behind a non-unique anchor and a `trap … EXIT` pasted into an interactive shell · F-205
thirteen documents produced while consolidating sixty-nine away · and a verdict built on a shadowed
variable that announced *"the backup target is NOT ATTACHED"* while the same report said *"E: is
present"*.

**D347 AMENDED: Tailscale is the SOLE transport, not "NOT load-bearing".** The 26-Aug outage proved
it. Recorded in the Register as a ruling amending a ruling, not as a silent edit.

---

## §1 — MENTAL MODELS (added this session)

- **A test must post the way the caller posts.** A signed-in test client is not the caller. Two checks
  passed for reasons other than the ones they name, and the check written to fix them did the same.
- **The first fix in a dark leg is a log, not a theory.** There is no version of this evening in which
  F-194 is found without F-197 being fixed first.
- **A route is not reachable because it exists; it is reachable because something lets it in.**
- **A mirror without purge can only be true about what was added.** It can never tell you what is
  gone, so it is not evidence of what is on the machine.
- **Neither store is authoritative by position.** Compare by md5, never by where a file sits. The
  repo was the fresher store and project knowledge the stale one — the opposite of the assumption.
- **Strike a fault by finding its mechanism absent, never by finding a filename absent.** Three
  correct-looking steps and a wrong answer, because none of them asked where the mechanism was.
- **A rollback in an interactive paste must be an explicit command, never a trap.** `trap … EXIT`
  does not fire in the shell you are typing into; a reverted file sat on disk while it was believed
  restored.
- **`py_compile` proves a file parses, not that it runs.** A `NameError` shipped twice past it.
  **pyflakes catches it, and is now used beside `py_compile`.**
- **An anchor that is not unique is not an anchor.** The insertion matched in two places and both
  were patched.
- **Preserve before you retire.** Copy, hash-verify, prove present in a pushed commit — *then*
  remove. The reverse order is how F-89 lost three canonical documents permanently.
- **Configured is not scheduled.** Eleven months of an empty folder were read as a backup that kept
  failing; nothing had ever been asked to run.
- **A count is measured on the machine, not inferred from a record.** The token lives in five stores,
  not the three the record carried.

---

## §2 — THE LIVE BACKLOG

> **The maintained copy is `OWNER_TODO_LIVE.md`** (project knowledge, un-manifested by design,
> refreshed at every close as step A10). This is the close-time snapshot.

**⭐0 — owner actions:**

- **PUBLISH** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` on manojz. The whole S203
  close is committed locally only until this runs.
- **Copy the pin list** — on the VPS:
  `cp /root/deploy/repo/deploy_kits/KB_canon_all/live_pins_S203close.txt /root/deploy/live_pins.txt`
  then `python3 /root/deploy/verify_live_pins.py`. **Publish first.** *(Note: the new medical-PC and
  manojz rows are BLIND to this checker by construction — F-186. It cannot reach either machine.)*
- **TOKEN ROTATION** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`) — aging since 21-Aug, still the
  oldest and highest-severity item. **It lives in FIVE stores, not three (F-202):** the VPS unit · the
  medical PC · the manojz cache · `D:\Downloads\MARG_TOKEN_S187.txt` · a loose file under
  `margsync\_to_delete\S201_20260825\loose\`. **Parked at your ruling** — but a rotation done against
  the old count of three would be incomplete.
- **TEST ONE RESTORE.** No restore of a Marg backup has ever been tested. Eleven months of files
  nobody has opened. The offsite leg is now automatic and proven; the restore is not.
- **The previous financial year** (`d1-sanjeevni-20250401-20260331`) is **40 days stale with one
  copy** — last backed up 17-Jul. Take one and let the agent carry it offsite.
- **Pravesh exits 31-Aug** · July cash top-ups Rs 4,519 · Surendra Rs 516 · Arjun's actual-paid ·
  Shivani's two August items · **AF-3's duplicate-advance scan before the August close**.
- **F-173** — the April-2025 NEFT advice file's shifted account column. Still the only open item where
  money may already have left for the wrong party.
- **Generate 25-Aug's Marg sale report** — the picture correctly reports it missing.
- **F-185** — the repo visibility ruling is yours, on the corrected figures: 62 mobile-shaped numbers,
  **no diagnoses, ever**.
- **Marg support**, one message: (a) can `margwin.exe` generate or export a named report from the
  command line? (b) **not** "why does automatic backup fail" — F-201 settled that: **it was never
  scheduled.** Ask instead how to schedule one, given `margwin.exe` holds `D:\MARGERP\Data` open.

**⭐1 — builder queue, in the owner's stated order:**

1. **D350 §2/§3/§4 — the reinstall kits FIRST.** §4 the reinstall kit, **Marg and its data first**,
   the pipeline second · §2 verification at both ends, measured never inferred · §3 what B2 must show.
   **§1 the Drive fallback stays PARKED. §5 was done at S202 — verify, do not redo.**
2. **F-195** — make the pipeline-gate check actually bite: post the way the caller posts, from an
   unauthenticated client, and prove it RED against the reverted gate before it counts as coverage.
3. **F-200** — the inverse check across stores: for every document in both project knowledge and the
   repo, compare by md5 and reconcile the differences. Owed.
4. **AF-1 (F-206)** — it is armed in `SEND_TO_CLINIC.bat` on the medical PC. Either check `%HTTP%`
   before the ACCEPTED branch and delete `%RESP%` before `curl`, or at minimum put the cure —
   deleting one line from `sent_hashes.txt` — where the person at the machine can find it. It is
   written nowhere today.
5. The rest: F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 · Staff
   Console Phase 0 (four owner rulings owed) · **Purchase Portal (D335)**.

**⭐2 — the August close** remains the first fully live enforced run.

**⭐3 — blocked:** the no-clinic-ID bills → Docterz migration · Lab PC / Labmate.
**D348 conflicts with `MARG_INGESTION_REFERENCE_v1` §9 item 5** — D348 rules a missing clinic ID is
`info` and counts in full; `ingest.min_confidence` = 0.70, tuned for OCR, sends it to review anyway.
Flagged in the Register, **not resolved**; the reference itself says the threshold is an owner
decision, not a code one.

---

## §3 — INSTALL DISCIPLINE (updated)

Unchanged, plus four earned today:

- **`pyflakes` runs beside `py_compile`, always.** `py_compile` proves a file **parses**, not that it
  **runs**; a `NameError` shipped twice past it. Both, on every Python file, before anything moves.
- **An insertion anchor must be proven unique before it is used.** Count the matches. The `NameError`
  existed because the anchor matched in two places and both were patched.
- **Exact-count gates.** `721/721`, never a pattern that might match. And an exact count is only
  evidence if the projection was **written before measuring** — every one of this session's was, and
  every one landed: +7, +6, +2, and a gate fix that correctly added **none**.
- **Red-proof every new check.** Run it against the **unpatched** file first and record what actually
  fails: R1's seven → **five go RED** (the two that pass were already true); R3's six → **check 10
  FAILS**. A check that has never been seen red is not evidence — **F-195 is the instance where this
  was skipped and the checks turned out not to bite.**
- **Reverse-apply every kit onto its live pin** before it counts as installed. Every file this session
  returned **exactly** to its recorded pin.
- **Never `trap … EXIT` in an interactive paste.** A rollback the owner must trigger is an explicit
  command he types, visible in the block, not a shell feature that silently does not fire.

---

## §4 — THE EOS AUTOMATION BOUNDARY (moved, deliberately, and recorded)

The owner changed the delivery rule at this close: ***"copy block please, and make it default
everywhere"*** — **a copy block is now the default for EVERY machine**, not only the VPS, superseding
the deliver-a-`.bat`-to-double-click habit. **And where Claude has write access, it installs directly
rather than handing over work** — `S203_R3` was installed that way, onto manojz, because
`D:\Downloads` is connected.

**What has NOT moved:** the owner installs anywhere Claude has no write access, and **he holds every
credential**. No token, password or key enters a session. Nothing already live is rebuilt without his
explicit OK, and the manual workflow always stays as the fallback.

---

*HANDOFF_RUNBOOK v137 · written at the S203 close · supersedes v136.*
