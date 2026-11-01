# S682_IPD_IMPLANT_BILLS — IPD kit 4: the implant bills desk, the cheque, the suppliers' ledger

*The parent, session 374, 01-Nov-2026. D804 and D807; the owner's answers on the mock-up (https://claude.ai/artifact/D4BQUWfNKqoXHt5uZBJmcw), 07:39–07:40 IST: the steps' words, "change vendor to supplier", "DTH cheques can be for multiple cases … this is always not shared which bills were cleared in the cheque", the cheque written by "any of us", old cases settled only by him.*

## What it gives them

**The implant bills desk** — the tab *Implant bills* on IPD cases, `/finance/surgery/implants`, for Shavez and Dr Manoj. Every implant line of the new cases, grouped by step, in the order the money moves. A line opens in place with the one entry its step needs.

| step | in his words | the entry |
|---|---|---|
| Not raised yet | the dealer has not sent the bill | the bill: number, date, amount, in whose name, **Scan the bill** |
| Bill raised | bill entry done, bill scanned | credit: the cheque (new, or *part of cheque …*); cash: nothing — Dr Manoj's payment moves it |
| Cheque received | the hospital's cheque is in hand | **Handed to the supplier** (date, note) |
| Paid to the supplier | awaiting the supplier's word | **The supplier confirms** (date, how) |
| Supplier confirmed | the account is square | shown for a month, then under *Confirmed* |

- **The bill** replaces the estimate as the implant's figure; the estimate is kept and shown. *Step back — the bill was wrong* asks why and returns the line to Not raised.
- **The cheque on its own.** At the top of the desk: *A cheque that came on its own — write it, tie its bills later* (the supplier it is made out to, number, date, amount, from). Anyone on the page writes it. Its unassigned money is shown until every bill is tied; a line then takes it as *part of cheque …*, or the cheque's own page takes the amounts against each line. Removing a cheque stays Dr Manoj's.
- **Dr Manoj's payment** on the supplier's page has *This payment settles* ticks for the cash lines; the ticked lines move to Paid to the supplier.
- **Old cases** never come to the desk. On the supplier's page, *Old cases with this supplier's implants — settle one by one*: cleared · I still owe · the supplier owes me, with the amount; it enters the ledger dated that day and the line becomes Supplier confirmed. Dr Manoj only.
- **Section 6** on every case: each implant's bill (with scan), cheque, payment and confirmation, and *Open on the implant bills desk →*.
- **Supplier**, never vendor, on every screen. The addresses `/finance/surgery/vendors` and `/vendor/<id>` are unchanged, so no link breaks.

What stays as it was: the implant line on the case and its step drop-down in section 2; the ledger's arithmetic; the hospital payments; who sees the actual cost (Dr Manoj alone).

## What it changes on the box

One file, `/root/finance/surgery_cases.py` 89a668a9 → ffd19158, **rebuilt on the box from its live bytes** by `make_s682.py` (16 counted edits, the appended desk, the whole-word pass vendor → supplier) and compared to the kit's copy before anything is placed. Data on the first request, additive: columns `surg_implant.estimate_p`, `surg_paper.implant_id`, `surg_cheque_alloc.implant_id`; tables `surg_implant_bill`, `surg_implant_event`, `surg_pay_alloc`. The database is copied before placing. Restarts clinic-finance only.

## Proof

- **Walk** `walk_s682.py`: the previous kits' 260 checks carried (seven rewritten by design and marked) plus section L, 69 checks for kit 4 — **329 of 329** on a made-up database and on a copy of the live one. The control on the live file: 248 of 260 (the kit-4 checks red).
- **Probe** `probe_s682.py` through the real finance app on copies: 22 of 22; its control on the old file: red.
- **Installer rehearsed** on a made-up root: DRY, install, ALREADY INSTALLED, a changed live file refused, a forced red after placing puts the file back.
- **Cold review:** round 1 found one blocker (a `%` in a name would have broken the supplier's page) and two corrections (a removed cheque now steps its lines back; an allocation to a removed implant line counts nowhere) — all built, each with a walk check (L10).

## Install

The publish first. Then one server line, inside the window 04:00–23:30 IST (about two minutes: the walk runs three times on copies):

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s682kit && cp -rp /root/deploy/repo/deploy_kits/S682_IPD_IMPLANT_BILLS /tmp/s682kit && bash /tmp/s682kit/install_S682_IPD_IMPLANT_BILLS.sh
```

**Undo:** the installer prints its one-line undo (the backup `surgery_cases.py.bak_S682_89a668a9` back, clinic-finance restarted). The added columns and tables are harmless to the old file.

No patient name, number or secret is in this kit (F-185).
