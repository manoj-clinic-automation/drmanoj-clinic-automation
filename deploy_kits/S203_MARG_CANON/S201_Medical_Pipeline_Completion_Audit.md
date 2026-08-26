> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by measurement.** Successors:
> **`S203_MEDICAL_PC_PINS.md`** at `deploy_kits/S203_CENSUS_BACKUP/`
> (md5 `976a6f0ccc22318a603d055f81541f71`) — the first pins ever read off the medical PC itself —
> and **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §3.1 / §3.2**
> (md5 `579ea885e440e76af73de3ecc4542d71`).
> Its §2 pins were read from **manojz's never-purging mirror, not the machine**, and master §3.1 lists
> six things that mirror wrongly implies. Its §4 "found 25-Aug" claim is **the error corrected at
> master §9 #8**: the C: output tree was recorded in `S180_Marg_Sample_Findings.md` on **15-Aug**, ten
> days earlier. Acting on this audit re-circulates that error.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201 — MEDICAL PIPELINE: completion audit

**25-Aug-2026 19:12 IST. The medical PC → manojz → Drive → clinic-server pipeline, audited end to
end after the S201 work. Every figure below was read from the running systems.**

---

## 1 · THE THREE HEALTH SURFACES — all green

```
pull heartbeat : END 25-08-2026 19:10:19.14 -- ok
medical beat   : MEDICAL PC HEARTBEAT   2026-08-25T19:06:18
picture        : days with NO export : 0    exports NOT on server : 0
```

## 2 · LIVE PINS (manojz, `D:\Downloads\margsync\MargPull\`)

| file | md5 |
|---|---|
| `marg_router.py` | `bbc50f9172211925755eeaa25920d1cf` |
| `marg_watch.py` | `2076fe1d8d145524be16ae857b3d838d` |
| `marg_gate.py` | `f09cfe61d052d5dc8dd402d2e3a85422` |
| `marg_rescan.py` | `ae92e3316efa07360c884c7c67379957` |
| `medical_inventory.py` | `3ee927f023f68dd4a0c5c8b28b0037b4` |
| `xlsx_stdlib.py` | `bbe11a8953f66c27126c48e773cfbe35` |
| `signatures.json` | `3e9cbba02ffb4e0f131738eee7a465f7` |
| `PULL_FROM_MEDICAL.bat` | `d64b636b5bf2418e037e9a78893e0466` |
| `PULL_HIDDEN.vbs` | `9a3ba9ba3bb7376bd166f12624d282c3` |

**Medical PC:** agent `S201.7` live (S201.8 in Drive, installs on the next run);
watcher `aa55cdb5` watching **three** roots.

Selftests: router **OK** · watcher **OK** · gate **49/49** · rescan **12/12**.

## 3 · THE ARCHIVE

| type | files |
|---|---|
| SALE_BILLWISE | 10 |
| STOCK_CLOSING | 8 |
| STOCK_EXPIRY | 6 |
| DOCUMENT_PDF | **7** |
| PURCHASE_BILLWISE / PURCHASE_SUPPLIERWISE | 1 / 1 |
| _rescued | 11 |
| _REFUSED / _UNKNOWN | 7 / 1 — none of them Marg exports |

`index.csv`: **41 rows, 15 columns, 0 malformed** · 33 VERIFIED · 7 REFUSED · 1 UNKNOWN.
Delivery state: 3 accepted · 6 duplicate · 1 superseded · **no undelivered reports**.
`_UPLOAD_NOW` is **empty** — nothing needs a manual upload.

---

## 4 · THE FINDING THAT MATTERED MOST

**Marg has TWO output trees, and only one was ever known.**

```
D:\MARGERP\users\<id>\report\REPORT_n.XLS      <- known since S180
C:\Users\Public\MARG\<id>\all\REPORT.PDF       <- found 25-Aug, S201
```

Every document in this KB — including the two references rewritten earlier the same day —
described only the first. The second matters more than it looks:

- **It is on C:.** The Tailscale share is `\\100.119.151.40\DDrive` — **D: only**. manojz cannot see
  C: at all, and never could.
- So the census, the recent-files sweep and the ignored-file counter — every tool built to answer
  *"what did Marg actually write?"* — all scan the D: share, and **all three would have answered
  "nothing" with complete confidence.**
- `REPORT.PDF` is a **fixed slot**, overwritten on every export — the same race as `REPORT_1.XLS`,
  and the same reason capture must be local rather than on a 10-minute pull.

