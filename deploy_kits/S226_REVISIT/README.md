# S226_REVISIT — "when they revisit the same item, they don't see the quantity"

The owner, relaying the counters mid-count:

> *"They enter a quantity for an item, and then they are told some more quantity
> has come up physically. And when they revisit the same item, they don't see the
> initially entered quantity."*

Driven, and it reproduces — and it was worse than reported.

| what they did | what happened |
|---|---|
| counted an item to a figure **different** from Marg's, went away, came back | boxes came back filled — this part was fine |
| counted an item to a figure **equal** to Marg's, went away, came back | **the entry box was gone entirely.** The figure was safely saved; nothing on screen showed it |
| pressed **OK** (accepting Marg's figure), then opened that item again | **two empty boxes**, because OK saved only the total and never the strips-and-tablets breakdown |

In two of the three cases a counter had every reason to believe his entry had been
lost, and would type it again from nothing — which is exactly what he must not
have to do when more stock turns up and the figure needs *adjusting*.

## What changed

**The row says what was counted, without opening anything.**

```
BIO D3 MAX      1*15      358   23 strips 13 tablets
                you counted 305 · 20 strips 5 tablets · 11:04
```

In the convention set everywhere — strips and tablets, pieces for orthotics —
and the time on the wall clock, never UTC.

**Coming back to a counted item opens it, filled in.** Auto-open on a difference
as before, and now whenever the counter has *searched* for the item — which is
how anybody revisits one since the search box went in. Deliberately not for a
whole 373-row list: three hundred open forms is not a screen.

**OK records the breakdown too.** Accepting Marg's figure now stores the strips
and tablets that make it up, so the boxes repopulate instead of showing blanks
over a figure that is really there.

## Proof

`WALK_revisit_s226.py` — **30 / 30**, driven at phone width:

* revisiting a counted item shows what was entered, in both boxes
* the row says it without opening anything, in strips and tablets
* **the figure can simply be adjusted** when more stock turns up — 20 strips
  becomes 23 and the total moves 305 → 350
* an item counted as **OK** also shows its figure on return, boxes filled
* everything the search box and the chips already did, unchanged

`EVIDENCE_submit_regression_s226.txt` — **30 / 30**, the whole report-and-send
flow re-run against this file.

## Installing during a count

Safe, and proven the same way each time: the count lives in the browser's own
storage under `sanj-stock-live-v1` and this does not touch it. Amir reloads once
and carries on — and this time the reload leaves him better off, because every
item he has already counted will start showing its figure.
