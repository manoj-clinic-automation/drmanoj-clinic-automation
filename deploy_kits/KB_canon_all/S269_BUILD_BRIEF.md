# S269 BUILD BRIEF — the parent project, 18-Sep-2026

**One document instead of ten.** What this session changed, what it found, and what the next session
should pick up. Kits S316 – S320. Five live, none owed.

---

## 1 · WHAT WENT LIVE

| kit | machine | what it does | pin |
|---|---|---|---|
| **S316_SHEETS_SEEDED** | VPS | The doctor's two sheets arrive **written**, not blank: 19 X-ray studies (from the S223 extraction of the clinic's own 6,177-entry X-ray register) and 17 procedures (from the S225 rulings). His work is approve · edit · reject · add. | `owner_sheets.py` → `5705f7ff` + two seed files |
| **S317_UNIT_STATE** | VPS | The nightly code bundle now records **whether each scheduled job is switched on** — the `*.wants` enable symlinks read off the disk, plus `systemctl is-enabled` / `is-active` per carried unit. Closes **F-496**. | `code_bundle.py` `a70bf6e2` → `c7f33e55` |
| **S318_UNIT_GAP** | VPS | Carries **seven more unit files** (both `call-*` timers, staff-register, staff-ledger, assetapp, attlistener, attendance-dashboard) and makes the gap report itself: a section naming every enabled unit **of ours** the bundle does not carry. | `code_bundle.py` → `598e55a4` |
| **S319_WITNESS_INFO** | VPS | The health page's never-fired card stops counting the two rows that **cannot** fire (`flags`, `margqueue` — no red branch, by the S195 ruling). It reads **five** now, and the card says why. | `finance_app.py` `c9f73b18` → `0191de01` |
| **S320_CANON_CURRENT** | manojz | The nightly canon gate now watches for **two rows of one family both claiming CURRENT** (F-384 / F-449). Read-only, no new report, no owner step — applied with the file tools. | `canon_sums.py` `9750116d` → `8ad03ef4` |

Publish **`86efcdd`**, 18-Sep 20:12 IST. Canon gate from a fresh clone: **654 of 654**.

---

## 2 · THE FINDING THAT PAID FOR ITSELF THE SAME DAY

**S317's first live run listed every enable symlink on the box — and eleven enabled units matched none
of the bundle's four patterns.** The *code* of the staff register and the asset app had been backed up
for months while **the unit file that starts them was in no store at all**, and two `call-*` timers
were missing although their services were carried.

S318 fixed seven of them within the hour. **Four remain, and they need one word from the owner:**

```
email-agent.timer · fitlog.service · gutlog.service · rxguard.service
```

Ours, or the hosting panel's? The gap section names them every morning until they are ruled on, which
is the point of building the report rather than a one-off list.

---

## 3 · D525 ANSWERED — SEVEN NEVER-FIRED CHECKS ARE REALLY THREE

Read from `finance_app.py`, not from the page:

- **`flags` and `margqueue` cannot fire at all** — only `ok`/`info` branches exist, deliberately. Fixed by S319: the witness no longer counts them.
- **`drawer` fires on 1-Oct** (45 days after the 17-Aug cash count) and **`renewals` on 20-Sep** (seven days before the arms licence). Both prove themselves with nobody doing anything.
- **`backup` and `outbox`** are honest guards whose condition has not occurred; each is provable by fault injection against a *copy* of the books (`FINANCE_DB`, `FINANCE_BACKUP_DIR` and `FINANCE_RENEWALS_STALE_H` are all env-overridable).
- **`watcher` is the real finding.** Its red branch needs `alive is False` **at render time**, and its own code says the agent restarts the watcher within 60 seconds while the realistic failure — the medical PC off or unreachable — is routed to `info` by the S202 ruling. **Fourteen days of green there mean nothing.** Recommended ruling: red during clinic hours when the heartbeat is stale, info outside them. **Owner's call.**

Evidence paper: `03_WORKING_PAPERS\_EVIDENCE\S269\S269_NEVER_FIRED_SEVEN.md`.

---

## 4 · TWO MISTAKES OF MINE, BOTH RECORDED

1. **I told him a published kit had never been installed.** I read the 18-Sep 01:35 bundle, saw the old legs file, and concluded S310 had never run. It had — that morning, *after* the bundle was taken. **The bundle is 01:35 evidence and nothing later.** Retracted in his chat and written into the routine as v16's first new rule.
2. **A URL I put in a kit's closing line does not exist.** `/finance/freshness` 404s and always has: the collector writes a **file**, and no route serves it. Also now a rule: a URL is a live route or it is not printed.

