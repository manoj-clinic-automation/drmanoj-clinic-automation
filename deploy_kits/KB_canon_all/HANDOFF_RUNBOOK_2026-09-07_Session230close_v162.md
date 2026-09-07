# HANDOFF RUNBOOK — v162 · written at the S230 close, 07-Sep-2026, 23:30 IST

*Supersedes v161. Tier 0. §2 is the live backlog and is the only part that must be read before work.*

---

# §0 · WHAT HAPPENED AT S230

One long day across three machines. The spine was finished at S229; with the core done the owner
asked for **a map of the whole estate** — what exists, where it sits, whether it is still alive, what
is redundant, what backs up what, what connects to what, which staff hold which part — for a stated
purpose: *"to integrate the system properly on a strong foundation … so that the maintenance and
further development is easy and does not require data plumbing and reconfirmations from my side all
the time."*

**Eleven assessment documents** were written (System Atlas · Backup and Resilience · Redundancy
Register · Surface and Roles · Order of Work · Apps Script Census · Renewals and Vendor Register ·
Local Apps and Data · the two Medical PC documents · the Roadmap), **four kits built**, and **five
Phase 1 items closed**.

**The diagnosis, and it explains most of a year's trouble:**

- **Fault A — nothing has a retirement step.** Cron lines for jobs that have never produced a file.
  A Marg backup folder empty since October 2025 whose scheduler still looks configured. A renewals
  register that permanently drops anything 45 days overdue. A push-watcher log that stopped on
  01-Jul-2026 while its files kept arriving by a route nobody recorded.
- **Fault B — nothing reports its own age.** The cause of A.
- **Fault C — asserting from one source. This one is the assistant's.**

**Five Phase 1 items closed:** 1.1 Tailscale key expiry disabled on `medical` · 1.5 the restore
drill PASSED — *the first time this estate has proven a backup restorable rather than assumed it* ·
1.4 the previous financial year's Marg backup was already safe (a claimed "largest exposure" that was
covered before it was raised) · 1.3 the off-box shipper live, 55 files, AES-256, monthly pinned
forever · **1.2 the freshness layer live — 26 legs, 26 OK, cron 08:05.**

**PHASE 1'S EXIT TEST IS PASSED:** every backup and pipeline leg can state its own age on one
screen, and the oldest is within its window.

**The finding this close is remembered for is F-355.** The shipper discovered files by extension and
left `/root/staff_ledger/ledger.jsonl` — the only record of what each member of staff owes — out of
the bundle, with **86 self-tests green**. The tests were written from the same assumption as the
code. Only the live machine could see it. Fixed to 55 files with `secrets_skipped` unchanged.

**The owner corrected the assistant four times and was right four times**, every correction
checkable in data already on his own disk.

---

# §1 · MENTAL MODELS — carry these

1. **A backup that cannot state its own age has not been taken.** Now enforced by the freshness page.
2. **A green self-test proves the kit against your idea of the world. Only the live machine can tell
   you the idea is wrong.** Three sessions in a row have paid for this lesson (S208, S209, S230).
3. **A watcher is never armed on its first install** (D418). One unarmed read first — it is the step
   most likely to find an error, and it found one at S230 within a minute.
4. **Configuration, not code** (D417). If adding or retiring a thing requires a code change, it will
   never be retired. `freshness_legs.json` is the pattern to copy.
5. **Watch the data, not the log.** A log can be touched by a job that then fails.
6. **A leg is a thing that should tick.** Not every important file is a leg — the staff ledger is
   protected by the shipper, not watched by the page, because silence there is normal.
7. **Read the live shape, not the newest thing in the repository that resembles it.** A base kit plus
   eleven patch kits is not the base kit.
8. **A close report saying DONE is not evidence.** At this close the S229 record claimed the
   how-to-use pointers had been moved; they had not, and had been stale for three closes.

---

# §2 · THE LIVE BACKLOG

## ⭐ NEXT — Phase 1 remainder

**1.6 · Credential consolidation.** The Marg token exists in **five** places where three were
recorded; the GCP service-account key has spare copies; `Dr_Manoj_Master_Credentials.xlsx` sits in
`D:\Clinic backups`; four MyOperator literals belong in Script Properties; and **F-358 — the private
ntfy topic URL is hard-coded as a default in `clinic_watchdog.py`, in two copies in the repository.**
A change-things step: prepare fully offline, one decision at a time.

**1.7 · The renewals register made self-advancing (F-360).** Roll `dateISO` by `cycleMonths`, or
record `lastDoneISO` and compute from it, so nothing can fall out of the list permanently. **Then add
the eight missing technical vendors — Tailscale first**, because its key expiry stops the entire Marg
lane. Changes a live personal-account script: built and shown, installed only on his word.

**1.9 · The medical PC capture chain (F-362).** `MargAgent.cmd` sits in the owner's Startup folder,
so the watcher, heartbeat and hourly backup run only inside his RDP session; a reboot on 29-Aug cost
21½ hours of uncaptured trading. Fix prepared, not applied: a boot-time scheduled task running as
SYSTEM — with the caveat that SYSTEM changes which account writes to the Drive folder, so the offsite
copy may need a real path on `C:`.

## OWNER ACTIONS — small, none urgent

1. Confirm **`dr-manoj.in` renewed on 29-Aug** and give the new expiry, so the entry can be corrected
   before it drops out of the register permanently around 13-Oct.
2. Say whether the **`drmanojagarwal.in` transfer** happened — that entry disappears around 26-Sep.
3. The **personal item dated 27-Sep** is the only near-term one in the whole register.

## PARKED BY THE OWNER — do not restart without his word

- **All Apps Script work** until Phases 1 and 2 complete (D414). **Two standing holds inside that:
  the ICICI bank ingest is LIVE and load-bearing — only the email digest was retired, and they share
  one project; and the callback tracker is not to be touched at all.**
- **Bitwarden** beyond the one key already stored (D415).

## STILL OPEN FROM S229

The item-level purchase rows reached the VPS with HTTP 200, which proves the POST was accepted and
**not** that they landed in a table the stock screens read. Both types are marked
`"uploadable": false`. **Count April/May/June item-level purchase rows on the box and compare against
the three archived exports.**

---

# §3 · INSTALL DISCIPLINE

- Build and test offline · `py_compile` in the container, never in the mounted repo · then the owner
  installs from **one line per command**, `\cp` not `cp`.
- **Verify a kit gate from INSIDE its own folder.**
- **Run `git --no-optional-locks check-ignore` over every file of a kit before proposing the publish
  (F-359).** The blanket `*.json` rule silently swallows any kit that ships settings, and
  `PUBLISH_ALL.bat` then refuses the whole publish naming nothing. It has cost two cycles.
- **Never run plain `git` against the mounted repo (F-233)** — it leaves an `.git/index.lock` the
  shell cannot delete and breaks the owner's next publish.
- The publish is **his double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.

---

# §4 · THE BOUNDARY

Nothing live is rebuilt without his explicit OK, and the manual path stays as fallback. He is not an
engineer and does not want technical choices put to him: make the call, state it in one line, and
proceed. Ask him only for what nobody else can do — a GUI step, a credential, a decision. Chat short;
the long form belongs in project documents.

**And the rule earned at S229 that outranks any script:** *when the owner tells you something about
his own shop, check it against the data before restating what a tool says.*

---
*Runbook v162 · S230 close · supersedes v161.*
