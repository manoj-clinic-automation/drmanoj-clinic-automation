# S538_PACK_PARTS — the accountant pack: splits by their parts, the bank check, one row per charge (D714)

Kit of session 311 (the parent), 12-Oct-2026. Numbers claimed on the System Board (`_numbers` v379): kit S538.
Faults it closes: F-867, F-868, F-869 (the pack only — see *Not touched*).

**The owner, 06:11–06:29 IST 12-Oct, on September's pack:** *"your current split payment in the doctor's revenue report is
confusing and does not clarify us"* · *"any other wallet payment not coming through the email data is not a wallet payment …
only for the Consultation fees"* · *"If the doctor's consultation report can identify this online razor pay payment, then I feel
there is no need for the email setup part."* — and at 07:53 IST, on the preview: *"would not like to raise this to reception or
anyone if the total cash and the online payments are satisfactory then we will keep it aside and populate it in one place where
I can see and manage if required and send it to the manager level Shavez … the rest all seems fine."*

## What it does — `/root/finance/packs.py` and one line of `packs.html`
1. **The income sheet** counts every split payment by its real parts (Docterz prints *Cash: … , Online Payment: …* on the line;
   the server holds them in `clinic_day_tender`). No *split* column. A split whose parts the export did not carry is named
   in its own column, never guessed. Each day's parts must add to its total (a *Check* column says so when they do not).
2. **A booking** made on Docterz's appointment page through Razorpay (into the Yes Bank clinic account) is a **consultation
   line carrying Razorpay's `pay_…` number**; only that fee is the booking — another line of the same visit is expected in
   ICICI (F-869). **Any other *Wallet*** is a reception entry error, shown as such and decided against the bank: online if the
   bank received at least that much more than Docterz shows that day, cash if not, *waiting* while the bank's day is not in.
3. **The bank check — the owner's only:** the month's two totals (Docterz online + card; the card machine's settlements), then
   each day against the settlement credited to the clinic's ICICI account the next calendar day. It is a link on his packs page
   (*the clinic bank check (yours only)* under row 2) — **not** in the accountants' workbook or mail, **not** on Shavez's
   checklist, and no day is put to reception. Giving it to Shavez is the owner's choice (a later small step, at his word).
4. **The payment digest** is one row per charge: a renewal or confirmation mail and a receipt of the same vendor and amount
   within 7 days are one payment (the receipt kept; two receipts are never joined). Its sheet says *payment papers found in
   mail — they overlap the card spends*.
5. The owner's line under pack row 2 gives the month's two totals and the counts — on his page only: the accountants' mail and
   Shavez's checklist no longer carry that line (until now the mail did).

| file | from | to |
|---|---|---|
| `/root/finance/packs.py` | `368aa68cfd03176dce99816043390ea1` | `382081fa886000065e648d63dc793ece` |
| `/root/finance/packs.html` | `d25452a51f2f5fdd5c1e2b39b54bd9ff` | `499069693a21de84fbad09d427a5fb0c` |

Built on the box from the live bytes by `make_s538.py` (10 + 1 counted anchors; nothing written unless each occurs once).
Restarts `clinic-finance`. No table, no setting, no data is written.

**Not touched:** `clinic_money.py`, `finance_clinic_day.py` (its day page still makes a booked visit's procedure line
*portal* — F-869 stays open there), `clinic_register.py`, `clinic_day_pdf.py`.

## Proven before the publish
- `walk_s538.py`: 33 checks on a made-up month (no person, no number) — splits by parts; the booking as the consultation fee
  only; a Wallet decided online / cash / waiting; the bank check's exact, more, less, no-Docterz and waiting days; the digest's
  one-charge, two-receipts and nine-days cases; the accountants' workbook and mail and Shavez's checklist without the bank line.
  A cold review by a fresh agent found one defect (a booked consultation paid as a split was netted against the whole day's
  parts, so another patient's split could turn the booking into a 'Wallet' error); fixed patient by patient and walked (A6b).
  **Negative controls:** the old files fail 13 of them; the pre-review build fails A6b; a copy with the booking rule broken fails 3; with the mail guard
  removed, 1; with the checklist guard removed, 1.
- **September on a copy of the server's database (12-Oct 01:40):** the nine days 11, 14, 17, 19, 22, 23, 24, 25, 29 equal to
  the rupee (and 1-Sep, outside S305's exports); 12-Sep ₹2,950 short; every day's parts add to its total; Apple ₹24,900 once.
  Run in IST and in UTC. The owner saw the September workbook before the install (F-761).
- The installer rehearsed on a made-up root: green, ALREADY INSTALLED, and red after placing puts the old file back.

## Install
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S538_PACK_PARTS/install_S538_PACK_PARTS.sh
```
## Undo
```
\cp -p /root/finance/packs.py.bak_S538_368aa68c /root/finance/packs.py && \cp -p /root/finance/packs.html.bak_S538_d25452a5 /root/finance/packs.html && systemctl restart clinic-finance
```
