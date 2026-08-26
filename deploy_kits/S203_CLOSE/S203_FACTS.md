# S203 — THE MEASURED FACT SHEET (source for every close document)

**26 August 2026 · FULL build session.** Every value here was read from a machine or a file
during the session, not recalled. Build the close documents from THIS, never from memory
(D172/D188).

## 1. LIVE PINS THAT MOVED

| file | machine | was | now | kit |
|---|---|---|---|---|
| `marg_router.py` | manojz `D:\Downloads\margsync\MargPull\` | `bbc50f9172211925755eeaa25920d1cf` | `781e5ff66d4eca6b6ed4703bf692fb46` | S203_R1 |
| `PULL_FROM_MEDICAL.bat` | manojz, same | `92f03999d0a14d00b7f552dbb4d44c05` | `cfb8b13d028a3bdc69a70701056392ec` | S203_R2 |
| `PULL_HIDDEN.vbs` | manojz, same | `9a3ba9ba3bb7376bd166f12624d282c3` | `084fc4523b0e855c8d29b54c144bb60b` | S203_R2 |
| `pipeline_status.py` | manojz, same | `51cf10c9f2543fcd48a61ee7f8faf51a` | `0b3dd968f31cdb48a910539a087206c6` | S203_R3 |
| `medical_agent.py` | MEDICAL `D:\SendToClinic\` | `69e60d778ab61a8d50c79394e2951309` | `7b9a76f24abc5be369186507279cfaad` | S203.3 |
| `medical_census.py` | MEDICAL, same | `b53af03aaf16f011d3c15bb059637a5f` | `a7706d60965e45545e93a4eaa94fa892` | S203.6 |
| `finance_app.py` | VPS `/root/finance/` | `50ac4c86a3985bf82269d650d5e46f0f` | `374a0b82803068bb52e43ab9a921c1e9` then **`7948cee0e00494bbee30de1c51d03d74`** | B2 gate, then B2 test |

**Unchanged and verified:** `marg_watch.py` (medical) `aa55cdb51521c796a9167ee7d27a368f` ·
`xlsx_stdlib.py` `bbe11a8953f66c27126c48e773cfbe35` · `SEND_TO_CLINIC.bat`
`e19a8a777ac22fe75a242f1eb9762185` · `Startup\MargAgent.cmd`
`edcb2f2e2ef1258d4e0d3bae9ef38460` · manojz `signatures.json` `3e9cbba02ffb4e0f131738eee7a465f7`.

**FIRST MEDICAL-PC PINS EVER TAKEN** — 8 files, `deploy_kits/S203_CENSUS_BACKUP/S203_MEDICAL_PC_PINS.md`.
Drift on that machine had been undetectable by construction: the pin checker runs on the VPS
and cannot reach it, and manojz's mirror never purges.

## 2. TEST COUNTS — every projection written before measuring, every one landed

| suite | was | now | delta |
|---|---|---|---|
| `marg_router.py` selftest | 14 | **21** | +7 exactly |
| `pipeline_status.py` selftest | 15 | **21** | +6 exactly |
| VPS smoke | 719 | **721** | +2 (gate fix added none, correctly) |

**Red-proofs run, not assumed:** R1's seven new checks against the unfixed file → **5 go RED**
(the two that pass were already true). R3's six against the unpatched parser → **check 10
FAILS**. Reverse application on every file returned **exactly** to its live pin.

## 3. WHAT WENT LIVE

- **S203_R1** — `marg_router.py`: an unreadable `.xls` was refused *above* the archive-and-index
  block, so it was never copied to `_REFUSED`, never written to `index.csv`, and — because
  `seen` is rebuilt from `index.csv` each run — re-refused every ten minutes for ever, with the
  only message going to a discarded console. Fixed by lifting the tail into
  `_archive_and_index()` called by **both** paths.
- **S203_R2** — `PULL_FROM_MEDICAL.bat` + `PULL_HIDDEN.vbs`: `-- ok` was written
  unconditionally, and `pipeline_status.py:122` relays that word to the clinic server as
  liveness. The pull also kept **no log at all**. Now every step's exit code is checked, the
  word is earned, and `_logs\pull_YYYY-MM.log` + `_logs\pull_console_YYYY-MM.log` exist.
- **S203_R3** — `pipeline_status.py`: carries the backup's age to the clinic server. Reports
  the **stick's** age, never Marg's same-disk `serverbackup`, with a check asserting exactly
  that. Installed by Claude directly (owner has D:\Downloads connected).
- **The B2 gate (VPS)** — see §4.
- **`medical_agent.py` S203.3** — the offsite backup leg: copies every backup file from `E:\`
  and the newest `serverbackup` pair into Drive, bounded to 64 MB a pass, and carries the
  backup's age in every heartbeat with a warning past 3 days.
- **`medical_census.py` S203.6** — the on-machine audit tool: report census, drives, backup
  folders, Marg data size, unfiltered scheduled tasks, Marg config, an md5 for every live file,
  whether Marg is running, the Windows power history, and `D:\SendToClinic` as it really is.

## 4. THE CHAIN — three faults, each visible only because the one before it was fixed

1. **18:38** — R2 gave the pull a log. Until then nothing could be seen.
2. **18:44** — its FIRST log ended `pipeline_status: post failed (HTTP Error 401)`. That line
   had printed on every pull since S202 and been discarded every time.
3. **18:51** — traced to `_gate()`, a `before_request` that fails closed and exempts exactly
   three literal paths: the cron token (any path), `MARG_TOKEN` for `/finance/api/marg-push`,
   `RENEWALS_TOKEN` for `/finance/api/renewals-push`. **`/finance/api/pipeline-status` was
   added at S202 and never added to that list**, so every real post was refused **before**
   `api_pipeline_status()` ran. Its own token check was unreachable dead code.
   **B2 had never once reported.** Proven both ways: a POST from the VPS with the server's own
   `FINANCE_MARG_TOKEN` returned **401 `not_signed_in`** before and **HTTP 200
   `{"ok":true,"received_at":"2026-08-26T18:52:00"}`** after.
4. **19:17** — proven from the REAL caller, not a curl: three consecutive
   `pipeline_status: 200 (token from medical PC (live))` in the pull's own console log,
   including the **scheduled** runs at 19:10 and 19:17.

**Why it shipped broken:** the smoke suite DOES post with the `X-Finance-Marg` header — but on
`c`, a **signed-in** test client, so `_gate()` waved it through on the **session** and the token
clause was never exercised. The check above it, *"an unauthenticated pipeline post is REFUSED"*,
returned 401 from the **route's** check rather than the gate — **both checks passed for reasons
other than the ones they name.** The token substitution is also only half applied: the test sets
`os.environ["FINANCE_MARG_TOKEN"]` while `_gate()` reads the module-level `MARG_TOKEN` bound at
import.

## 5. THE BACKUP — the crown jewels, measured then fixed

**Measured on the machine:** `E:` present, 28.5 GB free of 28.9 · 177 files, 0.4 GB · newest
**22-Aug** · `E:\auto` and `E:\MARGBCKUP\auto` **EMPTY**, `E:\MARGBCKUP` last written
**09-Oct-2025** · **six non-Microsoft scheduled tasks, all Google and OneDrive** · 115 Marg
config files, **none mentions backup** · `margwin.exe` running (pid 7172) so `D:\MARGERP\Data`
(1,075 files, 0.9 GB) is open FoxPro tables · previous FY last backed up **17-Jul**.

**So the record was wrong.** F-191(c) said the automatic backup "was configured and has never
once run". **Nothing in Task Scheduler and nothing at startup runs a backup — it was never
scheduled.** The empty `auto` folders were never going to fill.

**Marg's own `serverbackup` is not a substitute:** day-of-week `.mst` files near-daily, but the
real ~2.3 MB `*_c18_d_*` pair only on 26, 25, 22-Aug then a **12-day gap** to 10-Aug — and it
sits on **D:, the same disk as the data**.

**Fixed:** the agent now copies the stick offsite automatically. **Proven at 19:37 —
`offsite: 182 file(s), 0.41 GB … offsite copy is COMPLETE`, newest backup 0.2 days old.**
The owner took a fresh backup and it was carried offsite within the hour, unattended.

**Still open:** no restore has ever been tested; the previous financial year is 40 days stale
with one copy.

## 6. DOCUMENTATION — 69 files to 3 (the owner's ruling)

Owner: *"we need the current state with all other relevant kb, and retire all other to marg,
medical history … so that future reference is to the best and pointed data and sources."*
Chosen shape: **three files** — `MARG_MEDICAL_CURRENT.md` (13 KB, the only thing read) ·
`MARG_MEDICAL_HISTORY.md` (248 KB, append-only, 58 index rows, 57 chronological entries) ·
`MARG_WALL_CARD.html` (one printed page beside the medical PC). Plus
`MARG_REPORT_EXPECTATIONS.md`. In `deploy_kits/MARG_MEDICAL/`.

**The three rules that stop it re-growing:** new knowledge EDITS current, the replaced text
moves to history — never a new file · a session's output is a change to CURRENT or an entry in
HISTORY, session records are not canon · anything written to work something out is a WORKING
PAPER, stamped at birth, folded at the close.

**Preserved first, retired second:** 52 Marg/medical documents copied into
`deploy_kits/S203_MARG_CANON/` and hash-verified; the folder now holds **67 files, `md5sum -c`
exit 0**. Only then were **18 removed from project knowledge**, each proven present in the
**pushed commit** `f94ff27a8b89f01363e62c9f800acd55ff4ff00d` first.

**Deliberately NOT retired:** `S179_Sanjeevni_Medical_Module_Build_Contract_v1` (its claimed
successor exists nowhere — bannered UNCERTAIN, treat as KEEP) · `S203_KB_CENSUS_PHASE12` and
`S203_PENDENCY_RECONCILIATION` (whole-KB, findings still live).

## 7. FINDINGS TO MINT — next free F-194

1. **The B2 gate** — `/finance/api/pipeline-status` never added to `_gate()`'s exemption; B2
   never reported from S202 until 26-Aug. **Third instance of AF-2's shape** (a monitor born
   dead). CLOSED.
2. **The smoke suite tested that route with a signed-in client**, so the token path was never
   exercised. **And the check added at S203 to fix this does NOT bite** — reverting the gate
   still gave 721/721. Recorded as green-and-meaningless rather than left looking like
   coverage. **OPEN.**
3. **`-- ok` written unconditionally** and relayed to the clinic server as liveness. CLOSED.
4. **The pull kept no log** — `PULL_HIDDEN.vbs` discarded stdout every ten minutes. CLOSED.
5. **`marg_router.py`: an unreadable file vanished** — no `_REFUSED` copy, no index row,
   re-refused for ever. CLOSED.
6. **manojz's mirror is `robocopy /E` with no `/PURGE`** — it never deletes, so it still showed
   340 files, an AutoHotkey install and three tools the machine's own listing proves are gone.
   **Reasoning about the medical PC from the mirror is unsafe.** CLOSED by measurement.
7. **PROJECT KNOWLEDGE WAS THE STALE STORE, NOT THE REPO.** Two documents exist in both and are
   not byte-identical; in both cases the **repo** copy is better, carrying superseding
   annotations written at the S197 fold that never travelled back. The four lines missing from
   the project copy of the encryption note are exactly the warning that would have prevented
   the S203 master reference asserting a superseded finding as current. **RULE: neither store
   is authoritative by position — compare by md5, never by where a file sits.** OPEN (an
   inverse check across stores is owed).
8. **F-191(c) was wrong**: the automatic backup was never scheduled, not "configured and never
   ran". CLOSED by measurement.
9. **The token lives in five stores, not three** — the VPS unit, the medical PC, the manojz
   cache, `D:\Downloads\MARG_TOKEN_S187.txt`, and a loose file under
   `margsync\_to_delete\S201_20260825\loose\`. OPEN (rotation parked by the owner).
10. **The operational runbook copy on manojz was the S201 version** (`f02cd8bd…`), missing the
    guest-access fault that caused the outage. Corrected to `c2b5251f…`. CLOSED.

**Assistant's own faults, recorded not softened:** a verdict built on a shadowed variable that
announced "the backup target is NOT ATTACHED" while the same report said "E: is present" · a
`NameError` shipped twice because an insertion anchor matched in two places and `py_compile`
cannot catch it (**pyflakes can, and is now used**) · `trap … EXIT` pasted into an interactive
shell, so a reverted file sat on disk while it was believed restored · a test that counts +2
and proves nothing · and thirteen documents produced while consolidating away sixty-nine.

## 8. DECISION TO MINT — next free D351

**D351 — the Marg/medical documentation model.** D247's Register+Archive pattern applied to the
one subsystem that never received it: one CURRENT, one append-only HISTORY, one printed card,
plus the three rules in §6. Owner-chosen from three options.

## 9. OWNER RULINGS THIS SESSION

- **12 June, +8,487 — CLOSED, do not pursue.** A sale report for that day now returns **zero
  sales**, and the only mechanism that would "fix" it re-applies the 12-June report, which
  **deletes that day's attributed and resolved review rows on a closed month**. Same ground on
  which it was accepted-but-not-applied at S202. Do not reopen without evidence from outside Marg.
- **Token rotation: PARKED** for now.
- **Documentation: three files** (current + history + wall card).
- **D350 scope** unchanged from S202.

## 10. OWNER PREFERENCE CHANGE

*"copy block please, and make it default everywhere"* — a copy block is now the default
delivery for **every** machine, not only the VPS, superseding the deliver-a-.bat-to-double-click
habit. And where Claude has write access, it installs directly rather than handing over work.

## 11. STATE AT CLOSE

Repo pushed at `f94ff27a…` (before tonight's later kits). `deploy_kits/`: `MARG_MEDICAL` (5
files) · `S203_MARG_CANON` (67) · `S203_CENSUS_BACKUP` · `S203_LIVE_TOOLS` (15 — five tools
that existed nowhere but the two PCs) · `S203_R1` · `S203_R2` · `S203_R3` · `S203_H1` ·
`S203_B2GATE`. Every folder carries a verified `SUMS.md5`.

**Not yet done:** the manifest rows for the new folders, the Register bump, `PUBLISH_ALL`,
and the on-box pin-list copy.
