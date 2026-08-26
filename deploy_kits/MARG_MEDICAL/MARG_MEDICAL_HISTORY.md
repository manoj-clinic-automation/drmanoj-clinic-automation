# MARG & THE MEDICAL PC — THE HISTORY ARCHIVE

**Append-only. One file. Everything that happened, in order, from S179 (14-Aug-2026) to S203
(26-Aug-2026).**

---

## WHAT THIS IS, AND WHEN TO OPEN IT

This archive absorbs the **entire Marg / medical-PC documentation history** — the S179–S203 session
records, the four reference documents, the S203 working papers, and the events they describe — into
one chronological file with an index at the top.

It exists because that history had grown into **sixty-odd separately-filed documents, all equally
loud**, none of them saying which of the others was still true. A reader could not tell a spent
route survey from a live operating procedure by looking at either. This is the project's own
**D247** pattern — a small register of what is true *now*, plus an append-only archive of everything
that happened — applied at last to the one subsystem that never received it.

### The three files, and only three

| file | answers | read it when |
|---|---|---|
| **`MARG_MEDICAL_CURRENT.md`** | *What is true right now?* | **always. This is the one you read.** |
| **`MARG_MEDICAL_HISTORY.md`** — this file | *Why is it like this?* | only when the current file leaves you asking why |
| **the printed wall card** | *What do I do in the next sixty seconds?* | at the machine, when something is wrong |

> **A note of honesty about the first row.** As of 26-Aug-2026 the current-state document is filed
> under its build name, **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v4.md`**, md5
> `df290c6f5cbb870af6c232db21bc2219`. Renaming it to `MARG_MEDICAL_CURRENT.md` is the owner's, at a
> close. Until that rename happens, **`MARG_MEDICAL_CURRENT.md` does not exist**, and this row names
> a file you will not find. Stated rather than glossed.

### The rules this file lives under

1. **APPEND-ONLY.** Nothing here is ever edited to make it read better in hindsight. A sentence
   that was believed on 15-Aug and disproved on 26-Aug stays as it was written, with the correction
   recorded *beneath* it (F-23). **History is never in conflict** — an entry that is false today is
   still a true record of what was believed then. A conflict exists only where a *current* document
   repeats it.
2. **NEVER TAKE A CURRENT FACT FROM HERE.** Every hash, count, path and pin below is a snapshot with
   a date on it. The current file owns the present tense.
3. **EVERY md5 IN THIS FILE WAS COMPUTED BY THE AUTHOR OF THIS FILE**, with `md5sum`, on the
   machine, on 26-Aug-2026, from the file it names. None is copied from a summary. None is
   abbreviated below eight characters in a claim (F-116). Where a hash is quoted *from* a source
   document rather than computed, it says so in those words.
4. **A FILENAME IS NOT PROVENANCE (D188).** Where two documents share a name, both are hashed and
   both are recorded.
5. **WHERE TWO DOCUMENTS DISAGREE, BOTH ARE RECORDED**, with which one won and why. Nothing is
   silently picked.
6. **WHERE SOMETHING COULD NOT BE ESTABLISHED, IT SAYS "NOT ESTABLISHED"** and names where the
   author looked.

*Built at Session 203, 26-Aug-2026, from `deploy_kits/S203_MARG_CANON/` (64 files, `SUMS.md5` =
`b099447b6afe2374093aa995b18053b6`, `md5sum -c` exit 0), from
`deploy_kits/KB_canon_S197fold/filed/`, and from the KB History Archive. No `git` command was run
(F-131). Nothing was deleted. No manifest-pinned document was edited. No token value was read or
printed. No patient identifier is reproduced.*

---

# INDEX

**Find your entry here. Do not scroll the body.**
Dates are the date of the event or the document, not the date it was filed.

| # | Date | S | Subject | What it settled | Superseded? |
|---|---|---|---|---|---|
| **1** | 14-Aug | 179 | **Marg sale report — first analysis** | **The money rule** — `cash = the CASH column`, `UPI = net − CASH`, never the `D.R.` mode field. Derived: `277,083 − 193,412 = 83,671 = 88,777 − 5,106`. 13 days, 13 exact matches against the Sheet | **Amended, not superseded** — see #12: S183 measured Marg's CASH column ₹1.32 lakh high over 119 days. The rule holds for *what Marg says*; not for *the drawer* |
| **2** | 14-Aug | 179 | **B1 medical reconciliation** | 121 legacy days imported, ₹26,81,566; **36 carry-forward breaks, net −₹84,533**; 14 missing days, 7 negative-cash days | Live, as history. The breaks became `cash_adjustment` rows |
| **3** | 14-Aug | 179 | **Sanjeevni module build contract v1** | D313's design; the ICICI merchant-statement identification (§7) | **⚠ STATUS UNCERTAIN.** Retired as "superseded whole by v2" — **no v2 exists anywhere in the repo.** Treat as KEEP |
| **4** | 15-Aug 13:55 | 180 | **Marg folder recon — the data layer** | **The tables are encrypted.** 16-byte prefix `19 a3 95 78 …`, period-256, no per-file key, `codepage=437`, `marguser.csv` the unencrypted control. And: *"very likely fully breakable in a focused session"* | **That last clause was FALSIFIED** — see #14. The format analysis stands and is the only copy |
| **5** | 15-Aug 14:30 | 180 | **Feed feasibility — seven routes surveyed** | Route 4 (pick the `.xls` off disk) wins. `up_sale`/`up_saleinfo` dormant; `MARGDEMO`; mail never configured; no SQL sync | **SUPERSEDED** (banner, 26-Aug) — the route was built. **Filed as S181; re-attributed to S180** (D188) |
| **6** | 15-Aug | 180 | **Sample findings — the real files** | The **3-column vs 9-column** variants; the **text-cell credit-note trap**; 23-of-23 bills labelled `.CASH` on a ~30% UPI day; **and `C:\Users\Public\MARG\17476\`** | KEEP — sole home. **Its C: line was lost and "re-discovered" ten days later** (#31) |
| **7** | 15-Aug | 180 | **The Daily Sale button settings** | The exact report-screen and Excel-delimiter settings — **the only recipe for regenerating the feed after a Marg reinstall** | KEEP. **Stale on two fields**: date range (see #57) and `Disc.Bill Sign` |
| **8** | 15-Aug | 180 | **Vendor requirement doc** | Licence `LIC-14116710`, E-Business ID `39548`, R1–R6, §8 acceptance list, **and §6 the silent truncation written up for the vendor** | KEEP — **the vendor asks have never been answered** |
| **9** | 15-Aug | 180 | **Transport design** | §3.4 the idempotent per-day upsert (why the feed self-heals), §3.5 self-checks, §3.6 PHI, §3.7 parallel-run | **PARTIALLY SUPERSEDED — §2 only.** The rest is current and is the sole home |
| **10** | 15-Aug | 180 | **Feed request and flow** | **§4A — sale-return correlation, measured on nine real credit notes.** 9/9 named, 5/9 fully compliant, 7/9 correlated | KEEP. **Two S203 documents attribute §4A to the wrong file** (#52 §0.3) |
| **11** | 15-Aug | 180 | **The action register — V/Q/O/U** | **V7, the silent truncation.** U11's measured attribution ceiling (3 of 36). U7: `DISCOUNT` is the channel, not `DR/CR`, by 18×. F-85/86/87/88 candidates | KEEP — the vendor asks V1–V9 / Q1–Q8 are open |
| **12** | 16-Aug | 183 | **Daily cash design + five months of Marg data** | **The decisive cross-check: Marg vs Darpan over 119 shared days.** Totals agree to **0.3%**; **Marg's CASH column overstates cash by ₹1,32,375**. Home medicine is the cause. Identity capture began 19-Jun | **NOT SUPERSEDED — and NOT CARRIED.** The current master mentions S183, home medicine and Darpan **zero times each** (verified by grep). This is the largest live gap found |
| **13** | 21-Aug | 195 | **Encryption finding — the optimistic note** | *"CONFIRMED XOR … So it is genuinely breakable."* Route: crib-drag from a REPORT_x.XLS, or a debugger dump | **SUPERSEDED 23-Aug by #14 — and then re-asserted as fact by master v2 on 26-Aug** (#51) |
| **14** | 23-Aug | 195 | **Decrypt partial key — THE THOROUGH NEGATIVE** | **Four attacks, 27,246 records, 7 files, all failed.** 0 bill numbers, 0 `"2026"`, no valid VFP field types, **identical 19-byte prefix across 809 B … 13 MB falsifies XOR-of-standard-DBF.** RETIRE remote decryption | **CURRENT. This is the winning document.** It was **repo-only and never in project knowledge** — which is exactly why v2 got it wrong |
| **15** | 21-Aug | 195 | **Email hardening + Marg guard build state** | The guard chain: `guard_and_send.py` reusing `marg_report.py` so its judgment equals the server's | **SUPERSEDED** — measured 26-Aug: **the guard chain is not on the medical PC at all.** Two divergent copies existed; reconciled at S203 (#54) |
| **16** | 21-Aug | 195 | **The medical kit — six files** | `SETUP_S195_MARG.md`, `GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py`, `SETUP_CHECK.bat`, `marg_export_macro_v2.ahk` (calibrated screen coordinates) | Kit preserved; **the installed instances are gone from the machine.** Two of the six exist only here |
| **17** | 22-Aug 02:05 | 195 | **S195 final pins** | The token crisis: `FINANCE_MARG_TOKEN` had lived somewhere transient; made durable in the systemd unit. `SEND_TO_CLINIC.bat = e19a8a77…` | **RETIRED.** Every VPS pin has moved many times. The one durable item was re-measured 26-Aug |
| **18** | 23-Aug | 195 | **Medical watcher LIVE reference** | The watcher is resident, autostarts at logon, bundled `pyportable`. **"The hidden villain: no system Python."** Task #10 standard | **STILL MANIFEST-PINNED AS "SOLE REFERENCE" while a newer document says it supersedes it.** Nearly every operational claim in it is now false (#44) |
| **19** | 22–23 Aug | 195 | **S195 close summary** | The `marg_net_sql` credit-note fix; the 18-Aug ₹23,879 phantom; the canon fold-in debt | **RETIRED** — folded into Archive §S195 at the S197 fold |
| **20** | 21-Aug | 195 | **Source-data retention policy** | 8 years, one zip per month per source; `index.csv` permanent; measured 68 KB average, 74% compression | **STILL A DRAFT AWAITING APPROVAL, and wrong three ways on paths/mechanism** (C-7) |
| **21** | 22-Aug | 195 | **The Auditor seed** | The role: *finds, never fixes.* Five slices. **"No claim without primary evidence you generated in this session."** | Manifest-pinned and **known-wrong**: it still tells the Auditor to continue the F-series, which S196 overrode |
| **22** | 24-Aug | — | **AUDIT RUN 1 · slice 1 · the cash trail** | **AF-1…AF-6**, each with reproduced evidence. **AF-3's duplicate-advance scan command exists nowhere else** | Never re-run. **No slice 2 was ever executed.** AF-5 was dropped in transcription (#47) |
| **23** | 25-Aug 09:15 | 201 | **THE OUTBOX HAD NO CONSUMER** | Eleven verified reports stranded three days. `uploaded=queued` asserted a send that could not occur. **"The automation did not break the push; it hid it."** | **SUPERSEDED — F-179 CLOSED.** The Fault Register is the only register of fault status |
| **24** | 25-Aug | 201 | **The rebuild plan — eight parts** | **Faults A–M**, each with a file and a line. **4 of 7 failure modes had no monitoring at all.** *"Every server-side check watches arrival at the VPS."* | KEEP — Parts 6–8 unbuilt; one of only two homes of AF-5's substance |
| **25** | 25-Aug 14:23 | 201 | **Part 0 — the quarantine rescue** | **11 reports rescued.** The router blacklists by md5 *before* `identify()` — so every signature added stranded whatever it should have rescued. `data_from`/`data_to` added | **SUPERSEDED** — the rescan is now standing procedure. The 11 dates and the backup name stay here |
| **26** | 25-Aug | 201 | **Part 1 — capture everything; the agent** | **The watcher died at 10:37 and was found at 14:49, by accident.** *"That day's report survived on redundancy, not on design."* PDF path built. Three faults the author introduced, recorded | **SUPERSEDED** on mechanism. The 10:37 timeline is history and stays |
| **27** | 25-Aug | 201 | **The `.xlsx` time bomb, defused** | `xlrd 1.2.0` loses `.xlsx` at Python 3.9. Fixed by **removing the dependency**: `xlsx_stdlib.py`, stdlib only. **170 cells vs openpyxl, 0 mismatches** | KEEP — **the only proof `xlsx_stdlib.py` is correct**, for a file that exists on two PCs and in no repo |
| **28** | 25-Aug | 201 | **Parts 2/3/4** | An `end_marker` per report type, **derived from real samples, never guessed**; the range-export day-credit bug; the spool routed whenever non-empty. **₹476,393 agrees across two independently generated reports** | KEEP — the per-type derivations exist nowhere else |
| **29** | 25-Aug 17:03 | 201 | **A1FIX — the born-dead check** | AF-2 closed. **The offline smoke harness is reproducible from the repo by hash** — the recovery recipe. **And a fault retracted the same hour**, because a stale repo copy was read instead of the live file | **SUPERSEDED** on pins. The recovery recipe survives in `S201_PARKED_BACKLOG` §B |
| **30** | 25-Aug | 201 | **"This month vs Marg" explained** | The red line is **the review queue, to the rupee**: 49 lines, ₹51,868. And a wrong rule retracted: *"A rule that fits two days and predicts the third wrongly is not the rule"* | KEEP — a current canonical document cites it by name |
| **31** | 25-Aug 19:12 | 201 | **The completion audit** | *"Marg has TWO output trees, and only one was ever known."* The C: tree, the 343-file runaway, the popup fix | **SUPERSEDED BY MEASUREMENT.** Its pins were read from the never-purging mirror; **its "found 25-Aug" is false — it was written down on 15-Aug** (#6) |
| **32** | 25-Aug 19:20 | 201 | **What is left for you** | Three tasks. The 18 Marg database files on the health surface | **SUPERSEDED** by `OWNER_TODO_LIVE`. *"Two task lists is how an item gets done twice or never"* |
| **33** | 25-Aug | 201 | **The parked backlog** | A1–A5, B1–B6, **C1–C8**, D1–D3, E (AF items), F (KB hygiene) | KEEP — **four of C3–C8 were recommended for F-numbers and none was minted** |
| **34** | 25-Aug | 201 | **MARG_PIPELINE_REFERENCE_v1** | The chain as it runs; **the upload contract, written down for the first time**; all three token copies together for the first time | **Tier-1 CURRENT — and wrong in five places** (#44): two roots not three, `marg_router` as a step, the multipart filename, the `--learn` field list, `xlsx_stdlib` "not yet installed" |
| **35** | 25-Aug (corr. S202) | 201 | **MARG_PIPELINE_MAINTENANCE_FLOW_v1** | The 60-second check — **three files, none needs a login**. The guest-access fault by symptom, with `cmdkey`. *"DO NOT re-enable insecure guest access to fix this"* | **Tier-1 CURRENT.** But **the copy on manojz that you would actually open is the S201 one** and does not contain the fix for the outage that produced it |
| **36** | 25-Aug | 201 | **MARG_INGESTION_REFERENCE_v1** | **D313: the import never touches the money.** The confidence gate, table by table. `marg_net_sql`. *"Never write a second way of summing Marg rows"* | **Tier-1 CURRENT** and the sole home of the ingestion half. **§9 item 5 keeps a question D348 retired hours after it was written** |
| **37** | 26-Aug | 202 | **THE 8h40m OUTAGE — and D350** | The pull died 23:08, found 07:33. **Every component healthy; Windows had blocked unauthenticated guest access.** *"A system with two paths and no switch has one path."* §8 records the counter-argument | Contract **NOT YET BUILT.** Owner scoped it to §2/§3/§4/§5; **§1, the Drive fallback, is PARKED at his ruling** |
| **38** | 26-Aug | 202 | **The pendency audit — N1…N13** | Six S201 faults never minted; **the AF-series has no bridge to the F-series**; two canonical rows contradict each other; the coverage map predates the estate | Largely still open |
| **39** | 26-Aug | 202 | **OWNER_TODO_LIVE** | The living list. **Token rotation, aging since 21-Aug, still the oldest and highest-severity item.** ⭐0a: the backup | **Un-manifested by design.** The only list with a numbered step (A10) keeping it current |
| **40** | 26-Aug | 202→203 | **START_HERE_SESSION_203** | *"Six of nine findings were the assistant's."* **"A monitor is proven against the thing it monitors, running, in its real state — never against a fixture."** | The session-entry document for S203 |
| **41** | 26-Aug | 202→203 | **The KB consolidation plan** | The gate: **nothing is retired until it is provably recoverable from TWO independent stores, by hash.** Retirement is a MOVE, never a delete | **§5 NOT YET APPROVED.** Nothing may be removed until it is |
| **42** | 26-Aug 06:32 | 203 | **The system map, from the record** | **C-1…C-11, every conflict in the record**, both sides quoted. §8: the five-line true summary | **SUPERSEDED** — written from the record; the master was written from the machine, and corrects three of its statements. Its §5 D350 gap tables stay here |
| **43** | 26-Aug | 203 | **The code truth map** | **Since S201 the pull produces no log at all.** Every swallow site named with a line. `marg_router.py:349-354` — the file that vanishes for ever, invisibly | KEEP — the only reading of the code |
| **44** | 26-Aug | 203 | **The document verification — 82 claims tested** | **42 VERIFIED · 17 WRONG · 12 STALE · 11 UNVERIFIABLE.** *"The mirror is a graveyard, not a census"* — 450 files against the machine's 77 | KEEP — the evidence base for the master's §9, and the only audit of the reference set that exists |
| **45** | 26-Aug | 203 | **The document inventory** | **69 documents · 8 pinned · 17 wildcard-only · 5 named-but-absent · 39 orphans · 30 in one store** | KEEP — with §0.3's misattribution correction applied |
| **46** | 26-Aug | 203 | **The KB census, phases 1 & 2** | **76 project documents exist in no other store; 90 are named nowhere in the manifest.** And: **the 98% headroom figure that drove the whole exercise cannot mean what it appears to mean** | KEEP — in active use |
| **47** | 26-Aug | 203 | **The pendency reconciliation** | C3–C8 re-tested one by one. **AF-5 was never lost — it was dropped in transcription** by the document that triaged it | KEEP |
| **48** | 26-Aug ~09:44 | 203 | **THE PRESERVATION PASS** | 51 documents that existed in **exactly one store** copied into the repo and hash-verified. **The precondition for any retirement** | Live. **The folder is still not manifest-pinned** |
| **49** | 26-Aug | 203 | **Master reference v1** | The first consolidation | **SUPERSEDED TWICE. v1 lost three whole subjects**: encryption, the money rule + V7, and the entire ingestion half |
| **50** | 26-Aug | 203 | **Master reference v2** | Restored all three subjects; corrected the token list to five stores | **SUPERSEDED.** §4.3 asserted the **superseded** 21-Aug encryption note as current fact |
| **51** | 26-Aug 10:10 | 203 | **The precedence map — and C16** | **The rule: every fact is owned by exactly one document CLASS.** And the catch: *"v2 §4.3 sides with the SUPERSEDED note … this is the one place v2 has introduced a new conflict"* | Its §0 verification block is a dated snapshot (55 rows; the folder now has 64) |
| **52** | 26-Aug 09:57 | 203 | **The retirement list** | 13 RETIRE · 8 KEEP+PROMOTE · KEEP · 5 CANNOT DECIDE. **§0.3 corrects a misattribution in two other documents and in its own author's earlier report** | Its §1 md5s are **pre-banner** and now stale by one banner, by design |
| **53** | 26-Aug 10:39 | 203 | **Master reference v3** | Corrected §4.3 to the thorough negative; **added §0.1, the precedence rule** | **SUPERSEDED by v4.** **Its pre-banner hash `579ea885…` is cited in 16 files in this folder and matches no file that exists** (see §TEACHES) |
| **54** | 26-Aug 10:40 | 203 | **THE PROJECT KB WAS THE STALE STORE** | The inversion: **the repo copy was the better one, twice.** *"Neither store is authoritative by position."* The two divergent pairs reconciled | Live. **`S203_MARG_DOC_POINTERS` §E #3 still lists this reconciliation as owed** — it was done in the same folder |
| **55** | 26-Aug 10:11 | 203 | **The document pointers** | *"I found an old Marg document. Is it still true?"* — the 16-row answer table, plus §B, §C, §D, §E | **Stale in three places** already (see its entry) |
| **56** | 26-Aug 10:39 | 203 | **The coverage-map addendum** | **Six rows the `SYSTEM_DOC_COVERAGE_MAP` has never had** — including 🔴 backup/DR, the least-protected part of the estate | **DRAFT. Nothing applied.** The map is manifest-pinned and must not be edited outside a close |
| **57** | 26-Aug 10:38 | 203 | **MASTER REFERENCE v4 — CURRENT** | Adds **§2.1, the manual Marg export that everything downstream begins with** — no document carried the trigger step as part of the flow — and **corrects the 15-Aug recipe's month-to-date range to ONE BUSINESS DAY** | **THIS IS THE CURRENT DOCUMENT.** Read it, not this file |
| **58** | — | — | **WHAT THIS HISTORY TEACHES** | The six recurring patterns, each evidenced from the entries above | — |

---

# THE BODY — CHRONOLOGICAL

All md5s below were computed with `md5sum` on manojz on 26-Aug-2026 unless the entry says otherwise.
All source files are in `deploy_kits/S203_MARG_CANON/` unless a different path is given.

---

## SESSION 179 · 14–15 August 2026 — before there was a pipeline

### 1 · The money rule is derived
**`S179_Marg_Sale_Report_Analysis.md`** · md5 `da742177633bc023c7c19198b4774b4a`

Source: one export, `SANJEEVNI AUG SALE REPORT UPTO 13 AUGUST 2026.XLS` — Marg ERP 9+, **345 bills,
1–14 Aug 2026** — plus one Marg backup archive.

**What it established, and it is still the foundation of the feed:**

> ```
> net total                277,083
> CASH column total        193,412
> difference                83,671   <- non-cash
> UPI-mode bills, net       88,777
>    less cash inside them   5,106
>                           83,671   <- identical
> ```
> **So the ingestion rule is: cash = the CASH column; UPI = net − CASH. Never derive cash from the
> mode field.**

Twelve bills marked UPI carried a cash portion — split payments, ₹5,106 in total. A label cannot
represent a split; a column can. **This derivation is the proof; the master carries the rule and not
the proof.**

**Also settled here, and nowhere else:**

- **Thirteen days, thirteen exact matches** between Marg's day total and the typed Google Sheet
  figure. *"Whoever types the daily figure reads it off Marg and gets it right, every time."* The
  ₹84,533 of historical drift is **not** a revenue-recording problem.
- **Three days with zero UPI bills** — 11-Aug (25 bills), 13-Aug (31), 14-Aug (23) — at a counter
  that normally runs 25–40% UPI. Read as the mode field defaulting to cash. *"Do not treat this as
  a discrepancy to explain away."*
- **The description field carries a patient ID, and it is stable.** 254 of 345 bills read
  `<phone> <NAME> <3–5 digit number>`; **190 distinct phones, not one ever paired with a different
  trailing number.** That consistency is what makes it an identifier rather than a coincidence.
- **The field truncates at 33 characters.** `PRADEEP KUMAR GUPTA 77` is cut mid-ID; six bills sit at
  exactly 33 characters and have probably lost digits.
- 91 bills have no phone at all — `PROSIJER` procedure bills, codes like `BPJ`/`CPU`/`WR`, bare
  names, one 9-digit typo, one running the ID onto the name (`ASHOK AGARWAL7657`). These land on
  WALK-IN rather than being guessed at.
- **18 credit notes carry negative amounts.**
- **The `.jmbkh` Marg backup is a dead end** — a zip whose every member is password-protected; all
  28 `.mbk` files refuse to extract. *"Keep exporting this report; the backup is for restoring Marg,
  not for feeding us."*
- **The report needs its own adapter, not the generic CSV one**, for two reasons: the date is not a
  column (it lives in group-header rows, so the parser must carry the current day forward), and it
  is a real BIFF `.xls` whose trailer rows must be recognised and skipped.
- **The day totals give a built-in self-check**: parse the bills, sum them, require the sum to equal
  Marg's own `DAY TOTAL` before accepting a single line.

**Three questions it asked the owner:** is the trailing number the clinic's patient ID · check the
ICICI merchant statement for 11 and 13 August · why do `PROSIJER` bills show cash collected.

> **⚠ HOW THIS WAS LATER AMENDED — read with entry 12.** The rule as stated is correct about *what
> Marg records*. It is **not** correct as the drawer figure. On 16-Aug, S183 measured Marg's CASH
> column against Darpan's own independent filing over 119 shared days and found Marg **overstates
> cash by ₹1,32,375**, because Marg books every home-medicine bill as fully paid in cash and those
> are never collected at the counter. **The current master carries the rule from this entry and not
> the amendment from entry 12.** Recorded here in full, struck by nothing, because both are true of
> different questions.

### 2 · The legacy import, and what it found
**`S179_B1_Medical_Reconciliation_Report.md`** · md5 `9726d5ecaaee4609d8ff40c71a6a9f63`

Produced by `finance_import_medical.py` from the legacy Google Sheet. **Offline run. Nothing
installed, nothing served, no rupee corrected.**

| | |
|---|---:|
| Days imported | **121**, 2026-04-01 → 2026-08-13 |
| Sale total | ₹26,81,566.00 |
| of which UPI | ₹8,83,533.00 (32.9%) |
| of which cash | ₹17,98,033.00 |
| Expenses | ₹84,442.00 |
| Deposited to bank | ₹16,59,114.00 |

**The carry-forward breaks — because `Old Balance` was confirmed to mean yesterday's closing cash,
every disagreement is an unexplained movement:**

| | |
|---|---:|
| Breaks found | **36 of 121 days (29.8%)** |
| Upward corrections | +₹4,46,090.00 |
| Downward corrections | −₹5,30,623.00 |
| **Net unexplained** | **−₹84,533.00** |

The five largest: 2026-06-13 **+₹1,04,403** · 2026-05-30 **−₹90,538** · 2026-04-08 **+₹84,943** ·
2026-08-13 **−₹74,604** · 2026-05-16 **−₹55,000**.

Open exceptions: `carry_forward_break` 36 (₹9,76,713 absolute) · `missing_day` 14 ·
`negative_cash` 7 (₹2,57,894).

**Proof the import is faithful:** the ledger's final closing cash **−₹30,056.00** equals the sheet's
own last `Total Cash` **−₹30,056.00**. And the independent arithmetic: cash sales − expenses −
deposits = ₹54,477 against an actual closing of −₹30,056 — **a gap of ₹84,533 needing explanation**,
the same number as the net of the breaks.

*"Nothing was corrected."* Each break became an `open` row waiting for a reason.

### 3 · The build contract, and the status nobody can settle
**`S179_Sanjeevni_Medical_Module_Build_Contract_v1.md`** · md5 `3297bfbbbdf85090adfabe35b95987e2`
(this hash includes the S203 uncertainty banner; the pre-banner hash recorded by the retirement list
is `f6de1a5eaa59f1c685caca988ad1a3b8`, quoted from that document, not computed here — the file no
longer exists in that state)

A **DRAFT for sign-off**. Thirteen owner directions read back as requirements. Candidate numbers
D313 (architecture) and F-84.

**§1 — the one design rule that fixes everything:**

> ```
> opening(today)  =  closing(yesterday)          <- COMPUTED. Read-only. Cannot be typed. Ever.
> closing(today)  =  opening + cash sales − expenses − cash out + cash back in ± adjustment
> ```
> *"There is no cell anywhere that lets a person overwrite the running balance. That is the whole
> fix."* An adjustment stays possible — *"the drawer is real, and real drawers have surprises"* —
> but as a visible, dated, reasoned, doctor-approved row.

**§7 — the UPI email, found by searching the mailbox rather than asking:** sender
`merchantsolutions@icici.bank.in`, subject `MerchantStatement-DD-MON-YYYY`, daily ~08:00–09:40 IST,
attachment a machine-readable `.xlsx` — **and already split by business**, merchant
`100000000312505` = Sanjeevni Medicos, `100000000306941` = the clinic. *"I had assumed the UPI
cross-check would need OCR on a PDF — approximate, confidence-scored, arguable. It doesn't."*
One honest caveat left open: whether `ICICI_POS_CD` covers *all* digital collection or only ICICI
QR/POS.

Build order B1…B7, ending in a **7-day parallel run before the Google Form is retired**.

> **⚠ ITS STATUS CANNOT BE ESTABLISHED.** `S203_MARG_RETIREMENT_LIST.md` §1 row 12 classifies it
> RETIRE on the strength of *"superseded whole by v2, which says so"*. **No
> `S179_Sanjeevni_Medical_Module_Build_Contract_v2` exists anywhere in this repository** — searched
> by filename across the whole tree on 26-Aug; the only match is the v1. The retirement list's own
> §4 #1 records that this document **was never read from project knowledge at all**. **No successor
> document and no successor md5 can be named here honestly.** Treat as KEEP.

---

## SESSION 180 · 15 August 2026 — the reconnaissance

> **A labelling fault, recorded because it is the project's own subject.** The feasibility survey
> (entry 5) was written and uploaded as **`S181_Marg_Feed_Feasibility.md`** and its body still says
> *"Session: 181"*. Derived from the artefacts rather than the labels: the last close-out was S179,
> it named the next session 180, and `S180_Marg_Folder_Recon.md` was created **before** that
> close-out — so it is S179 work carrying a forward-guessed S180 label, and the survey inherited the
> error and went one further. **Both are Session 180 work.** Minted as finding candidate **F-85**:
> *session-numbered artefacts are being labelled with a forward number before the session that would
> carry it has opened.* Kin to D188.

### 4 · The data layer — and the prediction that was wrong
**`S180_Marg_Folder_Recon.md`** · md5 `f3393979354411105a253e2715fabe7b`
Surveyed 2026-08-15 ~13:55–14:05 IST, read-only, **while Marg was live and actively writing.**

**The headline: the live Marg data files are NOT directly readable.**

**The layout, established byte by byte:**
```
[16-byte Marg prefix][encrypted 32-byte DBF header][encrypted 32-byte field descriptors][0x0D][records]
```
Universal prefix: `19 a3 95 78 <63|53> 44 f1 98 55 93 67 a1 be c0 2d da` — byte 4 is `0x63` for data
tables and `0x53` for several config tables.

**Properties proved, not guessed:**
1. **Deterministic, position-keyed, period 256.** In `acgroup.c18`, `dis.c18` and `saletype.c18` the
   header's known-zero run at `0x22–0x2b` is byte-identical to the 8th field descriptor's known-zero
   run at `0x122–0x12b` (`22 68 42 34 e0 88 44 92 45 c7`), and likewise `0x42–0x4f` ≡ `0x142–0x14f`.
2. **No per-file key, no salt, no IV.** Identical across every table, every financial year, and even
   across the `System`/root `.ini` tables. *"One key serves the whole installation — and, by
   implication, probably every Marg installation."*
3. Not a plain XOR or ADD keystream — reconstructing from known-zeros yields ~46%/~41% printable.
4. **The residual is a bit-rotation.** A per-column rotation correction lifts printability to
   **95.5%**, with recognisable fragments.
5. **Partial real decrypt achieved:** version byte **`0x30`** (VFP with memo) and last-update date
   **26-08-14**, matching the file's mtime. `nrec`, `hdrlen`, `reclen` and the field names did not
   resolve.

**The extension scheme, which nobody would guess and which decides which files matter:**
`.c18` = FY 2026-27 (**32 tables, 34,831,187 bytes, live**) · `.c17` = the year before (32 files,
71 MB) · `.c16`…`.c05` older years · `.d01` a **second live book**, small, also written that day ·
186 `.cdx` indexes named `c18dis.cdx` for `dis.c18` — *"a parser must map them explicitly."*

**The plaintext exceptions, which matter more than the ciphertext:**
- **`CONFIG.FPW`** — 156 bytes, plaintext, quoted in full. Two things of real value:
  **`codepage=437`** (decode character fields as CP437) and **`resource=marguser.csv`**.
- **`D:\MARGERP\marguser.csv` is a plain, unencrypted VFP DBF** — 52 records, header length 520,
  record length 48, first field `TYPE C(12)`. *"This proves the VFP runtime reads both plain and
  obfuscated tables — encryption is applied selectively by Marg's own code."* **It is the control
  for testing any parser.**
- **`daybook.xml`** — 1,205,131 bytes, **fully plaintext Tally XML**, 791 vouchers (Sales 636,
  Purchase 89, Sale Return 34, Receipt 25, Payment 5, Contra 2), March 2026 only. Confirms the bill
  series `A00nnn` independently.

**Read/lock behaviour, which the whole capture design later rests on:** 18 of 19 table copies
succeeded on a running Marg; one transient failure on `mewsale.c18` at 13:59 succeeded on retry two
minutes later. *"Expect occasional transient failures on hot tables; retry-with-backoff is
sufficient, an exclusive lock is not the failure mode."*

**Also flagged:** `serverlog.fpt` is **768,569,536 bytes** and growing daily · the mail directories
are empty · `System\margsqlconnection.ini` untouched since the install stamp · `.ini` paired with a
same-named `.fpt` is **a table, not a config file**.

> **⚠ THE PREDICTION IN §4.3 AND §10 WAS FALSIFIED.** This document says the obfuscation *"is very
> likely fully breakable in a focused session"* and recommends *"Budget one focused session."*
> **It was budgeted, it was spent, and it failed** — see entry 14. The format analysis in this
> document is correct and is the **only copy of it anywhere**; the tractability verdict is not.
> **The current master carries none of this section**: `19 a3 95 78`, `codepage`, `marguser`,
> `period` — verified by grep on 26-Aug, all absent from v4.

**One internal inconsistency, recorded because a filename is not provenance and neither is a count.**
§4.2 says the comparison ran across *"23 encrypted files (all 16 `.c18` tables copied…)"*. §1 says
*"18 of 19 requested table copies succeeded"*, and §3.2 inventories **32** `.c18` tables. The three
counts cannot all be right. **Which is correct is not established** — the copies themselves are gone.
Nothing downstream turns on it; recorded so a future reader does not treat "16" as the size of the
`.c18` set.

### 5 · Seven routes surveyed, one chosen
**`S180_Marg_Feed_Feasibility.md`** · md5 `d9cabc4a27bb4401d0062a8bfb05635c` (post-banner; the
pre-banner value recorded by the retirement list, quoted not computed, is
`6db52a89106e17e17769f2d31be6f24d`; the original upload as `S181_Marg_Feed_Feasibility.md` was
21,413 bytes, md5 `c2086db25b39c02e8c29bc6cf4dc634c`, quoted from its own provenance note)

**Banner, added 26-Aug-2026:** *SUPERSEDED — a route survey whose verdicts are spent.*

| Route | Verdict |
|---|---|
| **4 · Export folder / daily sale XLS** | **SUPPORTED-AND-AUTOMATABLE** — *"only the trigger is manual"* |
| 3b · Marg's own scheduler | POSSIBLE-WITH-A-SETTING |
| 3c · e-business cloud uploader | POSSIBLE-WITH-A-SETTING |
| 1 · Auto-email a daily report | NEEDS-MARG-SUPPORT |
| 3a · Task Scheduler / CLI | NOT-DETERMINABLE FROM HERE |
| 3d · Tally XML on a schedule | NOT-AVAILABLE |
| 2 · MySQL / SQL sync | NOT-AVAILABLE as configured |

**The live evidence that has NOT been retired with the verdicts:**
- **Marg runs an unattended daily job and it demonstrably works** — `serverbackup\` holds a rotating
  seven-day set, all current, fire times **08:16 to 13:56 IST**. *"The trigger is event-based, not
  clock-based … a feed built on it must not assume 'arrives by 21:00'."*
- **`report\auto\` exists under every Marg user and is empty on every one.** *"It has never produced
  a file on this install, so this is inference, not proof."*
- **`up_sale.ini` (984 B) and `up_saleinfo.ini` (600 B) exist and are DORMANT**, frozen at
  2026-08-01 09:14 — written once at schema init — while eight master tables (`up_party` 221,489 B,
  `up_pro` 399,585 B, `up_os`, `up_stype`, `up_group`, `up_payid`, `up_users`, `up_proadd`) resync
  **several times an hour**, all in the same second, at E.BUSID `39548`.
- **Mail has never been configured, not broken.** `emailserver\` and `emailpend\` both return zero
  entries; `margmail.fpt` is 1,536 bytes and `margmailp.fpt` 512 — *"consistent with no message
  bodies ever stored."* But `margsms.txt` is plaintext and live: **28 outbound messages
  30/06–14/08/2026, sender ID `MARGDEMO`** — a demo sender, carrying a customer-outstanding-balance
  template, not a sales summary.
- **A correction to S180's own speculation.** S180 flagged `syncdata.*`, `margsync.c18` and the SQL
  config together as "an active SQL sync layer". *"That was wrong, and this session corrects it."*
  All seven `ebusiness` upload files, `syncdata.*` and `margsync.c18` move **in the same second**;
  the SQL config files sit still. It is the cloud uploader, not a database mirror.
- **The report itself, found in place:** `D:\MARGERP\users\61376\report\REPORT_1.XLS`, **90,112
  bytes, written 2026-08-15 09:59 IST**, genuine OLE2/BIFF, **not encrypted**, 426 rows × 9 columns,
  title `BILL WISE SALES STATEMENT FROM 01-08-2026`, bills `A002660`…`A002986` plus 18 `CN` rows,
  `GRAND TOTAL` gross 285,273.40 / discount 7,298.86 / **net 277,083.00 / cash 193,412.00**, footer
  `Total No. of Bills: 345`. Sheet name **`MARG ERP 9+ Excel Report`** — which also settles the
  version question S180 could not answer from file properties.
- **What could not be checked from that session, and the commands to check it:** no shell existed on
  the device bridge. *"netstat -ano | findstr ":3306"" · "sc query … findstr /i "mysql maria sql"" ·
  "schtasks /query /fo LIST /v | findstr /i "marg""* — **not established whether these were ever run.**

### 6 · Two reports under one filename
**`S180_Marg_Sample_Findings.md`** · md5 `2621975e30be0f66b59a8d842bb928e2` · 2026-08-15

Inputs: `REPORT_1.XLS` (33,280 B, md5 `e81f97fe…` as quoted in the document — not recomputed here,
the file is not in this folder) from `D:\MARGERP\users\61376\report\`, and `report.txt` (2,420 B,
md5 `da087842…` quoted) from **`C:\Users\Public\MARG\17476\`**.

**The headline: this is NOT the report the survey documented.**

| | Survey's file | The file just supplied |
|---|---|---|
| Title | `BILL WISE SALES STATEMENT **FROM** 01-08-2026` | `… **AS ON** 14-08-2026` |
| Coverage | 14 days | **one day** |
| Written | 09:59 | 11:45 |
| Columns | **9** | **3** |

*"Same menu, same filename, same folder — two different reports."*

**The 3-column variant cannot feed the finance module.** One money column, `BILL VALUE`; **no CASH
column**, so the S179 money rule is impossible to apply. *"The 3-column report knows how much was
billed and nothing about how it was paid."* The `report.txt` from the C: tree is the same 3-column
report in text form — checked bill by bill, same 23 bills, same total. It adds nothing.

**The mode field is confirmed worthless, with proof.** **All 23 of 23 rows carry `.CASH`.** Against
the survey's own 14-day totals (net 277,083 / cash 193,412 → UPI ≈ 30%), that cannot be true. *"So
the `.CASH`/`.UPI` field is not the tender — it is an account or ledger label."* The trailing `#`
marker is **also not the tender**: 18 of 23 rows carry it, matching nothing. *"Its meaning remains
unknown. Do not build on it."*

