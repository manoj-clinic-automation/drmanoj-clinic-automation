# S399_DAY_TRUTH_5 — the procedure bill the approvals page missed (F-632)

**Sanjeevni project · session 283 · 25-Sep-2026 · kit claimed on board/_numbers v91→v92.**

## What the owner saw
A procedure-medicine sale was not taken off the day's cash on the approvals page. The bill is
**A003806 of 23-Sep, "PROSIJER <patient>", Rs 195 cash** (Darpan's own spelling; the word list has it).
The 22-Sep procedure bill (A003790, 195) was taken off correctly.

## Why (read from the 25-Sep 01:05 server database and the S367 code)
The ingest's lookup ladder (S221, rung *same-day visit*) found a patient for the bill, so it went to
`sale_item` — which keeps **no customer text** — and never to the review queue. `day_resync` pass 2
looked for Darpan's label words **only in the review queue**, so it could never see this bill, and the
day's cash read 195 too high (23-Sep: 11,799; correct 11,604).

The ingest **does** keep the bill's own text for every bill it laddered (`identity_resolution.bill_name`)
and for every bill whose name disagreed with its clinic ID (`identity_dispute.bill_name`).

## The change
`/root/finance/day_resync.py` **ddbb12eb (S367) → c62e98b971fab7c6802b74b9029c291e (S399)**, built by
`make_s399.py` from the live bytes with anchored edits:
- pass 2 also reads the label words in those two tables (amount from Marg's own bill, `sale_bill.net_p`);
- an **approved** day holding a label bill with no deduction is **named** in the run's output, never touched.

No other file. Nothing restarted (the file runs from the existing cron line `# S356_DAY_TRUTH_2`).

## Proof
`walk_s399.py`: 10 checks on a scratch copy of the live database with the walk's own rows (F-627),
incl. the negative control (S367 does not see the bill). Walked RED against the S367 file (6 fail).
On the 25-Sep database: 23-Sep gains A003806 → the day panel reads cash 11,604, without cash 257.

## Also found by the sweep (named, not changed — approved August days, August closed on the counts)
17-Aug A003014 HOME MEDICINE 1,076 and 18-Aug A003043 / A003044 (Rs 1 each) carry no deduction.
The August cash was proved to the rupee against the physical counts (S361), so they were left as they are.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S399_DAY_TRUTH_5/install_S399_DAY_TRUTH_5.sh
```
