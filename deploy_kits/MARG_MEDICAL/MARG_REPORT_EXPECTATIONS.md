# WHAT MARG SHOULD SEND, AND WHEN

**Session 203 · 26 August 2026.** Companion to `MARG_MEDICAL_CURRENT.md`.

> **Why this exists.** `MARG_PICTURE.txt` can tell you a *sale* report is missing, because
> a daily sale report is the one thing the system knows to expect. For every other report
> type it knows the shape but **not the rhythm** — so a purchase export that stops arriving
> for three months looks exactly like one that was never wanted. This file turns "what
> should arrive" from an assumption into a decision.

---

## 1. THE ONE THAT IS ENFORCED TODAY

### `SALE_BILLWISE` / `DETAIL` — **every business day**

The only report that reaches the books. Everything else is archived and read by people.

| | |
|---|---|
| **Due** | one per business day, exported the next morning for the day before |
| **Sundays** | **excluded** — not a gap, never alarmed |
| **Coverage begins** | **2026-08-17** (`MargArchive\_coverage_from.txt`). Before that no daily export existed, so an earlier missing day is pre-history, not a fault. *This line exists because on 26-Aug the picture guessed and claimed 56 missing days.* |
| **Completeness** | proven by an `end_marker` — a truncated export is refused, not filed |
| **Where it goes** | archived → outbox → clinic server → **you approve it** |
| **What "missing" means** | a business day at or after 17-Aug with no export, or an export the server never received |
| **Watched by** | `MARG_PICTURE.txt`: *days with NO export* and *exports NOT on server* — both should read **0** |

**If a day is missing:** generate that one day again in Marg (§3 of `MARG_MEDICAL_CURRENT.md`).
It is picked up within ten minutes. Nothing else to do.

> **`SALE_BILLWISE` / `SUMMARY1` should never be exported.** It has three columns and no
> CASH column, so cash and UPI cannot be separated. The router refuses it and marks it
> not-uploadable. If one appears, someone set `Report Type = Summary-1` by mistake.

---

## 2. THE ONES WITH NO AGREED RHYTHM — **your ruling needed**

These are captured, verified and archived correctly. **Nothing knows when to expect them**,
so nothing can notice when they stop. What is actually on the server today:

| Report | Held | Newest | Proposed cadence | Why that |
|---|---|---|---|---|
| `PURCHASE_BILLWISE` | 1 | 23-Aug | **monthly, on or after the 1st** | it is the input to the Purchase Portal (D335); S198 already set the precedent of one item-wise export per month |
| `PURCHASE_SUPPLIERWISE` | 1 | 23-Aug | **monthly, with the above** | the supplier view of the same month; useful only as a pair |
| `STOCK_CLOSING` | 8 | 23-Aug | **monthly, at month end** | stock valuation is a month-end figure; more often is noise |
| `STOCK_EXPIRY` | 6 | 23-Aug | **monthly** | it is an action list — what to return or push before it expires. Dated by the file's own timestamp, because its only dates are in the future |
| `DOCUMENT_PDF` | 7 | 25-Aug | **on demand** | whatever you print or export by hand. No cadence; never alarmed |

**Say yes, or change the numbers, and I will teach the picture to check them.** Until then
these five types are archived faithfully and watched by nobody.

> **The honest position:** three of the five have been sent **once**, on 23-Aug, in a
> session that was setting the pipeline up. If they were meant to be regular, they have
> been missing for a month and nothing said so. That is exactly the gap this page closes.

---

## 3. WHAT "MISSING" MUST MEAN, PER TYPE

A rhythm without a definition of *late* is not a rule. Proposed:

| Type | Late when | Alarm |
|---|---|---|
| Sale, daily | no export for a business day by **noon the next day** | on the picture, and on the clinic server |
| Purchase pair, monthly | nothing for the previous month by the **5th** | on the picture |
| Stock closing, monthly | nothing for the previous month by the **5th** | on the picture |
| Stock expiry, monthly | none in **35 days** | on the picture |
| PDFs | never | none |

**Deliberately not alarmed, and each for a reason:**
Sundays · any date before `_coverage_from.txt` · a deliberate backfill of an older day ·
several exports of the same day, the latest wins · a delivered report still sitting in
`_outbox`, which is kept by design.

---

## 4. WHEN ONE IS ACTUALLY MISSING

1. **Check the machine is on and logged in.** Nothing runs on the medical PC until someone
   logs in — no capture, no heartbeat, no backup. `heartbeat.txt` older than about fifteen
   minutes means that, and nothing more sinister.
2. **Re-export that one period in Marg.** One business day for sales; one file per month
   for anything historical — never month-to-date with item detail, which truncates
   silently at about day 6.
3. **Confirm from `MARG_PICTURE.txt`**, not from Marg and not from `_last_pull.txt`.
4. If it still does not arrive, send me `_logs\pull_YYYY-MM.log` and `MARG_PICTURE.txt`.
   Those two answer almost everything now that the pull keeps a record.

---

## 5. WHAT THE PICTURE CHECKS TODAY — and what it would check

**Today:** business days covered, days with no export, exports not on the server. **Sale
reports only.**

**Once you rule on §2**, the same page gains one line per type — *last purchase export:
34 days ago, due monthly* — so a report type that quietly stops is visible in the same
place as everything else. That is the build; the ruling is the part I cannot do.

---

*Companion to `MARG_MEDICAL_CURRENT.md`. Cadences in §2 are proposals, not decisions —
they become rules when you say so, and the picture is taught them in the same session.*