**Three good results:**
- **(a) Credit notes are plain negatives** — `CN00167 -1150.00`, `CN00168 -77.00`. No sign column.
- **(b) A parsing trap, caught before it could bite.** Positive rows are **numeric** cells (type 2);
  the two negative rows are **text** cells with leading spaces — `' -1150.00'`, `'   -77.00'`.
  *"A parser that trusts the cell type, or reads only numeric cells, would silently drop every credit
  note and overstate the day."* `float(str(cell).strip())` handles both. A live example of F-78:
  parse the value, never assume its shape.
- **(c) The self-checks work.** 21 sale rows 19,170.00 + 2 credit notes −1,227.00 = **17,943.00**,
  against a `DAY TOTAL` cell of **17,943.00** ✓, and `Bills: 23` against 23 rows ✓. *"The file proves
  its own arithmetic to the rupee. The adapter can safely refuse any file that doesn't."*

**The design consequence, which held:** *"The adapter must identify the variant before parsing …
On an unrecognised layout it must refuse the file and say so, never guess a column position. A file
is not identified by its name or its path (D188)."*

> **⚠ THE MOST EXPENSIVE LINE IN THE WHOLE ARCHIVE IS THIS DOCUMENT'S LAST ONE.** In an italic
> footnote it records:
>
> > *"Also noted: `C:\Users\Public\MARG\17476\` is a Marg user folder (`17476`) not seen in the S180
> > folder survey, which found only `50018`, `61376` and `a` under `D:\MARGERP\users\`."*
>
> **Ten days later — 25-Aug, entry 31 — the same path was recorded as a new discovery**, and the
> manifest's §S201 block still says *"Marg has TWO output trees, and only one was ever known … Every
> document in this KB … described only the first."* **That sentence is false of project knowledge.**
> The path and the user id were written down on 15-Aug. **The blind spot was in the canon, not in
> the project's knowledge** — the fact was recorded in the one store nothing indexes, hashes or
> reads. Corrected at master v4 §9 #8. `61376` and `50018` appear nowhere in the Archive, Register,
> Fault Register or manifest **to this day**.

### 7 · The button settings — the only reinstall recipe there is
**`S180_Marg_Daily_Sale_Button_Settings.md`** · md5 `3f46935784261a18f50da552d6fd31ee` · 15-08-2026

Prepared for the Marg engineer to save as a one-click default. **Verified, not guessed** — taken
from a real export whose arithmetic was checked line by line: every money column summed exactly to
`DAY TOTAL` and `GRAND TOTAL`, and `GROSS − DISCOUNT + TAX + DR/CR` reproduced `NET AMT.` on every
bill.

**Report screen — `BILL WISE STATEMENT`:** Operator Name *blank* · Stock Less `No` ·
**Report From `01` of the current month** *(CHANGE)* · To current date · Cash/Cr/Disc. `Both` ·
Club Cash Sale `No` · Less Cr/Dr Adj. `Yes` · Add Challans `No` · Patient Mobile *blank* ·
Pres.By Mobile *blank* · Report For `2 Sale-S/R-Brk` · **Report Type `Detail`** *(the critical one)*
· width `80 Col` · **Disc.Bill Sign `1-Bill+Item+Volume`** *(CHANGE)* · Day Total `Yes` ·
**With Item Deta. `Yes`** *(CHANGE)* · Single Party / Selected Group / Selected COMPNA `N`.

**Excel export screen — `SELECT DELIMETER LINE/HEADER`, "do not change them":** separator `Header` ·
line as heading `No`/`1` · data starts at line `5` · data ends `0` · format `Formated`.

**The caution it carried, which turned out to matter:** *"`Disc.Bill Sign` is being changed from
`2-Bill+Item` to `1-Bill+Item+Volume`. The verified file used `2-Bill+Item`. Adding volume discount
may add or shift a column … Please export once with the settings above and send that file for
checking before the button is saved."*

**§E, why item detail is included** — repeat/self-refill patterns, partial pickup, discount leakage.
On the verified file `DR/CR` carried adjustments of up to **₹19 on a ₹319 bill (6%)**, booked as
round-off. And the practice note from the owner, 15-08-2026: *"Darpan on most days; a reserve person
on roughly 2–4 days a month; **Amir enters purchases only**, about twice a week. Each has their own
Marg login."*

Four questions for the Marg engineer, none answered to date: can the button set the date range
automatically · can the operator/biller be a column · can the filename be date-stamped · the two
automation requests already sent.

> **⚠ STALE ON TWO FIELDS, corrected at master v4 §2.1 on 26-Aug.**
> **(a) The date range.** This document specifies `Report From = 01` of the current month. **Do not
> follow that for an item-detail export** — month-to-date *with* `With Item Deta. = Yes` is the exact
> combination that truncated at day 6 of 15, silently (entries 8 and 11). Current and correct
> practice is **one business day per export**; historical backfill is one file per month.
> **(b) `Disc.Bill Sign`.** Master v4 §2.1 specifies **`2-Bill+Item` *(proven)*** — the value the
> verified file actually used. The `1-Bill+Item+Volume` change proposed here was never proven and
> the caution above was never discharged. **Not established whether the test export was ever made.**
> Everything else in this document is current and is **the only recipe for regenerating the feed
> after a Marg reinstall.** After a vendor reinstall the buttons are gone and these settings are the
> only way back.

### 8 · The requirement written for the vendor
**`Marg_Report_Requirement_Sanjeevni.md`** · md5 `ee3cd2549948d6437ef75480d9dadec0` · raised
15-Aug-2026, support route AnyDesk

**Sanjeevni Medicos, 35G/15B Rampur Bagh, Bareilly · Marg ERP 9+ · Licence `LIC-14116710` ·
E-Business ID `39548`.**

*"This document is objective on purpose. Every requirement below has a test that either passes or
fails."*

**Two saved reports, differing in three fields only:** Report A "Daily Sale (Accounts)" —
month-to-date, `Disc.Bill Sign 4-Bill`, `With Item Deta. No`. Report B "Daily Sale (Detail)" —
today, `1-Bill+Item+Volume`, `With Item Deta. Yes`.

**R1** one click · **R2** automatic daily generation *(with the empty `report\auto\` folder cited as
evidence the facility exists)* · **R3** two separate output files, because both currently write
`REPORT_1.XLS` and one would overwrite the other · **R4** *(new)* **a DATE column on every bill row**
— *"at present the date appears only as a group heading row … so any change to page breaks, sorting
or heading placement silently mis-dates the bills"* · **R5** automatic email, noting the mail
facility *"appears never to have been set up … This is a fresh configuration, not a repair"* and that
the sender is still `MARGDEMO` · **R6** historical export **one file per calendar month**.

**§6 — the defect, and the document calls it "the most important item":**

> A month-to-date report **with item detail switched on** does not export completely. It stops
> part-way through and gives **no error and no warning.**
>
> | Requested | `FROM 01-08-2026 TO 15-08-2026` (15 days) |
> |---|---|
> | Rows produced | 1,207 |
> | Pages | 44 |
> | **Days actually present** | **only 01-08 to 06-08 (6 days)** |
> | Day 06-08 | incomplete — **no `DAY TOTAL :` row** |
> | Days 07-08 to 15-08 | **entirely absent** |
> | `GRAND TOTAL :` row | **absent** |
>
> *"The file opened normally in Excel and looked complete. Only the missing `GRAND TOTAL` row
> revealed that it was not."*

Three questions to the vendor: is there a page/line/memory limit · can it be raised · **if not, can
the export be made to fail with a visible error rather than write a partial file silently.**

**§7, what must not change:** the nine column headers, their names and their order · the `DAY TOTAL`
and `GRAND TOTAL` rows · the `Total No. of Bills:` footer · the `CN…` negatives.

> **STATUS: KEEP, and OPEN.** *"The vendor asks have never been answered"* — recorded at S203, and
> master v4 §11 items 3 and 11 still carry two of them. This is an **open instruction**, not
> history. It is also the only place the licence number is written down.

### 9 · The transport design — and the part of it that is still the only home
**`S180_Marg_Feed_Transport_Design.md`** · md5 `4c5b8b48c88d42b480ea8d66d9f508df` (post-banner;
pre-banner `144a1a406851fec73f6885cfe514d97e`, quoted from the pointers document)

**Banner, 26-Aug: ⚠ PARTIALLY SUPERSEDED — §2 ONLY. THE REST IS CURRENT AND IS KEEP.**

**§0/§1 — why the upload beat the watcher, at the time.** The owner pointed out what the survey
missed: *"staff generate report each day that's printed till now for Google form; now with portal
for Darpan a soft copy can be easily set up."* Two facts settled the open question — the report is
**already generated every day**, and Darpan **already makes a daily portal entry**. The comparison
table's decisive row: an upload **fails loudly** because it is attached to a human action; a watcher
**fails silently** — *"this is its whole failure mode."*

**§2 — the route ranking, and this is the superseded part:**

| Rank | Route | Status as written 15-Aug |
|---|---|---|
| 1 — build now | Darpan uploads the `.xls` through the Daily Sale tile | design |
| 2 — vendor, in parallel | auto-report scheduler, or `up_sale`/`up_saleinfo` | request drafted |
| **3 — do not build** | **Folder watcher on `users\*\report\REPORT_1.XLS`** | *"fallback only"* |
| 4 — do not build | Decrypting the Marg DBFs | unsupported |

**What actually happened: route 3 — the one ranked "do not build" — is the system that exists.**
The resident watcher went live at S195 and every report since has travelled that way. Route 1 was
never built. *"Read §2 as history, not as an open choice."*

**§3.4 — the idempotent per-day upsert, and this is why the feed self-heals.** *"The design does not
need to know which it is."* Parse **every** date section present, **upsert each day by date**, never
blind-append — so re-uploading the same file twice changes nothing and a fourteen-day file corrects
all fourteen. *"A day Darpan forgets to upload is repaired by the next upload that spans it."*

**§3.5 — the file must prove itself before it posts:** each day's bill rows sum to that day's
`DAY TOTAL` · the `DAY TOTAL` rows sum to `GRAND TOTAL` · the bill count matches the footer. *"On
any mismatch: refuse the whole file and name the day that failed."*

**§3.6 PHI** — the patient-revenue spine **reads, never posts**; F-31/F-49 rules; git-ignored before
the first `git add`.

**§3.7 — and this is the standing protocol in one paragraph:** S179 found the Marg report exact on
13 of 13 days, so the adapter should become the primary line source and OCR demoted. *"That is a
change to a live, working app. Per the standing protocol — nothing already live is rebuilt without
explicit OK, and the manual workflow always stays as fallback — it does not happen on my
initiative."* Recommended shape: **run in parallel for one clean period, compare, only then demote.**

> §3.4, §3.5, §3.6 and §3.7 are the **only home** of that material. `S203_MARG_RETIREMENT_LIST.md`
> §3 keeps this document for exactly those sections.

### 10 · The sale-return correlation, measured on nine real credit notes
**`S180_Marg_Feed_Request_and_Flow.md`** · md5 `efef42c53049ec27758489d950398088`

**§1 — what was settled on five real exports, measured not inferred:**

| | |
|---|---|
| Money rule | `cash = CASH column` · `non-cash = NET − CASH`. **Measured: non-cash was 36.9% of net over 5 days** |
| Why not the `D.R.` field | *"It agrees with CASH on **133 of 138 bills** — but the 5 it misses are **split-tender** (`.UPI` with part cash: net 3000 / cash 1000). A label cannot represent a split; the CASH column can."* |
| Completeness test | *"A complete export always ends with a `GRAND TOTAL` row."* Its absence means the export stopped early |
| Cross-validation | **01-08-2026 was exported twice, by different runs. Both gave 37 bills, ₹28,119.00 net, ₹16,411.00 cash. Identical** |
| Patient identity | Marg writes `<phone> <NAME> <clinic id>` — **ID last.** `finance_ingest.split_clinic_id()` expects it **first** and returns `None` for every real Marg line, so all bills would land on WALK-IN. Handled upstream |
| Attribution coverage | of 147 real bills: **77% carry a clinic ID, 71% a phone, 82% joinable by one or the other** |

**§4 — the four design invariants:**
1. **Darpan sees the flags and explains them; only the doctor or Bhawna clears them.** *"He is the
   operator on most days, so if the page ever lets him mark his own exceptions resolved, the control
   becomes a formality."* Kin to D272.
2. **Flag few things, trend everything.** Flag per-bill only above a threshold on **both size and
   proportion** (₹19 on ₹319 = 6% surfaces; ₹3 on ₹500 does not). *"The rate is the real detector:
   spreading discounts across many small bills makes the rate rise rather than fall."*
3. **Two confidence thresholds, not one.** *"For revenue attribution a wrong guess costs a rupee in
   the wrong history; for a discount audit it points at the wrong patient, day and operator."*
4. **The missing-day alarm must be verified live before the sweep is trusted.** *"An unattended
   sweep's failure mode is silence."*

**§4A — SALE RETURNS, DECIDED. Measured on the 9 credit notes in the 6-day sample:**

| | |
|---|---|
| carry at least a name | **9 of 9 — none is anonymous** |
| carry name **and** mobile **and** clinic ID (the standing counter rule) | **5 of 9** |
| correlated back to a prior sale within the 6-day file | **7 of 9** |
| returned drugs also found in that patient's earlier sale | conclusive on one (**6 of 6 items**), partial on three |

*"The two that did not match are a window artefact, not a data failure."* **`CN00154` (−₹1,700, the
largest in the period) carries a clinic ID, a mobile and a name — its original sale simply predates
the file.** So **the lookup runs against the database, not the day's file.**

The design that followed: the counter rule stands and is now *measured* (5 of 9), so it becomes a
staff number rather than an instruction · **reception lookup and next-day reconciliation are the
same index run in opposite directions — build it once** · correlation is clinic ID → mobile → name,
corroborated by the returned **medicine names** · **the flag is not "a return happened" but "large,
and still unmatched after the database has been searched" — the `CN00154` shape** · timing is
next-day, so nothing has to run at the counter.

*"A return is cash out of the drawer with no goods trail unless something checks it. Correlating to
a real prior sale, and to the specific drugs on it, is what makes a fictitious return hard."*

> **⚠ A MISATTRIBUTION, CORRECTED.** **Both `S203_KB_CENSUS_PHASE12` row 51 and
> `S203_MARG_DOC_INVENTORY` §3 attribute §4A to `S180_Marg_Feed_Transport_Design`, and both use it
> as the reason not to retire that document.** They are wrong. Proven by `grep -l 'CN00154'`, which
> returns `S180_Marg_Action_Register.md` and **this** file only; `Transport_Design`'s heading list
> runs §0–§6 with no §4A. Corrected in `S203_MARG_RETIREMENT_LIST.md` §0.3 — *"the reason was
> attached to the wrong file"* — and in the S203 banner on `Transport_Design` itself. **The census
> and inventory rows were not corrected in place** and still carry the error.

### 11 · The action register — V7, and the ceiling
**`S180_Marg_Action_Register.md`** · md5 `599d315625fdf3aca11fa9aa70e6f5b3` · 15-08-2026

**V — VENDOR TASKS, none answered to date:** V1/V2 the two buttons · V3 save the delimiter settings
· V4 separate files · V5 schedule both daily · V6 configure email · **V7 the historical item-wise
ledger, ONE FILE PER MONTH** · V8 enable `up_sale`/`up_saleinfo` · V9 the operator column.

> **⚠ V7 — the one thing that must not be got wrong.** *"A month-to-date range with item detail was
> tested on 15-08-2026. It ran past 44 pages and **the export truncated at day 6 of 15 — silently.**
> The file opened, the rows were there, only the `GRAND TOTAL` was missing. A request for months of
> item-wise history in a single file will fail the same way and will look complete."*
> **One file per calendar month, each ending in its own `GRAND TOTAL` row.** *"'Did we get
> everything?' becomes pass/fail instead of a judgement."*

**Q — eight vendor questions**, including **Q7**: *"Is there a page or line cap on the Excel export?
This is what truncated our month-to-date-with-items file. If it can be lifted, V7 gets much
simpler."* Still open at master v4 §11 item 11.

**O — owner tasks**, including **O3**, and this is what the August cutover rested on: *"Verified Marg
data today covers 01–05 August. **06–14 August was inside the export that truncated and has been
validated by nobody.**"* And the reason it matters: `finance.db` already held the legacy import for
Apr 1 → Aug 13, so for 01–13 August there would be **two independent sources for the same days — a
real reconciliation, not a substitution.** *"Marg has the bills the Sheet did not, so this export is
the thing that can close those gaps rather than merely avoid re-typing them."*

**U — what was built and installed that day**, each with its evidence:

| # | Item | Evidence |
|---|---|---|
| U1 | Sale returns reach the books — the `amount <= 0` filter no longer eats credit notes | installed 15-08 20:38 · **INGEST 50/50** · 121 days intact |
| U2 | **`marg_report.py`** — refuses what it cannot trust | installed 21:14 · **selftest 64/64** offline, 38/38 on the box |
| U3 | `finance_returns.py` + `sale_line_item` — a credit note traced to its sale | **RETURNS 28/28** · additive: adds 6 objects, removes none, re-run a no-op |
| U4 | Expiry + 30-day window rules, as flags driven by settings | in the same module |
| U10 | Two confidence thresholds — 4 digits (111 of 113 real IDs) trusted at 0.95–0.99 | in both modules |
| U11 | `finance_identity.py` — **proposes; never assigns** | **IDENTITY 44/44** |
| U13 | `xlrd 2.0.2` on the VPS | installed |
| U1-fix | Resolving a queued sale RETURN no longer 500s | **SMOKE 179/179**, proved BEFORE 500 / AFTER 200 |

**U11's measured ceiling — the finding, not the feature.** Roster of 94 patients from six days,
against the 36 lines with a name but no clinic ID: **1 corroborated, 2 unique, 2 near, 0 ambiguous,
31 none — 3 of 36 safe to offer.** Of the 31 unmatched, **29 are distinct names**; only one repeats.

> *"That reframes the 82% attribution figure: **it is not a defect to engineer away, it is roughly
> the share of pharmacy business that is clinic patients at all.** The other ~17% (₹19,979 over six
> days) is counter trade. **Do not spend effort on cleverer name matching — the ceiling is set by
> who walks in.**"*

**U7 — a correction to an earlier working assumption, and it is a factor of eighteen:**
```
138 sale bills · with a DISCOUNT value:  84   total  Rs 3,634.00   (~3% of gross)
                · with a DR/CR    value:  16   total     Rs 199.00   ( 0.16%)
