> ## ⚠ PARTIALLY SUPERSEDED — §2 ONLY. THE REST OF THIS DOCUMENT IS CURRENT AND IS **KEEP**.
> **§2, the route ranking, was superseded on 26-Aug-2026**: the route was chosen and built, and what
> was built is in `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §2
> (md5 `579ea885e440e76af73de3ecc4542d71`). Read §2 below as history, not as an open choice.
> **§3.4 (the idempotent per-day upsert that makes the feed self-healing), §3.5 (the self-checks),
> §3.6 (PHI handling) and §3.7 (the parallel-run recommendation) are the only home of that material
> and remain current** — `S203_MARG_RETIREMENT_LIST.md` §3 keeps this document for exactly those
> sections.
> **One correction to the record, not to this file:** §4A — the sale-return correlation design
> measured on nine real credit notes — **is not in this document.** It is in
> `S180_Marg_Feed_Request_and_Flow.md` (md5 `efef42c53049ec27758489d950398088`). Both
> `S203_KB_CENSUS_PHASE12` row 51 and `S203_MARG_DOC_INVENTORY` §3 attribute it here; they are wrong,
> as `S203_MARG_RETIREMENT_LIST.md` §0.3 records.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S180 — Marg Daily Sale Feed: Transport Design + Vendor Request

**Session:** 180 (see the numbering correction in `claude/S180_Marg_Feed_Feasibility.md`)
**Date:** 2026-08-15
**Parents:** D313 (finance subsystem architecture) · `S179_Finance_LIVE_State` · `S180_Marg_Feed_Feasibility`
**Status:** DESIGN — nothing built, nothing installed. Needs owner OK before any code.

---

## 0. What changed since the survey

The survey ranked a **background folder watcher** on the pharmacy PC as the cheapest working route
(§4/§5). The owner has pointed out a simpler one that the survey missed because it only looked at
the pharmacy PC and not at what the clinic already has:

> *"staff generate report each day that's printed till now for Google form; now with portal for
> Darpan a soft copy can be easily set up for him to add to day's entry in VPS."*

Two facts in that sentence settle the open question in survey §4/§5:

1. **The report is already generated every day.** It is not occasional. Until now it was *printed*
   and the printout was used to fill the Google Form. So there is no "will staff run it daily?"
   risk — they already do, and have been doing so for as long as the Form has existed.
2. **Darpan already makes a daily entry in the portal** (the `Daily Sale` maker tile, live since
   S179). The feed does not need a new habit — it needs the existing habit to carry a file.

**This replaces the watcher as the primary route.** The watcher is not built.

---

## 1. Why the upload beats the watcher

The watcher is *more* automatic and *less* reliable, which is the wrong trade for this clinic.

| | Portal upload (Darpan) | Folder watcher |
|---|---|---|
| New software on the pharmacy PC | none | an agent that must run forever |
| New scheduled task to maintain | none | yes |
| Network path clinic → pharmacy PC | none needed | required, must stay up |
| Fails silently? | **no** — it is attached to a human action | **yes** — this is its whole failure mode |
| Detection when it stops | the existing missing-day rule (D313) shouts | nothing, until someone notices |
| Cost to abandon later | zero | wasted build |

The decisive point is the fourth row. An unattended watcher that quietly stops is precisely the
class of fault this project keeps minting findings about — F-75 (a cron that silently destroyed its
own artefact every fire), the follow-ups watcher incident of 01-Jul. D313 already commits to
*"missing days shout and never go silent."* An upload attached to Darpan's existing daily entry
inherits that alarm for free. A watcher would need its own, and would then be a second thing to
monitor.

The one thing the watcher buys — removing the human — is exactly what the **vendor routes** (§3)
buy properly, and those need Marg either way.

---

## 2. Route ranking, revised

| Rank | Route | Status |
|---|---|---|
| **1 — build now** | Darpan uploads the `.xls` through the existing Daily Sale tile | design below; needs owner OK |
| **2 — vendor, in parallel** | Marg auto-report scheduler → `users\<id>\report\auto\`, or enable `up_sale`/`up_saleinfo` in the e-business cloud sync | request drafted in §5; Marg works by AnyDesk |
| **3 — do not build** | Folder watcher on `users\*\report\REPORT_1.XLS` | fallback only, if 1 and 2 both fail |
| **4 — do not build** | Decrypting the Marg DBFs (S180 recon) | unsupported; breaks on any Marg update |

Route 1 is **disposable by design.** If Marg switches on either vendor route, the upload control is
deleted and nothing is lost. That is the argument for building it today rather than waiting for the
vendor: the vendor call has a lead time of days, the upload has a lead time of hours, and the two do
not conflict.

---

## 3. Design of the upload route

### 3.1 Where it lives
The existing `Daily Sale` maker tile (`finance_entry.html`, maker `darpan`). One new control:
**Attach today's Marg report**. No new page, no new login, no new service, no new port.

### 3.2 The adapter
Per D313 the line source is *"a pluggable adapter selected by column map, not code."* This is the
`marg_export` adapter in `finance_ingest.py` — a new column map, not a new code path. The column map
is already known from the survey (§4, Appendix B):

```
BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH
```

### 3.3 The money rule — settled at S179, restated here so it cannot drift
```
cash for the day  =  the CASH column
UPI  for the day  =  NET AMT. − CASH
```
**Never** derive the payment split from the `D.R.` mode field. S179 measured this against the bank
and the CASH column won; the mode field (`.CASH` / `.UPI`, sometimes with a trailing `#`) is
descriptive, not authoritative.

