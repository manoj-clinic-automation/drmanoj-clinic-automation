# S264_PAY_MONTHS — the payment sheet gets its months back

## What was wrong

The owner opened the tile, got **September**, and found no way from there to any
other month. The only route to August was the hub — and the hub's month link goes
to `/page/month/<m>`, the **purchase audit** (bill by bill, PROVISIONAL, FINALISE
August). So he asked for August's *payment sheet* and got August's *purchase audit*,
and reasonably read the old screen as the new flow having glitches.

Two separate faults, both real:

1. `/page/pay` lands on the newest month and the sheet printed **no link to any
   other month**. The walk proves the before-state: not one other month appeared.
2. The two screens never named each other, so there was nothing on either page to
   tell him which job he was looking at.

## What changed — three edits and one helper

- **The payment sheet gains a month strip.** Every month the purchase book holds,
  six at a time, short labels so they fit a phone (`Sep 26  Aug 26  Jul 26 …`).
  The month being read is marked and is not a link to itself.
- **The payment sheet's own sub-line now reads as a sentence.** It was
  *"…the sheet this month is paid from. the same month, bill by bill"* — a dangling
  link. It now says: *"To check the bills themselves, open the purchase audit for
  this month."*
- **The purchase audit page says what it is, and where to pay.** Its first line is
  now *"This is the purchase audit — one row per Marg bill. To pay the month, open
  the payment sheet for August 2026."*

The strip is styled inline on purpose: this kit does not touch the stylesheet.

## The walk — 37 checks, and it navigates

The complaint was navigation, so the walk navigates. It loads **both** files — the
one being replaced and the patched one — each against its own copy of the real
database:

- **the before-state is proved, not assumed**: the old sheet offered no way to any
  other month, and the old audit page said nothing about a payment sheet;
- the tile still lands on the newest month;
- the strip is on the page, and **every month is one tap away**;
- **every link in the strip is followed and must open 200** — the walk reads the
  hrefs off the page itself rather than guessing them;
- the month being read is not a link to itself;
- every month's sheet names the month it is showing, and carries the strip;
- the two screens name each other, in sentences that read;
- `/hub`, `/scans`, `/orders`, `/book` come back **byte-identical to before**;
- the sheet's own figures — every vendor, every payable, every lane — are unchanged;
- the audit page is **byte-identical apart from the one sentence added**.

Proven against a fixture root: clean install, **ALREADY INSTALLED** on re-run, a
deliberately wrong to-pin → **restored byte-identically**, and the database
untouched throughout. This kit writes no data at all.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S264_PAY_MONTHS/install_S264_PAY_MONTHS.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `c4a64353e3b8d6ed0e0d46fe0ec32954` | `8d7b1eadc70d122ff181002692815bd7` |

## Files

| file | what it is |
|---|---|
| `patch_pay_months_s264.py` | the three anchored edits and the strip helper |
| `walk_s264.py` | the 37 checks, before and after, following the links |
| `install_S264_PAY_MONTHS.sh` | pins, backup, patch, walk, restart, roll back |