```
*"An earlier draft built the flag design around `DR/CR` because that is where the first large single
value appeared. `DISCOUNT` is the real channel by a factor of eighteen."* And the consequence:
*"if ~3% is discounted on six bills in ten, a return processed at list price systematically refunds
more than was taken."*

**Real-data proof of U3, end to end over the six-day export:**
```
CN00158  conclusive    6 of 6 medicines matched, 2 days earlier
CN00152  conclusive    1 of 1        CN00153  conclusive  1 of 1
CN00157  conclusive    1 of 1        CN00151  patient_only
CN00154  none + large_and_unmatched   <- the Rs 1,700 one
CN00155  patient_only  CN00156 patient_only  CN00159  none
```
**Proved on a Marg-shaped file:** before, 2 rows kept and the day attributed ₹2,150.00; after,
3 rows kept and ₹1,750.00. *"The refund was ₹400 — the old code overstated the day by exactly that,
silently."*

**Self-caught during the build, and worth as much as the feature:** *"`marg_report`'s CSV was
emitting **full 10-digit phone numbers**. `patient_ref` stores `phone_last4` and nothing more … so
that was a fuller exposure than both the schema's intent and the standing masking rule."* Fixed;
outputs grepped for any 10-digit string, none found. **Finding candidate F-86.**

**Why not simply allow negative amounts** — the reasoning is the reusable part: `sale_item.amount_p`
is `CHECK (amount_p >= 0)` and SQLite cannot drop a CHECK with `ALTER TABLE`. Removing it meant
create-copy-drop-rename on a live table holding 121 days of real patient data — *"a data migration,
to change a reporting behaviour."* Storing the magnitude with the direction in `service` **touched no
table and no row**; only one view changed. **Decision candidate D314.**

**The four finding candidates minted here, all of which recurred later:**
- **F-85** — forward session-numbering (entry 5's banner).
- **F-86** — *"a reader built for a PHI source emitted full phone numbers because it was written
  against the report's shape, not against the destination schema's masking rule."*
- **F-87** — *"A change was shipped to a test suite that could not be run offline — twice."* Kin to
  F-84. **"RULE: if a test suite cannot be run, making it runnable is the first task, not an optional
  one."* Remedied with an asset (`dev_seed_smoke_db.py`), not a resolution.
- **F-88** — *"A passing `md5sum -c` proves a kit is internally consistent, not that it is the
  intended kit."* A stale download's checksums match its own files. **This is the fault that decides
  entry 54, eleven days later.**

**And the record-keeping owed at close-out, listed in full** — `finance_ingest.py`
`872ec33e…` → `2cd0f264…`, `marg_report.py` NEW `28b47d447cfd966411742055717a5c56`,
`finance_returns.py` NEW `a46a87e6…`, `finance_app.py` `61e36d55…` → `7b62b7ae…`,
`finance_identity.py` NEW `81092e3c…`, the `v_day_attribution` view redefined, `sale_line_item` new,
`xlrd 2.0.2` added — *"none of the above is committed yet … the repo is now two sessions behind."*

*(All hashes in that paragraph are quoted from the document, not computed — the files are on the VPS
and were not reachable.)*

---

## SESSION 183 · 16 August 2026 — five months of data, and the amendment nobody carried

### 12 · The Marg-vs-Darpan cross-check
**`S183_Sanjeevni_Daily_Cash_Design_and_Marg_Findings.md`** · md5 `de4f88b3a48e71c19e708f6a1d274f41`
**Status: DESIGN + EVIDENCE. Nothing built, nothing installed, no live file touched.**

**The need, in the owner's words:** *"Daily cash drawer visibility is a need, not attainable in the
current system."* Three attempts had failed in three different places — the Google Form (friction at
the staff end), the connected Sheet (a chore for the owner to open), GAS emails (the detail got
buried). *"The common fault is that each attempt moved the effort somewhere rather than removing
it."*

**§2 — the control, an owner ruling of 16-Aug:** **the morning Marg export is run by Shavez or
reception staff, not by Darpan.** *"The real gain is segregation of duty: the person who holds the
cash is no longer the person who produces the record of what was sold … Any gap becomes visible
arithmetic rather than an accusation. Nobody has to be suspected for the system to work, which is
what makes it survivable in a small practice."*

**§3 — the daily identity, and the property that decides the export shape:**
```
   Marg NET − HOME-MEDICINE bills = COLLECTABLE = cash + UPI + card
   cash on hand = opening + cash collected − drawer expenses − advances − deposits = closing
```
*"**Cash on hand is a CHAIN.** A missed day breaks it, and every figure after the gap is wrong until
someone repairs it. This is the strongest argument for a month-to-date export: any single run sweeps
up every missed day automatically, so the chain self-heals no matter who was on leave."*
**Medical tenders (owner, S183): cash and UPI only. Never Razorpay. A card is swiped rarely, on the
same ICICI POS machine** — so card + UPI reconcile against one bank source.

**§4 — the source:** 8 exports covering **1 Apr → 15 Aug 2026**, read with the live `marg_report.py`
(md5 `28b47d447cfd966411742055717a5c56`, verified against the box at S183 — the same hash this
archive computed on manojz on 26-Aug, ten days later, on `MargPull\marg_report.py`).
**124 distinct business days, zero overlap, 3,162 bills, 16,118 item lines.**
```
NET      2,748,671.00
CASH     1,980,916.00   (72.1%)
NON-CASH   767,755.00   (27.9%)
```
Every file passed the parser's own arithmetic self-checks.

**§4.0 — THE DECISIVE CROSS-CHECK, and this is the entry the current documents do not carry.**
The 121 legacy days already carry Darpan's own Google-Form declaration, imported at S179. Joining
that against the Marg export on the **119 shared days** gives **two fully independent records of the
same days.**

| Comparison | Marg | Darpan | Verdict |
|---|---:|---:|---|
| **Day total** | 26,54,543 | 26,47,321 | **agree to 0.3%** — 118 of 119 days within ₹2,000 |
| **Cash figure** | 18,99,768 (72%) | 17,67,393 (67%) | **Marg overstates cash by ₹1,32,375** |

> **Two conclusions, both load-bearing:**
>
> 1. **Marg is authoritative for the TOTAL and only the total.** *"Independent agreement to a third
>    of a percent means the feed is trustworthy for revenue and the historical filing was honest."*
>    The single day over ₹2,000 apart is **12 June** (Marg 23,252 vs Darpan 14,765, +8,487) —
>    *"isolated, worth one look, not a pattern."*
> 2. **"Marg's CASH column must never be used as the cash figure. It is wrong by ₹1.32 lakh over the
>    period. The cash/UPI split can come only from Darpan's declaration, arbitrated by the bank.
>    This is the empirical proof that the human-declares-the-split design is necessary, not ceremony
>    — the shortcut of trusting Marg's cash column would have been ₹1.3 lakh wrong."**

**And it gave the variance alarm a measured threshold rather than a guessed one:** a live day whose
Marg total and Darpan-declared total differ by more than **~₹2,000** escalates to the owner. **118 of
119 historical days clear that bar.**

**§5.2 — HOME MEDICINE, which is the cause:** **20 bills · ₹24,413 · Marg records every one as FULLY
PAID IN CASH.** `HOME MEDISUN` 14 bills ₹16,597 · `HOME MEDICINE` 6 bills ₹7,816. These are billed
and never collected at the counter. **How Darpan handles it today (owner, S183): he deducts the
home-medicine cash in his paper copy, and the NET cash is what carries into the Google Form.**
*"That is why the §4.0 totals still reconcile to 0.3% — his declared figures already have
home-medicine removed."*

Three rules this forces: home bills subtracted from **both** the day total and the cash figure
before any drawer comparison · detection by a **configurable vocabulary list, never hard-coded** —
*"two spellings already exist in five months, and a third will appear"* · **every excluded bill
listed on the day's view** — *"a bill that vanishes silently is worse than one that reconciles
wrongly, because nobody can see it to argue with it."*

> *"The new system must do that deduction automatically … Left undetected it would manufacture a
> shortfall against someone who did nothing wrong, the fastest way to destroy trust in a new
> system."*

**§4.1 — two practice changes, visible in the data:**

| Month | Bills | Patient identity captured | Cash share |
|---|---:|---:|---:|
| Apr 2026 | 702 | **0%** | 86% |
| May 2026 | 677 | **0%** | 73% |
| Jun 2026 | 718 | 33% | 63% |
| Jul 2026 | 710 | 87% | 70% |
| Aug 2026 (to 15th) | 355 | 82% | 66% |

**Patient identity capture began on 19 June 2026.** Not one bill before that date carries a phone or
a clinic ID. 19-Jun = 30%, 20-Jun = 85%, then 75–100%. *"A practice starting and bedding in within
two days."* **Consequence: roughly 1,700 bills from 1 April to 18 June have no patient identity at
all and will attribute to WALK-IN. This is not a fault and is not recoverable — it is simply when the
practice began."*

**§4.2 — the 100%-cash window, SETTLED.** 21 April → 6 May 2026 · 14 trading days · 364 bills ·
₹3,03,035 · 99.2% labelled cash, with clean edges on both sides (20-Apr 87% cash, 7-May 77% cash).

> **SETTLED by the §4.0 cross-check — no memory required.** Darpan's own filing declares
> **₹84,613 of UPI across those same 14 days** that Marg labelled cash (25-Apr: Darpan 51% UPI;
> 2-May: 58% UPI). *"So the window was **not** cash-only — UPI was collected and Darpan recorded it
> correctly; **Marg simply stopped writing the UPI split into its CASH column for two weeks.**"*
>
> **The paragraph immediately below that block, in the same document, still reads:** *"At the 31.3%
> non-cash rate every other day runs at, roughly **₹95,000** of that window is sitting mislabelled as
> cash. That is an estimate from a rate, not a measured fact,"* and *"The question to ask is 'what
> changed on 21 April?'"* — **which §9 then records as ANSWERED.** Both texts are left standing in
> the original. **That is correct F-23 practice** (the superseded reasoning is struck, not deleted),
> and it is recorded here so a reader who lands mid-document does not take the ₹95,000 estimate for
> the answer. **The measured figure is ₹84,613.**

**§5.1 — PROCEDURE bills: nothing to build.** Ten bills across five months, and **Marg already zeroes
them itself** (`gross 851.15 · DR/CR −850.39 · NET 0.00 · CASH 0.00`). *"No subtraction rule is
needed. One less thing to build, and one less thing to get wrong."* Noted for the record: **`DR/CR`
therefore carries two distinct meanings** — ordinary round-off, and full write-off of a non-charged
bill. **Anything that interprets `DR/CR` must expect both.**

**§5.3 — credit notes:** 168 bills, −₹56,561 across the five months, already negative, already
netted under D314. What is owed is a **display surface** — the owner asked for returns shown
distinctly, not merely netted away.

**§7 — a correction worth as much as the findings.** Six of the eight exports are genuine
Excel-2007 `.xlsx`; `marg_report.py` read via `xlrd 2.x`, which handles legacy `.xls` only. *"The
first conclusion drawn was that an Excel round-trip had destroyed the patient identity in four
files. **That was wrong.**"* Two of the six carry identity perfectly (69% and 85%) — consistent with
their dates being after 19 June. The missing identity is §4.1's practice change, not a conversion
artefact.

> **The lesson, and it nearly cost a wrong recommendation:** *"the arithmetic self-checks passed on
> every file, and that was read as 'the data is sound.' **The self-checks validate the money columns
> and say nothing whatever about the description column. A green light is only green about the thing
> it checked.**"* Kin of F-95 and one level up from F-88.

**§8 — build status:** B1 the `.xlsx` reader **BUILT + PROVEN** (new `marg_report.py` md5
`829f4344df6e086510bb0fb6112ecb77`, quoted from the document; `.xls` path byte-for-byte unchanged;
selftest 38/38) · B2 the `marg_export` column map — **7 rows, not 8: `phone_last4` is barred by the
`our_field` CHECK** · B3 `marg_backfill.py` v2 · B4–B9 to build.

**§6 — what the Marg export can and cannot tell us:** it answers what was sold per bill per item
(16,118 lines), the day total *and proves its own arithmetic*, and cash vs non-cash. **It cannot
separate UPI from card within non-cash**, and it can identify uncollected bills **only** via the
home-medicine vocabulary. *"So Darpan's remaining job is small and honest: split the non-cash into
UPI and card, declare his drawer, and post expenses and advances. Everything else arrives already
proven."*

> ## ⚠ THIS ENTRY IS THE LARGEST LIVE GAP THE ARCHIVE FOUND
>
> **This document is not superseded, is not retired, and is not carried.**
>
> Verified by grep against `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v4.md` (md5
> `df290c6f5cbb870af6c232db21bc2219`) on 26-Aug-2026:
>
> | searched for | occurrences in master v4 |
> |---|---:|
> | `S183` | **0** |
> | `home medi` / `HOME MEDI` | **0** |
> | `Darpan` | **0** |
> | `1,32,375` or `132,375` | **0** |
> | `84,613` | **0** |
> | `0.3%` | **0** |
>
> Master v4 §4.4 states the money rule from entry 1 — *"cash = the CASH column"* — flatly, marked
> `[S179 report analysis, verified against a real day: CASH column total 193,412]`, **with no
> mention of the ₹1,32,375 overstatement, no mention of home medicine, and no mention that the
> cash/UPI split is a human declaration arbitrated by the bank.** S183 is absent from the master's
> §10 "current and authoritative" list and absent from its "must be preserved, and are at risk"
> list. It appears in the S203 census and inventory only as a row.
>
> **Both are true of different questions**, and that is precisely why the omission is dangerous: a
> reader of the master alone would take Marg's CASH column as the drawer figure, which S183 measured
> at ₹1.32 lakh wrong over 119 days. **This is a MECHANISM document repeating a fact whose owner
> corrected it** — a live instance of the precedence map's own §1.2 rule.
>
> **Recommended, and not done here:** the money rule in the current file gains one paragraph naming
> this document and the home-medicine deduction. **Nothing in this archive edits the master.**

---

## SESSION 195 · 21–23 August 2026 — the longest build session, and the cipher

### 13 · The optimistic encryption note — 21 August
**`S195_Marg_dbf_Encryption_Finding.md`** · md5 **`2053ab46f327606dac36b9fc38d9cfc4`**
*(and its un-annotated project-knowledge twin, retained beside it as
`S195_Marg_dbf_Encryption_Finding.md.from_projectkb_unannotated`, md5
`805f71d7bf5a1cc568dc9d896fdad4b2`; the copy in `deploy_kits/KB_canon_S197fold/filed/` is a third
byte-state, md5 `2b4525492549a644ad97e3bb198d4137`. **Three files, three hashes, one name** — all
computed here.)*

**Banner, 26-Aug: ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT.**

**What it established that still stands:** the supported channels were ruled out first, with the
vendor and by research — **the API Gateway is paid cloud only · there is no ODBC · Tally XML is
accounting only and carries NO item lines.** *"So item-level daily data must come from either the
REPORT export (Method B, already working, has items) or decrypting the tables."* And the mechanism:
Marg **`bsVault` → Chilkat32.dll**; research refs XOR-KPA (Didier Stevens `xor-kpa`, NVISO),
bsVault↔Chilkat (Marg care #49348).

**What it claimed, and this is the superseded part, quoted in full so the supersession is visible:**

> *"Cipher = **global repeating-key XOR, key length 256 bytes** … **CONFIRMED XOR**: using the DBF
> header's known-zero bytes (offsets 12–27, 30–31) as the key there, the version byte decrypts to
> **0x30** (valid VFP) and record length to **256** — both correct. **So it is genuinely breakable.**"*
>
> Why frequency analysis stalled: *"record columns are numeric/coded fields (e.g. `dis` stores an
> item CODE → `pro.c18`, not the drug name), so they are NOT space-padded — the 'most-common byte =
> space' assumption fails on ~16/18 test columns."* Resume plan: **known-plaintext crib-dragging**
> against a matching `REPORT_x.XLS`, or **a debugger dump of the 256-byte key from
> `MARGWIN.EXE`/bsVault on the Marg PC (one-time, most reliable).**
>
> **Status: PARKED by owner 21 Aug** to prioritise the AHK auto-generation and guard-and-send.

**SUPERSEDED THE SAME SESSION** by entry 14. The `filed/` copy and the S203 copy carry the four-line
supersession note; the project-knowledge copy never did — **and that omission caused a real error
five days later** (entries 50, 51, 54).

### 14 · The thorough negative — 23 August. THE WINNING DOCUMENT.
**`S195_Marg_decrypt_partial_key.md`** · md5 **`3f83f1594fcb22e29b6aba0458e6574b`**
*(identical in `deploy_kits/S203_MARG_CANON/` and `deploy_kits/KB_canon_S197fold/filed/` — verified
here by hashing both.)*

Two background workflows attempted the crack on 21 Aug. Its own first line: *"Corrected verdict
below — **it supersedes the earlier optimistic 'crackable via crib-drag' note.**"*

**Four independent attacks over ALL 27,246 records and ALL 7 co-encrypted `*.c18` files:**
1. per-column printable/charset attack
2. space-pad / null-pad fill hypotheses + brute single-byte fill
3. cross-file CHAR-witness union for a global key — **pinned only 54 of 256 columns**
4. DBF zero-crib + displacement-chain reconstruction

**All four failed on the record fields.** The decisive negatives, under the header-verified partial
key and every derived key:

- **0** occurrences of bill numbers (`A00nnnn` / `CN00nnn`) anywhere in any 256-phase.
- **0** occurrences of `"2026"` in any phase; **no all-digit columns.**
- Field descriptors do **not** decode to valid VFP types — `dbfread`: *"Unknown field type"*.
- Record columns are coded/binary (~73% dominant byte, ~110 uniques per column) — not space-padded
  ASCII, so field-type charset pinning has no target.
- **All 7 files share an identical 19-byte header prefix despite sizes 809 B … 13 MB.** *"Under
  simple XOR of a standard DBF the prefixes would differ (per-file date, record count, header
  length). **Identical prefixes falsify 'XOR-of-standard-DBF'.**"*

**Conclusion:** there **is** a 256-byte repeating XOR *period* (autocorrelation confirms it), but the
plaintext under it is **not a standard DBF** — Marg applies a fixed wrapper plus a per-record or
non-XOR transform. **"Only byte0 (0x30) and rec_len (256) ever 'verify', and those are consistent
with coincidence/wrapper, not a real decrypt."** — i.e. the two "confirmations" entry 13 rested on
are named here as the coincidences that made it look breakable.

**Decision (recommended): RETIRE remote decryption.** *"Method A's only value-add over Method B was
avoiding the GUI. But Method B already yields bill-wise sales WITH item/drug lines, daily … Do not
spend more remote effort on the cipher."* The only route left is **a runtime debugger dump of the key
AND algorithm from `MARGWIN.EXE`/bsVault on the Marg PC — heavy, uncertain RE.** The encrypted
samples are kept on manojz (`…\_to_delete\margdata\*.c18`, gitignored) in case that is ever done.
Workflows recorded as resumable: `marg-dbf-decrypt-wf_e765f56d-53e.js`,
`marg-dbf-decrypt-finish-wf_728a2ed1-88d.js`.

> **WHY THIS DOCUMENT MATTERS BEYOND THE CIPHER.** It was **repo-only. It has never been in project
> knowledge.** So a search of the store that sessions actually read found only entry 13 — and on
> 26-Aug master v2 §4.3 duly asserted *"genuinely breakable … parked, not because it failed"* as
> current fact. **The document that would have prevented the error existed, was correct, and was in
> the wrong store.** Caught at entry 51; corrected at entry 53. This is the whole case for entry 54.

### 15 · The guard, the email agent, and a document that exists in two states
**`S195_Email_Hardening_and_Marg_Guard_BuildState.md`** · md5 **`bf1837b76a39e8d32ff80ab6d980c2aa`**
*(annotated, the one in force)*
**`…md.from_projectkb_unannotated`** · md5 **`e1420f1190d40007b5cf3b6e54f9642c`**
*(the project-knowledge copy, retained beside it)*
*(the `KB_canon_S197fold/filed/` copy is md5 `b60efae40f7ed732ba621967d4f700b6` — the annotated body
without the S203 banner. All three hashed here.)*

**Banner, 26-Aug: ⚠ SUPERSEDED — the guard chain described here is not on the medical PC at all.**

**⭐5 email-agent hardening — kit `deploy_kits/S195_EMAIL/`.** `email_agent.py` → md5
`2c191082c27cb9a4acc52bb0e068aa2b` (quoted). (a) "Answered" now tracked by a **Gmail label**
`clinic-agent-done`, not the read/unread flag — server-side raw search, per-message re-check, subject
fallback, **label applied only AFTER a reply is sent**, so a `Q:` opened before the poll is no longer
skipped and nothing is answered twice. (b) **Always reply, even on error** — *"a message is marked
done only when a reply truly left."* → *"this hardened build became live pin `e535c4f8…` after the
folded-subject fix later in S195."*

**The Marg guard — kit `deploy_kits/S195_MARG/`.** *"The 'fail visibly, never a silent partial' gate
in front of the existing sender."*
`guard_and_send.py` (md5 `6c248d5712731256c576722ad85f3ef1` — **verified here against the kit copy
in this folder, identical**) **reuses `marg_report.py`** (bundled, an exact copy of the live
`finance/marg_report.py` md5 `28b47d447cfd966411742055717a5c56` — **also verified identical here**)
*"so its judgment == the server's."*

**Exit 0 only when** the file is single-day Detail, ends with `GRAND TOTAL :`, arithmetic balances,
and the business date is sane. Date rules `--expect any|today|yesterday|YYYY-MM-DD`; `any` allows a
single-day file up to `--max-age-days 3`, still blocking truncated / Summary-1 / range / stale.
On GREEN it copies to `Sent\` **named by business date** (`REPORT_2026-08-19.XLS`) per the owner's
request of 21 Aug; **incomplete files are never archived**; `SEND_TO_CLINIC.bat` untouched.

**Validated against REAL exports:** the 17/18/19-Aug SENT files and users 50018/61376 pass with the
right date, bill count and split — *"confirmed 61376 = UPI-reclassified: 19-Aug ₹44,120 day, cash
18,790 / non-cash 25,330 vs 50018 all-cash"* — and the 1–15 Aug and 14–15 Aug ranges, a synthetic
truncated file, an arithmetic mismatch, a Summary-1 and a stale file are **all refused**
(8/8 suite + real-file checks GREEN).

**Access facts confirmed S195:** `D:\dr-manoj-git` mounts read-write · **`Z:\MARGERP` is list-only —
full metadata, contents unreadable** · delivery mechanism proven: kit tar → SendUserFile →
`device_commit_files` → `device_bash` extract + md5 verify → owner `PUBLISH_ALL.bat` → box.

> **⚠ THE TWO COPIES ARE NOT THE SAME DOCUMENT, AND NEITHER IS A SUPERSET.** Diffed here on 26-Aug.
> The **annotated** copy carries three later outcome notes the project-knowledge copy does not:
> the `e535c4f8…` live pin · *"Superseded by the medical-PC leg's portable-Python packaging"* ·
> *"(Retired — encryption negative, `S195_Marg_decrypt_partial_key.md`.)"* on Method A.
> The **project-knowledge** copy carries three facts the annotated copy does not:
>
> - the AHK macro's blocked input, in full: *"one screen recording of a real Marg export on medical
>   **(menu → Report Type=Detail → date → save REPORT_1.XLS → keys used)**"*;
> - Method A's stated purpose: *"**truncation-proof regeneration with a real per-row DATE column**"* —
>   i.e. the decryption route existed to solve V7, which no other document says;
> - *"**Z: network drive contents still cannot be staged — 'Could not stat' confirmed S195**; local
>   folders read fine."*
>
> **Neither copy is a superset. Both are retained side by side in the folder** (entry 54). The
> reconciliation resolved which one is *in force*; it did not merge them. **The three facts above
> live only in the sidecar.** Recorded here so they survive whatever happens to the sidecar.

### 16 · The medical kit — six files, and two of them exist only here
**`S195_medical_kit/`** — every hash computed here:

| file | md5 |
|---|---|
| `SETUP_S195_MARG.md` | `cc4416dc8f22a998b0a18dd42c4d8b99` |
| `GUARD_AND_SEND.bat` | `4d66ff96aeb7f4691b88806b9d291c16` |
| `SETUP_CHECK.bat` | `990a6e120e7817b83fe969ee35df0bb6` |
| `guard_and_send.py` | `6c248d5712731256c576722ad85f3ef1` |
| `marg_report.py` | `28b47d447cfd966411742055717a5c56` |
| `marg_export_macro_v2.ahk` | `acec9ae9c1417e2fda8222e41e0628aa` |

**`SETUP_S195_MARG.md`** carries the instruction that never worked: *"**Install Python** (once) …
tick 'Add python.exe to PATH' … `pip install xlrd==1.2.0`"*. **It was never done against the portable
interpreter**, which is why the medical guard could never run (entries 26, 33 C5). `SETUP_CHECK.bat`
is the later, correct shape — it finds the bundled `pyportable\python.exe` **first** and says
`RESULT: NO_PYTHON` with *"the Microsoft Store stub does not count"* if it cannot.

**`marg_export_macro_v2.ahk`** is the calibrated AutoHotkey v2 macro, and it holds something no
document repeats: **the screen coordinates captured on the medical PC on 21-Aug-2026** —
`CFG_TILE_X := 1804, CFG_TILE_Y := 941` (the Daily Sale tile) · `CFG_RTYPE 1132,850` (Report Type) ·
`CFG_WITEM 984,992` (With Item Deta.) · `CFG_VIEW 641,1414` · `CFG_EXCEL 1391,1254` — and the flow
they encode: *"1. Click the 'Daily Sale' tile · 3. Report Type → Detail · 4. With Item Deta → Yes ·
5. View → Enter ×(1-2) · 6. Excel button → Enter ×(few)."* It targets
`D:\MARGERP\users\61376\report\REPORT_2.XLS` and is shipped with `RunGuard := false`. **PARKED.**

> **STATUS: the kit is preserved; the installed instances are gone.** Measured 26-Aug:
> `GUARD_AND_SEND.bat`, `guard_and_send.py` and `marg_report.py` are **absent from the medical PC**
> and survive there only in manojz's never-purging mirror, dated 21-Aug. **Two of the six files are
> absent from `deploy_kits/S195_MARG/` and now exist only in this folder.**

### 17 · The final pins, and the token crisis
**`S195_FINAL_PINS.md`** · md5 `e8dda44c8aa13af10513e3d1638ddb4e` (post-banner; pre-banner
`c368c43fedb41786fcade130f0ea0931`, quoted from the pointers document) · **22 Aug 2026, 02:05 IST**

**Banner, 26-Aug: ⚠ RETIRED.**

**The crisis, in its own words:** *"`FINANCE_MARG_TOKEN` now declared in
`/etc/systemd/system/clinic-finance.service`. **This was the crisis**: it had lived somewhere
transient, so any restart killed the sender. Now durable."*

VPS at close: `finance_app.py = e3a4ba79c2e060bcebe11c075bdbbc7b`, SMOKE 573/573, with the day's
chain recorded: `d2863c30 → 85df28fe → f25ed489 → fe596b29 → 89ab3e8e → e3a4ba79`. Backups: cron
`5 1 * * *`, verified nightly, **restore proven (126 days, 3141 items)**.

Medical PC: `SEND_TO_CLINIC.bat` — *"untouched proven v3 `e19a8a777ac22fe75a242f1eb9762185`."*
**That is the one durable line in the document**, and on 26-Aug it was independently re-measured on
the machine and carried into master §3.2 — *"so that fact now has two sources for the first time."*
Also: `find_sale_report.ps1` in its own file, because *"embedded in a batch if-block, cmd mangled
the escaped pipes and it silently found nothing."* And `marg_export_macro_v3.ahk` — PARKED, with the
one-line next step: check `AutoHotkey64.exe`'s FileVersion; if 1.x, install v2.

**Two test lessons, recorded as F-106 shape, and they are the reusable part:**
> 1. *"Three checks asserted the month's non-cash was EXACTLY `"350.00"` with exactly 2 heads. True
>    only while no real no-payment bills existed. Darpan filed the first (₹3,000, 20 Aug) and all
>    three went red **with no code change.**"* Now they assert the rule (`>=`, "included"), and the
>    tile check asserts the tile **agrees with** the month endpoint — *"stronger than the frozen
>    number it replaced."*
> 2. *"The router selftest used a real report name as its 'unknown' example and went red the moment
>    that report was onboarded."*
>
> **"Tests must describe rules, not snapshots."**

And the S195 severity ruling that governs the health page to this day: **"Flags are `info`, never
`warn` — they always exist, so letting them drive the tile would light it permanently and turn the
warning into wallpaper."**

Owner actions at 02:05, recorded as they stood: apply the 21-Aug push (37 bills, ₹49,181) ·
**rotate both tokens — cron + Marg were exposed in chat** · **18 Aug: total 23,879 → 25,176** (*"his
copy AND Marg agree; the entry was short ₹1,297 — he counted right"*) · 17 Aug ₹20,000 salary advance
to the Staff Ledger · after which the drawer should read **₹175,201** = Dr Bhawna 1,56,235 + owner
18,963 + Darpan's real ₹3.

### 18 · The watcher goes live — and the document that is still labelled "sole reference"
**`S195_Medical_Watcher_LIVE_Reference.md`** · md5 `885090ab946b61e7b5a990a14a190a15`
**(unbannered by design — it is manifest-pinned; editing it would halt Phase 0.)**

**"Status: WORKING, confirmed by capture test."** 23-Aug, final.

**The hidden villain, and the standard that came out of it:**
> *"The medical PC has **no system Python** — `python.exe` on PATH is the Microsoft Store **stub**
> that prints 'Python was not found' and exits. Every launch that used bare `python`/`pythonw` died
> instantly and silently."*
>
> **Task #10, the standing standard:** *"All clinic PCs use bundled `pyportable\python.exe`, called
> by full path — never a system install. Portable = version-pinned, zero-install, no admin,
> copy-the-folder to a new PC. **Ship pyportable with every medical/lab/reception kit.**"*

The install as it then was: watcher `D:\SendToClinic\marg_watch.py` (stdlib only), autostart
`%APPDATA%\…\Startup\**MargWatcher.cmd**` over **two** folders, *"no admin, no Task Scheduler (the
earlier `Register-ScheduledTask` approach failed — task 'Marg export watcher' never registered;
abandoned)."* Router: five report types self-classify. Two known-broken things: **manojz cannot push
to medical** (read-only share), and RDP copy-paste, since fixed.

And the PowerShell detail that later became a trap: *"`$args` is reserved in PowerShell — use `$al`.
Pass args as an ARRAY, not one string."*

> ## ⚠ NEARLY EVERY OPERATIONAL CLAIM IN THIS DOCUMENT IS NOW FALSE — and one is destructive.
> Measured 26-Aug (entry 44, claims #79–#90):
>
> | it says | measured truth |
> |---|---|
> | *"This doc is the single reference"* | **superseded** by `MARG_PIPELINE_REFERENCE_v1`, which says so in its own header |
> | watches two folders | **three** — `medical_agent.py:51-52` and the live heartbeat |
> | *".txt is ignored — the watcher only takes .xls/.xlsx"* | `EXTS = (".xls", ".xlsx", ".pdf")` since S201 |
> | named `<stamp>__<slot>__<md5>.xlsx` | **wrong twice** — it is `digest[:8]`, and the original extension is kept: `20260826-081436__REPORT_2__813fd43c.XLS` |
> | autostart `MargWatcher.cmd` | **no such file exists.** The only startup entry is `MargAgent.cmd`, running the **agent**, which launches the watcher as a child |
> | *"Router — five report types"* | **8 signature blocks across 6 types**, plus `DOCUMENT_PDF` hard-coded — a seventh archive type with no signature |
> | its restart recipe `Stop-Process -Name python,pythonw` | **DESTRUCTIVE IF FOLLOWED.** `pythonw` is the **agent**. This kills the supervisor as well as the watcher, and **nothing restarts the agent until the next logon** — the heartbeat stops, kit updates stop, watcher restarts stop, *"and the PC looks perfectly normal meanwhile."* PowerShell 5.1.19041.6456 is present, so the recipe still runs exactly as written |
>
> **And it is STILL PINNED IN THE MANIFEST as *"SOLE reference for the Marg capture pipeline"*.**
> Raised as `S202_PENDENCY_AUDIT` **N3**, precedence-map **C5**, system-map **C-2** — **open at every
> one of them.** *"Two canonical documents each claiming to be the reference."* The fix is a label
> change on the manifest row, **not an edit to this document** (F-184, F-107). Its own kit file
> `READ_ME_FIRST.txt`, sitting one folder away in the live mirror, contradicts it on both counts
> — *"registers a logon task ('Marg export watcher')"* and *"Needs Python 3 (already on this PC)"*.

### 19 · The S195 close summary
**`S195_Close_Summary_FINAL.md`** · md5 `1e8b97efbebd4dc67fd8542d9ac3dc4d` (post-banner; pre-banner
`b1bcdceec46223c08783782c56092824`, quoted) · **RETIRED 26-Aug — folded into Archive §S195.**

*"The longest build session to date."*

**Faults found and fixed — the session's real lessons, quoted because they are the pattern list:**
- **Credit-note sign counted twice in 2 of 3 readers** → *"the 18-Aug '23,879' phantom that nearly
  reversed a correct correction."*
- **Repeated rollbacks, one root habit:** *"asserting against shapes not printed — invented fixture,
  guessed JSON, self-matching search string, reserved `$args`, mis-diagnosed encoding. Remedy
  adopted: `pyflakes` + `tools/check_late_locals.py` + `tools/check_row_keys.py` before packaging any
  kit; **never assert against an unprinted shape.**"*
- **The 8-of-90 blind monitor** — *"a clean checklist meant no bank data, not agreement."*
- **The medical PC had no system Python** — the whole watcher-install saga.
- **manojz cannot write to medical** — *"every 'push to medical' feature assumed an OS-forbidden
  write."*

**Owner decisions at close (22–23 Aug):** token rotation **PARKED to next session** (both exposed
tokens still live) · the 17-Aug ₹20,000 to the Staff Ledger **only against a written, scanned
application from Darpan** · **the medical delivery pipe: the owner will install Google Drive for
Desktop on the medical PC**, so ToMedical becomes a mounted-drive local copy and *"the medical-side
puller build is DROPPED."* — the decision the whole S201 delivery channel later rested on.

**⚠ The canon fold-in debt, and it is worth quoting because it is the same reasoning as entry 41:**
> *"Sessions 193, 194, and this 195 exist as standalone `S19x_*` close docs, **not yet folded** …
> Per D247/F-23 discipline, **bolting three sessions of change onto a stale canon at the tail of an
> exhausting build session is exactly how a stump/delta fault gets made.** Recommended: a dedicated
> fold-in (EOS-light) session … **Flagged so it is not lost — this is the honest state, not a
> skipped step.**"*

### 20 · The retention policy — a draft that is still a draft
**`Clinic_Source_Data_Retention_Policy_v1.md`** · md5 `90831162f985359b69725b1dc874e679` · S195,
21 Aug 2026 · **"draft for owner approval"**

**Sizing, measured not estimated:** 8 real Marg sale exports, **average 68 KB, compressing 74%**.
6 types/day over 8 years = **314 MB zipped**. *"Storage volume is a non-issue … **The thing that
actually scales badly is file count** — 6 × 365 × 8 ≈ 17,500 loose files, which makes any sync client
slow and any folder unbrowsable. Policy should optimise for file count and findability, not bytes."*

**"VPS: never."** *"Not because of size, but because it reverses a deliberate design.
`api_marg_push` writes the upload to a temp file and deletes it in a `finally` block … and an
applied push has its `parsed_json` set to NULL, 'no PHI at rest'. Storing exports on the VPS would
undo that on purpose."*

**Rules:** source exports **8 years** · `index.csv` **permanent** *("it is the ledger of what was
ever received")* · current FY loose, closed FYs **one zip per month per source** · `_spool` purge
after 7 days · `_REFUSED`/`_UNKNOWN` purge after 90 days keeping only the `.txt` reasons · medical
`Sent\` purge at FY end. **"Not tax advice … Confirm the retention period with your CA."**

**§6, and it is the honest line in the document:** *"`finance.db` **is the books**; the exports are
only the source documents. Its backup is a separate and higher-priority concern … **An archive of
exports is no substitute for a database backup.**"*

> **⚠ STILL A DRAFT, AND WRONG THREE WAYS** (system map **C-7**, precedence map **C13**):
> the working copy path is given as `D:\MargArchive\` (live: `D:\Downloads\margsync\MargArchive\`) ·
> its **"single highest-value step"** — putting the archive *inside* a Drive-synced folder — **was
> built instead as `robocopy`, which excludes `_spool` and `_outbox`**, so the pending-send queue has
> no offsite copy at all · medical origin is given as `Sent\` against the live `_captured\`.
> *"Correct the three path/mechanism errors **before** it is approved, not after."*
> It is also **the only canonical document that names Labmate**, and only for export retention.

### 21 · The Auditor is seeded
**`AUDITOR_SEED_v1.md`** · md5 `b4e349cbcf01547ff774a7c3c434bb21` · ideated S195, three passes,
22-Aug-2026 · **manifest-pinned, Tier 1**

**The role:** *"You are the **Auditor** … deliberately a different role from the builder that
constructed it. **You find; you never fix.**"*

**Why the separation exists, in its own words:** *"in S195 the builder shipped five consecutive
faults, every one caused by asserting against a shape it had not looked at — an invented test
fixture, a guessed JSON body, a search string that matched itself, a variable collision, a
mis-diagnosed encoding. **Reading code caught none of them; printing the actual shape caught all of
them.** The auditor is the institutionalisation of that lesson: **no claim without primary evidence
you generated in this session.**"*

**Read order — INVERTED from the builder's Phase 0, on purpose:** verify the manifest, then go
**straight to code and data** and build your own map, and **only then** read the narrative docs **as
a diff against it**. *"Where doc and map disagree, that disagreement is a finding regardless of which
side is wrong."*

**Two surfaces.** **A · the software estate**, organised by fault class, all observed live in S195:
*two-copies-of-a-rule · monitoring that cannot see · silent drops · partial-state masquerading as
complete · authz drift · doc-vs-reality drift · secrets in transit and at rest · vacuous tests.*
**B · the system of work**: aging of open owner actions · single-person gates · single-machine hubs
*("manojz is publisher + puller + mirror + offsite at once")* · **whether each documented manual
fallback has ever been rehearsed.**

**Five slices**, rotating weekly. Slice 1 is the **CALIBRATION RUN**, with the sharpest instruction
in the whole document set: *"Five faults were found and fixed here in S195. **An auditor that finds
nothing notable in this slice is broken; report yourself, not the estate.**"*

**Rules of evidence:** primary evidence + reproduction + a *"how would we know today"* test +
severity = **money-at-risk × silence** · **every run re-executes the previous run's evidence; a
finding that no longer reproduces is demoted, not carried** · *"A clean result must state coverage:
'clean, of the 60% I could exercise' — never bare 'clean'"* · *"Success metric: did this run change
what happens next week — not finding count. **Volume is audit theatre.**"*

> **⚠ THIS DOCUMENT IS MANIFEST-PINNED AND KNOWN-WRONG.** Under *Rules of evidence* it says
> **"Register format: continue the existing F-## series (Fault_Action_Register)"** — and **S196
> overrode that**, which is why the Auditor's run emitted an **AF-** series instead. The seed still
> instructs the live weekly Auditor to do the thing that was overruled. *"An F-23 situation for the
> owner's ruling, not a silent edit. **Raise it; do not patch it.**"* Open at precedence-map §C and
> at entry 47.

---

## 24 August 2026 — the Auditor's only run

### 22 · AUDIT RUN 1 · slice 1 · the cash trail
**`AUDIT_RUN_2026-08-24_slice1.md`** · md5 `17746ec35727c14e2c5b173c9235fce7`

Read-only throughout; no VPS or live database reached (the unattended rule). **No F-numbers minted —
the F-series fork rule.**

**Calibration verdict up front:** *"slice 1 produced **2 high, 2 medium, 2 low candidates**, each
with primary evidence generated this run (two by executing the real code, one by an empirical
reproduction of the failure). **The auditor is not returning a bare 'clean' on the slice that yielded
five faults in S195** — the calibration criterion is met."*

**Phase 0 (auditor variant):** fresh anonymous clone · `KB_canon_S198close` `md5sum -c` **12/12 OK,
exit 0** · all five Tier-0 pins recomputed and matched · **live-pin recoverability: an md5 index of
every file in the repo and inside every kit tarball (LF-normalised variants included) recovers
44 of 45 pins byte-exact.** *"The audited bytes are therefore the LIVE bytes, recovered by hash
(D188), not the stale working trees."*

**AF-1 · HIGH — the Marg sender can report "ACCEPTED" for a report that never left the PC, then
permanently refuse to resend it.** `SEND_TO_CLINIC.bat`, kit `S187_M1a`.
*Mechanism:* the sender writes the reply to `last_response.txt` via `curl -o`, then decides success
by `findstr "ACCEPTED-FOR-REVIEW"`. **`curl` does not touch the output file when the connection
fails** — so on any network failure the file still holds the **previous** run's reply. The batch then
prints ACCEPTED, logs ACCEPTED, **and appends the file's md5 to `sent_hashes.txt`**, after which
every future run skips this exact report as ALREADY SENT.
*Primary evidence, reproduced that run with curl 8.5.0:* seeded `last_response.txt` with an ACCEPTED
body, ran the batch's exact curl invocation against an unreachable host → **curl exit 56,
`last_http.txt` = `000`, `last_response.txt` unchanged** — the findstr match would fire.
*"The HTTP code is captured but never consulted before the ACCEPTED check."*
*Severity:* *"a full day's pharmacy staging (₹20–30k typical) delayed indefinitely, behind a success
message … **the cure (deleting one line in `sent_hashes.txt`) is written nowhere.**"*
*Fix shape:* `del last_response.txt` before each curl, and gate the ACCEPTED branch on `HTTP == 200`.

**AF-2 · HIGH — the save-time "does your total match Marg?" check has never fired: born dead at
S195.** `_marg_total_for_date()` (~line 3843) scans for days keyed `business_date`/`net_p`; the only
writer of `parsed_json` stores `date`/`expect`/`lines_csv`/`items_csv`. **The reader can never match
a real staged push.**
*Primary evidence, executed:* staged a payload through the app's own DDL with the writer's exact key
shape, called the **real** reader → `(None, None)`. Re-wrote with the reader's keys →
`(40000, 'the Marg report received')`.
*Corroborating absence:* **the push-path test stub fabricates the reader's key shape** — *"the fixture
mirrors the reader, not the writer. The S195 lesson ('an invented test fixture') recurring inside the
machinery built to encode it."*
*How would we know today:* `SELECT COUNT(*) FROM data_flag WHERE code='TOTAL_VS_MARG';` — **predicted
0.** *"Any non-zero number falsifies AF-2 and I will demote it."*

**AF-3 · MEDIUM — a failed approval can leave a posted Staff-Ledger advance behind, and the retry
posts it again.** `make_entry` **appends to `ledger.jsonl` immediately and durably**; `ledger_posted=1`
is only committed at the end. A later failure in the same approval (`to_paise` accepts "500.50" and
the whole-rupee check raises **after** earlier advances have posted) does `con.rollback()` — *"the
finance stamps vanish, **the JSONL rows do not**. The idempotency guard is exactly the stamp that was
rolled back."* *"A duplicated ₹15,000 advance is a duplicated salary deduction."*
**Its scan command exists in exactly one place — this document, §Commands 2** — and
`OWNER_TODO_LIVE` ⭐0 #7 orders it run **before the August close**.

**AF-4 · MEDIUM — five checker-grade routes never got the F-127 rule.** `/finance/api/month/<ym>`
(per-day revenue, **closing balances, the owner's personal drawings**), `/api/days`,
`/api/day/<date>/lines` (**patient name + clinic id**), `/api/parked`, `/api/month/<ym>/close-check`
— no `require()`, no internal role scoping. *"**The contradiction is the finding:** the same file
scopes the maker deliberately elsewhere … The rule 'what a maker may see' is copied per-route, and
these five never received it."* Neither maker page calls any of them, *"so scoping them breaks
nothing."*

**AF-5 · LOW — the medical-PC guard runs a different parser than the server, while claiming
"its judgment is identical to the server's".** `deploy_kits/S195_MARG/marg_report.py` =
**`28b47d44…`** (S180); the server runs **`6411a57d…`** (S193_DISC). *"Failure direction is closed,
not open"* — an `.xlsx` the server accepts is REFUSED locally with *"file poori/theek nahi hai"* and
reception re-exports fruitlessly. LOW — *"but the premise justifying a local guard at all
('identical judgment') is currently false, and the copies will keep drifting."*

**AF-6 · LOW — one live pin's bytes exist nowhere off the box as a file: the maker's money-entry
page.** Of 45 live pins, only `finance_entry.html 92477b06…` matches **no file in the repo or inside
any kit tarball** — a 26,745-file hash sweep, stored and LF-normalised. Cause: `S193_UX` was an
**in-place patch kit** — it shipped `patch_pages.py`, not the resulting page. *"Reproduced the
recovery this run: `S190_F3`'s `finance_entry.html` + `S193_UX/patch_pages.py` → output hashes
exactly `92477b068c67e28661b049b7f3385708`. **So the bytes are derivable — but only via a two-step
recipe documented nowhere as the recovery path.**"*

**Surface B — the system of work:** token rotation **day 3 open**, still listed highest severity ·
Darpan's SPECIAL approval deadline is the August close · **manojz is still publisher + puller +
mirror + offsite in one box (slice 4's subject)**.

**The coverage statement, which the seed requires and which is the model for all of them:**
> *"**Roughly 70% of the cash trail's code surface exercised, 0% of its live data** — the four
> commands above are the bridge."*

> **STATUS: this run was never re-executed and slice 2 was never run.** The seed's own rule — *"every
> run re-executes the previous run's finding evidence"* — has therefore never been exercised. AF-1
> was later confirmed still live from the code (entry 43). AF-2 was closed at entry 29. **AF-5's
> label was dropped in transcription and went missing from the project's working memory for eight
> sessions** — entry 47.

---

## SESSION 201 · 25 August 2026 — the pipeline is audited and rebuilt

### 23 · THE OUTBOX HAD NO CONSUMER
**`S201_Marg_Outbox_Never_Drained_Finding.md`** · md5 `4a1579db3d7dbcb03d153124d2c1aa07`
(post-banner; pre-banner `d0adbd36217ad4922ef0474b2bdd5774`, quoted)

**Raised 25-Aug ~09:15 IST by the owner:** *"made a Marg sale report this morning, saw it being
pushed from a cmd window, but it is not on the approvals page and I can't find it in margsync."*

**Verdict: the report is SAFE and CORRECT. It was never sent.**

| Time | Event |
|---|---|
| 08:16 | Marg export #1 → `_captured\20260825-081605__REPORT_1__25c1ff95.XLS` |
| 08:20 | pull → routed → **VERIFIED** → archived + Drive offsite · `uploaded=queued` |
| 08:27 | Marg export #2 (owner re-ran with the correct single date) → `…__3b456d9c.XLS` |
| 08:30 | pull → routed → **VERIFIED** → archived + offsite · `uploaded=queued` |
| — | **push to `followup.dr-manoj.in` — NEVER HAPPENED.** `send_log.txt` last entry **22-08-2026 09:39** |

*"**The cmd window you saw was the capture/pull, not a push.** … It looks exactly like success. It is
not the sender."*

**Why the owner could not find the file:** *"the router renames every file by the business date
inside it and files it into a type/month subfolder — it is never called `REPORT_1.XLS` again."*
Both copies parse clean and identically: **SANJEEVNI MEDICOS · 24-08-2026 · 22 bills · gross
13,881.15 · discount 916.35 · NET ₹12,964.00 · cash ₹10,462.00 · non-cash ₹2,502.00.** The only
difference is the title — `FROM 23-08 TO 24-08` vs `AS ON 24-08` — *"which changed the md5 and
produced two archive entries for one day's trade. No data was lost or duplicated."* 23-Aug was a
Sunday.

**Root cause — a queue built with no consumer:**
```python
# marg_router.py 314-318
if verdict == "VERIFIED" and sig and sig.get("uploadable"):
    shutil.copy2(path, os.path.join(cfg["outbox"], name))
    res["uploaded"] = "queued"
    out("            -> queued for upload in Outbox")
