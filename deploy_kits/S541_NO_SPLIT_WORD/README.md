# S541_NO_SPLIT_WORD — kit S541 (session 313, 13-Oct-2026) · D718 · F-869

**The owner, 05:28–05:34 IST 13-Oct:** *"in the main place those payments were recorded as they were and the split payment should totally disappear from any description"* · *"required mostly from October and if possible from September"* · *"clearly 600 is the consultation and the other is whatever entered in the patient bill whether it is x-ray or a procedure"*.

## What changes

| file | from → to | what |
|---|---|---|
| `/root/finance/finance_clinic_day.py` | f6729d83 → 2c539bad | 20 counted edits: each 'Split Payment' line shows how it was actually paid; the SPLIT PAYMENTS card, the month table's Split column and the *Split ₹* tender bit gone; the day's cash / online / card include each bill's parts; F-869 (portal only for a consultation line with a Razorpay number) |
| `/root/finance/clinic_day_pdf.py` | 150192e2 → 1534818b | 11 counted edits: the same words in the PDF (it reads `finance_clinic_day`'s matching — one place, two outputs); its SPLIT PAYMENTS table gone |
| `/root/finance/packs.py` | 382081fa → ada0860a | 2 counted edits, wording only: the accountants' income sheet no longer says 'split' |
| `/root/finance/clinic_money.py` | b3ddc8d2 → b0408f82 | 5 counted edits, at his word 07:26 (*"everywhere this part of split bill does not come"*): the morning match says *part of bill*, its two other 'split' sentences reworded; F-869 in its own channel rule |

**The matching, per bill (clinic ID of the day):** the bill's parts from `clinic_day_tender` against its 'Split Payment' lines in page order (consultation first). Every item wholly in one part wherever the parts allow it (one to one, or a group of items to one part); otherwise items fill in order and one item shows two parts — *Cash ₹400 + Online ₹400*. No parts → *mode not known*, never guessed. The day's total never moves; what no part covers is shown as *Mode not known*.

**Not touched:** `clinic_register.py` (the counter sheet — it shows no 'split'). `clinic_upi_check.py` and `clinic_upi_report.py` are hand-run tools whose words reach no page; left as they are. No data is written — read-only pages.

## Proof (S313, on manojz, the 13-Oct 01:35 copy of the database)

- every readable string in the four files (not docstrings, not Docterz's own mode word) free of 'split';
- made-up day: 29 checks green (with the morning match's reading and F-869 in its channel rule) — a one-to-one bill, a grouped bill, one item in two parts, a bill with no parts, a booked visit whose procedure line carries the Razorpay number (F-869), the month table, the PDF, the income sheet;
- negative control: the old four files fail 20 of 22 of the same checks;
- 36 real days from 01-Sep: 373 checks green — 42 bills (31 one to one, 7 grouped, 4 one item in two parts), 90 lines given words; every day's modes add to the old page's total; no day's online figure moved; no 'split' on any day page, month table or PDF.
- Before 01-Sep, 15 days have bills whose parts the export never carried; they read *Mode not known* (totals unchanged).

## Install — one line on the VPS

`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S541_NO_SPLIT_WORD/install_S541_NO_SPLIT_WORD.sh`

`DRY=1` before `bash` runs every gate and the walk and writes nothing.

## Undo

`\cp -p /root/finance/finance_clinic_day.py.bak_S541_f6729d83 /root/finance/finance_clinic_day.py && \cp -p /root/finance/clinic_day_pdf.py.bak_S541_150192e2 /root/finance/clinic_day_pdf.py && \cp -p /root/finance/packs.py.bak_S541_382081fa /root/finance/packs.py && \cp -p /root/finance/clinic_money.py.bak_S541_b3ddc8d2 /root/finance/clinic_money.py && systemctl restart clinic-finance`