Found by exporting one real PDF and watching where it did *not* appear: `CAPTURES: 4`,
`IGNORED: 0`. Not ignored — invisible. **A synthetic test file would not have found this**, because
it would have been placed where we already believed reports lived.

**Proven end to end at 18:50:**
`C:\Users\Public\MARG\17476\all\REPORT.PDF` → watcher 18:46:18 → pull 18:50 →
`DOCUMENT_PDF · 2026-08-25 · 7617f1b4 · VERIFIED` → Drive offsite.

## 5 · THE RUNAWAY I CAUSED, AND CLOSED

Agent S201.3 retried a kit install **every 30 seconds** and wrote a **backup before** knowing the
write would succeed. **343 attempts between 15:28 and 18:20 — 4.1 MB of identical backups** on the
medical PC, mirrored to manojz, still growing when the audit found it.

Three faults, all mine, all fixed in S201.5/.6:
1. backup taken before writability was proven → now: clear read-only, prove writable, *then* back up;
2. backup named by timestamp → now named by **source md5**, so retries cannot multiply it;
3. retried forever → now **3 tries**, then left alone until the source bytes change, with the refusal
   carried in the heartbeat rather than only in a log nobody reads.

S201.6 also fixed the prune that silently removed nothing (it hit the same read-only flag and only
logged on success) and made the agent's extension list track the watcher's.
S201.8 replaced the ignored-file **denylist with an allowlist** after watching Marg's C: tree put 18
database files (`.dbf .cdx .idx .fpt .xff .C18`) on the health surface. No denylist stays ahead of a
database directory.

## 6 · THE POPUP

The scheduled task launched the batch directly, so a console sat on screen for ~15 seconds every ten
minutes. The GUI route wanted a password (the task stores credentials).

Solved without the owner touching anything: the batch now hands off to `PULL_HIDDEN.vbs` and exits,
and attempts **once** to repoint the task at that launcher — with `< nul` so a credential prompt
fails instantly instead of hanging a hidden process forever on input nobody can see.

```
19:00:01  SUCCESS: The parameters of scheduled task ... have been changed.
19:10:02  START ... 19:10:19 END -- ok     <- verified under the new action
```

*Recorded honestly: `< nul` fed an empty password and schtasks warned the task might stop running.
It did not — that task runs only when the owner is logged on, so there was no stored credential to
lose. The warning was real and the risk was taken knowingly; the 19:10 cycle was the proof.*

## 7 · CLEANUP — three places, nothing deleted

| where | what |
|---|---|
| **manojz** | 7.6 MB → `D:\Downloads\margsync\_to_delete\` — superseded scripts, old kit tarballs, a screen recording, a 0-byte file named `finance marg token.txt`, a 20-Aug snapshot of the Marg users folders, and the stale `SendToClinic` copy carrying the AF-1 sender. **`token.txt` was kept** — it is the live cache. All four selftests re-run green afterwards. |
| **medical** | `CLEANUP_MEDICAL.bat` delivered — the 343 loop backups, the guard chain (which cannot run: no spreadsheet reader on that Python), the parked AutoHotkey macro, the superseded watcher setup. Bin at `D:\_to_delete_S201\`, **outside every watched folder** so the watcher cannot re-capture what was just tidied away. |
| **Drive** | `CLEANUP_DRIVE.bat` delivered — the first watcher-install attempt, the dead `ADD_MARG_REPORTS_to_watcher` snippet, the S195 delivery test, the S201 probe. Amir's NEFT advices and the vendor reconciliation left alone: real deliveries, not clutter. The folder's `READ ME` was **rewritten** — it described a relay disabled at S195. |

## 8 · WHAT IS STILL TRUE AND UNFIXED

- **AF-1 is still armed on the medical sender.** `SEND_TO_CLINIC.bat` decides success from a
  response file curl does not overwrite on failure, then blacklists the hash. Kept deliberately as
  the only medical-side fallback if manojz is down; `marg_gate.py` is the safe path.
- **The medical guard cannot run at all** — no `xlrd`, no `openpyxl` on that Python. `xlsx_stdlib.py`
  would fix it and is not yet on that machine.
- **No PC-side live pins.** `verify_live_pins.py` runs on the VPS and cannot reach either PC.
- **`MEDICAL_RECENT.bat` scans D: only** — it cannot see Marg's C: tree, which is exactly where the
  blind spot was. It needs a local variant that runs on the medical PC.

---
*S201 completion audit · read from the running systems. No patient identifiers reproduced; no tokens
read or printed.*
