# S195 — Why the bank could only witness 8 days in 90

**Finding date:** 22-Aug-2026 · **Status:** cause identified, fixed, backfill run, **closed**.

## The symptom

The new cash/UPI correction checklist read *"Nothing to correct."* That looked like good
news. It was not. A read of the live database showed:

```
bank UPI statements loaded (90d): 8
days in the books      (90d): 80
days that disagree: 0
```

Zero disagreements **out of eight checkable days**. The other seventy-two days had no bank
side at all, so nothing could be checked. An empty checklist that looks clean is worse than
no checklist.

## The cause

Nothing was broken. The pusher (`gas/VPS_Push_UPI.gs`, S179) worked — it simply never looked
back more than three days, and it started late.

Evidence from the connected Gmail:

- ICICI sends `MerchantStatement-DD-MON-YYYY` from `merchantsolutions@icici.bank.in`,
  about **5 messages a day** — three merchant IDs (Sanjeevni / Clinic / NK Pathology)
  across two send times, delivered to `DRMANOJKRAGARWAL@`, `DRMANOJHUF@` and
  `BHAWNAMITAL@`.
- Statements were present in the mailbox continuously back to at least **18-Jul-2026**.
  Of the 141 messages sampled: **132 in INBOX, 9 in TRASH**, 69 still unread. They land in
  Primary and were never being consumed.
- Attachment naming matched the pusher's filter exactly, e.g.
  `100000000306941_MSDR_MANOJ_AGARWAL_CLINIC_26072026_ICICI_POS_CD.xlsx` — so the filter
  was never the problem.
- The only alert the pusher ever sent: **15-Aug-2026 09:38, "UPI push NOT configured —
  FINANCE_VPS_TOKEN is missing from Script Properties."** That was its very first run. The
  token was supplied afterwards, and every run since succeeded silently.

So: the pusher's history began ~14-Aug because that is when it began, and its three-day
window meant it could never reach backwards. **Eight statements was exactly right for a
system that started a week ago and only ever looks three days back.**

## The fix — `gas/VPS_Push_UPI.gs` v2 (`fac84c5b4a5a14b6345d4cce52c1ad39`)

Two changes, both about not losing days. Everything else — URL, token, attachment filter,
MID list, the "remember what was pushed" dedupe, the alert-only-on-failure rule — is
byte-for-byte the S179 behaviour.

1. **Daily window 3 days → 10 days.** A long weekend, a failed run or a holiday used to
   push a day permanently out of reach. Ten days gives the retry room to work.
2. **`backfillUpiStatements()`** — a repeatable history walk over `newer_than:150d`,
   searching **`in:anywhere`**, so statements sitting in Trash are pushed without anyone
   restoring them by hand (the Gmail connector has no permission to untrash, and did not
   need it). Time-guarded at 4.5 minutes (GAS kills a run at 6), and because the dedupe is
   per-file it is fully resumable. Reports `MORE TO DO` or `Complete`.
3. **`verifyUpiPush()`** — reports whether the token and the daily trigger exist, and how
   many files have ever been pushed. Never prints the token, only its length.

Tested against a stubbed Apps Script runtime before shipping: the `.zip` twin, a wrong MID
and a junk attachment are all ignored; the valid files push; a second run pushes nothing and
skips both; the backfill issues the `in:anywhere` query and paginates.

---

## OUTCOME — backfill run 22-Aug-2026 08:06 IST

The GAS project is **"UPI Reconciliation"** in the clinic account (`drmka.ortho@gmail.com`).
`VPS_Push_UPI` is a second script file inside it, alongside the older `Code.gs` that
reconciles the Google-Form figures against the ICICI tabs in the Daily Clinic Reports sheet.
*(Recorded because it took a project export to establish. The trigger list at
`script.google.com/home/triggers` names it in ten seconds if it is ever needed again.)*

One run, 94 seconds:

```
backfill: pushed 134, already had 29, failed 1   Complete: nothing left to send.
Failures: - 100000000312505_MSSANJEEVNI_MEDICOS_23072026_ICICI_POS_CD.xlsx
            -> Exception: Address unavailable
```

That failure is a transient GAS network blip, and by design it is **not** marked done, so
the next run retries it. It is 23-Jul — behind the correction floor either way.

**What the VPS holds now:**

| unit | statements | range |
|---|---|---|
| medical | **56** (was 8) | 06-Jun … 20-Aug |
| clinic | 55 | 06-Jun … 20-Aug |
| lab | 50 | 09-Jun … 21-Aug |

Clinic and lab had **no** bank witness in the finance app before this at all — that is new
capability, not just recovered history.

**And the verdict on the split, now that it can actually be judged:**

```
days that disagree: 8 total — 1 from 1-Aug (Amir's list), 7 older (not chased)
  2026-08-06  books 10779.00  bank 10809.00  +30.00  UPI booked as cash
```

Eight disagreements across roughly fifty-six checkable days, and **exactly one since 1-Aug,
worth ₹30**. The morning cash/UPI split — read off the POS screen and typed by hand — is
being done well. That is worth saying plainly, because the apparatus was built on the
assumption that it might not be, and the honest conclusion from the evidence is that it is.

The apparatus still earns its place: it is what lets that sentence be *said* rather than
hoped, and a ₹30 error on 06-Aug is exactly the size of thing that used to surface three
days later as a drawer that would not balance.

**Note on `medical` ending 20-Aug while `lab` reaches 21-Aug:** ICICI sends a day's
statement the following morning, and the merchants do not all send at the same moment. The
daily 09:30 trigger closes that gap by itself; no action.

## The lesson worth keeping

A monitoring system that can only see one day in ten reports "all clear" in exactly the same
words as one that sees everything. The health page's *UPI evidence* line — which names the
days with **no statement matched** — is what separates the two, and it is the line to read
first, before believing any clean result from the cash/UPI checks.
