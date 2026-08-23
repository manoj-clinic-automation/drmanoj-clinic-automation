# S195 — The bank statement chain, LIVE (23-Aug)

**Status: running end to end, verified.** First filer run archived 8 statement files into
`Clinic Data Archive / Bank Statements / 2026` (six ICICI account PDFs + two account .txt),
mailed them to both accountants, and copied Sanjeevni's to ToMedical. Owner spec: ICICI +
YES monthly statements land in the personal Gmail; **everything** goes to the two
accountants; the **Sanjeevni** ones also go to **Amir** (WhatsApp-only, no email — receives
files on the medical PC).

## The chain, end to end

```
personal Gmail  (ICICI + YES statements)
   │  Bank_Statement_Relay.gs (personal GAS) — forwards once, marker [STMT]
   ▼
clinic Gmail (drmka.ortho)
   │  Bank_Statement_Filer.gs v3 (clinic GAS "UPI Reconciliation", daily 07:00)
   ├─► Drive: Clinic Data Archive / Bank Statements / <YYYY> / <date>_<name>   (all)
   ├─► email to BOTH accountants, one mail per statement, [STMT] stripped     (all)
   └─► Drive: Clinic Data Archive / ToMedical                  (Sanjeevni, PER FILE)
          │  manojz "Marg pull from medical" task, every 10 min
          ▼
       medical PC  D:\SendToClinic\FROM_CLINIC   ← Amir
```

## Confirmed senders (from the 22-Aug survey — not guessed)

`corp.stmnts@icici.bank.in` · `estatement@icici.bank.in` · `estatement@yes.bank.in` ·
`shadab.khan2@icici.bank.in` (ICICI RM — sends all six ICICI accounts in ONE mail) ·
`vikrant …@yesbank…` (YES RM, owner-confirmed; matched as *vikrant AND yesbank*, never bare
`vikrant`). **Excluded:** `credit_cards@` (CC Saver already files those + they auto-forward).
The owner's own `Fwd:` copies share the threads and are skipped (`from:drmanojkragarwal`).

**Why the RMs matter:** the official e-statements are password-protected (customer-id
passwords). The RMs send the same statements as OPEN PDFs. Owner decision: rely on the RM
mails; the official protected ones are backup, forwarded untouched (cleaner audit trail).

## Recipients (baked in)

- Hemant Mourya `hemantmourya47@gmail.com` · Shyam Agarwal `shyamagarwalbly@gmail.com`

## Amir routing — PER ATTACHMENT (v3)

Sanjeevni = **YES a/c ···1923, ICICI a/c ···9819** (owner, 23-Aug). Shadab's mail carries
all six ICICI accounts together, so routing is per-file: only attachments whose name
carries `1923` or `9819` (or `sanjeevni`) go to ToMedical; the rest only archive + go to
accountants. Verified: the first run's `…019205009819….pdf` was archived and has been
copied into ToMedical manually, so Amir's July ICICI statement is en route.

## ⚠ OPEN REQUIREMENT — YES BANK customer-id → account map (owner to supply)

The **official YES e-statements identify the account by CUSTOMER ID (···63 / ···38), not
the account number** — so `1923` does not match them. v3 handles this safely, not silently:
such a statement is archived but NOT sent to Amir, and the run log prints a NOTE naming it
and asking which customer id is Sanjeevni's.

**Owner action (stated 23-Aug):** obtain from YES Bank the full customer-id list for all
YES accounts and share for **live verification**; Cowork then adds the Sanjeevni customer
id (e.g. `···63`) to `SANJEEVNI_MATCH` so official YES statements also route to Amir. Until
then, the RM's open PDFs (which show the account number) cover the need. *This requirement
also belongs on the accountant/requirements checklist the owner maintains.*

## Files (`deploy_kits/S195_STMT/`)

| file | md5 | state |
|---|---|---|
| `Bank_Statement_Relay.gs` | pasted live incl. Vikrant | LIVE, daily 07:00 |
| `Bank_Statement_Filer.gs` **v3** | `f879f0cd354f07a9e467ff6a221561c1` (repo) | paste over live to enable per-file Amir routing |

## Nothing left but two small things

1. Paste **filer v3** over the clinic filer (trigger stays) — enables the 1923/9819 routing.
2. When the YES customer-id list arrives → live-verify → add Sanjeevni's id to the filer.
