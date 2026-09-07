# S231 BUILD BRIEF — the one document to read before starting

*Written at the S230 close, 07-Sep-2026, 23:30 IST. It replaces reading the eleven S230 assessment
papers. Read this, then Runbook v162 §2, then start.*

---

## 1 · WHERE THE ESTATE NOW STANDS

S230 mapped the whole system and then fixed the thing the map exposed. Before S230 **this estate had
no way to notice that something had stopped.** It now has three:

| runs | what it does | proof it is alive |
|---|---|---|
| **01:50 nightly** | off-box state backup — 55 files, AES-256 before it leaves the box, September's monthly revision pinned forever | a fresh line in its state file, and it appears as a leg on the page below |
| **08:05 daily** | **the freshness layer** — 26 legs, one page, one shout per leg per day | `/root/finance/freshness.html` · `/root/finance/freshness.summary.log` |
| **twice yearly** | the restore drill — downloads, decrypts, opens and counts the backup | its own state file, also a leg |

**Phase 1's exit test is passed:** every backup and pipeline leg can state its own age on one screen,
and the oldest is within its window.

## 2 · THE FIRST FIVE MINUTES OF S231

**Read four pins back from the box** — the S230 close recorded them as PREDICTIONS from published kit
bytes, DECLARED-PENDING:

```
md5sum /root/state_backup/clinic_state_backup.py /root/finance/verify_restore.py /root/finance/freshness.py /root/finance/freshness_legs.json
```

Expect `425e77f5…` · `f67ee579…` · `6476d1d2…` · `ad223bc6…`

**Then confirm the freshness layer actually ran unattended at 08:05:**

```
tail -3 /root/finance/freshness.summary.log
```

A `legs=26` line dated today, everything inside its window. **A missing 08:05 line is the finding**,
and it is more important than whatever else was planned.

## 3 · WHAT TO BUILD — Phase 1's remainder, in order

**1.6 · Credential consolidation.** *The change-things step; prepare offline, one decision at a time.*
The Marg token exists in **five** places where three were recorded. The GCP service-account key has
spare copies. `Dr_Manoj_Master_Credentials.xlsx` sits in `D:\Clinic backups`. Four MyOperator
literals belong in Script Properties. And **F-358: the private ntfy topic URL is hard-coded as a
default in `clinic_watchdog.py`, in two copies in the repository** — rotating it means changing every
publisher at once, so it is a planned change, not a quick fix.

**1.7 · The renewals register made self-advancing (F-360).** Today `nagRenewals` drops anything more
than 45 days overdue **permanently**, and nothing ever rolls `dateISO` forward by `cycleMonths` —
which is recorded on every entry and used by nothing. Roll it forward, or record `lastDoneISO`.
**Then add the eight missing technical vendors, Tailscale first**, because its key expiry stops the
entire Marg lane and it is in no register today. Changes a live personal-account script: build it,
show it, install only on his word.

**1.9 · The medical PC capture chain (F-362).** `MargAgent.cmd` sits in the owner's Startup folder,
so the watcher, the heartbeat and the hourly backup sweep run **only inside his RDP session**. A
reboot on 29-Aug cost 21½ hours of uncaptured trading, and the only signal was an absence. Fix
prepared, not applied: a boot-time scheduled task as SYSTEM — **caveat: SYSTEM changes which account
writes to the Drive folder, so the offsite copy may need a real path on `C:` instead.**

## 4 · WHAT NOT TO TOUCH

**⛔ The ICICI bank ingest is LIVE and load-bearing.** The owner retired the **email digest**; the
bank leg lives in the same Apps Script project and was never retired. An earlier "retired in purpose"
label was withdrawn and all trigger-disarming suspended. **⛔ The callback tracker is not to be
touched at all.** All other Apps Script work is parked until Phases 1 and 2 complete (D414).
**Bitwarden is parked** beyond the one key already stored (D415).

## 5 · THE FIVE RULES THIS SESSION COST MOST TO LEARN

1. **A green self-test proves the kit against your idea of the world. Only the live machine can tell
   you the idea is wrong.** 86 green checks could not see that the only record of what each person
   owes was outside the backup (F-355). A listing on the box saw it at once.
2. **A watcher is never armed on its first install (D418).** One unarmed read first. At S230 it found
   a declared leg pointing at a log file that has never existed (F-356).
3. **Configuration, not code (D417).** If retiring a thing needs a code change, it never gets retired
   — which is the whole of Fault A. `freshness_legs.json` is the pattern.
4. **Watch the data, not the log.** A log can be touched by a job that then fails.
5. **A close report saying DONE is not evidence.** At this close the S229 record claimed the
   how-to-use pointers had been corrected; they had not, and had been stale for three closes.

## 6 · STILL OPEN FROM S229

Item-level purchase rows reached the VPS with **HTTP 200**, which proves the POST was accepted and
**not** that they landed anywhere the stock screens read — both types are marked
`"uploadable": false`. Count April/May/June item-level purchase rows on the box against the three
archived exports.

## 7 · THE OWNER'S THREE SMALL ANSWERS, WHEN CONVENIENT

1. Did **`dr-manoj.in`** renew on 29-Aug, and what is the new expiry? *(It drops out of the register
   permanently around 13-Oct if not corrected — and every screen in this estate runs on it.)*
2. Did the **`drmanojagarwal.in`** transfer happen? *(Drops out around 26-Sep.)*
3. The **personal item dated 27-Sep** — the only near-term entry in the whole register.

---
*S231_BUILD_BRIEF · S230 close · next free **D419 · F-363**.*
