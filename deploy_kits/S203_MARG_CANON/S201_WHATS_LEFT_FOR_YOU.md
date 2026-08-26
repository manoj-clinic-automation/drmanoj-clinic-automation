> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by `OWNER_TODO_LIVE.md`** (md5 `0f0645f1a78415d571c8fe867b8b0432`),
> which is the living list and the only one with a numbered step (A10) keeping it current, and by
> **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §11 — OPEN ITEMS** (md5 `579ea885e440e76af73de3ecc4542d71`).
> This is a point-in-time owner list from 25-Aug and it is a day stale by construction. **Two task
> lists is how an item gets done twice or never.**
> *(Note: `S203_MARG_RETIREMENT_LIST.md` §1 row 10 cites "master §6" for this — that was the v1/v2
> numbering. In v3 the open-items table is §11; §6 is "How to know it is working".)*
> Its one unique item — the 18 Marg database files on the health surface — stays here.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201 — WHAT IS LEFT FOR YOU

**25-Aug-2026 19:20. Three things. Full paths. Nothing is broken; nothing is urgent.**

---

## 1 · ONE INSTALL — do this one

**Machine: the MEDICAL PC.** Double-click:

```
F:\My Drive\Clinic Data Archive\ToMedical\INSTALL_AGENT.bat
```

**What it does:** installs agent **S201.9** and, by itself, three files into
`D:\SendToClinic\` — `marg_watch.py`, `xlsx_stdlib.py`, `medical_census.py`.

**Why:** two reasons, folded into one install so you only do this once.

- Marg's C: tree put **18 of its own database files** (`.dbf .cdx .idx .fpt .xff .C18`) on the
  health surface as "ignored". None is a report. S201.9 switches that counter to an **allowlist**,
  so it flags only formats a report could actually be. `IGNORED` should read **0** again — and when
  it doesn't, it will mean something.
- It delivers the **census that can see the C: drive** (item 3 below).

**How you know it worked:** the heartbeat says `agent S201.9`. Read it at:

```
F:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt
```

---

## 2 · TWO TIDY-UPS — whenever convenient. Nothing is deleted; everything moves to a bin.

**Machine: manojz.** Double-click:

```
D:\Downloads\margsync\MargPull\CLEANUP_DRIVE.bat
```
Tidies the Drive delivery folder. Amir's NEFT advices and the vendor reconciliation are left alone.

**Machine: the MEDICAL PC.** Double-click:

```
F:\My Drive\Clinic Data Archive\ToMedical\CLEANUP_MEDICAL.bat
```
Moves 343 junk backup files, the guard chain (which cannot run — that Python has no spreadsheet
reader), the parked AutoHotkey macro and the superseded watcher setup into `D:\_to_delete_S201\`.

**And on manojz, when you feel like it,** look through and empty:

```
D:\Downloads\margsync\_to_delete\
```
7.6 MB parked. Nothing in there is live. It is a bin, not a backup.

---

## 3 · ONE NEW TOOL — after install #1, run it once

**Machine: the MEDICAL PC.** Double-click:

```
F:\My Drive\Clinic Data Archive\ToMedical\MEDICAL_CENSUS.bat
```

**Why it has to run there.** Every other census tool runs on manojz, over the Tailscale share
`\\100.119.151.40\DDrive` — the **D: drive only**. Marg's PDFs live on **C:**. So those tools would
report "nothing there" with complete confidence, and be wrong. This one runs on the machine and sees
both drives.

It lists every report-shaped file on the medical PC and says whether each reached the archive,
cross-checked against the archive index through the Google Drive copy. It writes:

```
F:\My Drive\Clinic Data Archive\FromMedical\CENSUS.txt
```

which syncs back, so I can read it without you pasting anything. Read-only; changes nothing.

---

## THAT IS ALL

Everything else in the Marg pipeline is done, running and verified. The three health surfaces to
glance at any time — none needs a login:

```
D:\Downloads\margsync\MargPull\_last_pull.txt                        (manojz, every 10 min)
H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt            (medical, every 5 min)
D:\Downloads\margsync\MARG_PICTURE.txt                               (the day-by-day picture)
```

If something looks wrong, the fault flow by symptom is in
`MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` — written to be usable without reading anything else.

**Decisions still waiting on you** (not tasks — judgements only you can make):

- `ingest.min_confidence` for Marg, currently 0.70 and tuned for OCR rather than a structured export.
- One look at the 21-Aug report: 16 of 37 bills fell below that bar, against ~25% on other days.

---
*S201 · everything else is recorded in `OWNER_TODO_LIVE.md` and the S201 documents.*
