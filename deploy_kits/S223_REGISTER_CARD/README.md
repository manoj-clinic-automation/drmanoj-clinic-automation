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

## THE DRAWER COUNT — and the thing it closes

**The owner, 04-Sep:** *"staff hands over the cash before leaving, to dr Bhawna, and a format is
coming to my mind — they can type the quantities of currencies, with option for coins at bottom,
as a sweep for any such days, it sums up for them, they click ok, or do a recount."*

Built exactly so. **Quantities, never amounts** — counting notes into piles is what a person
actually does, and typing a total invites the total they EXPECT rather than the one in their hand.
₹500 down to ₹10 as notes, ₹20 down to ₹1 as coins underneath, each line showing what it comes to
and a running total as they type. Then **Yes — handed over** (default: Dr Bhawna) or **Count again**.
Alisha does it mostly, sometimes Shivani, rarely Shavez — all three already hold the tile.

**Physiotherapy cash is included in what the drawer should hold**, on the owner's instruction: it
is one physical drawer, so expected = register cash across every section PLUS physio cash.

### And then his "just a thought", which turned out to be the best idea of the night

> *"a figure for the Docterz and mpr reconciliation also? just a thought, but it will solve
> drawer cash"*

**It does, and from the opposite direction.** A bill paid by UPI but rung as CASH makes the
register's cash figure too high — so **the drawer comes up short by exactly that amount, the same
evening**, without waiting days for a bank statement. And when the MPR finally arrives, **the bank
is over by the same figure**. Two independent measurements of one mistake, from opposite ends.

When they match, the screen says it in words:

> *The drawer is short by exactly what the bank is over — ₹300. That is a bill paid by UPI and
> written down as cash. **No money is missing**, and two separate records say so independently.*

When they point the same way but do not match to the rupee, it says that instead — *"something
else is in there too"* — rather than pretending the case is closed.

**This is what turns the ₹43,330 from a suspicion into something checkable on the day it happens.**

## ⚠ THE OUTAGE THIS KIT CAUSED, AND WHAT IT CHANGES

**The first version of this kit took the whole finance app down.** Not this screen -- the whole
app, 503, money system included, at 04:35 on 04-Sep. It was rolled back in one paste and the box
was back on `fd478faf…` within a minute, with nothing lost.

The cause, from the box's own traceback:

    File "/root/finance/clinic_register.py", line 74, in init
        con = db_getter()
    File "/root/finance/finance_app.py", line 90, in db
        if "db" not in g:
    RuntimeError: Working outside of application context.

`init()` created its table by calling `db()` **at import time**. `finance_app.db()` lives on
`flask.g`, which exists only inside an application context, so it raised, the import failed, and
gunicorn refused to boot: *"Worker failed to boot."*

**`stock_app` has done this correctly since S213** -- `ensure_schema(con)` at the top of every
route, never in `init()`. Its `init()` was read for the MOUNT SIGNATURE and not for how it creates
its tables. **Reading half a pattern and assuming the other half.**

**And the render test passed, which is the part worth recording.** It handed the module a plain
sqlite connector that works anywhere. The real one raises outside a request. So the test proved
that the code worked *with the test's own scaffolding* -- **F-286 exactly: a walk that supplies its
own scaffolding proves the scaffolding.** The test now uses a getter that raises outside an
application context, exactly like the real one, and section 0 asserts that `init()` opens no
connection at all and creates no table until the first request.

**The install line now checks the service came back and rolls itself back if it did not.** An
install that can leave the owner at a 503 is not finished, however green its tests were.

## Not in this kit

A tile. The card is reachable from the Day Revenue page and by address; whether the counter gets a
tile of its own is a decision about their phone screen, not about this build.
