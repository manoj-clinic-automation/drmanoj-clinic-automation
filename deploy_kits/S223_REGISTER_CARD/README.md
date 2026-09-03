# S223_REGISTER_CARD — the counter's register, entered on the box

**The owner:** *"wont add in tracker folder for data discipline reasons, and add a card column,
solves the issue, put the sheet on vps as a day entry card, easy to fill, less errors, automatic
matching by your setup"*

All four instructions are in here. The spreadsheet is superseded before it was ever used.

## Why a third record changes everything

The clinic has had **two** records of a day's money — Docterz, and the bank. When they disagree
there is no way to adjudicate: you guess. And the guessing has gone both ways — sometimes the POS
is believed in the morning, sometimes the physical entry is accepted with nobody checking the MPR.

The register is a **third, independent** record, and three is categorically better than two:

| what agrees | what it tells you |
|---|---|
| register + bank agree, **Docterz differs** | the entry was **mis-keyed** |
| register + Docterz agree, **bank differs** | look at the **feed**, not at the counter |
| Docterz + bank agree, **register differs** | the register total was written wrong |
| all three differ | that day needs **a person**, not a formula |

**Two-way checks produce arguments. Three-way checks produce answers.**

## The card

`https://followup.dr-manoj.in/finance/clinic/register` lists recent days and which are done.
Each day opens to nine boxes — **consultation / x-ray / procedures**, each **cash, UPI and card** —
and nothing else. No patient, no bill, no name. Under a minute on a phone.

**Card is here because the owner added it, and it closes a hole.** The ICICI feed carries no card
at all (measured: all 1,115 ingested transactions read UPI). Without a card column the counter would
have had to bury card money inside UPI, and the comparison would have inherited that error and
blamed the counter for it.

Under the boxes, the three records sit side by side with the verdict in a sentence.

## What it refuses to do

- **It never half-saves.** One unreadable number and NOTHING is written — every bad field is named
  and the day is left as it was. A part-saved money row is worse than an unsaved one, because it
  looks finished.
- **A blank box is zero; a typo is a refusal.** `12oo` does not become 1200, and it does not become
  0 either.
- **It never shows a missing statement as zero.** A date the bank has not settled reads
  "not arrived".
- **It never accuses.** The page says in those words that it does not decide who is right. There is
  no "shortage", no "missing", no "responsible" anywhere in it — asserted in the test, not intended.

## Proven — 35/35 GREEN

`EVIDENCE_register_s223.txt`. A real Flask app, a real database, real form posts, assertions on the
database and on the delivered bytes: the gate refuses on GET **and** on POST and writes nothing;
a bad number names both offenders and leaves the table empty; a good save converts rupees to paise,
turns a blank into a real zero, records who and when, and is audited; an edit updates rather than
duplicates and keeps the original author; **all five three-way branches produce the right verdict
and the right sentence**; and a day with no statement reads "not arrived" rather than 0.

**Two of those checks failed first, and both were the test's fault** — one hunted the word "short",
which appeared inside the page's own promise never to say anyone was short; the other looked for a
phrase that HTML had wrapped across a line. F-293, twice more. The tests were fixed, and the page's
wording tightened to "it never accuses anyone", which is better English anyway.

## Not in this kit

A tile. The card is reachable from the Day Revenue page and by address; whether the counter gets a
tile of its own is a decision about their phone screen, not about this build.
