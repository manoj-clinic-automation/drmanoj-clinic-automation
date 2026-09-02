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

## Install / rollback
`INSTALL_ONE_PASTE.txt`. Rollback is a single `\cp` of the timestamped backup — no
restart, nothing else to undo.
