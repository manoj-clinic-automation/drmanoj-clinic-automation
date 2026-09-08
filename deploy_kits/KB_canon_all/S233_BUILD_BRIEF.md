# S233 BUILD BRIEF — the one document to read before starting

*Written at the S232 close, 08-Sep-2026. It replaces reading this session's papers. Read this, then
Runbook **v164** §2, then start.*

---

## 1 · WHERE THE ESTATE STANDS

**S231 found out what the estate had not been watching: its own secrets. S232 found out what its
CHECKS cannot see.**

| | state |
|---|---|
| the four S230 resilience/freshness pins | ✅ **now in the pin list and READ BACK from the box** — they were in none, from S230 to S232 (F-369) |
| the publish gate | ✅ **refuses credentials as well as numbers** — 0 false alarms across the repository |
| the medical PC capture chain | ✅ **starts at boot** (F-362) — a reboot no longer loses trading data |
| the six stale `.env` copies on the VPS | ✅ **quarantined** (F-368), nothing deleted |
| Tailscale key expiry | ✅ **disabled on BOTH nodes** |
| the nightly unattended task | ✅ **standing work and an evergreen entry point** — eleven empty nights ended |
| the item spine | 🔴 **BUILT AT S229 AND NOTHING READS IT** |
| the WABA token | 🔴 **CONTAINED, NOT REVOKED** — the only genuinely blocked item |

## 2 · THE FIRST THING TO BUILD — the Google plane, into the chain that already works

> **⚠ THIS SECTION WAS REWRITTEN AFTER THE CLOSE.** Its first version said the projects and Sheets
> had *"no backup anywhere"*. **The owner challenged it and he was right.** The measured position is
> **`claude/S232_BACKUP_STATUS_CORRECTED.md`** — read it before starting.

**What already exists, and must not be rebuilt.** `clinic_state_backup.py` v2 has shipped
**AES-256-encrypted bundles to Google Drive nightly since S230** — 55 files, read-back verified, cron
01:50, September pinned forever — and **its restore has been drilled and passed**, the only leg in
this estate ever proven rather than assumed. Its key lives in three places: the VPS,
`F:\ClinicBackup\S230_STATE_BACKUP\`, and **Bitwarden** (D415).

**The seven live Sheets are the actual gap** — `Call_Durations`, `WA_Inbox`, `Call_Verdicts`, the
Accounting sheet, the UPI recon tabs, `Trip.csv`, the Payment Register. **Zero copies anywhere**,
confirmed by search at S232. **They are the data.** The code can be rewritten; these cannot. **Put
them inside that existing nightly bundle. Do not invent a second mechanism.**

**The code is largely covered already.** Six of the eight projects holding real code have a source
copy on disk — `dashboard\` (14 files, verified against live at S230), the three in
`deploy_kits\S230_GAS_EXPORT\`, and the Janitor and CC-saver files in `gmail-automation\gas\`. The
two without a copy are dead and under the no-touch rule. **So the real fault is that nothing
refreshes:** every copy is a one-off snapshot that goes stale the first time someone edits in the
browser, and nothing says so. **Build the weekly re-export that diffs against the copy on disk.**

**Ten projects are named; an eleventh is only inferred** from an orphaned trigger with no project
name. **Identify it before including it.** And **resolve the `VPS_Push_UPI.gs` duplicate** — a
200-line copy and the live 263-line one, both in the repo (D202/F-201).

**D426 (S232) is what makes this buildable without the owner:** Drive/Gmail/Notion reads and Drive
**write** are in scope for an unattended run, bounded to new files and new versions of documents this
project authored.

**`claude/S232_APPS_SCRIPT_TRIGGERS_READ.md` tells you which projects are actually armed**, so cover
the live ones first.

🛑 **READ, NEVER ACT.** The ICICI → VPS bank chain is load-bearing across three projects; the Clinic
Callback Tracker is **not to be touched at all**, nor its dead ancestor, which carries an unscoped
`removeTriggers()`.

## 3 · THEN, IN ORDER

**⭐2 · Sanjeevni steps 2+3, CLUBBED** — derivation off the screens, the four lanes pointed at the
spine. S229 says why they club: *"separately they each look like churn with nothing to show, and
together they are the moment the screens stop disagreeing."* Every derived number carries its
**coverage as data, not as a sentence**. **No screen changes behaviour.** Everything visible in the
product plan is downstream of this.

**⭐3 · Step 4 — sections as jobs**, screen by screen, **with the owner — he asked to be part of it.**
Six role maps (`S230_SURFACE_AND_ROLES` §6), not forty-two tiles. Three cheap fixes ride along: one
Stock Check tile sending three people to the same wrong door · **no list of counts and no "start a
new count"**, though a count is the unit of work in this whole system · six English money-tile names
a Hindi-first staff member cannot tell apart.

**⭐4 · The WABA rotation**, on MyOperator's reply. Then self-hosted ntfy (**D427**) and Bitwarden
(D421).

**⭐5 · Last:** the watchers and the three-month expiry window · the direct push (D402) · **the junk,
by evidence, after the shape is known.**

## 4 · WHAT IS BLOCKED, AND ON WHAT

🔴 **One thing: the WABA rotation, on ONE answer** from MyOperator (Ms. Khushi Jain) — **do the old
and new tokens overlap, and for how long?** Overlap means calm and staged; no overlap means a timed
change to four places with patient messaging down in between.

**Nothing else waits.** S232 established that four of the five items parked "behind the rotation"
never needed to be — *"not to be touched MID-rotation"* is not *"wait for the rotation"*, and the
owner is the one who asked the question that surfaced it.

**Held by him, not blocked:** the PWA install (until the restructure is done) and the Sanjeevni/Marg
project split (develop first, decide later).

## 5 · THE SIX RULES THIS SESSION COST MOST TO LEARN

1. **A hash gate proves the rows it HAS and says nothing about the rows it does not have.** Four live
   files sat outside every pin list for three sessions under a green gate. **When you verify a set,
   ask what is missing from it.**
2. **A design document becomes a lie the day it ships.** Re-issue it as-built at the close that ships
   it, or banner-retire it then.
3. **Two stores agreeing is not correctness** — both copies of the advance policy were byte-identical
   and both wrong. Only a person who knows the clinic catches that.
4. **Cadence, not recency, decides whether a silence means anything.** Two triggers, both quiet seven
   days; one dead, one a healthy monthly job.
5. **A selftest that cannot fail is not a test.** Make it fail once on purpose.
6. **To prove a source edit changes nothing, compare compiled CODE OBJECTS, not the diff.** 312 of
   them matched for `S232_F370_COMMENT`.

## 6 · THREE THINGS THAT WILL BITE IF FORGOTTEN

- **`/root/_quarantine_S232_F368_20260908_111131/` must not be deleted until after the rotation.**
- **`deploy_kits/S232_F370_COMMENT/staff_ledger.py` is the new BASE** for the next kit on that file.
- **`GIT_OPTIONAL_LOCKS=0` does not avoid F-233** — measured. Rename `.git\index.lock` aside.

---
*S233_BUILD_BRIEF · S232 close · next free **D428 · F-372**.*