```
**"Nothing on any machine reads `_outbox`."** Grep of manojz *and* the whole repo returns nothing.
**Every VERIFIED sale report since 17-Aug — 8 files — still sitting there.**

> **The sentence that names the class:** *"**So the S195 watcher work quietly replaced the human's
> reason to click the sender.** Before S195, the operator ran GUARD_AND_SEND and the report went.
> After S195, the export is captured automatically, a cmd window flashes, everything *looks*
> handled — and the one manual step nobody removed stopped being done. **The automation did not
> break the push; it hid it.**"*

**Aggravating factor: the word `queued` is a lie.** *"`uploaded=queued` in `index.csv` and 'queued
for upload in Outbox' on screen both assert a pending send. **There is no queue-runner.**"*

**§5 — the health check that should have caught it:** *"Either it is red and the warning was not
seen, or it has died into its `except` the way both A4 cards did at S196 (F-162). **A freshness check
that stays green through a three-day outage is worse than no check at all.**"* *(Disproved later the
same session — entry 24 §1: "the freshness check did not die into its `except`.")*

**Three faults proposed:** the queue with no consumer · **F-b: the router names a file by the
title's requested range rather than the dates actually present** — *"`…2026-08-23_to_2026-08-24`
contains 24-Aug only. A future reader could take that name as evidence 23-Aug traded zero"* ·
F-c, the freshness check.

**SUPERSEDED 26-Aug — F-179 is CLOSED.** *"The Fault Register is the only register of record for
fault status. **A finding document is not a place to check whether something is still broken.**"*

### 24 · The rebuild plan — thirteen named faults and eight parts
**`S201_Marg_Pipeline_Rebuild_Plan.md`** · md5 `23ef95fdb8f4adea7bb4760b58bf7ba1`

Three parallel audits — **the code as it actually is** (read line by line off manojz), **the
documentation**, and **the health surface**. *"Design constraint throughout: the same pipeline must
serve the Lab PC / Labmate ERP next. Every part below is specified source-agnostically — a new source
must attach by adding a *profile* and a *signature*, never by copying a script."*

**§0 — a correction owed first, and it is the model for how a retraction should read:**
> *"Earlier today I told the owner, and wrote into `medical_inventory.py`'s own docstring, that 'the
> router re-files a report … but never corrects the index row.' **That is false. There is no
> re-filing code path anywhere.**"* The router blacklists by md5 at `:249-250`, *"before
> `open_sheet()`, before `identify()`"*, and `append_index()` opens in `"a"` mode with no update
> path. What actually happened: the two July purchase reports in the type folders are **hand-made
> copies placed out-of-band** on 23-Aug — *"byte-identical duplicates, no `.txt` sidecar, mtimes
> matching the folder-creation minute rather than the `copy2`-preserved source mtimes."*
> *"**This matters beyond the correction: the real fault is worse than the one I described.**"*

**Broken or absent, confirmed — A through M, each with a file and a line:**

| | fault | evidence |
|---|---|---|
| **A** | `D:\MARG REPORTS` is watched by nothing | `START_MARG_WATCHER.bat` L23. *"The canonical `S195_Medical_Watcher_LIVE_Reference.md` states it **is** watched — **the sole reference doc is wrong on its own diagram.**"* |
| **B** | a signature added never rescues an already-indexed file | `:249-250`. Live casualties `633a54d3`, `fbea55de`, `1beac275`, `df20b4d2` |
| **C** | one header variant kills a whole report family, permanently | six real closing-stock exports refused for `['S.No.','Description','Total Stock','Unit']` |
| **D** | PDF/CSV structurally invisible, **and silently so** | `EXTS = (".xls",".xlsx")` L45; `capture()` returns `False` **with no output**. Five real Marg PDFs sitting in the mirror |
| **E** | truncation checked only for sale reports | `ends_with()` returns `True` when `end_marker` is absent |
| **F** | only SALE_BILLWISE is `uploadable` | *"'reached the archive' ≠ 'reached the clinic'"* |
| **G** | a multi-day range export is credited to `date_to` only | *"my code, my bug. Did not bite today only because 23-Aug is a Sunday"* |
| **H** | the spool doubles as the dedupe memory, and nothing is ever cleaned up | *"emptying `_spool` re-captures everything"* |
| **I** | routing only runs if something new was captured | `if do_route and new:` |
| **J** | **the guard sends anyway when Python is missing** | `GUARD_AND_SEND.bat` L72, L92-96 |
| **K** | the guard runs a different parser than the server while claiming byte-identity | AF-5 |
| **L** | `TOTAL_VS_MARG` has never fired once | AF-2 |
| **M** | no PC-side live pins exist | *"This is how K's two-build parser drift went unnoticed"* |

**Monitoring coverage — 4 of 7 failure modes have none:** watcher dead **NONE, unbounded** · pull
task dead **NONE, unbounded** · generated-but-never-sent 26–36h *"+ time until someone opens the
portal"* · sent-but-rejected **silence only, no reject counter** · exported as PDF **NONE — and the
alarm that eventually fires names the wrong cause** · mid-month day never generated **NONE** ·
Drive offsite failing **NONE**.

> **The structural fact, and it is quoted in six later documents:** *"**Every server-side check
> watches arrival at the VPS.** It cannot see the medical PC, manojz, the archive, or Drive. Four of
> seven failures are on the blind side of that line, and no amount of server-side work will fix that
> — **the pipeline must report in.**"*

**The eight parts**, ordered by **(money at risk × silence)**: 0 rescue what is stranded · 1 capture
everything and never reject in silence *(including: "**Do not** parse `.SPL` spool files … Instead
set a **virtual PDF printer** as Marg's report printer")* · 2 identification that can learn ·
3 integrity for every type, and **"One parser, not three"** · 4 storage/transport/retention,
including **the token inventory** · 5 the manual fallback chain, *"manojz local path → the medical PC
→ regenerate in Marg"* · 6 health wired to catch the maximum, **nine additions, six of them riding
one heartbeat POST**, including a **never-fired witness** — *"any check with zero lifetime firings
renders `info: never fired since <date>`. **This alone would have surfaced L on day two instead of
never.**"* · 7 documentation rebuilt · 8 generalise to the Lab PC.

**And the rule proposed for all of it:** *"every part ships with the check that proves it, in the
same kit. **Five of the last eight faults in this subsystem were faults in the *monitoring*, not the
data path** — built without selftests, wired to nothing, or reading keys nobody writes. This plan
should not add a ninth."*

**STATUS: KEEP.** Parts 6–8 are unbuilt. `S203_PENDENCY_RECONCILIATION` Thread 2 records it as **one
of only two homes of AF-5's substance**.

### 25 · Part 0 — eleven reports rescued
**`S201_Part0_Rescan_Record.md`** · md5 `66ace6c5d0551633e8cb1d25ff515b40` (post-banner; pre-banner
`4247b6153f649f7607e8cace84bae7e0`, quoted) · *"recorded as it moved (F-97)"*

**What was installed:** `marg_rescan.py` **NEW**, selftest **12/12** · `RESCAN.bat` NEW (dry run by
default; `APPLY` commits) · `marg_router.py` gains `data_from`/`data_to` · `signatures.json` gains
**`STOCK_CLOSING / TOTALS`** · **`index.csv` migrated 13 → 15 columns, 11 rows corrected**, backup
**`index.csv.before_rescan_20260825-142311`**.

> **The design rule enforced, and it is the reusable one:** *"`marg_rescan.py` makes no classification
> decision of its own. It imports `marg_router` and calls `identify()`, `verify()`, `dates_from()`,
> `canonical_name()`. **Re-implementing the router's opinion is the exact fault that left a
> two-builds-old parser on the medical PC claiming byte-identity with the server (AF-5). A second
> opinion is a second thing to drift.**"*

**The classification change, which was the owner's point:** *"`date_from`/`date_to` are what the
**title claims**. `data_from`/`data_to` are the dates the **rows actually carry**. They are recorded
separately and neither is inferred from the other."*

**Result — 11 reports rescued** (UNKNOWN/REFUSED → VERIFIED and correctly filed):
STOCK_CLOSING/TOTALS **2024-01-20 · 2024-10-05 ×2 · 2025-06-03 · 2026-06-03 · 2026-08-09** ·
STOCK_CLOSING/DEFAULT **2026-07-01** (scrap store) · STOCK_EXPIRY **2026-08-23 ×2** ·
PURCHASE_SUPPLIERWISE and PURCHASE_BILLWISE **2026-07-01 → 2026-07-31**.
Index: **VERIFIED 16 → 26 · UNKNOWN 5 → 1 · REFUSED 13 → 7. No file exists in two places.**
`_rescued/` holds the 11 quarantine copies and their stale sidecars — *"a record, not a deletion."*

**Still quarantined, correctly** — none of them Marg exports: three untitled ITEM LIST files,
`SANJEEVNI SUPPLIER LIST`, two test workbooks, `SALE BOOK FORMAT`, and **`SANJEEVNI ORTHOTIC STOCK
22 JAN 2024`** (header `S.No. · Description · MARG · ACTUAL` — the owner's manual physical-count
comparison sheet). *"No signature was written for that last one deliberately: **it is not the
pipeline's business.**"*

**New fault found, not yet fixed:** *"**`.xlsx` support on manojz depends on an old Python,
silently.** `xlrd 1.2.0` reads `.xlsx` only below Python 3.9 … Proven this session: the same
`ITEM DUMP STOCK 9 AUG 2026.xlsx` opens fine under manojz's Python and raises `'ElementTree' object
has no attribute 'getiterator'` under 3.10. **The day manojz's Python is upgraded, every `.xlsx`
Marg export becomes 'not a readable .xls' — and it will look like a refusal, not a breakage.**"*

**SUPERSEDED 26-Aug** — the rescan is now standing procedure in `MARG_PIPELINE_REFERENCE_v1` §7 and
`…MAINTENANCE_FLOW_v1` §3. The eleven dates and the backup name stay here.

### 26 · Part 1 — the watcher died at 10:37, and the agent was built
**`S201_Part1_Capture_And_Agent_Record.md`** · md5 `900920aa7ef18760894ca8984e3be771` (post-banner;
pre-banner `8be4f6c758b2054e14861189c49c5b35`, quoted)

**§1 — THE INCIDENT THAT SET THE PRIORITY.**
> **"The medical-PC capture watcher died at 10:37 and was discovered at 14:49, by accident."**
> The 14:49 survey reported `NO python process is running. THE WATCHER IS DOWN`. Working backwards:
> `_captured` held the 08:16 and 08:27 exports, so the watcher was alive then. **At 10:37:00 the
> owner saved `REPORT_2.XLS` (the 22-Aug report) and it is not in `_captured`.** At 10:37:41 Marg
> wrote `marg_system_shutdown….tmp`. Nothing was captured after that.
>
> **"That day's report survived on redundancy, not on design."** manojz's 10-minute pull reads
> `\\medical\MARGERP\users` directly, so it collected `REPORT_2.XLS` at 10:40 without the watcher.
> **"Two independent paths existed and one of them worked — and *nothing told anyone the other had
> failed*."**

**§2 — the delivery channel, proven both directions.** Google Drive for Desktop on the medical PC
(streaming mode, `F:\My Drive`) makes the S195 relay unnecessary: `Cowork → H:\…\ToMedical → medical
F:\`, and `medical → F:\…\FromMedical → H:\ → Cowork`. **Both legs tested live.** *"No inbound access
to the medical PC is required for either direction."*
Routes explored and ruled out: **Tailscale SSH** (server is Linux/macOS only) · **writable SMB
share** (viable, one permission change, still worth doing) · **PowerShell Remoting over Tailscale**
(*"the real control layer, not yet built"*) · **Cowork on medical** (*"a session binds to one device,
so it cannot replace manojz"*).

**§3 — what went live on manojz.** `marg_router.py` `d63045b15011a51cd5e86757c06fbbb9`: PDFs get
their own path — `%PDF` header check, **`%%EOF` truncation check**, dated by mtime, archived to
`DOCUMENT_PDF/<YYYY-MM>/`, **never uploadable** — *"and the scan filter widened: `main()`'s walk only
looked for `.xls/.xlsx`, so a captured PDF would never have been handed to `process()` at all.
**Two filters decide what is seen; both must agree.**"* And `marg_watch.py` `aa55cdb5…` now checks
**magic bytes per extension**, so a PDF renamed `.xls` is refused at the watcher.

> *"**Capturing a PDF is not the same as being able to use it.** No figures can be read out of one on
> these machines. It is kept, hashed, dated and offsited so it stops being invisible; **it does not
> become data.** That distinction is written into the index row, not just into this doc."*
> The index reason, verbatim: *"captured and archived. A PDF cannot be read into the books — if these
> figures are needed, run the same report again and save it as Excel."*

**§4 — the medical agent** (S201.4, stdlib only, bundled python 3.11.9 with **no third-party
packages at all**): supervises the watcher as a child, checking every 30 s and **restarting within a
minute of a death** · **heartbeat every 5 minutes** into `FromMedical` carrying watcher
alive/pid/restarts, what it is *actually* watching **read from the running configuration**, captures
today, **the installed watcher's own md5**, kit status, Marg's report slots, disk free · and
**`IGNORED`: files in the watched folders the watcher cannot take** — *"the PDF blind spot made
countable. A report the pipeline skips now appears by name instead of being invisible while a
downstream alarm blames the network."* · applies allowlisted updates, compile-checked and
**verified by hash after writing**. **"The agent never updates itself — a process overwriting its own
running code is how an unreachable machine is lost."**

**§5 — what is NOT done.** *"**The medical PC is still running the OLD watcher** (`25126388…`,
`EXTS = (".xls", ".xlsx")`). Confirmed from the manojz mirror … not inferred."* Installer v2 failed:
it copied the new watcher to a temp file, compile-checked it, then tried to `move` it over
`marg_watch.py` **while the watcher was still running** → *Access is denied* → **"And it printed
`UPDATED` anyway, because the move's failure did not stop the script."** Installer v3 stops
everything **before** any file is touched, clears the read-only flag, and **hash-compares the
installed file against the source** — *"printing `UPDATED and VERIFIED` or `***NOT UPDATED***`, never
a guess."*

**§6 — the faults, including the three the author introduced, recorded because they are the same
classes being fixed:**
> 1. *"**`log()` wrote to stdout before the log file.** Under `pythonw.exe` there is no console and
>    `sys.stdout` is `None`, so the agent died on its first line leaving no trace of why — **inside
>    the tool built to end silent failures.**"*
> 2. *"**Installer v2 reported success it never verified** — the same fault as AF-1's sender, which
>    this session criticised that morning."*
> 3. *"A large PowerShell paste was reordered by the console … Delivery moved to a double-clicked
>    `.bat`; **a file that is *run* cannot be reordered by a terminal.**"*

Plus: the `.xlsx` time bomb · **the medical guard cannot run at all** (no `xlrd`, no `openpyxl`) ·
watcher death unmonitored (closed by §4) · `NEEDS_UPLOAD` and `FROM_CLINIC` do not exist on the
medical PC.

### 27 · The `.xlsx` time bomb, defused by removing the dependency
**`S201_Part1_xlsx_Dependency_Removed.md`** · md5 `52fe31ae61f7a868927f8231b1537c98`

**Why not just install openpyxl:** *"Because that means pip on every clinic PC, including a bundled
interpreter with no packages and no reliable way to add them — and the Lab PC after that.
**A dependency that must be installed on every machine is a dependency that will be missing on one of
them.** The S195 setup doc already told someone to `pip install xlrd==1.2.0`; it was never done
against the portable interpreter, which is why the medical guard has never been able to run."*

**What was done instead:** *"An `.xlsx` is a zip of XML, and the standard library can open a zip and
parse XML. **`xlsx_stdlib.py` reads it directly — no third-party package, nothing to pin, works on
any Python 3.**"* — `bbe11a8953f66c27126c48e773cfbe35`, **verified identical on both machines here.**
*"Deliberately not a general library: it returns cell values as text and numbers, which is all the
Marg parsers ever ask of it. Numbers come back as floats exactly as xlrd returned them, so nothing
downstream sees a different shape."*

**Proof, not assertion:**
1. **Cross-validated against `openpyxl`** on a real Marg export (`SALE BOOK FORMAT.xlsx`,
   `9bf5c008`): **170 cells compared, 0 mismatches**, same sheet name, same dimensions.
2. **Proven on a Python where xlrd fails** — in a 3.10 shell: `xlrd` → `'ElementTree' object has no
   attribute 'getiterator'`; `marg_router.open_sheet()` → 33 rows × 4 cols, title
   `MAIN STORE CLOSING STOCK AS ON 09-08-2026`.
3. **Every `.xlsx` in the archive — 9 files — read with the standard library alone.**

**Also closed in this pass:** `_UPLOAD_NOW` and `MARG_PICTURE.txt` refreshed **by the 10-minute
pull**, not only when a human runs `MARG_STATUS.bat` — *"the surface that says 'someone must upload
this by hand' was stale exactly when it mattered"* (audit gap G10) · and *"**the census must never
again grade the pipeline's homework with the pipeline's own answers — that circularity is what
produced the false '0 not captured' earlier today.**"*

**STATUS: KEEP.** *"The only proof `xlsx_stdlib.py` is correct"*, for a file master v4 §8 lists as
existing nowhere but two PCs.

### 28 · Parts 2, 3, 4 — the end markers, and the registry that learns
**`S201_Parts2_3_4_Record.md`** · md5 `e02af11363bd0f235493bb230e164150`

**PART 3 · truncation is now detected for every report type.** *"`ends_with()` returns `True` when a
signature declares no `end_marker`, and only `SALE_BILLWISE/DETAIL` declared one. So a purchase or
stock export that stopped mid-print was filed `VERIFIED "structural"` and looked perfectly healthy.
**A partial stock count is worse than none.**"*

**Evidence first — every archived report of each type was opened and its tail read:**

| type | last data row | marker adopted |
|---|---|---|
| PURCHASE_BILLWISE | `TOTAL │ 476393 │ - │ 476393` | `TOTAL` |
| PURCHASE_SUPPLIERWISE | `GRAND TOTAL │ 476393 │ - │ 476393` | `GRAND TOTAL` |
| STOCK_CLOSING (both variants) | `TOTAL │ │ 76 │` | `TOTAL` |
| STOCK_EXPIRY | `TOTAL │ │ │ 832` | `TOTAL` |

**Checked before applying, not after: 16 would pass, 0 would be refused.** Then applied, then every
archived report re-verified: **26 still VERIFIED, no regressions.**
`SALE_BILLWISE/SUMMARY1` deliberately still has **no** marker — *"no sample of that variant exists to
derive one from, and the signature now says so in a note rather than carrying a guess. **A guessed
marker would refuse real reports.**"*

> **Worth recording:** *"`PURCHASE_BILLWISE` totals **476,393** and `PURCHASE_SUPPLIERWISE` totals
> **476,393** for the same July period. **Two independently generated reports agreeing to the rupee
> is a genuine cross-report integrity check**, and a natural basis for the deep purchase verification
> Part 3 still owes."*

**PART 3 · a range export now covers every day inside it — *my own bug*.** *"`build_picture()` and
the send logic both keyed a report by `date_to` alone. A catch-up export covering 01→15 Aug would
have counted as **15-Aug only**, with the other fourteen days reading `MISSING` — and if a newer
single-day export existed for the 15th, the range file would have been marked `superseded` and its
earlier days **never sent at all**. **It never bit because the only range export we have spans a
Sunday.**"* Fixed with `covered_days()`/`span_key()`: **the DATA range wins over the title range
where it exists** · a delivered range delivers **every** day inside it · a report is sent unless
**every** day it covers already has a delivery at least as new. Selftest **39 → 49**.

**PART 4 · the spool is routed whenever it holds anything.** *"A routing run that died … left its
files in the spool, and **no later run would touch them** until an unrelated new file happened to
arrive."*

**PART 2 · the registry learns by itself.** *"Adding a signature used to rescue nothing … **Nobody
did — for two purchase reports and eight stock exports.**"* `marg_rescan.py --if-signatures-changed
--apply` now runs inside the 10-minute task, comparing `signatures.json`'s md5 against
`MargArchive/_signatures_seen.md5` and **doing nothing at all unless the registry has changed.**
*"Proven live: silent when unchanged → fires when a signature is edited → re-arms afterwards."*

**What the 10-minute task now does, end to end:**
```
stamp START -> pull + capture from medical -> route the spool (always, if it holds anything)
 -> re-judge quarantine IF the registry changed -> send anything the server lacks
 -> mirror medical's logs -> mirror MARG REPORTS -> offsite to Drive
 -> refresh the picture + manual-upload folder -> stamp END
