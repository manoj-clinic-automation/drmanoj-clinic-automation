# THE PERSONAL GOOGLE PLANE — canonical · v1 · S233, 08-Sep-2026

**Tier 1 · reference. Read it before touching anything in the owner's PERSONAL Google account, and
before designing anything that writes to the Payment Register or the renewals.**

Everything here was **read from the projects' own exported source on 08-Sep-2026**, not recalled and
not inferred. Both projects were exported by the owner that day; until then neither had a complete
copy anywhere. The exports live in two places, **and in neither of them is git**:

```
D:\Downloads\ClaudeCowork\04_SOURCE_DATA\S233_GOOGLE_EXPORTS_2026-09-08\
```

```
F:\ClinicBackup\S233_GOOGLE_EXPORTS_2026-09-08\
```

🛑 **THEY MUST NEVER GO INTO THE REPOSITORY.** `Janitor…json` carries passport numbers, driving-licence
numbers, an arms-licence number and its UIN, insurance policy numbers and three email addresses in
plain text; `Renewals_Master_v2` has a tab named `govt ID`. **F-185 forbids numbers in the repository**
and the publish gate would refuse them. This is permanent, not a temporary arrangement. Each folder
carries a `READ_ME_FIRST.md` saying the same thing.

---

## THE FOUR FACTS THAT MUST NOT BE REDISCOVERED

### 1 · THE RENEWALS ALREADY REACH THE VPS. Do not build that again.

`Renewal_Nag.gs` (inside the Janitor project) POSTs the renewal picture to the clinic VPS **on every
daily run — quiet days included**, precisely so the finance health card can show a stale feed the day
the script dies:

```
https://followup.dr-manoj.in/finance/api/renewals-push
```

It sends items inside a 35-day forward window plus anything overdue up to 45 days, authenticated by a
token held as a **Script Property** (`RENEWALS_PUSH_TOKEN`) — never in the source. The same file's
email nag is separate and deliberately quiet: silent unless something falls inside 21 days, then every
3 days, then daily inside 7, and it **keeps shouting until the `RENEWALS` entry in `Code.gs` is
advanced** — which is the action it exists to force.

**So "bring the renewals to the VPS" is largely DONE.** What was missing, and what S233's nightly pull
now takes, is a copy of the **sheet** — the Renewals Master v2 book itself, which is the master the
array and the push are both downstream of.

### 2 · THE PAYMENT REGISTER IS CREATED AND WRITTEN BY THE JANITOR. Do not fight that writer.

`registerSheet_()` **creates** the Payment Register on first run and remembers its id in a Script
Property (`REGISTER_ID`) — the sheet was never made by hand. Then every payment email the janitor
captures appends one row: date · vendor · description · amount · whether a PDF was saved · a Gmail
link. The amount is parsed out of the message body; the vendor comes from a name map.

**Consequence for the planned VPS payments table:** the Google sheet has a live append-only writer
running daily. A VPS table must treat the sheet as an **upstream source**, not as shared state, or the
two will diverge silently. Design it as a read of the sheet, not a second author of it.

### 3 · THERE IS A FOURTH LIMB OF THE BANK CHAIN, AND IT RUNS PERSONAL → CLINIC.

`Bank_Statement_Relay.gs` (also inside the Janitor project) forwards bank-statement mail from four
confirmed senders to the **clinic** account daily at 07:00, marked `[STMT]`, skipping self-sent
copies and anything without an attachment. The clinic side then files it.

**This falls under the standing "Apps Script: read, never act" hold.** The ICICI → VPS bank chain was
described as load-bearing across three projects; **it is four**, and the fourth lives in the account
this project had not mapped until S233.

### 4 · A THIRD PERSONAL BOOK EXISTS THAT NO LIST HAS CARRIED.

`Code.gs` references a **Personal Documents** sheet as `PERSONAL_DOCS_ID`, and updates rows in it —
identity-document records with expiry and lead-time columns. **It has no backup, it is not in the S233
pull, and no census, brief or register had ever named it.**

Recorded, not acted on. It belongs with the other two personal books when that item's turn comes.

---

## TWO REGISTERS OF THE SAME FACTS — a reconciliation owed

The Janitor's `Code.gs` carries its own renewal registry of roughly two dozen entries — domains, the
VPS, insurances, professional indemnity, biomedical-waste authorisations, clinic registration, civic
annual renewals — **and `Renewals_And_Vendor_Register_v1_S232` carries another set.** Neither is
derived from the other. **They will drift.** Reconciling them is queued in `OWNER_TODO_LIVE` ⭐1.

The Janitor's array is also the thing the nag and the VPS push both read, so **it is the operative
one**: advancing a date there is what silences a nag and changes what the VPS sees.

---

## WHAT THE CLINIC ACCOUNT DOES **NOT** HAVE — checked, 08-Sep-2026

The owner asked directly whether this work runs in parallel in the clinic account. **It does not.**
There is a `Clinic_Janitor.gs` inside the clinic's UPI Reconciliation project, but it is a different
thing: it archives ICICI merchant statements and a few other recognised classes out of the clinic
inbox, never trashes anything, and **never touches renewals, credit cards or the Payment Register**.
A search across every clinic-account script found no reference to the Renewals sheet and none to
credit cards.

**So the renewals and card-statement work exists in exactly one account, with one copy — the one
taken on 08-Sep-2026.**

---

## THE OWNER'S STANDING INTENT FOR THIS PLANE

Recorded from his own words, 08-Sep-2026, and not to be re-litigated:

- The legacy Google-Forms analysis system — staff daily form, vehicle tracker, ICICI UPI reports —
  **has migrated to the VPS and its email side is to be retired.**
- **Only the Callback Tracker survives** on the clinic side.
- The two personal projects should have **their data living on the VPS**, because they feed the
  credit-card folder in Drive, the Payment Register, and the renewals.
- **The VPS is a safe place to keep data** — his ruling, closed, not to be raised again.

Detail and sequencing: `claude/S233_GAS_FUTURE_WORK.md`.

---
*PERSONAL_GOOGLE_PLANE v1 · S233, 08-Sep-2026 · every fact read from exported source the same day ·
no number, no token and no identifier from those files appears in this document.*
