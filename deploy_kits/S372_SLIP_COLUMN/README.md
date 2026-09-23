# S372_SLIP_COLUMN — the physical slip number, first column of the daily report

**The owner, 23-Sep-2026:** *"assign that slip number to the daily report which you prepare so that the first column is
the physical slip number. Wherever … physical slip number is not available, leave it blank for the time being till the
staff get used to this workflow."*

**Where it shows.** The Day Revenue page — each day's per-patient table at
`https://followup.dr-manoj.in/finance/clinic/day/<date>` — and the same day's PDF (the one shared to WhatsApp from
`/finance/clinic/share`). Every section (paid consultations, X-ray, procedures, free revisits, free/concession) now
starts with **Slip**, then #, Patient, Clinic ID, Amount, Mode, Shift.

**Where the number comes from.** The Chamber Slip Log (D557): OPD book for consultations, revisits and concessions;
X-ray & Proc book for X-rays and procedures — matched on that day + that clinic ID. A person billed for both a
consultation and an X-ray shows two different numbers on two lines, as on paper. Void/cancelled slips never match;
a person with two live X/P slips shows the lower. Anything unmatched is blank — never a guess.

**Proof.** `walk_s372.py` 16/16: a scratch day with every section, two books, a void slip, a person without a slip,
an id-less line; page and PDF rendered through the real modules; the live modules as negative control (no Slip column,
no slip numbers, identical routes). On 21-Sep's real data the match covers 42 of 46 Docterz lines. Read-only on the
slip log; `finance_app.py` untouched. Restarts `clinic-finance`.
