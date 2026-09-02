# S219_SCANNER_V2 — scanner v2, finalised and deployed everywhere

**Owner's instruction, 02-Sep-2026:** *"THERE WAS A SCANNER V2 DEVELOPED. ITS TO BE
FINALISED WITH ALL ITS UPGRADES AND USED EVERYWHERE."*

v2 was built at S207 and **staged, never installed** — the live widget has been v1
(`4fe8c89386a54ce90786823b53df55bc`) since **S175**. This kit finalises it, fixes what
finalising exposed, and installs it.

## "Everywhere" is one file
Every surface reads the same physical file, `/root/assetapp/scanner_widget.js`:

| surface | how it gets there |
|---|---|
| Asset Register — reception bill intake | `scanner_widget_js()` route, `?v=` mtime |
| Asset Register — second scan surface | same route |
| finance — day scan · non-cash · expense | `SCANNER_JS`, served + mtime-versioned |
| finance — clinic day scan · clinic expense | same |
| Casepack | same shared file (v2's contract is unchanged) |

So **one file swap upgrades all of them at once**, and because both apps version the
URL by the file's mtime, **every browser cache busts itself**. No host page changes.
No service restart.

## What v2 brings (S207's work, unchanged)
Autocrop that finds the document — v1 never had any, it used a fixed 8% inset, so every
capture meant dragging four corners. Video capped at 55vh with sticky capture/save bars,
so the buttons stop falling below the fold on a portrait phone. Every control ≥44px.
It **refuses rather than guesses**: too small, too large, or no step across the edge and
it falls back to the old inset, because a confidently wrong outline is worse than a
neutral one.

## What finalising exposed — two defects, both fixed here
**1. The tests could never run anywhere but the machine that wrote them.** All four
suites hard-coded `file:///home/claude/scan/host.html` — the S207 sandbox path. This is
exactly the defect S212 found in three PC kits (*"hard-coded to the assistant's sandbox
mount and could not run on manojz at all"*). They now resolve `host.html` relative to
their own file, and run anywhere.

**2. The whole suite proved a configuration nothing runs.** `host.html` leaves
`allowIdCard` and `allowBatch` at their default of **true**. **Every live caller sets
both to false.** Under the real config the mode bar renders a single "Document" radio —
a group with one option, which is not a choice, 40px tall, **below the 44px thumb target
v2 exists to guarantee**, on every production screen. A green suite proving the wrong
shape: *a green selftest proves the kit, not the join* (S208/S209).

Fixed: with only one mode available the bar is not drawn at all. `camChrome()` already
guarded its lookups with `if (e)`, so nothing else needed to change.

## Proof
| suite | result |
|---|---|
| `t_detect.py` — 7 documents, known ground truth | **7/7** within 6%; blank frame correctly refused |
| `t_hard.py` — 9 adversarial cases | 6 exact · 2 correct refusals · tilt loose (documented) · vignette 28% (documented) |
| `t_regress.py` — every v1 feature in a real browser | **37 passed, 0 failed** |
| `t_layout.py` — 3 phone sizes, portrait camera | capture + save on screen at all three; **no tap target under 44px** |
| `t_liveconfig.py` — **NEW, S219** — the four real production configs | **32/32** |

Run on today's Chromium, not the one S207 used, and every S207 number reproduced exactly.

## The two known limits, stated not buried
**Tilt** — this finds an upright rectangle, not a perspective quadrilateral; held at an
angle the box is honest but loose, and the corners drag as they always did.
**Heavy vignette** — a strong radial falloff still over-reaches by ~28%. Fixing it
properly means perspective detection (OpenCV.js, an 8MB download onto a phone in a
pharmacy). S207's judgement was that this *"should be bought with evidence that this is
not enough, not before"*, and that judgement is kept. Both cases are still a large
improvement on v1, which was a fixed inset — wrong in **every** case by construction.

## What is still untested, and cannot be tested here
**Whether it feels right pointing a real phone at a real bill.** Everything above is
synthetic. The honest next step is one real scan on a real phone after install; if it
disappoints, rollback is one line and the corners still drag exactly as they do today.

## v2.1 — one label restored, and why it matters
The asset app's **own** smoke suite greps the widget for `"Add whole image"`. v2 had
shortened that button to `"Whole image"` during the 44px layout work, so with v2 installed
the app's suite ran **341 passed / 1 failed** — a red on a live system that is not a fault,
which is the "amber that is normal" this project refuses to leave lying around. The feature
was never gone (`id=addwhole` is in both versions and `t_regress` drives it); only its name
was. The label is now `➕ Add whole image` — descriptive again, still shorter than v1's
`➕ Add whole image (no crop)`, and every layout assertion still passes.

With this and the pharmacy-lane patch the app's suite is **342 passed, 0 failed** — the same
342/0 recorded against this app at S177.

## v2.2 — the scanner is told the page size (the owner's idea, and the right one)
He tried a real half-A4 bill and autocrop did not fire. Measured (`t_fillframe.py`), the cause
was not the background: **a page of print offers a rectangle every bit as convincing as the
paper**, and which one wins depends on the printed content. He then supplied the fact that
settles it — **>95% of pharmacy purchase bills are half A4** — so the scanner no longer has to
guess the shape it is looking for.

Opt-in, via `SCANNER_CONFIG`: `expectAspect` (0.7048 for A5), `expectLabel`, `expectTol`.
**Absent for every caller that does not set it, so nothing running today changes** — proven by
re-running all five suites and the app's own 342 checks with no prior set.

Three effects, in order of value:
1. **A framing hint while aiming** — keep some desk visible, fill about three quarters. That is
   not politeness: the detector fits the desk from a ring round the frame, so if the paper
   reaches the edges there is no desk left to fit.
2. **An aspect gate** — a candidate that is not the expected page is refused. The text block
   never is: margins make it wider and shorter.
3. **A better fallback** — an unconfident detection now hands back the *expected page*, in the
   right proportion, instead of a fixed 8% inset that is the wrong shape for a bill.

`expectTol` defaults to **0.15, measured not chosen**: the text blocks this rejects came out at
0.82 and 0.59 against a page of 0.705 — 0.16 away — while a page tilted 8° is only 0.09 away and
13° is 0.15. So it rejects the printing and still accepts a bill laid down crooked.

**Result (`t_sizeprior.py`), same sweep with and without the prior:**
```
accurate detections kept : 6 of 6
confident-WRONG boxes    : 6  ->  0
```

## v2.3 — page presets, and the overshoot that made them necessary
The owner scanned a bill in the asset app: *"vertically its very much extra area captured."*
That was **the fallback, not the detector** — when the aspect gate refuses, the outline it hands
back was the guide rectangle, and I had sized that at a fixed 80% of the frame. A guide sized by
guesswork overshoots the moment the bill sits smaller than the guess. His fix was better than
mine: *"how about adding a button for a5 size with medical bill button name?"*

**On the review screen** — where you can see the photo, not before the shot where a preset is
only a promise — there is now a row: **Medical bill (A5) · A4 · Strip · Free**. Tapping one
*finds the paper* (the brightest large region in the frame) and lays a rectangle of that shape
over it. One nudge instead of four drags.

`Free` is not decoration. >95% of purchase bills are half A4; the day one is not, a preset
without an escape is an obstacle. The choice is remembered, because reception scans a pile at a
time and choosing the same shape twenty times is the friction that gets a tool abandoned.

**Measured (`t_presets.py`), bills drawn at four positions and sizes:**
```
bill half the frame, centred   225,300,450,638  ->  225,299,450,639   1.00x area
bill small, high in the frame  280,120,340,482  ->  280,120,341,484   1.01x
bill three-quarters            135,180,630,893  ->  135,179,630,894   1.00x
bill off to the left            60,300,420,596  ->   60,300,420,596   1.00x
```
Within a pixel, at the bill's own size — not 80% of the frame.

*The harness got this wrong first: it sized the photo canvas but not the overlay, so the fit ran
against an overlay of the wrong size and every case failed. Recorded because a test that fails
for its own reasons is indistinguishable from a broken feature until you look.*

## Install / rollback
`INSTALL_ONE_PASTE.txt`. Rollback is a single `\cp` of the timestamped backup — no
restart, nothing else to undo.
