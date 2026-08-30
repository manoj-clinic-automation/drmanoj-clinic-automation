# START HERE — SESSION 208

**Written at the S207 close, 28-Aug-2026 IST.**

---

## Phase 0 — before any work

1. **Connect `Downloads` and `dr-manoj-git`** on manojz. Without `Downloads` there is no Marg
   archive, no config store and no ClaudeCowork.
2. **Verify `CANONICAL_MANIFEST.md` by md5, all tiers.** A mismatch halts work. **A row whose file
   is absent from project knowledge is not a failed row** — the Archive lives in
   `deploy_kits/KB_canon_all/` and is named there deliberately.
3. **Read Tier 0 only:** the manifest, `START_HERE_PROMPT_v6`, **KB Register v5.58**,
   **HANDOFF_RUNBOOK v141**, and any open incident.
4. **Open `D:\Downloads\ClaudeCowork\00_INDEX.md`.** ⚠ **Not `D:\ClaudeCowork\`** — that path is
   written into three canonical documents and is wrong in all three; S207 corrected the routine and
   the index but the folder-index doc in project knowledge still needs its title fixed.
5. Confirm, then ask which backlog item to start.

## Current canon

| | |
|---|---|
| KB Register | **v5.58** (S207 close) |
| KB History Archive | **v1.54** — in `deploy_kits/KB_canon_all/`, not project knowledge |
| Runbook | **v141** |
| Close-out routine | **`END_OF_SESSION_PROMPT_v10`** |
| Evergreen prompt | **`START_HERE_PROMPT_v6`** |
| Fault register | `Fault_Action_Register_v2_44` |

**Next free: D353 · F-218 (the fork above it is UNRATIFIED) · A-D25 · Session 208.**

## What S207 left, in one paragraph

Nine kits staged and none installed; the VPS untouched. **The expiry list was withdrawn** after the
owner challenged its source, and Marg's own report returned one row where twenty-eight had been
claimed. **F-185 was broken by this session's own kit and caught before publish**; there is now a
program that fails the build on a contact number. **R6 retires the manual expiry-removal method** in
favour of a stock adjustment voucher, and **R11 makes an employee code permanent** — a reused code
silently rewrites a departed person's attendance history.

## First things to pick up

1. **Bake the scanner in** — the owner's words: *"bake all in, will refine later if needed."*
2. **The staff exit flow**, modelled on the joiner. **Pravesh leaves 31-August.**
3. **A13 — move one KB reduction tranche** and report the measured `knowledge_size` delta.
4. **Add the external 1 TB SSD** to the store table in `COWORK_FOLDER_INDEX` and fix its title path.

## THE 1 TB DISK — DECIDED AT THE S207 CLOSE, SCOPED FOR THIS SESSION

**Owner asked: can the SSD mitigate what the clinic is exposed on? Answer: YES for two of the three,
NO for the biggest one — and the honest part is the NO.**

| exposure | does the disk help? |
|---|---|
| **The Marg backup stopped 7 May and no restore has EVER been tested** | **NO.** Copying a backup does not test it. A third copy of an unproven backup is a third unproven backup. **This needs the vendor engineer and a restore into a TEST company — nothing else touches it.** *(A secondary yes: it gives the `.mbk` files a second physical location beside the stick and Drive. Cheap, real, and not the point.)* |
| **`punches.csv` and `staff_master.csv` exist only on the VPS** | **YES, and this is the one worth doing.** Every punch ever taken, and the file that carries base salaries, live in exactly one place. A scheduled VPS → manojz → SSD copy removes a genuine single point of failure. **`staff_master.csv` must never go to GitHub or project knowledge (salaries) — the SSD is precisely the right home for it.** |
| **The medical PC's exports** | **YES, marginally.** Already mirrored to manojz and Drive; the disk adds a third cold copy for nearly nothing. |

### The constraint that shapes any design

**The disk is not always plugged in, and it does not mount in the session shell** — it is reachable
only by file transfer, which can write and read but cannot move or delete.

**Therefore every SSD job belongs to the agent on manojz, never to a session**, and must **tolerate
the disk being absent**: skip, log, report at the next close. **Never fail silently, never block the
thing it is backing up.** A backup job that blocks the pipeline is worse than no backup job — this
project already has F-179 and the 8h40m dark feed to prove it.

### Where this work goes: **THIS SESSION. Not a new project.**

Same estate, same agent, same backup story already half-built — **the offsite leg is proven working
and only the taking stopped.** A new project would split the very knowledge that makes this safe,
one session after the stores were deliberately consolidated. *(The split that was mooted is
Sanjeevni / Marg, which is a different axis entirely and still waiting on stability.)*

**Scope for S208, in order:** the VPS → manojz pull for the two attendance files first, because it
is the only true single point of failure on the list; then the SSD leg for both it and the Marg
backups; then, separately and with the vendor, **the restore test — which is the one thing no amount
of copying will do.**

## Standing constraints

Never touch the VPS · never swap a live file · never write into `ToMedical\` · never publish to
GitHub · never run `git` against `D:\dr-manoj-git` (F-233) · **no phone number in the repository
(F-185)** · never delete — move to `_to_delete\` · mask patient numbers · always IST · full-file
replacements only.

---
*START_HERE_SESSION_208 · regenerated at the S207 close.*
