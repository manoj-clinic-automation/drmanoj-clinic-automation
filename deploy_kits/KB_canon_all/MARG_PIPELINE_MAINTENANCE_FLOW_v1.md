# MARG PIPELINE — MAINTENANCE & FAULT FLOW

**v1 · 25-Aug-2026 (S201). The operational half: how to tell it is healthy, what to do when it is
not, and what to run routinely.** Written to be usable without reading any other document.

References: `MARG_PIPELINE_REFERENCE_v1.md` (how it works) ·
`MARG_INGESTION_REFERENCE_v1.md` (what happens on the server).

---

## 1 · THE 60-SECOND CHECK — is it healthy right now?

Three files answer it. **All three are on manojz. None needs a login.**

| # | open this | healthy looks like |
|---|---|---|
| 1 | `D:\Downloads\margsync\MargPull\_last_pull.txt` | a `START` and an `END … ok` **within the last 15 minutes** |
| 2 | `H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt` | written **within the last 10 minutes** · `WATCHER : ALIVE` · `IGNORED : 0` |
| 3 | `D:\Downloads\margsync\MARG_PICTURE.txt` | `days with NO export : 0` and `exports NOT on server : 0` |

**If all three are good, the pipeline is working.** Everything else is detail.

---

## 2 · THE FAULT FLOW — start at your symptom

### ▸ "A day's report is not on the approvals page"

```
1. MARG_PICTURE.txt  -- does that day have a report at all?
      NO  -> it was never exported. Run it in Marg for that exact date.
              (BILL WISE SALES, With Item Deta. = Yes, single date.)
      YES -> continue
2. Does the picture say "NOT SENT"?
      YES -> double-click  MargPull\SEND_OUTBOX.bat
      NO  -> it reached the server; continue
3. Is the DAY FILED?  /finance/approvals -> the day shows "NOT FILED"
      YES (not filed) -> file the day, then re-load that day's export.
                         This is the commonest cause and is not a fault.
      NO  -> it is on the server and applied. Check the Day Page figures.
```

### ▸ "Nothing has arrived all day"

```
1. _last_pull.txt -- is the 10-minute task running?
      no recent START      -> the scheduled task is not running.
                              Run MargPull\PULL_FROM_MEDICAL.bat by hand.
      "FAILED: medical PC unreachable" -> medical is off, or Tailscale is down.
      "FAILED: no python"  -> tell Claude.
2. heartbeat.txt -- is the medical PC capturing?
      older than ~10 min   -> the AGENT is not running on medical.
                              Re-run ToMedical\INSTALL_AGENT.bat there.
      WATCHER : DOWN       -> the agent will restart it within a minute.
                              If it says DOWN twice running, tell Claude.
      IGNORED : 1 or more  -> a file the watcher cannot take is sitting in a
                              watched folder. The heartbeat names it.
3. Still nothing -> MargPull\MEDICAL_RECENT.bat
      lists EVERY file written on the medical PC in the last 3 days, any type.
      If Marg wrote nothing, nothing was exported. That is the answer.
```

### ▸ "SEND_OUTBOX says REFUSED"

```
HTTP 401  -> the token changed. The sender reads it live from the medical PC,
             so this means the SERVER's token changed. Tell Claude; do not
             hand-copy tokens between machines.
HTTP 0    -> this PC could not reach the internet. Retry later; it retries by
             itself every 10 minutes anyway.
HTTP 5xx  -> the clinic server is unwell. Check followup.dr-manoj.in loads.
anything else -> MargArchive\_NEEDS_ATTENTION.txt has the server's own words.
```

### ▸ "A report was refused by the router"

```
MargArchive\_REFUSED\  -- every refused file has a .txt beside it giving the
                          reason, the title read, and the columns found.

"TRUNCATED - the completeness marker ... is missing"
      -> the export stopped early. Run it again in Marg.
"title matches X but the column layout does not"
      -> a report variant we have not taught the router. Send Claude the .txt.
"no signature matches this title"
      -> a report type the router has never seen. Send Claude the file.
```

**A refused file is never lost.** It is archived with its reason and can be
re-judged later — see §3.

### ▸ "The health page says This month vs Marg"

