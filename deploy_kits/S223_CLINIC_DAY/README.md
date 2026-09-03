# S223_CLINIC_DAY — the clinic's day revenue, on a screen

**Stage 1, part two. Part one (`S223_DOCTERZ_READER`) is already live and holds 68 days.**

## What goes live

| file | from | to |
|---|---|---|
| `/root/finance/finance_clinic_day.py` | NEW | the page, read-only, no JavaScript |
| `/root/finance/finance_app.py` | `f7dd9e57…` | **`fd478faf…`** — two lines, the mount |
| `/root/portal/portal.py` | `fbd4029b…` | **`e2f90752…`** — one new tile |
| `/root/portal/tile_grants.json` | `bfdf40dd…` | **`aaa12fec…`** — the tile granted to five people |

**The screen:** `https://followup.dr-manoj.in/finance/clinic/day`

The two most recent days side by side, then the whole month as a table — bills, consultations,
X-ray, procedures, the day's total, and the tender split by Cash / Online / Card / Split — with
previous- and next-month links and a **Print / Save as PDF** button.

## D367, made visible

> *"if totalling error is on docterz, sort it out, from individual entries, its their reporting
> method which is fixed, we can fix our side only"*

**Every figure on the page is computed from the itemised lines.** The sheet's own SUMMARY, Cash
and Online lines are stored beside them and **never displayed** — on 18 of the first 68 days they
disagree with the sheet's own total, and showing two numbers and a difference would hand everyone
something to decipher instead of something to use. The disagreement lives in `variance_note`, for
whoever is fixing it.

The render test proves that, rather than asserting it: on the days where the sheet disagrees with
the lines, **the sheet's figure does not appear anywhere in the delivered HTML**.

A **Split** figure is a bill paid by more than one method. The Day Revenue sheet carries a line's
Mode but not its legs, so a split is shown as a split rather than guessed at. The legs live in the
raw export, and recovering them is the tracker-side parser fix — proven offline, not yet installed.

## Who sees it

The tile is granted by name to **Shavez, Shivani, Alisha, Dr Bhawna and the owner** — his list.
The page's own gate is `require("maker", "checker", unit="clinic")`, the clinic roles that already
exist. **The two lists are the same five people by construction**: everyone granted the tile
already holds a clinic role, and nobody else is granted the tile. No new list was introduced, so
there is no new list to drift.

A login without a clinic role that reaches the address by hand gets a sentence explaining why, and
**no money on the page at all** — asserted in the render test.

## Proven before it ships

**Render test — 16/16 GREEN** (`EVIDENCE_render_s223.txt`). The real blueprint on a real Flask
app, a real database filled by the real ingester, the page fetched over HTTP, assertions on the
bytes a browser receives. It checks the gate refuses, the totals on the page are the totals in the
table, the month footer is the sum of its own days, the sheet's disputed figures are absent, the
print stylesheet exists, **there is no `<script>` tag at all**, an empty month says so, a missing
table says so instead of throwing a 500, and no mobile-shaped number or patient-UID shape appears.

**Tile walk — 8/8 GREEN** (`EVIDENCE_walk_tile_s223.txt`). 48 user × role × PC combinations: the
only thing gained anywhere is `Day Revenue`, nothing is lost, it reaches exactly the five named,
Darpan and Amir and a brand-new login do not get it, and with the grants file removed it fails
**closed** for staff while the owner keeps it.

## Provenance — how the from-pin was earned

No store held the live `finance_app.py`. It was **reproduced**: the S217/218 live capture
(`80c2323a…`) replayed through `S219_MARG_AUTOAPPLY` → `b42b1f08…` → `S219_RETURNS_M7` →
**`a57980c2…`** (the S219 close pin, exact) → `S220_DAY_TOTAL_TRUTH` → **`f7dd9e57…`** (the S220
close pin, exact). Every intermediate matched its recorded pin, so this patcher is anchored on
bytes that were read rather than on a filename that looked right (F-280, F-299).

## Two test failures worth recording, because both were the TEST's fault

The render test first reported the page leaking the sheet's cash figure. It was not: on days where
sheet and lines **agree** it is the same number, and the assertion had not excluded them. The tile
walk first reported the wrong people holding the tile; a by-name grant applies whatever role the
login carries, and the assertion had subtracted the two doctors from its own expected set.

Both are **F-293** — a test's own incompleteness must not be reportable as the subject's fault —
and both were corrected in the test, not worked around in the code.

## Not in this kit

The bank comparison (needs `upi_txn` queried for whether the ICICI MPR names the rail) · the
tracker-side parser fix that resolves the split legs · reconciling the reader against S211's
67-file rehearsal rather than the eight used here.