### 3.4 Idempotent per-day upsert — this is the important one

Today's sample file covered **01–14 Aug**, not a single day: it was a month-to-date run. The owner
says the report is generated daily. Both can be true — a daily run of a month-to-date report.

**The design does not need to know which it is.** The adapter will:

- parse **every** date section present in the file (`01-08-2026`, `02-08-2026`, …), not just the last;
- **upsert each day by date** — never blind-append;
- so re-uploading the same file twice changes nothing, and a file covering fourteen days corrects
  all fourteen.

This is strictly better than a single-day file: the feed becomes **self-healing**. A day Darpan
forgets to upload is repaired by the next upload that spans it. A day entered wrongly is corrected
by the next upload that spans it.

### 3.5 Self-checks — the file must prove itself before it posts
The report carries its own arithmetic, so the adapter can refuse a bad file rather than post one:

1. each day's parsed bill rows must sum to that day's `DAY TOTAL :` row;
2. the `DAY TOTAL :` rows must sum to the `GRAND TOTAL :` row;
3. the bill count must match the `Total No. of Bills:` footer (345 in the sample).

On any mismatch: **refuse the whole file and name the day that failed.** Do not post a partial file.

### 3.6 PHI handling
Column B (`DESCRIPTION`) carries patient name and phone number. Per D313 the patient-revenue spine
**reads, never posts** — attribution reconciles to the day total and cannot alter it. The uploaded
file and anything derived from it follow the F-31/F-49 rules already in force for `finance.db`,
`scans/` and `medical_*.csv`: never in the repo, never in a git kit, git-ignored before the first
`git add`.

### 3.7 What this replaces — **requires explicit owner OK**
S179 measured the Marg report against the Sarvam OCR path and found the report **exact on 13 of 13
days**. So this adapter should become the **primary** line source for the medical unit, with OCR
demoted to fallback.

That is a change to a live, working app. Per the standing protocol — *nothing already live is
rebuilt without explicit OK, and the manual workflow always stays as fallback* — it does not happen
on my initiative. **Recommended shape:** run the upload in **parallel** with what Darpan does today
for one clean period; compare; only then demote the current path. Nothing is retired on day one.

---

## 4. Open questions

| # | Question | Who | Blocks what |
|---|---|---|---|
| 1 | Do the `CN…` credit-note rows carry a negative `NET AMT.`, or a positive amount with a `DR/CR` sign? | the real file | adapter sign handling — **must be settled before the adapter is trusted** |
| 2 | Does Darpan's upload *replace* his typing, or run alongside it during a parallel period? | owner | §3.7 |
| 3 | Is the daily run always month-to-date, or sometimes a single day? | staff | nothing — §3.4 handles both. Asked only to know what to expect |
| 4 | Does the trailing number in `DESCRIPTION` equal the clinic patient ID? | owner (carried from S179) | patient-wise attribution later, not this build |

Question 1 is answered by the file itself the moment it arrives. Questions 3 and 4 block nothing.

---

## 5. Request to share with Marg (they work by AnyDesk)

*Copy-paste block. Phrased as "please do this on our machine", since the vendor connects remotely
and does the work themselves rather than telling us how.*

---

> **Sanjeevni Medicos — Marg ERP 9+ — request for a daily automatic sale export**
>
> We need the daily sale figures to leave this PC automatically each day, without a staff member
> having to click Export. Please connect by AnyDesk and set up **either** of the following — whichever
> your licence supports. Option B is our preference.
>
> **Option A — scheduled/auto report.**
> We currently run *Bill Wise Sales Statement* by hand; it saves to
> `D:\MARGERP\users\<user id>\report\REPORT_1.XLS`. We can see an empty `report\auto\` folder under
> each user. Please enable Marg's scheduled/auto report so this same report is generated
> automatically once a day and written into `users\<user id>\report\auto\`. Please confirm the exact
> filename and folder it will use, and whether the file is date-stamped or overwritten each day.
>
> **Option B — enable sale upload in the e-business cloud sync (preferred).**
> The e-business sync is already running on this machine and uploading masters several times an hour
> (`up_party`, `up_pro`, `up_os`, `up_stype`, `up_group`, `up_payid`, `up_users`). The slots
> **`up_sale`** and **`up_saleinfo`** exist but have not been written since 01-08-2026. Please tell
> us what subscription or setting enables them, and enable it. We also need to know **how we read
> that data from your side** — Marg Books portal, an API, or a scheduled cloud export — as our
> clinic system will consume it, not a person.
>
> **While you are connected, please also confirm:**
> 1. whether any Windows scheduled task already exists for Marg on this PC;
> 2. whether the sender ID for outgoing messages is still the demo sender `MARGDEMO`, and what is
>    needed to move to our own sender;
> 3. whether email of a scheduled report is available on our licence, and what SMTP settings it needs
>    (our mail queues are empty and appear never to have been configured).
>
> Please do not change anything else on this installation, and please tell us afterwards exactly what
> was changed.

---

## 6. What happens next

1. Owner attaches one real `REPORT_1.XLS` → I build the `marg_export` adapter offline, `py_compile`,
   self-checks green, and show the parsed output against the file's own totals before anything is
   installed.
2. Owner shares §5 with Marg by AnyDesk. Independent of step 1.
3. Owner decides §3.7 — parallel run vs straight cutover. Recommendation: parallel.
4. The upload control on the Daily Sale tile is built only after 1 and 3.

*Nothing in this document has been built or installed. No live file has been touched this session.*