Not an accounting error. That figure is **the value of sale bills where the
salesman did not enter a clinic ID at the till**, waiting to be matched to a
patient, pending the Docterz migration. Explained in full in
`S201_Month_vs_Marg_Explained.md`. **No action.**

### ▸ "A console window keeps popping up"

Fixed by `MargPull\FIX_POPUP.bat` (S201). If it returns, the scheduled task has
been repointed at the batch again instead of `PULL_HIDDEN.vbs`.

---

## 3 · ROUTINE MAINTENANCE — what to run, and when

| when | do this | why |
|---|---|---|
| **never** | the pull, the send, the rescue, the picture | all automatic, every 10 minutes |
| **when a day looks wrong** | `MARG_STATUS.bat` | the picture, on demand |
| **after teaching the router a new report type** | nothing | the pull re-judges quarantine by itself when `signatures.json` changes |
| **monthly** | `MEDICAL_INVENTORY.bat` | proves every export on the medical PC was captured |
| **if a machine was rebuilt / moved** | `MEDICAL_RECENT.bat` | shows what Marg is actually writing, anywhere on D: |
| **quarterly** | review `margsync\_to_delete\` and empty it | nothing is auto-deleted, by design |

**Teaching the router a new report type** — the whole procedure:

```
1. python marg_router.py --learn "<a real sample.xls>"      (prints a block)
2. paste the block into MargPull\signatures.json
3. wait 10 minutes
```
Step 3 is not a figure of speech: the pull notices `signatures.json` changed and
**re-judges everything in quarantine**, rescuing whatever that signature should
have caught. Never hand-copy a file into a type folder — that is how the index
came to disagree with the disk (S201 Part 0).

---

## 4 · WHAT EVERY FOLDER IS

**manojz — `D:\Downloads\margsync\`**

| folder | what it is | safe to empty? |
|---|---|---|
| `MargArchive\<TYPE>\<YYYY-MM>\` | **the archive.** Every verified report, named by the business date inside it | **no** |
| `MargArchive\_spool` | landing zone, **and the capture dedupe memory** | **no** — emptying re-imports everything |
| `MargArchive\_outbox` | queue for the clinic server | no |
| `MargArchive\_REFUSED` / `_UNKNOWN` | quarantine, each file with its reason | no — they can still be rescued |
| `MargArchive\_rescued` | quarantine copies whose rescue is proven | yes, eventually |
| `MargPull\` | **the live tooling.** Do not edit by hand | no |
| `medical_SendToClinic\` · `marg_reports_mirror\` | read-only mirrors of the medical PC | they refill by themselves |
| `_UPLOAD_NOW\` | reports still needing a manual upload. **Empty = nothing to do** | it manages itself |
| `_to_delete\` | parked by Claude, nothing deleted | **yes, when you have looked** |

**medical PC — `D:\SendToClinic\`**: `_captured` (the watcher's spool),
`heartbeat.txt`, `agent.log`, `pyportable\`, and the agent + watcher scripts.

**Google Drive — `Clinic Data Archive\`**: `MargArchive` (offsite copy),
`ToMedical` (Claude → medical), `FromMedical` (medical → Claude).

---

## 5 · WHAT TO SEND CLAUDE

Best to worst. **The first is usually enough on its own:**

1. `FromMedical\heartbeat.txt` — and say what you were doing.
2. The console output of whatever you ran, in full — including the lines before the error.
3. `MargArchive\_NEEDS_ATTENTION.txt` if a send failed.
4. The `.txt` sidecar from `_REFUSED\` if a report was refused.

**Do not** paste a token, or a file containing one. Claude reads the live token
off the medical PC itself and never needs to see it.

---

## 6 · THE THINGS THAT WILL BITE, AND WHY

- **A day that isn't filed holds its own Marg data out of the books.** By
  design (F-113). File the day, re-load the export.
- **Emptying `_spool` re-imports everything.** It is the dedupe memory.
- **Never hand-copy a report into a type folder.** Use `--learn` + wait.
- **Never hand-copy a token between machines.** The manojz copy is a cache the
  sender refreshes from the medical PC; a hand-copy went stale and answered
  401 for five days.
- **The medical PC's watcher starts at LOGON.** A machine left at the login
  screen after a reboot captures nothing — the heartbeat is what tells you.

---
*MARG_PIPELINE_MAINTENANCE_FLOW v1 · S201.*