And two publish refusals in two days that I could have caught before his double-click — the `.gitignore` allow line (S316) and a secret-shaped test fixture (S318). Both are v16 rules, and the repository's own gate is now something I run before naming a publish.

---

## 5 · HOUSEKEEPING DONE

- **`END_OF_SESSION_PROMPT_v16`** — built from v15's own bytes by anchored insertion, every v15 line proved still present. Seven new rules.
- **Project-knowledge tranche** — 262 documents checked against the clone and the Cowork manifest; **261 covered**; the one that was not (last night's unattended report) rescued to `01_RESCUED_FROM_PROJECT_KNOWLEDGE\S269_RESCUE\` and labelled a transcription, not a survivor. **Eleven deleted**, all superseded and all with proven survivors — the S265 Register among them, **byte-proven** identical to the repository copy (899,705 B, `9d53e7ee`).
- **`START_HERE_PROMPT_v8` deliberately kept.** The nightly unattended task still points at it; deleting it would have broken tonight's 02:05 run.
- **F-384 measured again** — four families with more than one CURRENT row in the manifest (`END_OF_SESSION_PROMPT`, `START_HERE_PROMPT`, `SANJEEVNI_SYSTEM_BOOK`, `START_HERE_SESSION`), corrected at this close and watched from now on by S320.

---

## 6 · WHAT THE NEXT SESSION PICKS UP

1. **Three one-word rulings** from the owner: the four units · the freshness page · the `watcher` ruling. And whether the nightly task may be repointed from `START_HERE_PROMPT_v8` to `v10`.
2. **The freshness table has no page.** If he says yes, it is a small owner-gated route serving the collector's own HTML — and it makes the URL S310 prints true.
3. **The fault-injection kit for `backup` and `outbox`** (§3), which closes D525 for good.
4. **The bank-SMS feed stays PARKED** until he says otherwise — his words, 18-Sep.
5. **His approvals on the two seeded lists** — 19 X-rays and 17 procedures are waiting on `/finance/clinic/sheets`.
6. **Two contact exports** for D545, whenever he has them.

---

## 7 · THE SECOND SITTING — HIS PAGE, THREE CORRECTIONS, ALL FROM HIM LOOKING AT IT

**S321_XRAY_VIEWS.** He typed in the rename box, typed a price, pressed **Approve** — and got *"page
not accessible"*. Every form on the page carried a **relative** action and the page is served without
a trailing slash, so every button posted one directory up, to routes that do not exist. **S316's walk
was 33/33 green and could not have caught it: it posted the routes by their own full URLs.** One
`<base href>` taken from the blueprint's own `url_prefix` repairs all eleven forms and any added
later. The same kit named every X-ray with its views and priced it from his own tariff — 1 view 300,
2 views 500, 11 x 14 400 and 600, wrist three views 800, pelvis both hips 400, chest AP and PA 300
each — and split chest into two studies because he described two.

**S322_PROC_SIDE.** Ten plaster sites became twenty lines, each carrying the word **fibre**, cast and
slab priced separately, with the consumables copied across; right / left asked on the ILI lines and
the limb X-rays. Side is a **marker, not two more rows**: one line, one charge, and the side belongs
to the visit.

**S323_PROC_ONLY.** His next three words each made the page smaller: the X-ray section off the page
(one click away, still editable), no turn-off on a side that is always asked, the consumables
read-only, and the names read shorthand-first — `A/K (Above knee) fibre cast`, `A/E (Above elbow)
fibre slab`, `ILI (shoulder)`. It also set the X-ray side flags that S322 had reported as **0**: its
safety rule had skipped every row he had already approved, and it printed the zero with no reason
beside it (F-545).

## 8 · THE CLOSE ITSELF

Canon at this close: Register **v5.111** · Archive **v1.108** · Fault **v2.96** (F-539 … F-547) ·
Runbook **v191** · routine **END_OF_SESSION_PROMPT_v16** · entry point **START_HERE_SESSION_271** ·
pins **live_pins_S269close.txt**. Decisions **D550 … D556**.

**One thing needs his hand on manojz:** the 03:10 nightly fired as a catch-up at ~04:03 IST on 19-Sep
and died inside the SSD mirror step, leaving a `.new` file and three reports still dated 18-Sep
(F-546). One double-click of `D:\Downloads\_kbtools\NIGHTLY.bat` puts it right; nothing is lost,
because the 18-Sep mirror is complete and CRC-tested.

**And his first task for the next session, in his own words:** *confirmation on how slips get logged.*