```
*(Note for a future reader: **that order is wrong** — measured on 26-Aug, the three robocopies run
**before** the rescan and the send. Entry 44, claim #12.)*

**Still owed in these parts:** deep verification for purchase and stock · **"One parser, not
three"** · outbox and spool lifecycle — *"nothing is ever removed; the spool doubles as the watcher's
dedupe memory, so tidying it re-imports everything"* · **token rotation — three copies (systemd unit,
medical PC, manojz cache). Owner action, and the oldest open item in the project.**

**STATUS: KEEP** — master v4 §10 names it must-preserve for the per-type `end_marker` derivations and
the ₹476,393 cross-report control.

### 29 · A1FIX — the born-dead check, and a fault retracted the same hour
**`S201_A1FIX_Live_Pin_Record.md`** · md5 `88b7cee03dab3f7a7a077b5ee4cc5db3` (post-banner;
pre-banner `c069cd4b36a604618cd5d2a4e47c0844`, quoted) · **25-Aug 17:03 IST, INSTALLED GREEN, first
pass** · `finance_app.py` `2c99b2c6…` → **`d930b6b5bca59e7f52ce46f6b88332fd`**, smoke **683**

**Auditor finding AF-2, closed.** *"Confirmed from the live bytes, not from the database. The S198_H2
kit in the repo hashes to the live pin exactly, so both functions were read directly — no
`SELECT COUNT(*)` needed. **The auditor's predicted `0` was right by construction.**"*
**The fix:** carry the two keys through; **purely additive**, because the apply path reads only
`date`/`expect`/`lines_csv`/`items_csv` and ignores every other key — *"so replay behaviour is
byte-unchanged."*

**The vacuous test replaced:** *"The push-path stub fabricated the **reader's** key shape, so the
suite stayed green while the feature was dead — **the S195 'never assert against an invented fixture'
lesson recurring inside the machinery built to encode it.**"* The three new checks go through the
**real writer** and then call the **real reader**.

**Proof chain:** offline differential on the seeded live-shape store, every imported module
hash-recovered to its live pin → **570/679 → 573/682, +3 exactly, fail set byte-identical (109
rows)**; on the box **680/680 → 683/683, +3 exactly.**

**A capability unlocked, and it is the recovery recipe:** *"The offline smoke harness was rebuilt from
the repo alone. **The live VPS bytes are recoverable**: `deploy_kits/S198_H2/finance_app.py` hashes to
the live pin exactly (**D188 — recover by hash, never by filename**)."* The recipe, verbatim:
```
finance_app.py      deploy_kits/S198_H2/finance_app.py               2c99b2c6
finance_ingest.py   deploy_kits/S194_TRIPLE/finance_ingest_S194.py   6cb83302
marg_report.py      deploy_kits/S193_DISC/marg_report_S193.py        6411a57d
staff_ledger.py     deploy_kits/S193_F6/staff_ledger_S193.py         acd7b538
finance_yesbank.py  deploy_kits/S186_R1a/finance_yesbank.py          5dcbdd3a
schema  deploy_kits/S193_DISC/finance_schema_S193.sql · seeder  deploy_kits/S193_F6/dev/seed_live_shape.py
then apply the four additive migrations (S182_clinic / S182_c2 / S183_marg_map / S186_reserve_yesbank)
```
*"This is what lets a kit's `+N exactly` projection be **measured** rather than guessed, before
anything touches the money system."* Kept alive by `S201_PARKED_BACKLOG` §B.

**A fault reported that was NOT real — retracted, and why.** The claim was that `vps_deploy.sh` could
not find any installer written since S196_HLT3, because its last line globs lowercase `install_*.sh`
while kit installers have been uppercase. **"That was wrong, and it was tested and disproven the same
hour."** Run live, the wrapper *"pulled, verified `SUMS.md5`, read `KIT_ID.txt`, **found and ran the
uppercase installer**, and stopped at the currency gate because the fix was already installed — a
clean no-op proof of the whole path."*
> **Where the mistake came from:** *"I read `deploy_kits/S182_C1a/deploy/vps_deploy.sh` — the stale
> *shipped copy* in the repo — and assumed the live `/root/deploy/vps_deploy.sh` matched it. **This
> is exactly D188 — a file's location is not its provenance — committed while quoting D188 in the
> same document.** Verify the live artefact, not a copy that shares its name."*
**The residual, minor and real:** the repo's shipped copy is stale relative to the live one. Still
open at `S201_PARKED_BACKLOG` A5 and `OWNER_TODO_LIVE` ⭐0b.

**SUPERSEDED** by the KB Register's live-file table. *"The pin this record fixes has moved repeatedly
since S201; the retirement list §1 row 5 counts four moves."* **Where the Register and the box
disagree, the box wins (D321(d), F-169).**

### 30 · "This month vs Marg" — it is the review queue, to the rupee
**`S201_Month_vs_Marg_Explained.md`** · md5 `fee7281ce03d5c1e3305fba5b0c0f038` · read-only, live
database queried via Termius, nothing changed

**The answer:** *"The red 'This month vs Marg' line is not an accounting discrepancy, and nothing is
missing from the books. **The difference is exactly the value of lines sitting in `sale_item_review`**
— bills the parser read with confidence below 0.70, waiting for a human to identify the patient."*

| day | open review lines | review value | health page difference |
|---|---:|---:|---:|
| 17-Aug | 9 | 9,990.00 | 9,990.00 |
| 18-Aug | 8 | 4,577.00 | 4,577.00 |
| 19-Aug | 7 | 3,500.00 | 3,500.00 |
| 20-Aug | 4 | 1,331.00 | 1,331.00 |
| 21-Aug | 16 | 30,045.00 | 30,045.00 |
| 24-Aug | 5 | 2,425.00 | 2,425.00 |
| **total** | **49** | **51,868.00** | **51,868.00** |

**What the check actually compares:** books = `v_cash_ledger.revenue_p`, the day's **entire** recorded
revenue; Marg = `marg_net_sql()` over **only the lines that were attributed**. *"So it subtracts
*attributed lines* from *the whole day*. **The remainder is, by definition, whatever was parked in
review. It can never be zero on a day with a single low-confidence bill.**"* And `days_differing` is
a bare `if bp != mp` — **no tolerance. One paisa lists a day.**

**A wrong rule retracted, and this is the paragraph worth keeping:**
> *"An earlier inference in this session — '**no clinic ID → dropped**' — was wrong. It fitted 21-Aug
> (21 of 37) and 24-Aug (17 of 22) exactly **and still fitted the wrong reason.** 18-Aug broke it:
> nine id-less bills worth 4,767, but the difference was 4,577. Bill **A003039 (₹190)** is id-less
> and was **ingested** — it cleared the confidence bar. 4,767 − 190 = 4,577.
> **A rule that fits two days and predicts the third wrongly is not the rule.**"*

**Verified live:** `18-Aug batch 126 partial 22 rows naive 23,879.00 signed net 20,599.00` ·
`24-Aug batch 128 superseded 0 rows <- a duplicate push, correctly discarded` · books 21-Aug
₹49,181.00 and 24-Aug ₹12,964.00, *"exactly the Marg reports' own totals."*
*"18-Aug's `23,879 / 20,599` are the very two figures `marg_net_sql`'s docstring records from the
18-Aug credit-note incident — **the live data confirms that history exactly.**"*

**Three faults:** the check compares two things that can never be equal, so the row is **permanently
red at `bad`** — *"precisely the 'wallpaper' condition the S195 ruling exists to prevent … The same
reasoning was applied to `data_flag` and never to this row"* · **`days_differing[:5]` truncates
silently**, with no "and N more" unlike the sibling line immediately above it — *"24-Aug was
differing and simply was not shown. **It was found by arithmetic** (books +12,964 vs Marg +10,539
while the listed five were unchanged), then confirmed in the code"* · **the page describes a workable
queue as an unexplained discrepancy** and neither says so nor links to `/finance/review`.

**Worth watching:** *"21-Aug had 16 of 37 bills below the confidence bar (43%) — well above the ~25%
of other days"* *(later answered: 57% capture, **staff behaviour, not a formatting fault** —
`S202_PENDENCY_AUDIT` N5)* · *"At ~8 lines a day it refills to roughly 250 a month if nobody works
it."*

**STATUS: KEEP** — `MARG_PIPELINE_MAINTENANCE_FLOW_v1` §2 points readers at it **by name**.

### 31 · The completion audit — and the "discovery" that was ten days old
**`S201_Medical_Pipeline_Completion_Audit.md`** · md5 `85a6bc7cac550a982711e8537c9f4c24` (post-banner;
pre-banner `a0452bbb7491ac2adc909945df254ca1`, quoted) · **25-Aug 19:12 IST**

**The three health surfaces, all green at the time:**
```
pull heartbeat : END 25-08-2026 19:10:19.14 -- ok
medical beat   : MEDICAL PC HEARTBEAT   2026-08-25T19:06:18
picture        : days with NO export : 0    exports NOT on server : 0
```

**The archive at that moment:** SALE_BILLWISE 10 · STOCK_CLOSING 8 · STOCK_EXPIRY 6 ·
**DOCUMENT_PDF 7** · PURCHASE_BILLWISE/SUPPLIERWISE 1/1 · `_rescued` 11 · `_REFUSED`/`_UNKNOWN` 7/1,
*"none of them Marg exports."* `index.csv`: **41 rows, 15 columns, 0 malformed · 33 VERIFIED ·
7 REFUSED · 1 UNKNOWN.** Delivery: 3 accepted · 6 duplicate · 1 superseded · **no undelivered
reports.**

**§4 — the finding that mattered most:** *"**Marg has TWO output trees, and only one was ever
known.**"*
- *"**It is on C:.** The Tailscale share is `\\100.119.151.40\DDrive` — **D: only**. manojz cannot see
  C: at all, and never could."*
- *"So the census, the recent-files sweep and the ignored-file counter — **every tool built to answer
  'what did Marg actually write?' — all scan the D: share, and all three would have answered
  'nothing' with complete confidence.**"*
- *"`REPORT.PDF` is a **fixed slot**, overwritten on every export — the same race as `REPORT_1.XLS`."*
- *"Found by exporting one real PDF and watching where it did *not* appear: `CAPTURES: 4`,
  `IGNORED: 0`. Not ignored — **invisible**. **A synthetic test file would not have found this**,
  because it would have been placed where we already believed reports lived."*
- Proven end to end at 18:50: `C:\Users\Public\MARG\17476\all\REPORT.PDF` → watcher 18:46:18 →
  pull 18:50 → `DOCUMENT_PDF · 2026-08-25 · 7617f1b4 · VERIFIED` → Drive offsite.

**§5 — THE RUNAWAY I CAUSED, AND CLOSED.** *"Agent S201.3 retried a kit install **every 30 seconds**
and wrote a **backup before** knowing the write would succeed. **343 attempts between 15:28 and
18:20 — 4.1 MB of identical backups** on the medical PC, mirrored to manojz, still growing when the
audit found it."* Three fixes: prove writable **then** back up · **name the backup by source md5, so
retries cannot multiply it** · **3 tries, then leave it alone until the source bytes change**, with
the refusal carried in the heartbeat *"rather than only in a log nobody reads."*
And S201.8 *"replaced the ignored-file **denylist with an allowlist** after watching Marg's C: tree
put 18 database files (`.dbf .cdx .idx .fpt .xff .C18`) on the health surface. **No denylist stays
ahead of a database directory.**"*

**§6 — the popup, solved without the owner touching anything**, by handing off to `PULL_HIDDEN.vbs`
and repointing the task **once**, with `< nul` *"so a credential prompt fails instantly instead of
hanging a hidden process forever on input nobody can see."* And recorded honestly: *"`< nul` fed an
empty password and schtasks warned the task might stop running. It did not — that task runs only when
the owner is logged on … **The warning was real and the risk was taken knowingly**; the 19:10 cycle
was the proof."*

**§7 — cleanup, three places, nothing deleted.** manojz 7.6 MB to `_to_delete\` including *"a 0-byte
file named `finance marg token.txt`"* — **`token.txt` was kept, it is the live cache** · medical to
`D:\_to_delete_S201\`, **"outside every watched folder so the watcher cannot re-capture what was just
tidied away"** · Drive, with *"Amir's NEFT advices and the vendor reconciliation left alone: real
deliveries, not clutter."*

**§8 — still true and unfixed:** AF-1 still armed on the medical sender, *"kept deliberately as the
only medical-side fallback if manojz is down"* · the medical guard cannot run at all · **no PC-side
live pins** · **`MEDICAL_RECENT.bat` scans D: only — it cannot see Marg's C: tree, which is exactly
where the blind spot was.**

> **⚠ SUPERSEDED BY MEASUREMENT, and it circulates one error.**
> **(a) Its §2 pins were read from manojz's never-purging mirror, not from the machine.** Master §3.1
> lists six things that mirror wrongly implies.
> **(b) Its §4 "found 25-Aug" claim is false** — corrected at master v4 §9 #8. **The C: tree was
> written down in `S180_Marg_Sample_Findings.md` on 15-Aug, ten days earlier** (entry 6). The
> sentence *"Every document in this KB … described only the first"* is false of project knowledge.
> **The manifest's §S201 block still carries it.** *"Keeping it in the read-store keeps that error in
> circulation."*

### 32 · What is left for you
**`S201_WHATS_LEFT_FOR_YOU.md`** · md5 `e53ce3548b753f8dffceb46404da8584` (post-banner; pre-banner
`907ff59bb8d41c64117cac4d239a932a`, quoted) · **25-Aug 19:20. "Three things. Full paths. Nothing is
broken; nothing is urgent."**

1. **One install**, on the MEDICAL PC: `F:\My Drive\Clinic Data Archive\ToMedical\INSTALL_AGENT.bat`
   — agent **S201.9** plus `marg_watch.py`, `xlsx_stdlib.py`, `medical_census.py`. Why: **Marg's C:
   tree put 18 of its own database files on the health surface as "ignored"** — the allowlist switch —
   and it delivers the census that can see C:. *"`IGNORED` should read **0** again — **and when it
   doesn't, it will mean something.**"*
2. **Two tidy-ups.** *"Nothing is deleted; everything moves to a bin … It is a bin, not a backup."*
3. **One new tool**, and the reason it must run there: *"Every other census tool runs on manojz, over
   the Tailscale share — **the D: drive only**. Marg's PDFs live on **C:**. So those tools would
   report 'nothing there' with complete confidence, and be wrong. **This one runs on the machine and
   sees both drives.**"*

**Decisions still waiting on the owner — "not tasks — judgements only you can make":**
`ingest.min_confidence` for Marg, *"currently 0.70 and tuned for OCR rather than a structured
export"* · one look at the 21-Aug report.

**SUPERSEDED** by `OWNER_TODO_LIVE`. *"This is a point-in-time owner list from 25-Aug and it is a day
stale by construction. **Two task lists is how an item gets done twice or never.**"*

### 33 · The parked backlog — C1 to C8
**`S201_PARKED_BACKLOG.md`** · md5 `3083d35fb29b5565d2bebb4b6aeb2b26` · *"Everything open at the end
of S201, parked in one place so nothing lives only in a chat scroll."* Ordered within each section by
**(money at risk × silence)**.

**A · owner actions:** A1 **rotate both tokens** — *"open since 21-Aug — the project's oldest and
highest-severity item"* · A2 run `INSTALL_AGENT.bat` · A3 decide `min_confidence` — *"Default 0.70
was tuned for **OCR**, where an unreadable scan looks like an anonymous one. A structured Marg
export's only uncertainty is a missing ID … **A business judgement, not a code decision**"* · A4 the
21-Aug report · A5 sync the stale `vps_deploy.sh`.

**B · designed, not built:** B1 month-vs-Marg honestly · **B2 the pipeline heartbeat checks**,
including the **never-fired witness** *"which would have surfaced AF-2 on day two"* · B3 deep
verification for purchase and stock · **B4 one parser, not three** — *"the guard should load the
server's parser **by hash or refuse to run**, and must never send when it cannot verify"* ·
B5 outbox/spool lifecycle · B6 offsite verification.

**C · faults found, not fixed — and this is the list that was never minted:**
C1 the month check compares incomparable things · C2 `days_differing[:5]` truncates silently ·
**C3** the approvals WALK-IN warning is wrong twice · **C4** two parsers look for a clinic ID,
*"the same class `marg_net_sql` was created to end"* · **C5** the medical guard cannot run at all ·
**C6** *"**a re-apply wipes that day's review queue** … Any resolution must be recorded somewhere
that survives a re-import … **Matters directly to the Docterz plan**"* · **C7** no PC-side live pins,
*"which is how C4's two-build drift went unnoticed"* · **C8** AF-1 still armed on the medical sender.
Plus the retraction, kept in place: *"(retracted) — `vps_deploy.sh` … **disproven live**."*

**D · blocked:** D1 the review queue on the **Docterz EMR migration** — *"Match key will be
`bill_date + patient_name + phone_last4`; the phone is **last-4 only** (F-86), so design for that"* ·
D2 the Lab PC, *"S181 warns revenue arithmetic is **inverted** between medical and clinic/lab — 'the
single most dangerous copy-paste in the build'. **Do not assume replication.**"* · D3 Purchase Portal.

**E · from the Auditor, still untriaged: AF-3, AF-4, AF-6.** **AF-5 is not listed** — see entry 47.

**F · KB hygiene owed at the next fold**, including *"Retire `S180_Marg_Feed_Transport_Design`"*,
*"`SYSTEM_DOC_COVERAGE_MAP_S147` has no row for clinic-finance, Marg capture, the medical PC, manojz
or the Lab PC. **It predates the whole estate**"*, and *"Correct `S195_Medical_Watcher_LIVE_Reference`
or mark it superseded."*

> **STATUS: KEEP, and mostly still open.** `S202_PENDENCY_AUDIT` N1 established that **the S201 close
> minted F-179…F-183, which cover different things, and C3–C8 have no register entry at all.**
> *"This is F-108's exact shape, recurring."* Re-tested one by one at entry 47.

### 34 · MARG_PIPELINE_REFERENCE_v1 — the first real reference, and the five things it gets wrong
**`MARG_PIPELINE_REFERENCE_v1.md`** · md5 `97b3cf73f7f83c0860bde2d911596ff7` · **Tier-1 CURRENT**

*"Supersedes `S195_Medical_Watcher_LIVE_Reference.md` as the authoritative description of Marg
capture and transport … **Everything here was verified against the running systems on 25-Aug, not
copied forward.** Where a previous doc disagreed with reality, the disagreement is named."*

**Why it exists:** *"The previous sole reference was **wrong on its own diagram** in one direction
and right in another, and nobody could tell which. The router's design doc and the upload contract
were unreachable. The coverage map predates this entire estate. **A new engineer following the old
pointers landed on a stale or missing document at three turns out of four.**"*

**§2 — what was believed and was not true**, and it corrects the rebuild plan's own fault A:
*"'the resident watcher also captures `D:\MARG REPORTS`' — **TRUE**, and proven from the running
process's own command line. An S201 code audit read `START_MARG_WATCHER.bat` (one folder) instead of
the actual autostart `MargWatcher.cmd` (two) and reported the opposite. **Trust the running process,
not a script that may not be the one running.**"*

**§3 — THE UPLOAD CONTRACT. "No spec existed anywhere."** Reconstructed from the live endpoint:
```
POST https://followup.dr-manoj.in/finance/api/marg-push
Header:  X-Finance-Marg: <FINANCE_MARG_TOKEN>
Body:    multipart/form-data, field name "file"
```
`200` + `verdict ACCEPTED-FOR-REVIEW` = **staged; nothing has entered the books** · `401` +
`not_signed_in` = *"**The token was wrong or absent** — the request fell through to the session gate.
**This is what a stale token looks like; it does not say 'bad token'**"* · `503` = token absent
server-side, **fail-closed by design (F-84)**.
**Rules that matter to any client:** *"The uploaded file is **parsed and deleted inside the same
request** (S186). The VPS keeps no export file — so a report can never be 're-read from the server'."*
· staging is not applying · **"The endpoint does NOT dedupe by content"** · *"**Never** decide success
from a response *file* that a failed request leaves untouched — that is AF-1."*

**§4 — WHERE THE TOKEN LIVES, all three copies, "no previous doc listed them together":** the VPS
systemd unit · the medical PC's `token.txt`, *"deliberately excluded from the manojz mirror
(`/XF token.txt`)"* · the manojz **cache** — *"`marg_gate.py` reads the live token off the medical
share at send time and refreshes this copy … **Before S201 this was a hand-copy from 20-Aug and had
been answering 401 for five days while medical's own copy worked.**"*

**§5 — the runbook**, eight steps, *"each step names where the truth lives"*, including the
guest-access diagnosis with `cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass` and the reason:
*"`MEDICAL\user` has none, and **Windows refuses passwordless network logins**"*, plus
**"CREDENTIALS ARE STORED PER WINDOWS USER."**

**§6 — folders, and what is never cleaned:** `_spool` is *"byte-safe landing zone that defeats Marg's
slot reuse. **Also the watcher's dedupe memory** — emptying it re-captures everything. Never
pruned"* · *"Google Drive offsite is `robocopy /E` — append-only, no purge. `_spool` and `_outbox` are
excluded, so **the pending-send queue has no offsite copy.**"*

**§7 — adding a report type:** `--learn`, paste, wait ten minutes. And: *"**Derive a marker from a
real sample; never guess one**, or real reports get refused."*

**§8a — launching Marg from a script (added S202):** *"`margwin.exe` **must be started with its own
folder as the working directory** … Launched from anywhere else it refuses with *'Few important files
not found in SYSTEM / Please RE-INSTALL software!'* — **which is badly misleading and would panic
anyone reading it on a live pharmacy system.**"* And honestly: *"Marg **does** accept a command-line
argument and resolves it as a path (`/?` returns 'Invalid path or file name'), but **there is no
evidence it can be told to RUN A REPORT.**"*

> **⚠ TIER-1 CURRENT AND WRONG IN FIVE PLACES**, measured 26-Aug (entry 44):
> **§1 "BOTH folders"** — it is **three** roots; the third is on C:, so a reader of the canonical
> reference alone does not know a whole output tree is captured · **§1 `marg_router.py` drawn as a
> pipeline step** — *"`PULL_FROM_MEDICAL.bat` contains no `marg_router` invocation in 228 lines"* ·
> **§1 the step order** — the three robocopies run **before** the rescan and the send, so *"a report
> sent this cycle is offsited only next cycle"* · **§3 the multipart filename** — the sender
> transmits the **archive** name and has a selftest asserting `REPORT_1.XLS` is *not* sent ·
> **§7 the signature field list** — `--learn` emits **no `end_marker` and no `dating`**, so *"follow
> §7 literally and you install a signature with no truncation check, which is the exact failure
> `signatures.json` says the marker exists to prevent"* · **§9 `xlsx_stdlib.py` "not yet on the
> medical PC"** — it is, `bbe11a89…`, and has been since 25-Aug 19:28 · **§4 the token list** — three
> stored copies is still right, but there are **five distinct stores** and a **fourth consumer**
> (`pipeline_status.py`, S202) the doc predates.
> *"On the oldest open item, a rotation list that is wrong about which files exist is the failure
> mode itself."*

### 35 · MARG_PIPELINE_MAINTENANCE_FLOW_v1 — the sixty-second check
**`MARG_PIPELINE_MAINTENANCE_FLOW_v1.md`** · md5 `c2b5251f55762490ad219b8855a18dd8` ·
**Tier-1 CURRENT** · *"Written to be usable without reading any other document."*

**§1 — THE 60-SECOND CHECK. Three files. All three are on manojz. None needs a login.**
`_last_pull.txt` — *"a `START` and an `END … ok` **within the last 15 minutes**"* ·
`FromMedical\heartbeat.txt` — *"written within the last 10 minutes · `WATCHER : ALIVE` ·
`IGNORED : 0`"* · `MARG_PICTURE.txt` — *"`days with NO export : 0` and `exports NOT on server : 0`"*.
**"If all three are good, the pipeline is working. Everything else is detail."**

**§2 — the fault flow by symptom**, including the one that cost eight hours:
> **▸ "The pull says unreachable but the medical PC is ON"** — *"**This is the 26-Aug-2026 fault. It
> cost 8h40m and every component was healthy.**"* `ping` → no reply means the machine or the tunnel;
> **a reply means the share is refusing us.** `dir \\100.119.151.40\DDrive\MARGERP\users` →
> *"…security policies block unauthenticated guest access"* → **"THIS IS IT. Windows stopped allowing
> anonymous access to the share. Nothing is broken; nothing was hacked."** Fix by **authenticating**,
> then check the task's Run-As account, because credentials are per Windows user.
>
> **"DO NOT re-enable insecure guest access to 'fix' this. Forums recommend it. It switches off a
> protection that exists to stop a machine on the network reading shares without proving who it is —
> on the PC holding patient records. The credential above takes a minute and keeps the protection."**

**§2a — the D347 correction** · **§3 — routine maintenance**, whose most useful row is *"**after
teaching the router a new report type** — do **nothing**; the pull re-judges quarantine by itself"*
and *"**Never hand-copy a file into a type folder — that is how the index came to disagree with the
disk.**"*

**§5 — what to send Claude**, best to worst, *"the first is usually enough on its own"* — and
**"Do not paste a token, or a file containing one. Claude reads the live token off the medical PC
itself and never needs to see it."**

**§6 — the things that will bite:** a day that isn't filed holds its own Marg data out of the books,
**by design (F-113)** · emptying `_spool` re-imports everything · never hand-copy a report into a
type folder · never hand-copy a token · **"The medical PC's watcher starts at LOGON. A machine left
at the login screen after a reboot captures nothing — the heartbeat is what tells you."**

> **⚠ FOUR WRONG CLAIMS, and one of them is live right now.**
> **§2's 401 diagnosis contradicts its own §6 and the code** — it says a 401 means *the server's*
> token changed *"because the sender reads it live from the medical PC"*; but `resolve_token` falls
> back to the manojz **cache** when the share is unreachable, *"which is exactly the five-day failure
> the reference doc §4 describes and which the send log records."* **The correct instruction is: read
> the `token source:` line `marg_gate` prints.** · **§2/§3 `MEDICAL_RECENT.bat` and
> `MEDICAL_INVENTORY.bat`** cannot see `C:\Users\Public\MARG` — *"'Proves' overstates what the tool
> can do,"* and *"the doc instructs the reader to accept 'Marg wrote nothing' as the answer."* ·
> **§4 `_UPLOAD_NOW` "Empty = nothing to do"** — the folder is **never** empty; `refresh_upload_folder`
> always writes a `READ_ME.txt`. The correct test is *"contains only `READ_ME.txt`."* ·
> **§4 the medical folder map omits `token.txt`** — *"Omitting `token.txt` from the folder map of the
> machine that holds it is the significant miss."*
>
> **And the live one:** *"the copy of `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` sitting at
> `D:\Downloads\margsync\` — **the one you would actually open** — is `f02cd8bd…`, the **S201**
> version. The canonical current is `c2b5251f…`, corrected at S202 to carry the guest-access fault by
> symptom. **The operational copy does not contain the fix for the outage that produced it.**"*
> F-134's shape: a derived copy not rebuilt with its source. *(The `f02cd8bd…` value is quoted from
> master v4 §9; it was **not** hashed by this archive — that file is on manojz outside the connected
> folders.)*

### 36 · MARG_INGESTION_REFERENCE_v1 — the server half, and the one rule
**`MARG_INGESTION_REFERENCE_v1.md`** · md5 `4d603b727a91a7c782992f092fc949e3` · **Tier-1 CURRENT**

*"Every statement here was verified against the **live bytes** … and against the **live database**,
queried read-only on 25-Aug. **Nothing is inferred from a doc.**"*

**§0 — THE ONE RULE THAT EXPLAINS EVERYTHING: "The Marg import never touches the money."**
Money = `day_line`, what the maker types. Attribution = `sale_item`, from the export.
*"`finance_ingest.py` **contains no reference to `day_line` at all.** It cannot change a rupee of
recorded revenue. **This is D313, and it is the reason a half-attributed day is not a half-counted
day.** Consequence: **a 'books vs Marg' difference is never missing money.**"*

**§4 — the confidence gate, table by table**, and the two consequences that surprise everyone:

| what the name field holds | confidence | outcome |
|---|---|---|
| marg_report supplied a clinic_id | 0.99 | attributed |
| an ID **and** a name | 0.95 | attributed |
| an ID, no name | 0.60 | **parked** |
| a name, no ID | 0.50 | **parked** |
| nothing at all | 0.99 — the re-parse never runs | attributed to **WALK-IN** |

> 1. *"**A bill with a name is treated 'worse' than a bill with nothing.** That is deliberate, not a
>    bug. The S186/F-114 comment states the principle: '**A review queue is for lines a human can
>    resolve.**' A nameless bill has nothing to look up; a named bill is resolvable, so it waits."*
> 2. *"**`marg_report` and `finance_ingest` both look for a clinic ID, by different rules** …
>    Verified live: 18-Aug bill A003039 (₹190) is id-less to `marg_report` and was ingested. This is
>    why the approvals page's warning **overstates what actually parks, and names the wrong
>    destination** — they go to review, not WALK-IN."*

**§6 — THE SIGNED NET, ONE EXPRESSION, EVERY READER:**
```python
marg_net_sql(a) = SUM(CASE WHEN a.service LIKE '%return%' THEN -a.amount_p ELSE a.amount_p END)
```
*"This exists because on **18-08-2026** the day held one credit note of ₹1,640: the true net was
**20,599** and a second reader displayed **23,879** — out by exactly 2 × 1,640, and close enough to
the figure under dispute to send a real investigation down the wrong road for an hour."*
**"Rule: never write a second way of summing Marg rows."**

**§8 — the review queue and the Docterz plan.** *"The queue already holds exactly the right set …
Verified on 18-Aug: 8 of 8 parked bills carry a name; 5 of 8 also carry a phone; none have neither."*
**The match key will be `bill_date + patient_name + phone_last4`**, the phone **last 4 only** (F-86)
— *"so a full-number lookup against Docterz is not possible. **Worth designing for now rather than
discovering later.**"* And: **"A re-apply wipes and rebuilds the queue for that day … So resolutions
must be recorded somewhere that survives a re-import."**

**§9 — five faults in this half**, including *"**Two parsers look for a clinic ID.** The same class of
fault `marg_net_sql` was created to end."*

> **⚠ §9 ITEM 5 KEEPS A QUESTION THAT WAS RETIRED HOURS AFTER IT WAS WRITTEN.** It says
> `ingest.min_confidence` *"is an owner decision, not a code one."* **D348, minted the same session,
> closed it by MEASUREMENT** — 192 bills over seven days, every one 0.95+ or 0.50, *"a has-clinic-ID
> switch imported from an OCR path that has no OCR here."*
> **A ruling is amended only by a ruling — and a reference cannot keep a retired question alive.**
> The manifest flags the discrepancy rather than silently editing it (F-23) and leaves the ruling to
> the owner. **Three documents still carry the retired question**: this one, `S201_PARKED_BACKLOG` A3,
> and `S201_Month_vs_Marg_Explained`. The fix is a **struck line in place, not a deletion.**
> Open at C4 / C-3 / N4.
>
> **Also: this document is the sole home of the entire ingestion half.** Master v4 §4.5 defers to it
> and carries none of D313's detail independently. **It cannot be retired.**

---

## SESSION 202 · 26 August 2026 — eight hours and forty minutes

### 37 · THE OUTAGE, AND THE D350 CONTRACT
**`S202_Marg_Transport_Resilience_D350_CONTRACT.md`** · md5 `64dfdd17d085642a1174fd034f92b93f`
**DESIGN CONTRACT, for the owner's signature · NOT YET BUILT**

> *"**Every rupee of Sanjeevni pharmacy revenue reaches the books through two Windows PCs and the
> link between them.** On 26-Aug that link failed silently for eight hours and forty minutes."*

**§0 — the fault.** *"At **23:08 IST on 25-Aug** the pull stopped working. It was found at **07:33
the next morning**, and only because the owner asked why a report had not arrived."*

**"Everything was healthy."** The medical PC was on — *"the owner was in an RDP session with it."*
Tailscale was up and showed `medical` as `active; direct 192.168.1.37:41641`. The agent was running,
the watcher was alive, Marg was capturing, Drive was syncing.

**"The single thing that failed** was Windows on manojz applying its default policy against
*unauthenticated guest access* to SMB shares. manojz had been reading `\\100.119.151.40\DDrive` as an
anonymous guest; a policy refresh closed that door."

**Three things made it expensive:**
> 1. *"**Nothing was watching that leg.** Reports piled up on the medical PC while the server showed
>    nothing wrong, because every server-side check watches *arrival at the VPS*."*
> 2. *"**The error message named the wrong causes.** 'Is it switched on and Tailscale connected?' —
>    both were true. **It listed the two innocent causes and not the guilty one.**"*
> 3. *"**A working alternative route was sitting idle.** Google Drive carried the heartbeat across
>    the entire outage without interruption. The captures could have travelled the same way.
>    **Nothing was wired to try.**"*
>
> **"The lesson this contract encodes: a system with two paths and no switch has one path."**

**§1 — two transports, one automatic switch.** Primary Tailscale SMB; fallback Google Drive,
*"already installed on both machines … **proven under exactly the failure this contract addresses**,
because it kept working throughout."* **The agent copies, never moves** — *"the primary path must not
be weakened to enable the fallback."* If both are unavailable, `SEND_TO_CLINIC.bat` remains the manual
path **and is never removed (D347)**.

**§2 — verification at both ends, MEASURED, NEVER INFERRED.** *"The rule this comes from: on 26-Aug
**both endpoints were healthy and the link between them was dead. Two green lights either side of a
broken wire.**"* The agent reports Tailscale state, whether `DDrive` is still shared, and power and
session state — boot time, sleep/wake gaps, who is logged in and since when, whether it is an RDP
session. manojz reports **"an actual reachability test of the share, performed, not deduced"**, which
transport this cycle used, and whether any credential exists at all. *"**A changed Tailscale address
must be visible the moment it changes**, not eight hours later … the durable fix is the MagicDNS
name, so the number can never be the fault again."*

**§3 — what B2 must show, the owner's ruling taken as written.** Three states, and the third is the
one worth quoting: **"Running on the FALLBACK — `warn`, and it stays `warn` for as long as it is
true."**
> *"**Why the fallback is a warning and not an 'ok'.** A fallback nobody notices becomes the new
> normal. If the system runs on Drive for three weeks and Drive then fails, there was no warning at
> either step — the first failure was invisible and the second looked like the first. **Working by
> the reserve route is a degraded state, and it must read as one.**"*
And the diagnosis requirement: **"not 'the pipeline failed' but 'the PC answers, the share refuses —
most likely credentials'."**

**§4 — THE REINSTALL KIT, "the part that matters most."**
> *"**Neither PC could be rebuilt today from anything written down.** Everything that carries
> pharmacy revenue lives on two machines, and the knowledge of how to recreate them lives in session
> transcripts."*
One kit per machine, each stating what to install and in what order, which files go where with their
md5s, which credentials are needed and how to store them — **"never the values, which are the
owner's alone"** — the scheduled tasks and the account each must run as, and **"the checks that prove
it worked, so a rebuild is verified rather than hoped."**
**"It must be rehearsed, not merely written. A recovery document nobody has followed is a guess."**

**§7 — the build order, and its rationale:** documents, then verification, then the B2 states, then
the reinstall kits, **then** the fallback. *"**Every step before the last is observation.** If the
fallback is built first and its switch is wrong, the failure it causes is invisible — which is the
fault this whole contract exists to end."*

**§8 — A COUNTER-ARGUMENT, RECORDED.** *"A reasonable objection: **this adds moving parts to
something that worked for months**, and each new part can itself fail … Complexity is not free, and a
fallback that misfires can corrupt the primary path."* And the honest concession: *"if the owner
would rather have only §2, §3 and §5 — verification, visibility and correct documents, without a
second transport — **that is a coherent position and a much smaller change.** It would leave one
path, watched properly, and a rebuild kit. **Today's outage would then have been caught in ten
minutes instead of eight hours, without any new route existing.**"*

> **STATUS: NOT BUILT.** The owner scoped it at the S202 close to **§2 / §3 / §4 / §5**, with
> **§4 the reinstall kits, "Marg and its data first"**, and **§1, the Drive fallback, PARKED at his
> ruling** — i.e. **he took the §8 counter-argument.** That ruling must survive, or a future session
> rebuilds a transport he declined. §5's document corrections were done at S202 for the two
> references; **the D347 correction in the decisions index is still not made.**

### 38 · The pendency audit — N1 to N13
**`S202_PENDENCY_AUDIT.md`** · md5 `5bcd7f86decfdbb158a579e27568f377` · *"every item traced to the
document that states it — nothing carried from memory"*

**§6 — what this sweep found that no list was carrying:**
- **N1 · Six faults documented at S201 were never minted.** *"The close minted F-179…F-183, which
  cover different things. C3–C8 have **no register entry.** **This is F-108's exact shape,
  recurring.**"* Verified by grep returning 0 for each.
- **N2 · The AF-# series has no bridge to the F-# register.** *"AF-1, AF-2, AF-3, AF-4, AF-6 appear
  **zero times** in the Fault Register. **Two parallel finding systems, no reconciliation step** —
  and **AF-5 is unaccounted for in any document I can reach.**"*
- **N3 · Two canonical rows contradict each other** — the "SOLE reference" label.
- **N4 · `MARG_INGESTION_REFERENCE_v1` §9 item 5 contradicts D348.** *"Filed as delivered rather than
  silently edited (F-23); **your ruling owed.**"*
- **N5 · `S201_PARKED_BACKLOG` A3 and A4 are stale** — A4 was answered in-session: *"57% capture,
  **staff behaviour, not a formatting fault**."* *"The doc needs a status pass or it will keep
  re-raising closed questions."*
- **N6 · The coverage map has no row for clinic-finance, Marg capture, the medical PC, manojz or the
  Lab PC.** *"**The document whose job is 'where is the reference for tool X' cannot answer for the
  systems you use daily.**"*
- **N7** retire `S180_Marg_Feed_Transport_Design` · **N8** the `ToMedical` README describes a relay
  disabled at S195 · **N9** `END_OF_SESSION_PROMPT` A8b owed · **N10 the cold kit is DUE** —
  *"**this is the cadence whose lapse permanently lost three canonical documents (F-89)**"* ·
  **N11** `gen_live_pins.py` header says v1.1, the manifest pins v1.2 — *"**a file's own claim about
  itself disagreeing with the register** — small, but it is the F-45 family and D188's own subject"* ·
  **N12** the pin-list path changed · **N13 the later Daily Flow v2 stages have no status anywhere** —
  *"Neither open nor closed."*

**§7 — what was closed at the S202 open:** **F-184 appended and repaired** — *"three instances, one
root. **Twelve absent canonical documents** filed into `KB_canon_all` … The folder's own verification
command now exits 0 with 201 rows OK and the inverse check clean."* · **the S201 F-107 condition
CLOSED** · *"**No live code moved · no live data changed · no pin moved.**"*

### 39 · OWNER_TODO_LIVE — the living list
**`OWNER_TODO_LIVE.md`** · md5 `0f0645f1a78415d571c8fe867b8b0432` · **refreshed at the S202 close**

> *"**This is the always-current truth.** `HANDOFF_RUNBOOK §2` carries the close-time *snapshot*;
> this file edits continuously, which is why it is **deliberately UN-MANIFESTED** — hashing it would
> make Phase 0 fail by design. **Nothing else checks it, so A10 is a numbered step.**"*
> And: *"Tick = struck through, moved to DONE with its session number, **never deleted**."*

**⭐0 #1 — TOKEN ROTATION.** *"Aging since 21-Aug; **still the oldest and highest-severity item in the
project.** Three copies of the Marg token … **Never hand-copy between machines.**"*

**⭐0a — THE BACKUP (F-191c), "the crown jewels":**
> *"Everything we have built is downstream of Marg. **Marg holds the actual pharmacy.**
> Backups are **manual**, every 2–4 days, to `E:\` (an HP USB 2.0 stick permanently attached to the
> medical PC). **Last: 22-Aug.** · **`E:\auto` and `E:\MARGBCKUP\auto` have been EMPTY since October
> 2025.** Automatic backup was configured and **has never once run**, while a human quietly filled
> the gap by hand. · The old financial year was last backed up **17-July**. · **All 308 MB sits on
> one drive attached to the machine it protects** — fine against a dead disk, useless against fire,
> theft or ransomware. · **No restore has ever been tested.** Eleven months of files nobody has
> opened."*

*(**The diagnosis in that paragraph was disproved hours later** — entry 57 §4.2: nothing in Task
Scheduler and nothing at startup runs a backup at all; **it was never scheduled.** The finding stands;
the diagnosis does not, and the vendor question in ⭐0 #9 is built on the wrong one.)*

**⭐0 #5 — F-173, the April-2025 NEFT advice file.** *"Its account-number column is SHIFTED against
its names, so **payments that month may have gone to the wrong accounts.** Still the only open item
where money may already have left for the wrong party."*

**⭐0 #8 — F-185, corrected.** *"I told you patient diagnoses were public. **That was false** — your
`.gitignore` had always excluded them. The real measure: **62 mobile-shaped numbers in tracked files,
no diagnoses, ever** … **Not the emergency I made it.**"*

**⭐3 — blocked, not forgotten**, and it carries the outstanding pendency in one paragraph:
*"`C3`–`C8` … were never minted as F-numbers · the **AF-# series has no bridge to the F-# register**
(AF-5 unaccounted for anywhere) · `SYSTEM_DOC_COVERAGE_MAP` has no row for … the medical PC, manojz
or the Lab PC · the later **Daily Flow v2 stages** … have no recorded status since S189 — neither
built nor cancelled."*

**HOUSEKEEPING:** the cold kit **taken at the S202 close and, for the first time, restore-tested** —
*"extracted to a clean directory, `md5sum -c` exit 0, 214 OK."* And on `END_OF_SESSION_PROMPT` v8:
*"**not needed.** A8b already exists in v7 and was followed; **F-184 was a failure to follow it, not a
gap in it.**"*

### 40 · START_HERE_SESSION_203 — and the rule that came out of S202
**`START_HERE_SESSION_203.md`** · md5 `1576f5f58b2ea348a6343ad3690666e9`

**What S202 did, in one paragraph:** *"Opened as housekeeping, became an incident. **The pharmacy
revenue feed was dark for 8h40m and nothing said so** — found only because I asked why a report had
not arrived. Every component was healthy … **F-187:** the Rs 20,000 that left Darpan's drawer on
17-Aug existed only as prose, settled by **physical count** after a plausible wrong theory was
disproved. **I overruled the assistant on applying the 12-June report and was right.** … Close:
**GREEN, match 47, drift 0.**"*

**⚠ WHAT S202 GOT WRONG, SO IT IS NOT REPEATED — the owner's own list:**
> *"**Six of nine findings were the assistant's.** A gate matching the bare word `OK`. A preflight
> demanding a binary the kit never uses. A generator's correct refusal silenced with `2>/dev/null`.
> **A monitor wired so it could only report success** — built the same morning as the witness
> designed to catch exactly that. **A dead machine's heartbeat read as proof it was alive.** And **a
> false claim that patient diagnoses were public**, pressed on me twice before it was checked
> properly.*
>
> *"**The rule that came out of it: a monitor is proven against the thing it monitors, running, in
> its real state — never against a fixture.** Every one of those surfaced from live data or from my
> own questions, **not from any test.**"*

**And the operating protocol, tightened:** *"**ALWAYS give me the COMPLETE path, and say which
machine it is on.** I said this twice at S202 and was given bare commands and a bare
`/finance/approvals` link. Full URLs. Full paths. Every time."* · *"**Prefer ONE file I double-click**
over a sequence of GUI steps or a long console paste."* · **"Work MAX ON YOUR OWN … bring me
decisions and installs, not keystrokes."**

### 41 · The KB consolidation plan — the gate
**`S203_KB_CONSOLIDATION_PLAN.md`** · md5 `dc8453cc7bbd3fa5d207abc9ea436917` · written at the S202
close · **"NOT YET APPROVED. Nothing is deleted until the owner signs §5."**

**Why now:** *"At the S202 close, project knowledge hit **1,958,788 of 2,000,000 tokens — 98%** — and
eight superseded documents had to be deleted mid-close to finish the routine. **Nothing was watching
that limit.** It is the same shape as F-191: a constraint with no watchdog, discovered by hitting
it."*

**Why it is dangerous:** *"Deletion is precisely the operation this project has been hurt by. **F-89
— a nine-session backup lapse permanently lost three canonical documents.** **The S131 stumps** — two
documents survived only because a cold backup had them; git and Drive did not. **F-23** —
`Diagnostics_v1_7` silently dropped sixteen lines while claiming to carry forward."*

> **"So the governing rule: nothing is retired until it is provably recoverable from TWO independent
> places. Not 'we think it's in git' — proved, by hash, in two stores, before anything moves."**

**§1 — the organising principle, which already existed.** `README_VERIFY.md`: **"project knowledge is
the READING copy; git is the VERIFICATION copy."** Hence the criterion: *"Project knowledge should
hold what a session needs IN CONTEXT … The repository carries everything, including history."*

**§2 — Phase 1, census, nothing deleted.** Four classifications, and *"**Orphans are the finding, not
the flab.** A document nobody registered is one nobody is checking. Expect some, and **expect at least
one that should have been Tier 1 all along.**"*

**§3 — Phase 2, the test that must pass**, and this is the inversion the whole exercise turns on:
> *"**If a session record holds something unique, it is not flab — it is an unregistered canonical
> document, and it gets promoted to Tier 1 rather than retired.** That inversion is the whole reason
> this phase exists."*

**§4 — retirement is a MOVE, never a delete**, into `deploy_kits/_retired_S203/` with its own
`MD5SUMS.txt`, listed as a single Tier-2 folder digest. **Four gates**: md5 present in the cold kit ·
md5 present in git history · the manifest updated **in the same pass** (F-134) · **Phase 0 passes
afterwards.** *"Any document failing 1 or 2 does not move. It gets copied INTO both stores first."*

**§6 — stop it recurring:** a size check at every close, warning below 15% headroom · and **a standing
question in Phase 0: *what is in one store and not the other?*** *"Asked routinely, an orphan cannot
accumulate for a year."*

**§8 — A COUNTER-ARGUMENT, RECORDED:** *"**Flab is cheap; lost documents are not.** … the failure mode
of doing nothing is 'I had to delete eight files during a close', while **the failure mode of doing
this badly is 'the S184 rationale exists nowhere'.**"* And the minimum viable version, offered
honestly: *"add the size check, remove superseded versions from project knowledge only, and leave the
session records entirely. That reclaims headroom, needs no judgement calls, and risks nothing."*

**§7's honest cost:** *"**This should not be done in the same pass as feature work.** Documents are
the one thing here that cannot be rebuilt from a backup of themselves … **Steps 1 and 2 are most of
the value and carry none of the risk** — if the session runs short, **stopping after the census is a
good outcome, not a failure.**"*

---

## SESSION 203 · 26 August 2026 — the day the record was audited against the machine

*Nine documents were written this day, in a traceable order. The order matters: each one found what
the one before it could not see, and the master reference moved through four versions in about eight
hours as a direct result.*

### 42 · The system map, built from the record — 06:32
**`S203_MARG_MEDICAL_SYSTEM_MAP.md`** · md5 `7c8ea601adfe0128febe2a13c6be7c03` (post-banner;
pre-banner `5221196a9e531416cc61aa77f5bc9f5b`, quoted) · *"built from the canonical record; every
canonical document hash-verified against `CANONICAL_MANIFEST.md` before being quoted"*

**§7 — EVERY CONFLICT FOUND IN THE RECORD**, both sides quoted, with which is newer. The eleven:

| | conflict | who wins |
|---|---|---|
| **C-1** | D347 *"NOT load-bearing"* vs the S202 references *"AND IT IS LOAD-BEARING"* | **the S202 references.** The decision-record correction is **still not made** |
| **C-2** | `MARG_PIPELINE_REFERENCE_v1` *"Supersedes S195…"* vs the manifest's *"SOLE reference"* | the reference. **Both Tier-1 CURRENT.** Open at N3 |
| **C-3** | `MARG_INGESTION_REFERENCE_v1` §9 item 5 vs **D348** | **D348.** Three documents still carry the retired question |
| **C-4** | the manifest says `MARG_PIPELINE_REFERENCE_v1` covers *"the two Marg output trees (D: and C:)"* | **the manifest is false — the document contains `C:\Users\Public\MARG` zero times** (grep) |
| **C-5** | Register pins `PULL_FROM_MEDICAL.bat 3c5389d5…`; **the box holds `92f03999d0a14d00b7f552dbb4d44c05`** | **the box** (D321(d), F-169). *"A live F-186 instance; cause not established"* |
| **C-6** | the repo `margpull/` mirror vs the live tooling — `marg_watch.py 25126388…` is *"the OLD watcher"* | **the box is live; the repo mirror is stale and unrecorded** |
| **C-7** | the retention policy vs reality, three ways | the pipeline references. *"The policy is still labelled 'draft' and has never been reconciled"* |
| **C-8** | PC-side pins across S201's own three records — `marg_router.py` reads `d63045b1…`, then `bbc50f91…`; `PULL_FROM_MEDICAL.bat` reads `d4af22f6…`, `090c553a…`, `d64b636b…` | *"**Successive within-session states, not contradictions** — but only the *last* is traceable, and **none of these files is in the KB Register's live-file table at all.**"* |
| **C-9** | F-96 vs F-185 vs the F-185 correction | *"**F-96 was right all along, at roughly ten times its recorded count, without the category that made it alarming.**"* Relevant here because **three copies of `marg_report.py` carry name+mobile+clinic-ID selftest fixtures, deliberately left untouched to avoid manufacturing record-vs-reality drift.** The D320 re-ruling is the owner's |
| **C-10** | the reference shows two watch roots; the completion audit says three | **three.** *"The reference was written earlier that day and never updated"* |
| **C-11** | the outbox finding proposes removing the medical sender's human click; **D347 rules it stays and is never removed** | **D347 is the ruling.** *"A reader of the S201 finding alone would think AF-1 was on a path to removal. **It is not**"* |

**§8 — THE SHORTEST TRUE SUMMARY**, and it is the best five lines in the whole document set:
> - **The medical PC generates everything and is protected by the least.**
> - **manojz does everything else, alone, and half its tooling exists nowhere but on its own disk.**
> - **The VPS can see nothing on either machine except what manojz chooses to tell it every ten
>   minutes.**
> - **One link — Tailscale SMB — carries every report, and there is no second one by the owner's own
>   deliberate ruling.**
> - **The one thing nothing protects is Marg's own data.**

**SUPERSEDED 26-Aug** by the master, *"which corrects three of its statements — AF-1 'still armed',
the backup 'configured Oct-2025 and never once run', and the 'four-copy `marg_report.py` problem'.
**It was written from the record; the master was written from the machine.**"* **Its §5 D350
item-by-item gap tables are not carried anywhere and stay in it.**

### 43 · The code truth map — what the code actually does
**`S203_MARG_CODE_TRUTH_MAP.md`** · md5 `4a7ff0a62eff51ed2c61e3aab3aa2e8b` · read-only code audit

**§3.1 — the biggest one: since S201 the pull produces no log at all.**
> The task runs `wscript.exe PULL_HIDDEN.vbs`, and `PULL_HIDDEN.vbs:17` runs the batch **hidden**
> (`0` = `vbHide`). *"Nothing in `PULL_FROM_MEDICAL.bat` redirects stdout to a file. So **every line
> printed by `marg_watch.py`, `marg_router.py`, `marg_rescan.py`, `marg_gate.py send` and
> `pipeline_status.py` is written to a console nobody can see and is then destroyed.** The only
> durable evidence a pull leaves behind on manojz is two lines in `_last_pull.txt`."*
>
> Lost every ten minutes: the capture retry warning · **every router `REFUSED` verdict and reason** ·
> the send's `REFUSED (HTTP %s)` and `server said:` · and *"`pipeline_status.py:309` … — **the
> monitor's own failure to report is itself unreported.**"*

**§3.2 — the named swallow sites**, of which the most serious is quoted here in full because nothing
else records it:
> **`marg_router.py:349-354`** — an unreadable spreadsheet sets `verdict="REFUSED"` and **returns
> before line 406**. *"The file is never copied to `_REFUSED\`, never gets a `.txt` sidecar, and **is
> never appended to `index.csv`**. Only the in-memory `seen` dict is updated, so next cycle it is
> found again, fails again, and is refused again — **for ever, invisibly, with no row anywhere saying
> so.** **This is the most serious single defect I found in the Python.**"*

Also: **no `errorlevel` check** after the watcher/router step, the rescan, or the send · the picture
step discards **stdout *and* stderr**, so *"a stale `MARG_PICTURE.txt` … looks exactly like a fresh
one"* · robocopy codes ≥8 only *print* — *"the offsite copy can fail every ten minutes for ever and
nothing on disk records it"* · **the scheduled task's own process always exits 0 before any work
happens, so Task Scheduler's 'Last Run Result' is meaningless as a health signal** · the router's
`main()` **returns 0 whatever the verdict counts are** · the agent runs the watcher with
`stdout=DEVNULL, stderr=DEVNULL` — *"if the watcher crashes, `agent.log` records only `WATCHER DIED
(exit %s)`, **never why**"* · `INSTALL_AGENT.bat` **kills every Python on the medical PC, not only
the pipeline's** · and the one genuinely well-instrumented failure path: the agent's crash handler,
which writes a traceback locally **and to Drive**, then re-raises.

**§3.3 — the consequence, stated plainly:**
> *"`_last_pull.txt` gains `END … -- ok` on a path that requires only two things to be true: a Python
> exists and the share is reachable. **Capture, routing, rescue, send and the picture can all have
> failed and the stamp still reads `ok`.** `pipeline_status.py:122` then reports that stamp verbatim,
> **so the server is told the pull ended ok too.** … the *reporter* was fixed so it fires on the
> unreachable-share path, but **the thing it reports on — the word `ok` — is still produced by a
> check that does not cover the work.**"*

**§6 #1 — the unresolved one, and it is the sharpest open question in the estate:**
> `marg_gate.py:31-32` (live on manojz): *"A false 'sent' is the expensive failure. **A repeat send is
> free — the server dedupes by content.**"*
> `MARG_PIPELINE_REFERENCE_v1` §3 and `MARG_INGESTION_REFERENCE_v1` §2: *"**The endpoint does NOT
> dedupe by content.** Sending the same bytes twice stages twice."*
>
> *"**If the reference is right, `marg_gate`'s stated safety margin does not exist**, and every path
> that loses `_outbox_state.json` stages **12 duplicate reports** into the approvals queue.
> **Resolve this against the server before anything else in this list.**"*
> **NOT ESTABLISHED which is true of the running server** — the VPS was not reachable from either PC
> this session, and this archive did not reach it either.

**§6 #5 — `README_PULL.md` is two things out of date**, and the consequence is live: *"a reader
following the README would also inherit `marg_router.py`'s defaults, `DEFAULT_ARCHIVE =
r"D:\MargArchive"` / `DEFAULT_OUTBOX = r"D:\SendToClinic\Outbox"` — **running `marg_router.py` by hand
with no arguments on manojz writes to two folders that are not the live ones.**"*

**§6 #9 — the measurement one double-click away and not taken:** a power-history section exists in
the newest `medical_census.py` but does not appear in the `CENSUS.txt` on disk, because the census has
not been re-run since the kit installed. *"**The evidence for the owner's 'pc is pwr off after 9 pm'
is one double-click away and has not been collected.** That single run would turn the backup-window
question from an assumption into a measurement."*

**§7 — two operational items found along the way:** the mirror holds **363** files named
`marg_watch.py.before_…`, one every ~30 s, *"deleted on the medical PC and surviving on manojz only
because `robocopy /E` has no `/PURGE`"* — wreckage from the S201.3 retry loop · and **a second copy of
the upload token in a folder named for deletion**, `…\_to_delete\S201_20260825\loose\finance marg
token.txt`. **"No token value was read or printed by this audit."**

### 44 · The document verification — 82 claims, 17 wrong
**`S203_MARG_DOC_VERIFICATION.md`** · md5 `f9eb31693da2319430dea6b34a419bfa`

*"Every factual claim in the four current Marg reference documents, tested against the live code on
manojz and against measurements taken from the MEDICAL PC on 26-Aug-2026."*

| verdict | count |
|---|---:|
| VERIFIED | **42** |
| **WRONG** | **17** |
| STALE | **12** |
| UNVERIFIABLE | **11** |
| **total** | **82** |

Evidence tags used throughout, and the discipline is the point: **CODE** (file + line, read that
session) · **MEAS** (measured on the medical PC) · **LIVE** (the live state files) · **DRIVE** ·
**REPO**. Every UNVERIFIABLE row says what was *tried*.

The corrections are recorded against their documents at entries 18, 34, 35 and 36. What belongs here
is what this pass found that lives nowhere else:

**§3 — WHAT THE DOCUMENTS OMIT ENTIRELY**, ordered by what would hurt most, restoring from nothing:
> 1. **"THERE IS NO MARG DATABASE BACKUP RUNNING. NOTHING ANYWHERE SAYS SO."** *"`D:\MARGERP\Data` is
>    1,075 files / 0.9 GB of open FoxPro tables … **Four documents describe how to keep a *report*
>    safe in triplicate and not one sentence covers the *database* those reports are drawn from.**"*
> 2. **`pipeline_status.py` — the S202 monitor — is in no document.**
> 3. **`MargBackups\` on Drive is in no document.** *"~180 `.mbk`/`.mst` files copied off the E: stick
>    today — **the only offsite copy of the Marg database in existence. Undocumented means
>    unmaintained.**"*
> 4. **Marg partitions its tables by financial year in the file EXTENSION.** *"Nobody restoring this
>    system would guess that, and it decides which files matter."*
> 5. `medical_census.py` and its products — `CENSUS.txt`, `SURVEY.txt`, `BACKUP.txt`, `heartbeat.json`
>    — *"are in the kit allowlist, are pushed to `FromMedical`, and appear in no document."*
> 6. **Two independent dedupe memories, not one** — `MargArchive\_spool` on manojz **and**
>    `D:\SendToClinic\_captured` on medical. *"Emptying either re-captures everything."*
> 7. **The pull does not watch `D:\MARG REPORTS` or `C:\Users\Public\MARG`.** *"Everything the doctor
>    saves by hand, and every PDF Marg writes to the Public folder, reaches the archive **only** if
>    the medical watcher copied it into `_captured` first. **The watcher is a single point of failure
>    for two of the three sources, and no document says so.**"*
> 8. `DOCUMENT_PDF` is a hard-coded archive type with **no signature** — *"`--learn` cannot produce it
>    and `signatures.json` cannot describe it."*
> 10. **The manojz git working copy is far behind the VPS** — *"no `marg-push` route at all. Anyone
>    treating it as the reference for the server half reads code that predates the whole ingestion
>    chain. **No document warns of this.**"*
> 12. **Restoring the medical PC needs, in order:** `pyportable\` *(there is no system Python — the
>    Store stub silently exits)*, `marg_watch.py`, `medical_agent.py`, `xlsx_stdlib.py`,
>    `medical_census.py`, `token.txt`, `Startup\MargAgent.cmd`, **and Google Drive signed in as
>    `drmka.ortho@gmail.com` with LOCAL (not streaming) content.** *"`medical_agent.py` is
>    **deliberately excluded from the self-update allowlist** — it is the one file that must be placed
>    by hand, **and no document lists this sequence.**"*

**§2 — TRUE BUT EXPIRING**, and the table is a design lesson in itself: *"Each of these is correct
today and will be silently wrong later."* Drive letters (`H:` on manojz, `F:` on medical) —
*"Google Drive for Desktop reassigns its letter when switched between streaming and mirrored. The
batch degrades gracefully — **silently, which is worse**"*, and *"the code already does the right
thing on medical (re-searches every letter each heartbeat). manojz does not; **that asymmetry should
be written down**"* · the file counts — *"**never quote counts as description — quote the file that
reports them**"* · the md5s — *"pin **only** what nothing else measures"* · and, most usefully:
*"'This doc is the single reference' (S195) … **a 'sole reference' label with no expiry is how S195
stayed in circulation after being superseded. Supersession belongs in `CANONICAL_MANIFEST.md`, not in
a self-description inside the document.**"* And: *"'the oldest open item in the project (21-Aug)' —
**the sentence gets less true every day it stays unchanged. State the date, not the ordinal.**"*

**§5 — A NOTE ON THE MIRROR, WHICH MAKES ALL OF THIS WORSE:**
> *"`PULL_FROM_MEDICAL.bat:103` runs `robocopy … /E` with **no `/PURGE`**. `margsync\medical_SendToClinic`
> therefore holds **450 files against the medical PC's 77.** Every file the doctor or a past session
> deleted from the medical PC is still sitting in the mirror, with its original timestamp, **looking
> live** …
> **The mirror is a graveyard, not a census. It is not evidence of what is on the medical PC**, and at
> least three of the errors in this report are what happens when it is read as if it were."*

### 45 · The document inventory and supersession map
**`S203_MARG_DOC_INVENTORY.md`** · md5 `49813347a0776e2823ba278140ab5fef`

**The totals:** **69 documents inventoried** · **8** individually pinned · **17** covered only by a
wildcard row, no md5 · **5** manifest-named but absent from the repo, or un-manifested by design ·
**39 ORPHANS in no manifest row of any kind** (9 repo-side, 30 project-side).

**§4 — contradictions between documents**, both sides quoted and the newer named. Its seven items are
the same family as entry 42's C-list and are recorded there; the two it adds are:
- **#1, the C: output tree** — the fullest statement of the fact recorded at entry 6 and re-discovered
  at entry 31. *"**The newer claim is FALSE and is still in the canon.** The S180 document is right."*
- **#6, the dedupe question** — *"**Not established from the record which is true of the running
  server.**"*

**STATUS: KEEP, with §0.3's correction applied** — this is the exercise's own evidence base.

### 46 · The KB census — and the number that drove the exercise
**`S203_KB_CENSUS_PHASE12.md`** · md5 `2b28f36faf1aabf8aa6a2e72d5d45fa7`

**§1.1 counts:** 167 rows in the project's document list · **163 distinct paths** (four appear twice)
· 1,821 files in the repository · 216 entries in `KB_canon_all` · **87** project docs with a
same-named file somewhere in the repo · **76 with none anywhere** · **90 named nowhere in
`CANONICAL_MANIFEST.md`**, of which **70 also absent from the repo**.
*"**90 documents in project knowledge are named nowhere in the manifest.** This is the plan's own
'most interesting category', **and it is the majority of the project's document set.**"*

**§2.2 — the finding that changes what the exercise is for.** This is the fullest statement of the
C:-tree loss (entry 6):
> *"The blind spot the S201 audit describes — 'the census, the recent-files sweep and the
> ignored-file counter … all three would have answered "nothing" with complete confidence' — **was a
> blind spot in the canon, not in the project's knowledge. The fact was recorded; it was recorded in
> the one store nothing indexes, hashes or reads.**
> **That is what an unregistered canonical document costs, measured in a real outage.**"*

**§2.3 — a second concrete cost, still live:** *"`OWNER_TODO_LIVE` ⭐0 item 7 requires **AF-3's
duplicate-advance scan** before the August close … **The scan command exists in exactly one place**,
`AUDIT_RUN_2026-08-24_slice1.md`, which has no repo copy and no manifest row. `AF-3` returns **zero
hits** in all four canonical stores. **If that document were lost today, the instruction would survive
and the means of carrying it out would not.**"*

**§3.1 — a correction to the premise of the whole exercise, and it is the most important paragraph in
the document:**
> The plan is founded on *"1,958,788 of 2,000,000 tokens — 98%"*, and the API today reports
> `knowledge_size: 1,404,142`. Three documents pulled as files and measured directly:
> ```
> KB_History_Archive_v1_49_S202.md    897,225 bytes   md5 06c6670a8a1155959e4f0961ad58e7c5
> KB_Register_v5_54_S202.md           380,810 bytes   md5 8fede84d7126e13fca17418e449f9d0a
> Fault_Action_Register_v2_41.md      344,065 bytes   md5 4883e3bdf08cba92da7597448e00f2da
>                                   -----------
>                                   1,622,100 bytes   -- three documents
> ```
> **"1,622,100 > 1,404,142."** Three documents alone exceed the reported total, before the
> 261,311-byte manifest and the other 159 documents are counted.
>
> *"**So the headroom number the consolidation is being driven by does not mean what it appears to
> mean.** … This matters directly: Phase 4 proposes 'warn below 15% remaining' — **that watchdog
> would be built on a metric nobody has validated. Validating it is a cheaper and safer first move
> than any deletion.**"*
>
> *(Those three hashes are quoted from the census, which computed them on files pulled from project
> knowledge. This archive could not recompute them — those files are in `KB_canon_all/`, outside this
> folder, and were not re-hashed here.)*

### 47 · The pendency reconciliation — and AF-5
**`S203_PENDENCY_RECONCILIATION.md`** · md5 `a70621d06a07d077eaa0fa032fedec5f`

**Thread 1 re-tests C3–C8 one at a time:** C3 **STILL TRUE**, recommend an F-number · C4 **STILL
TRUE** · C5 **NO LONGER TRUE AS WRITTEN** — *"there is no guard to run"* — with one new candidate in
its place · **C6 STILL TRUE, and recommended as the highest-priority of the six** · C7 **STILL TRUE
IN SUBSTANCE, PARTIALLY MITIGATED** · C8 **STILL TRUE, DELIBERATELY** — *"resolve it through the
AF↔F bridge."*

**Thread 2 — AF-5 is not unaccounted for. It was dropped in transcription.**
> *"`S202_PENDENCY_AUDIT` §6 N2 says 'AF-5 is unaccounted for in any document I can reach.' **That is
> resolved.** AF-5 is written out in full in `AUDIT_RUN_2026-08-24_slice1.md`, between AF-4 and AF-6,
> with its own heading, class, evidence and severity. **What happened is narrower and more
> instructive: `S201_PARKED_BACKLOG` §E — the doc that transcribed the Auditor's findings for triage
> — lists AF-3, AF-4 and AF-6 and silently skips AF-5. Everything downstream read §E, not the run, so
> the label vanished from the project's working memory while the run file sat unchanged.**
>
> **The fault itself was never lost, only its name.** AF-5's substance survives under two other
> identifiers raised independently the same session: `S201_PARKED_BACKLOG` **B4** and **C4**."*
>
> And re-verified that day: live server parser `6411a57d4517e0a06a02e1045b354138`; the guard parser
> `28b47d447cfd966411742055717a5c56`. **Two builds apart, exactly as AF-5 stated, eight sessions
> later.** *"AF-5 should be recorded as **STILL TRUE and re-verified**, not as missing."*

**The bridge, and the root cause is documentary rather than accidental:** `AUDITOR_SEED_v1.md`
instructs the Auditor to *"continue the existing F-## series"*, which S196 overrode — so the run
emitted an AF-series, and **nothing was ever written to reconcile the two.**

**Thread 4** re-checks the later Daily Flow v2 stages and finds them **neither built nor cancelled**
— the shape of the finding being that *"the decisions index records that a decision was **made**,
never whether it was **done**. **A built/not-built column is the one structural fix that would catch
this class unaided.**"*

### 48 · THE PRESERVATION PASS — the precondition for everything after it
**`README_S203_MARG_CANON.md`** · md5 `4acbc47d4050bb194ee80115c24006d7` · ~09:44, 26-Aug

*"Every document in this folder concerns Marg, the pharmacy feed, or the MEDICAL PC, and **existed in
exactly one store — the claude.ai Project — with no copy in this repository and none in the cold
kit**."*

**Why it exists, in its own words:** *"This project has lost documents before, permanently. **F-89** —
a nine-session backup lapse **permanently lost three canonical documents**. **The S131 stumps** — two
more documents survived only because a cold backup had them; **git and Drive did not.**
The governing rule adopted at S203 is that **nothing is retired from project knowledge until it is
provably recoverable from TWO independent stores, by hash** … **Before this folder existed, that rule
could not be satisfied for any Marg/medical document: there was one store.**
**This folder is the safety net that makes the S203 KB consolidation safe to attempt.**"*

**How the copy was made, and the check is the point:** *"Each file was read from the Project with
`project_read`, written byte-identically into a container, and copied here; **every file that landed
was then re-hashed on this machine and compared against the container copy** before this README was
written. **Any mismatch would have been reported and the file would not be listed as preserved.**"*

**What it is NOT:** *"**Not a replacement for the Project** — nothing was removed. **Not
manifest-pinned** — these rows are not (yet) in `CANONICAL_MANIFEST.md` … **Until then Phase 0 does
not verify them.** **Not a decision about retirement. It is the precondition for one.**"*

> **The folder's growth is itself the day's history, and it is recorded in the six `SUMS.md5` files
> retained beside it — every row count computed here:**
>
> | file | rows | when |
> |---|---:|---|
> | `SUMS.md5.before_S203_master` (`4642b0227c49c52957637e65e3eb94c9`) | **52** | the preservation pass |
> | `SUMS.md5.before_v3` (`c73c201250b927db95dcab1514a37c41`) | **55** | after the retirement list |
> | `SUMS.md5.before_pointers` (`728e35904dfb9625413c22bfc9a887bd`) | **58** | after the precedence map |
> | `SUMS.md5.before_reconcile` (`d1d8402b4d547bbd577504112e3f812f`) | **61** | after the pointers |
> | `SUMS.md5.before_v4` (`c0112e39ada23cec9e0833da816c2eca`) | **63** | after the reconciliation |
> | `SUMS.md5` (`b099447b6afe2374093aa995b18053b6`) | **64** | after master v4 |
>
> **Nothing was ever removed. Each generation was moved aside, never deleted** — which is why the
> chain can be read at all.

**STATUS: the folder is still NOT manifest-pinned.** Master v4 §11 item 13 and the retirement list §6
both put pinning **before** any retirement. **And the sharpest open question on the whole exercise,
from the retirement list §4 #5:** *"`git status` was not run (F-131). `OWNER_TODO_LIVE` ⭐0 #3 says the
S202 close is committed locally only until `PUBLISH_ALL.bat` runs. **If the preservation pass is
unpublished, the 'second store' is one disk, not two.**"*

### 49 · Master reference v1 — and the three subjects it lost
**`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md.superseded_by_v2`** · md5 `ffc51713065ac582a79087258fd08438`
*(pre-banner `57d12c8c46dd633a318f096344d02709`, 26,732 bytes — quoted from the retirement list, which
hashed it directly before the banner was added)*

The first consolidation of the whole subject into one document.

> **⚠ It lost three whole subjects, and the loss was found by checking it against the documents it
> claimed to consolidate:**
> - **§4.3 — that the database is ENCRYPTED.** *"§4.1 says '`mdis.c18` is the bill header table,
>   `dis.c18` the drug lines' and stops. **A reader could reasonably conclude those are readable
>   files. They are not.**"*
> - **§4.4 — the money rule and V7's silent truncation.** *"These are the two facts that decide
>   whether a report is *usable*."*
> - **§4.5 — the whole ingestion half.** `D313`, `marg_net_sql`, `phone_last4`, `clinic id` — all
>   absent.
>
> *"**Without that, someone re-opens a closed dead end.**"* Also wrong: the token list and the §10
> counts. **v2 added all three and corrected both.**

**One fault of its own, recorded at the retirement list §0.1:** it was **present in the folder but
NOT listed in `SUMS.md5`** — *"**it is the one document this whole exercise produced and it is the one
file in the folder its own checksum file does not cover.**"* Since fixed; the current `SUMS.md5`
covers all 64 files.

### 50 · Master reference v2 — and the one new conflict it introduced
**`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v2.md.superseded_by_v3`** · md5 `e8c4886890a2620c9c037b4a7bee57ce`
*(pre-banner `fc3058d92570fd12bbdb1d472270b7c9`, quoted from the precedence map, which verified it
against the value it was given)*

v2 closed all three of v1's gaps and corrected the token list to **five distinct stores** and the §10
counts. **Verified by reading v2 in full.**

> **⚠ AND IT GOT §4.3 WRONG — the one place the master was actively wrong.**
> **v2 §4.3, quoted:** *"**So it is genuinely breakable.** … The way in, when it is resumed:
> known-plaintext crib-dragging … Status: **PARKED by the owner on 21-Aug** … not abandoned, and
> **not because it failed**."*
>
> That is **entry 13** — the note superseded on 23-Aug by **entry 14**, including its two
> "confirmations" (`0x30`, rec_len 256) *"which the later analysis names as the coincidences that
> made it look breakable."* **§11 item 12 carried the same error** — *"parked, proven crackable."*
>
> **Why it mattered more than a wording fix**, in the precedence map's words:
> *"§4.3's stated purpose is 'the standing answer to why don't we just read Marg's database?' **As
> written, the standing answer is 'it's breakable, we just parked it' — an open invitation to spend a
> session on a road already surveyed and closed.**"*
>
> **And the cause is the whole reason entry 54 exists:** *"the successor **is in the repo and was
> never in project knowledge**, so a search of the Project alone found only the optimistic version."*

**A naming discrepancy, recorded not fixed** (precedence map §0): *"The repo file is
`…_MASTER_REFERENCE_v2.md`; the Project path is still `claude/MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v1.md`
carrying v2 content. **A document's filename is a claim about itself (D188, F-45 family). Rename the
Project copy to `_v2` at the close, or the next session hashes 'v1' and gets v2's bytes.**"*
**Not established whether that rename was ever done** — the Project store was not reachable from this
archive.

### 51 · The precedence map — and the rule that decides everything
**`S203_MARG_PRECEDENCE_MAP.md`** · md5 `e02653b286705bcda902de6cf11d24cd` · 10:10, READ-ONLY

**Why it exists — the owner's words:** *"your documents match our other kb which also might be having
related data, so as to avoid any conflicts and confusions later on."*
And the assistant's agreement, which is the design case: *"He is right, and the project has already
paid for this failure mode twice … **A master reference that restates what other documents own does
not remove the conflict — it adds a second place to go stale.**"*

**§1.1 — the three-way risk, named.** *"One fact can legitimately appear in three different documents
at once: the **Register**, because it is the current state; the **Archive**, because it happened; a
**reference**, because it explains how the thing works. **None of those is wrong. The failure is that
nothing says which of the three a reader should believe when they diverge — and they diverge
silently, because only one of them is ever updated.**"*

**§1.2 — THE RULE:**
> **"Every fact is OWNED by exactly one document class, decided by the question the fact answers. It
> may be RESTATED elsewhere only as a citation that names its owner. When a restatement and its owner
> disagree, the owner wins — and when either disagrees with a measurement, the measurement wins."**

| class | the question it owns | owner |
|---|---|---|
| **STATE** | *What is true right now?* | the Register's live-file table · master §3.2 (medical-PC pins) · the live state files |
| **MECHANISM** | *How does it work?* | the master · the three references |
| **RULING** | *What was decided?* | the decisions index · the signed contracts |
| **FAULT** | *What is wrong, and is it closed?* | the Fault Register (F-#) · the audit runs (AF-#) |
| **HISTORY** | *What happened, and why?* | **the KB History Archive — append-only, never corrected** |

**§1.3 — the four corollaries that do the actual work:**
> 1. **"HISTORY is never in conflict.** An Archive sentence that is false today is a dated record, not
>    an error — F-23 forbids editing it. **A conflict exists only when a STATE, MECHANISM or RULING
>    document repeats a stale fact.**"
> 2. **"The measurement outranks every document, including the master"** — D321(d), F-169: *the box
>    wins.* The master's own governing line says the same: *"When something contradicts what you see,
>    believe the machine and tell me."*
> 3. **"A RULING is superseded only by another RULING."** *"Conversely a reference cannot keep a
>    retired question alive — but it does, and that is conflict C4."*
> 4. **"A restatement with no owner named is a defect, not a convenience."** *"It is `marg_net_sql`'s
>    lesson generalised: 'never write a second way of summing Marg rows.' The same applies to prose.
>    **Duplication is how the 18-Aug ₹23,879 phantom happened.**"*

**§1.4 — the one-line test to apply to any sentence in the master:**
> **"*If this becomes false next Tuesday, which document does someone edit?* If the answer is not
> 'this one', the master must point instead of state."**

**§2** is a 20-row subject matrix; **§3** lists **D1–D10, ten places the master duplicates a fact
another document owns** — each with *why it will go stale*, of which the sharpest is **D2**:
*"§4.5 writes out the `marg_net_sql` expression. **This is the exact fault it exists to prevent** —
'never write a second way of summing Marg rows.' Two copies of an expression is how the ₹23,879
phantom happened. **Name it and point; do not transcribe it.**"* And **D8**: *"the master lists five
token paths; `MARG_PIPELINE_REFERENCE_v1` §4 owns the inventory and lists three. **On the oldest open
item, two lists of different lengths is worse than one wrong list.**"*

**§4.2 — C16, the catch**, is recorded at entry 50.

**§5 — six draft coverage-map rows** *(superseded by entry 56)*. **§6 — what to do, in order**, whose
first item is *"Correct master v2 §4.3 and §11 item 12 — it is the only place the master is wrong,
and it points a future session at a closed dead end."*

> **⚠ ITS OWN §0 IS A DATED SNAPSHOT.** It records *"`md5sum -c SUMS.md5` → **exit 0 · 55 rows · all
> OK**"*. The folder now has **64**. That is not an error — it is the correct behaviour of a
> verification block written at 10:10 on a folder that grew for the rest of the day. **Recorded so a
> reader does not treat 55 as the folder's size.** It also carries a **BLOCKER** worth preserving:
> *"the `Projects` tool remains disabled … **This document is staged at
> `/home/claude/S203_MARG_PRECEDENCE_MAP.md`** and must be published … by a session that has the
> tool."*

### 52 · The retirement list — 13 out, 8 promoted, 5 undecidable
**`S203_MARG_RETIREMENT_LIST.md`** · md5 `afb0c984e455aa4bdc3dda1954d25bbb` · 09:57, READ-ONLY

**Authority:** the owner's words — *"remove any which need to go or retire, we do all now and here
for once."*
**The gate, and it is not negotiable:** *"a document may be retired **only** if it is provably
recoverable, by md5, from a store other than project knowledge."*

**§0.2 — an independent content check, not a hash echo**, and this is the methodological core:
> *"A matching md5 in `SUMS.md5` proves the repo copy is **internally consistent**. It does **not**
> prove the repo copy carries the same content as the Project copy — **that is F-88's exact lesson.**
> So I ran a second, independent test: for each candidate I grepped the repo copy for distinctive
> verbatim strings **taken from my own full reading of the Project copies earlier today.** Those
> readings came from `project_read`, not from the repo, **so the two sources are genuinely
> independent.**
> **Result: every document tested carries its distinctive content.**"*

**§0.3 — a misattribution corrected, in the author's own earlier report and in the census** — the §4A
correction, recorded at entry 10. *"**The reason was attached to the wrong file.**"*

**§0.4 — THE BLOCKER, stated plainly rather than worked around:** the `Projects` tool was disabled
part-way through. *"I could not re-read any Project document after the tool was withdrawn. Everything
below rests on readings taken earlier in this same session, plus the repo bytes. **Where a document
was never read from the Project at all, it is CANNOT DECIDE, not RETIRE.**"*

**§0.5 — the sequencing condition:** *"An unpinned repo folder is the F-107 / F-184 condition
exactly. `KB_canon_all` went four sessions stale with twelve pinned documents missing and nothing
noticed, **because no numbered step maintained it.** `S203_MARG_CANON` has no numbered step either.
**RECOMMENDATION: pin first, retire second.** … Removing first moves a document from 'one store,
unindexed' to 'one store, unindexed **and unwatched**', which is not an improvement. **The whole cost
of waiting is one close.**"*

**§1 — RETIRE, 13 documents**, each with its repo proof and where its content now lives. Recorded at
their own entries above (17, 19, 13, 15, 29, 25, 26, 23, 31, 32, 5, 3, 42).

**§2 — KEEP + PROMOTE, 8 documents**, each with the unique item that earns it a manifest row —
including *(repo-only)* **`S203_MEDICAL_PC_PINS.md`** at `deploy_kits/S203_CENSUS_BACKUP/`, md5
`976a6f0ccc22318a603d055f81541f71` *(quoted — that folder is outside this archive's scope and the
file was not re-hashed here)*: **"the first medical-PC live pins ever taken"**, the `MargAgent.cmd`
text verbatim, the six things the never-purging mirror gets wrong, and the proof that no scheduled
backup was ever configured. **"Not in project knowledge, not in `S203_MARG_CANON`, in no manifest
row."**

**§4 — CANNOT DECIDE, five items**, and this section is the honest one:
> **#1** the S179 build contract and `S179_B1_Medical_Reconciliation_Report` — *"**I never read either
> from the Project.** … **if that cannot be confirmed, treat it as KEEP.**"* ·
> **#2** six repo-only `S195_*` documents in `KB_canon_S197fold/filed/`, Marg-touching but **not
> opened** — *"no redundancy verdict is claimed for them either"* ·
> **#3** whether any Project copy is byte-identical to its repo copy — *"**Impossible in principle**
> for documents under ~261 KB (inline text may corroborate, never convict *or acquit*), and
> impossible in practice now that the tool is withdrawn. **What I do claim: distinctive verbatim
> content survives in every copy tested.**"* ·
> **#4** Google Drive as a third store — *"`mnt/Clinic Data Archive` **failed to mount** … **absence
> there proves nothing.**"* *(It failed to mount for this archive's session too, on 26-Aug.)* ·
> **#5** whether the repo is published — **"the sharpest open question on the whole exercise."**

**§5.1 — two factual errors found in the master**, both since fixed: the token count wrong **in both
directions** *("'the manojz cache' and `D:\Downloads\margsync\SendToClinic\token.txt` are the same
file … so the list double-counts. And it omits one I can evidence")*, and §10's headline numbers
already stale — *"A reader deciding retirement from §10 would conclude no document can be retired at
all."*

**§5.4 — what the master gets right that nothing else did**, recorded *"because it is the reason the
exercise was worth doing"*: §3.1's list of what is **not** on the medical PC and the striking of
AF-1 · §3.3's warning that the S195 restart recipe kills the supervisor · §4.2's settling of the
backup question **by measurement** · **§5, which did not exist anywhere before** · §2's warning that
`_last_pull.txt`'s `ok` means almost nothing · and §9 #8 crediting the C: tree to 15-Aug.

> **⚠ ITS §1 md5s ARE PRE-BANNER AND NOW STALE BY ONE BANNER.** Expected and by design: the
> banners were added *after* this list was written. `S203_MARG_DOC_POINTERS` §A carries both values
> in a `md5 before` column for exactly this reason, and **the folder's regenerated `SUMS.md5` is the
> current authority.** *(Also, its §0.1 verification block records "52 rows / 54 files" — another
> dated snapshot of a folder that grew to 64.)*

### 53 · Master reference v3 — the correction, and §0.1
**`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md.superseded_by_v4`** · md5 `4364834a652275e4d2f2a8b6457e2028`
*(pre-banner **`579ea885e440e76af73de3ecc4542d71`** — see the warning below)*

v3 did two things: **corrected §4.3** to carry the thorough negative, with the crib-drag paragraph
kept **only as the historical first hypothesis marked superseded (F-23)** and **both** S195 documents
cited *"so the supersession is visible"*; and **added §0.1, the precedence rule** — the ownership
table and its five rules, imported from entry 51 into the master itself.

Its §4.3 also carries the honest post-mortem, which v4 still carries verbatim:
> *"**HOW THIS SECTION WAS WRONG IN v2, AND WHY IT MATTERS.** … The successor **is in the repo and
> was never in project knowledge**, so a search of the Project alone found only the optimistic
> version. **The consequence, had it stood: §4.3's stated job is to be the standing answer to 'why not
> just read the database?' — and it would have invited a wasted session.** **This is the
> two-sources-of-truth failure, caught by checking the master against the documents it claimed to
> consolidate rather than by trusting the newest summary.**"*

> ## ⚠ THE CITATION `579ea885e440e76af73de3ecc4542d71` MATCHES NO FILE THAT EXISTS
>
> **Verified here, 26-Aug:** that hash appears in **16 files** in `deploy_kits/S203_MARG_CANON/` —
> every S203 banner that names v3 as the successor, plus the pointers document, the coverage-map
> addendum, the system map, and two of the `SUMS.md5` generations. **A `find | md5sum` over all 70
> files in the folder returns it zero times.**
>
> **Why:** it is v3's **pre-banner** hash. When v4 landed, v3 was renamed and given a supersession
> banner of its own, moving its hash to `4364834a652275e4d2f2a8b6457e2028`. **Nothing rewrote the
> sixteen citations.**
>
> **This is not a fault of v3.** It is the mechanical consequence of prepending a banner to a
> document that other documents cite by hash — and it is worth stating plainly because **a reader who
> follows the project's own rule ("a filename is not provenance — the hash is") will find that the
> hash resolves to nothing at all.** Recorded, not fixed: **nothing in this archive edits a banner.**

### 54 · THE PROJECT KB WAS THE STALE STORE — the inversion
**`S203_PROJECTKB_WAS_THE_STALE_STORE.md`** · md5 `5f45f0659cfb8f8f6bfc223d5a9ac9f6` · 10:40

*"Recorded because it **inverts the assumption this whole consolidation was built on**, and because
it caused a real error in a master reference the same day."*

**What was assumed:** that project knowledge held the current documents and the repo held copies — *"so
the preservation pass copied project KB → repo, and the consolidation read the Project to decide what
was true."*

**What is actually the case:** two documents exist in both stores, are **not byte-identical**, and
**in both cases the repo copy is the better one** — the encryption finding (the repo copy carries the
superseding pointer) and the guard build state (the repo copy carries four outcome annotations).

> *"**Those four lines are exactly the warning that would have prevented the error.** At S203 the
> master reference asserted that the Marg encryption was 'genuinely breakable' … because the Project
> copy carries no such note and `S195_Marg_decrypt_partial_key.md` **is not in project knowledge at
> all.** The annotation had been written at the S197 fold, into the repo, **and never travelled
> back.**"*

**The rule this earns:**
> **"Neither store is authoritative by position.** The repo is not 'a copy of the KB', and project
> knowledge is not 'the live set'. When the same document exists in both, it must be compared by
> **content, by md5 — never assumed current because of where it sits** (D188, F-88). **A fold that
> annotates a document in one store and not the other creates a divergence that no check currently
> looks for.**"

**Concretely owed:** *"an **inverse check at the close** — for every document present in both project
knowledge and the repo, hash both and reconcile any difference, **keeping the superset.** This is
F-88's shape applied **across** stores rather than within one."*

**What was done:** both `S203_MARG_CANON` copies were **replaced with the annotated repo text** (the
banner kept on top), and *"the project-KB versions are retained beside them as
`*.from_projectkb_unannotated` — **moved, never deleted.**"*

> **⚠ TWO THINGS THIS ARCHIVE ESTABLISHED THAT THE DOCUMENT ITSELF DOES NOT SAY.**
>
> **(a) The reconciliation did NOT keep the superset — and the document does not claim it did.**
> Diffed here: the annotated copy that is now in force **lacks three facts the project-KB sidecar
> carries** (entry 15). *"Keeping the superset"* is named as the rule for the close; **what was
> actually done was a wholesale replacement with the better copy, with the other retained beside
> it.** That is a defensible choice and it lost nothing — **because nothing was deleted.** It is
> recorded here because the three facts now live only in a file whose name says it is superseded.
>
> **(b) `S203_MARG_DOC_POINTERS.md` §E item 3 still lists this reconciliation as STILL OWED** —
> *"Reconcile the two divergent `KB_canon_S197fold/filed/` pairs (§B)"* — when it had been done, in
> the same folder, at 10:40. The pointers document is timestamped 10:11. **A document that describes
> a folder cannot stay true to a folder that is still being worked on.**

### 55 · The document pointers — the fifteen-second answer
**`S203_MARG_DOC_POINTERS.md`** · md5 `9372fac0317ca867b34d2121df99712e` · 10:11

*"**'I found an old Marg document. Is it still true?'** Find it in the tables below. If it is listed,
**it is not current** — the row tells you what to read instead, where that document is, and which
section of the master carries the content. **If it is not listed, and it is not in
`S203_MARG_RETIREMENT_LIST.md` §1, it is current.**"*

**§A** — sixteen retired/superseded documents, each with successor, location, master section, and
**both** the post-banner and pre-banner md5 *("those citations are now stale by one banner, which is
expected and is why both values are here")*.
**§B** — superseded copies **outside** the folder, *"the copies a reader may actually open … They
were out of scope for the bannering pass, so they carry no warning at their top."*
**§C** — **declared superseded but MANIFEST-PINNED — do NOT banner or retire.** *"Editing or removing
any of these before its manifest row is amended **breaks Phase 0 on the next session** (F-184,
F-107). **The fix is a label change in the manifest, not an edit to the document.**"* Four rows:
`S195_Medical_Watcher_LIVE_Reference` · `MARG_INGESTION_REFERENCE_v1` §9 item 5 ·
`MARG_PIPELINE_REFERENCE_v1` §1 and §4 · `AUDITOR_SEED_v1`.
**§D** — **what is NOT retired**, *"listed so this index cannot be misread as 'everything old is
dead'."*
**§E** — five things still owed, including *"**The repo may be unpublished** … **Until it does, the
'second store' is one disk, not two** — which is the whole gate the retirement exercise rests on."*

> **⚠ STALE IN FOUR PLACES, all of them the same mechanism: it describes a folder that kept moving.**
> **(a)** Its one-line answer names the master as **v3** with md5 `579ea885…` — v4 landed 27 minutes
> later, and the hash resolves to nothing (entry 53). A **VERSION NOTE** was appended: *"v4 only ADDED
> section 2.1 and refreshed the section 2 chain table; **it renumbered nothing.**"*
> **(b)** §A row 3's **"md5 now"** for `S195_Marg_dbf_Encryption_Finding.md` reads
> `805f71d7bf5a1cc568dc9d896fdad4b2`. **Hashed here: that is the `.from_projectkb_unannotated`
> sidecar. The live file is `2053ab46f327606dac36b9fc38d9cfc4`.**
> **(c)** §A row 4's **"md5 now"** for the guard build state reads `e1420f1190d40007b5cf3b6e54f9642c`.
> **Hashed here: that is also the sidecar. The live file is `bf1837b76a39e8d32ff80ab6d980c2aa`.**
> Both rows were true when written and were invalidated by entry 54, half an hour later.
> **(d)** §E item 3 lists the reconciliation as owed when it was done (entry 54).
>
> **None of this is carelessness. It is what happens when an index and the thing it indexes are
> written in the same session** — and it is the single most concrete argument for the three-file
> shape this archive exists to create.

### 56 · The coverage-map addendum — six rows the map has never had
**`S203_COVERAGE_MAP_ADDENDUM.md`** · md5 `92b399e34718be6b6299d5aa1552bb41` · **DRAFT — nothing
applied**

*"`SYSTEM_DOC_COVERAGE_MAP_S147.md` is **manifest-pinned at `50085e7564cb83476a6f587782143048`** …
**It was not touched.** Editing it outside a close would change its hash and **halt Phase 0 on the
next session** (D172/D188)."*

**Why they are owed:** *"The map is the project's designated answer to 'where is the reference for
tool X'. It has **23 rows and not one** for clinic-finance, Marg capture, the medical PC, manojz, the
Lab PC or backup/DR — verified. **It is dated S147; the entire estate below was built from S179
onward.**"*

The six rows, with their status marks: **clinic-finance ⚠** *"Split ownership — and the manifest names
only the design document … `S179_Finance_LIVE_State` **describes the Marg adapter as something that
'needs its own adapter'**, i.e. unbuilt — it is **authoritative on design and out of date on state**
… **No consolidated reference exists for the non-Marg half**"* · **Marg capture ✅** *"wholesome set"*,
with two attached conditions · **the medical PC 🟡** *"operational, with a recovery gap … **Until S203
no pin of any kind covered this machine**, and **three live files still have no off-box copy**"* ·
**manojz 🟡** *"Named single point of failure … **audit slice 4, never run**"* · **Lab PC ⚠**
*"**NONE. There is no authoritative document, and this row exists to say so.**"* · **backup & DR 🔴**
*"**The least-protected part of the estate.**"*

**Its fold-in notes are the reusable part:**
> 1. *"**Do not apply this file by copy-paste alone.** Re-hash every md5 above at the moment of
>    folding — `S203_MARG_CANON` gained a pointers document and sixteen banners this session."*
> 2. *"**Update the manifest row … in the same commit as the edit.** The pinned hash becomes wrong the
>    instant the map changes, and a mismatched row **halts the next session's Phase 0.**"*
> 3. *"**Three rows carry a condition that must land with them, not after** … **A ruling is amended
>    only by a ruling** — D347's fix is a decisions-index correction, not a reference edit."*
> 4. *"**Honest gaps, stated as gaps and not filled with a plausible pointer:** the Lab PC has **no**
>    document · clinic-finance has **no** consolidated reference for its non-Marg half · three live
>    medical-PC files have **no** repo path."*

**STATUS: DRAFT. Nothing applied.** The map still has 23 rows.

### 57 · MASTER REFERENCE v4 — the current document
**`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v4.md`** · md5 **`df290c6f5cbb870af6c232db21bc2219`** · 10:38

**This is the document to read. Everything above is why it says what it says.**

**Its governing rule:** *"A statement about a running system is a claim with an expiry date … each
section marks its facts **[MEASURED 26-Aug]**, **[CODE]** with a line reference, or **[DESIGN]** …
**When something contradicts what you see, believe the machine and tell me.**"*
And its provenance claim: *"**Nothing here is carried forward on the authority of an earlier
document** — that practice is what produced the errors this replaces."*

**What v4 added over v3 — §2.1, THE MANUAL STEP:**
> *"**Everything downstream starts with a person clicking in Marg.** Nothing generates the report
> automatically … So this is step zero, and it is written here because **a chain document that starts
> at step two is missing its trigger.**"*
It carries the full report-screen recipe, the export-screen settings, **`Disc.Bill Sign = 2-Bill+Item`
*(proven)*** — and the corrected date range:
> **"⚠ ONE DAY AT A TIME — do not export month-to-date with item detail.** `S180_Marg_Daily_Sale_Button_Settings`
> (15-Aug) specifies `Report From = 01` of the current month. **Do not follow that for an item-detail
> export.** … Current practice, and the correct practice, is **one business day per export**;
> historical backfill is **one file per month.**"
And the two one-second checks: **`Report Type` must be `Detail`**, and **the title line must name the
range you asked for.**

**The things it establishes that nothing before it did:**
- **§3.2 — live pins on the medical PC, the first ever taken.** *"**Why these did not exist before.**
  `verify_live_pins.py` runs on the VPS and cannot reach either PC; the share is read-only and D:-only;
  the mirror never purges. **Drift on this machine was undetectable by construction from the day it
  was set up.**"*
- **§3.1 — what is NOT on the machine**, and the striking of AF-1: *"That file is not on the machine
  … **The fallback works; the fault attached to it cannot fire.**"*
- **§4.2 — the backup question settled by measurement:** *"It is not failing. **Nothing in Task
  Scheduler and nothing at startup runs a backup.** It was never scheduled. **The empty `auto` folders
  were never going to fill.** (115 Marg config files were read and none mentions backup, so the
  setting — if it exists — lives inside Marg's GUI or database and is the vendor's to explain.)"*
  And the easily-missed one: *"the **previous financial year** was last backed up **17-Jul — 40 days
  ago** — and there is one copy of it."*
- **§5 — BACKUP AND DISASTER RECOVERY**, *"**This section did not exist anywhere before today.** Four
  documents describe keeping *reports* in triplicate. **Not one sentence covered the 0.9 GB of
  pharmacy database they are drawn from.**"* And what was built that day: the agent copies closed
  backup files into `MargBackups\` on Drive, **bounded to 64 MB a pass so it can never delay watcher
  supervision**, *"**Never deletes, never overwrites a same-size file, copies via a `.part` name and
  renames, so a half-copy can never pass as whole.**"* Proven on first run: *"`offsite: 38 file(s),
  0.07 GB … 145 file(s) still to copy`. **The pharmacy backups left the machine that holds them for
  the first time.**"* And what it deliberately does not do: *"**It deliberately does NOT copy
  `D:\MARGERP\Data`** … **A backup that cannot be restored is not a backup, so it is not taken.**"*
- **§5.2 #2 — the restore warning:** *"**The restore must go into a NEW or TEST company, never the
  live one.** A restore over the live company with a 4-day-old backup destroys four days of billing
  **and looks like success while doing it.**"*
- **§1.2 — the mirror warning in one line:** *"**⚠ The mirror is not the machine** … **Never conclude
  anything about the medical PC from the mirror. Ask the machine.**"*
- **§9 — twelve corrections to the existing record, struck rather than deleted, per F-23.**

**Its §11 open items, as they stood at 10:38 on 26-Aug:** token rotation (five copies, not three) ·
the restore test into a TEST company · **can `margwin.exe` back up or export from the command line?**
· back up the previous financial year · `marg_router.py:349-354` · carry the backup age to the server
· refresh the stale runbook copy · correct D347 and strike AF-1 · **file the five orphan live tools
into the repo** · resolve the dedupe contradiction against the VPS · **is there a page or line cap on
Marg's Excel export?** · **decryption RETIRED** · **pin `deploy_kits\S203_MARG_CANON\` before
retiring anything.**

> **Two things this archive found that v4 does not carry** — recorded here, not fixed there:
> **(a) S183 in its entirety** (entry 12) — the ₹1,32,375 cash-column overstatement, home medicine,
> and the ₹2,000 variance threshold. **Verified absent by grep.**
> **(b) The cipher's characterisation** from entry 4 — the `19 a3 95 78` prefix, the period-256
> proof, `codepage=437`, and `marguser.csv` as the unencrypted control. **Verified absent by grep**
> (`19 a3 95 78` ×0, `codepage` ×0, `marguser` ×0). §4.3 carries the *verdict* — correctly, and at
> length — but **not the format analysis a future debugger session would need**, and it names *"all
> seven co-encrypted `*.c18` files"* where the S180 survey inventories **32** `.c18` tables and states
> that **every** table in `Data\` carries the prefix. Seven was the *attack sample*, not the set.
> `S180_Marg_Folder_Recon` remains the only home of that material and is correctly listed in v4 §10
> as *"must be preserved, and at risk."*

---

# 58 · WHAT THIS HISTORY TEACHES

Six patterns. Each is drawn only from the entries above, and each names them.

---

### 1 · The never-purging mirror — a copy that grows and never shrinks stops being evidence

`PULL_FROM_MEDICAL.bat:103` runs `robocopy /E` with **no `/PURGE`**. On 26-Aug the mirror held
**450 files against the medical PC's 77** (entry 44 §5) — every file ever deleted on the machine
still sitting there with its original timestamp, *"looking live."*

**It cost three separate wrong statements in one report** (entry 44, claims #19, #20, #50): a startup
script that is not the one running, a parser attributed to the wrong machine, and a guard reported as
present when it is gone. It cost the S201 completion audit its pin table (entry 31). And it is the
same shape one layer down: **`_spool` and `_captured` are both never-pruned dedupe memories**, so
tidying either **re-imports everything** (entries 24 H, 44 §3 #6).

> **The rule:** *"The mirror is a graveyard, not a census. It is not evidence of what is on the
> medical PC. **Ask the machine.**"* And the reason it was undetectable for so long, from entry 57
> §3.2: *"Drift on this machine was **undetectable by construction** from the day it was set up."*

---

### 2 · A monitor that can only report success

The pattern recurs at every layer of this system, and every instance was found by a human noticing
something, never by a test.

- **`_last_pull.txt` says `ok` on a straight-line path with no error test above it** — *"Capture,
  routing, rescue, send and the picture can all have failed and the stamp still reads `ok`"* — and
  `pipeline_status.py:122` **relays that word to the clinic server as pipeline liveness** (entry 43
  §3.3).
- **`SEND_TO_CLINIC.bat` decides success from a response file `curl` does not overwrite on failure**,
  then blacklists the report's hash so it can never be resent — AF-1, reproduced empirically (entry
  22).
- **The A1 `TOTAL_VS_MARG` check read keys the payload has never carried.** Born dead at S195, and
  *"the push-path test stub fabricates the reader's key shape — **the fixture mirrors the reader, not
  the writer**"* (entries 22, 29).
- **Installer v2 printed `UPDATED` after a move that failed** (entry 26 §6) — *"the same fault as
  AF-1's sender, which this session criticised that morning."*
- **The 8h40m outage:** *"**Two green lights either side of a broken wire.**"* And the error message
  *"listed the two innocent causes and not the guilty one"* (entry 37).
- **`marg_router.py`'s `main()` returns 0 whatever the verdict counts are**, and *"the scheduled
  task's own process always exits 0 before any work happens, so Task Scheduler's 'Last Run Result' is
  meaningless as a health signal"* (entry 43 §3.2).
- And at S202, in the owner's own words: **"A monitor wired so it could only report success — built
  the same morning as the witness designed to catch exactly that"** (entry 40).

> **The rules this earned, in the order they were learned:**
> *"**Tests must describe rules, not snapshots**"* (entry 17) · *"**never assert against an unprinted
> shape**"* (entry 19) · the **never-fired witness** — *"any check with zero lifetime firings renders
> `info: never fired since <date>`. **This alone would have surfaced AF-2 on day two instead of
> never**"* (entry 24) · and the one the owner wrote himself:
> **"A monitor is proven against the thing it monitors, running, in its real state — never against a
> fixture."**
>
> And the corollary that is easy to miss (entry 12 §7): *"**A green light is only green about the
> thing it checked.**" The arithmetic self-checks passed on every file and said nothing whatever
> about the description column.*

---

### 3 · A queue with no consumer

`marg_router.py:314-318` copied every verified report into `_outbox` and wrote `uploaded=queued`.
**Nothing on any machine read `_outbox`.** Eleven reports sat there for three days while every
surface was green (entry 23).

**The word itself was the fault:** *"`uploaded=queued` … and 'queued for upload in Outbox' on screen
both assert a pending send. **There is no queue-runner.** Any future reader of that index would
conclude these reports were on their way to the server."*

**And the cause was automation, not neglect:**
> *"**The S195 watcher work quietly replaced the human's reason to click the sender.** Before S195,
> the operator ran GUARD_AND_SEND and the report went. After S195, the export is captured
> automatically, a cmd window flashes, everything *looks* handled — and **the one manual step nobody
> removed stopped being done. The automation did not break the push; it hid it.**"

The same shape appears twice more: **routing only ran if something new was captured**, so a run that
died left files no later run would touch (entry 28) · and **`marg_router.py:349-354`** — an unreadable
file returns *before* archiving, so it is *"never copied to `_REFUSED`, never written to `index.csv`,
retried and re-refused every cycle — **for ever, invisibly, with no row anywhere saying so**"*
(entry 43). **That one is still open** (entry 57 §11 item 5).

> **The rule:** every queue needs a named consumer and a drain count, and **a status word that asserts
> a future action is a claim that must be checked** — not decoration.

---

### 4 · Annotated in one store, not the other

This is the pattern that cost a wrong section in a master reference on the day it was written.

At the S197 fold, `S195_Marg_dbf_Encryption_Finding.md` was annotated **in the repo** with four lines
pointing at its successor. **The project-knowledge copy was never touched, and the successor —
`S195_Marg_decrypt_partial_key.md` — has never been in project knowledge at all** (entries 13, 14).
So on 26-Aug a search of the store sessions actually read found only the optimistic note, and master
v2 §4.3 duly asserted *"genuinely breakable … parked, not because it failed"* as current fact
(entry 50).

> *"**Those four lines are exactly the warning that would have prevented the error.**"* (entry 54)

**The same document family carried a second instance:** `S195_Email_Hardening_and_Marg_Guard_BuildState.md`
existed in **three byte-states under one name** — `bf1837b7…`, `e1420f11…`, `b60efae4…`, all hashed
here — and **neither of the two originals was a superset of the other** (entry 15).

**And it generalises past the two stores:** the repo's shipped `vps_deploy.sh` is stale against the
live one and produced a fault report that had to be retracted the same hour (entry 29) · the
operational copy of the maintenance flow at `D:\Downloads\margsync\` **does not contain the fix for
the outage that produced it** (entry 35) · the repo's `margpull/` mirror still holds *"the OLD
watcher"* (entry 42, C-6) · and the manojz git working copy *"has no `marg-push` route at all …
**No document warns of this**"* (entry 44 §3 #10).

> **The rule this earned, and it is the most valuable single sentence in the archive:**
> **"Neither store is authoritative by position. The repo is not 'a copy of the KB', and project
> knowledge is not 'the live set'. When the same document exists in both, it must be compared by
> content, by md5 — never assumed current because of where it sits."**
> With the concrete remedy: **an inverse check at every close — hash both, reconcile, keep the
> superset.** *"**A fold that annotates a document in one store and not the other creates a
> divergence that no check currently looks for.**"*

---

### 5 · A ruling made on a count that was later measured differently

Decisions in this project have repeatedly been taken on a number, and the number has repeatedly
moved when someone measured it properly. **In every case the measurement won — and in every case the
decision built on the old number outlived it.**

| the count a decision rested on | what measurement found |
|---|---|
| **The C: tree was "found 25-Aug"** (entry 31; still in the manifest) | it was written down **15-Aug**, ten days earlier, in the one store nothing indexes (entries 6, 46) |
| **The token has three copies** (entry 34 §4; still in a Tier-1 reference) | **five distinct stores**, plus a fourth consumer the doc predates. *"On the oldest open item, a rotation list that is wrong about which files exist is the failure mode itself"* |
| **The watcher watches two roots** (entries 18, 34) | **three** — and the third is on C:, invisible to every audit tool built to check it (entry 44 #7, #58) |
| **The auto-backup "was configured and has never once run"** (F-191c, entry 39) | *"**Nothing in Task Scheduler and nothing at startup runs a backup at all. It was never scheduled.**"* The finding stands; **the diagnosis does not — and the vendor question is built on the diagnosis** (entry 57 §4.2) |
| **`ingest.min_confidence` is "an owner decision"** (entry 36 §9) | **D348 closed it by measurement** — 192 bills, every one 0.95+ or 0.50. *"A ruling is amended only by a ruling"* — and three documents still carry the retired question |
| **`marg_report.py`'s drift is on the medical PC** (AF-5, entry 22) | the file is **absent from the medical PC**; the two-builds-old copy runs on **manojz** (entry 44 #20). *"The drift moved machines; the doc still points at medical"* |
| **F-185: "patient diagnoses were public"** | *"**THE CENTRAL CLAIM WAS FALSE.** … 62 mobile-shaped numbers, no diagnoses, ever … **F-96 was right all along, at roughly ten times its recorded count, without the category that made it alarming**"* (entries 39, 42 C-9) |
| **"Project knowledge is at 98% of 2,000,000 tokens"** — the premise of the entire consolidation | *"**1,622,100 > 1,404,142.** Three documents alone exceed the reported total … **the headroom number the consolidation is being driven by does not mean what it appears to mean**"* (entry 46 §3.1) |
| **Marg's CASH column is the cash figure** (entry 1) | over 119 independently-recorded days it **overstates cash by ₹1,32,375** (entry 12) — **and the current master still carries the S179 rule alone** |
| **"no clinic ID → dropped"** | *"**A rule that fits two days and predicts the third wrongly is not the rule**"* (entry 30) |

> **The rules:** *"**the measurement outranks every document, including the master** … **the box
> wins**"* (D321(d), F-169) · *"**A ruling is superseded only by another ruling**"* · and, for the
> counts that are simply snapshots: *"**never quote counts as description — quote the file that
> reports them**"* and *"**state the date, not the ordinal**"* (entry 44 §2).

---

### 6 · An index and the thing it indexes, written in the same session

This is the pattern that produced this file, and the archive's own body is its evidence.

On 26-Aug the folder grew **52 → 55 → 58 → 61 → 63 → 64 rows** in about six hours (entry 48). Every
document written along the way described a folder that had already moved by the time the next one
landed:

- the **precedence map** verifies *"55 rows, all OK"* — the folder now has 64 (entry 51);
- the **retirement list** records *"52 rows / 54 files"*, and its §1 hashes are **pre-banner** and
  stale by one banner (entry 52);
- the **pointers** document names the master as **v3**, which was superseded 27 minutes later, and
  **two of its "md5 now" values now belong to sidecar files created half an hour after it was
  written** (entry 55);
- **`579ea885e440e76af73de3ecc4542d71`** — v3's pre-banner hash — is cited in **16 files in the
  folder and matches none of them**, because prepending a banner to a document moves the hash that
  everything else cites (entry 53);
- and the pointers document **still lists as owed a reconciliation that was completed in the same
  folder, half an hour after it was written** (entries 54, 55).

**None of that is carelessness.** Every one of those documents was correct when it was saved, and
every one of them was made stale by the next honest correction. That is what a flat pile of
equally-loud documents does: **it makes correcting one document a way of falsifying five others.**

> **The rule, which is the project's own D247 pattern and the reason this file exists:**
>
> **Keep exactly one document in the present tense. Let everything else be dated.**
>
> A current-state file may be rewritten freely, because nothing cites it by hash. An append-only
> history may be added to freely, because nothing in it claims to be current. **The failure mode of
> the last three weeks — sixteen citations pointing at a hash that no longer exists — cannot occur
> in a shape where only one file is allowed to move.**
>
> And the honest limit, from entry 41 §8, which applies to this file too:
> **"Flab is cheap; lost documents are not."** Nothing in this archive replaces a source document.
> Every entry above names its file and its hash, **and every one of those files is still on disk.**

---

## WHAT THIS ARCHIVE COULD NOT ESTABLISH

Stated plainly, with where the author looked.

1. **Whether the server dedupes a Marg push by content.** `marg_gate.py:31-32` says it does; both
   Tier-1 references say it does not. *Looked in:* the code truth map §6.1, the doc verification #28,
   the inventory §4 #6, master v4 §9 #11. **The VPS was not reachable from this session.** *"Being
   wrong here stages duplicates."*
2. **Whether `S179_Sanjeevni_Medical_Module_Build_Contract_v2` exists.** *Looked in:* the retirement
   list §1 row 12 and §4 #1, and its own S203 banner, which records a filename search across the
   whole repository returning only the v1. **No successor can be named honestly.**
3. **Whether the repository is published.** `git status` was **not** run (F-131). *Looked in:*
   `OWNER_TODO_LIVE` ⭐0 #3 and the retirement list §4 #5. **If it is unpublished, the second store is
   one disk, not two** — the gate the whole retirement exercise rests on.
4. **Whether the Project copy of the master was renamed to `_v2`/`_v3`/`_v4`.** The `Projects` tool
   was unavailable to the sessions that raised it, and this archive did not reach that store either.
   *Looked in:* the precedence map §0 and §6 #3.
5. **Whether the S180 `Disc.Bill Sign` test export was ever made.** *Looked in:* the button-settings
   document §C, the action register O2, master v4 §2.1 — which specifies the **proven** value
   instead. **Nothing records the outcome.**
6. **Google Drive as a third store.** `mnt/Clinic Data Archive` **failed to mount** for this session,
   as it did for the S203 retirement pass. **Absence there proves nothing.**
7. **The internal count discrepancy in `S180_Marg_Folder_Recon` §4.2** — "all 16 `.c18` tables" against
   §1's "18 of 19" and §3.2's inventory of 32. The copies are gone; **not established.**
8. **Every md5 attributed to a file on the VPS, or to a file outside
   `deploy_kits/S203_MARG_CANON/` and `deploy_kits/KB_canon_S197fold/filed/`, is quoted from the
   document that carries it and is labelled as quoted at the point of use.** Nothing was recomputed
   that could not be reached.

---

*`MARG_MEDICAL_HISTORY.md` · built at Session 203, 26-Aug-2026 · append-only · 58 index rows ·
every md5 computed with `md5sum` on this machine from the file it names, except where the text says
"quoted" · nothing deleted · no manifest-pinned document edited · no banner rewritten · no `git`
command run (F-131) · no token value read or printed · no patient identifier reproduced.*
