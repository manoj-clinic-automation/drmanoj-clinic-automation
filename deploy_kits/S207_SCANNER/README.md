# S207_SCANNER — scanner_widget v2

**Staged. The live file was not touched.** `assetapp/scanner_widget.js` on the VPS is exactly as it
was; this sits beside it for you to try.

---

## The three faults, and what each turned out to be

**1. No autocrop — it had never been written.** `resetCorners()` set a fixed 8% inset and that was
all of it. v1's own header says so: *"auto-detect ... are Stage 1B and deliberately NOT here."* A
licence fills perhaps a third of the frame, so every capture meant dragging four corners a long way.

**2. The camera hid the buttons because the video had no height limit.** `max-width:100%` and
nothing else. Held upright a phone returns a **portrait** stream, so on a 390px screen the video
rendered ~430–520px tall; with the heading, three mode radios, the hint and the open-camera row
above it, Capture landed near 700px — below the fold, Save further down still.

**3. The buttons really were too small.** `.btn` ≈ 33px tall, `.btn.small` ≈ **22px**, against ~44px
for a reliable finger. Three of the four stage buttons were the small variant.

---

## What v2 does

- **Finds the document** and places the outline on it. Dependency-free — nothing downloaded, runs on
  the phone the staff already hold.
- **Video capped at 55vh**, capture and save bars **sticky**, and the mode radios / hint / open-camera
  row **collapse while you are aiming** — they are no use then and they were 160px of the screen.
- **Every control at least 44px**, one primary action per row.

## How the detection works, and why this method

A document on a desk has one property nothing else has: it is a large coherent thing that is *not
the surface*. So the surface itself is fitted from a ring around the frame — as a shape, not a
colour — and every pixel is judged against the surface **at its own position**. What is left is
projected onto rows and columns, and the widest unbroken run is the document.

Fitting the surface as a shape is what handles a shadow across the desk and a flash falling off at
the corners. Judging per position is what stops a shadow from becoming the document.

**It refuses rather than guesses.** A box under 4% or over 98.5% of the frame, a fit the light
defeats, or a box whose edge has no step across it — each returns nothing and the old 8% inset is
used, exactly as before. **A wrong outline placed confidently is worse than a neutral one**, because
nobody checks a confident answer.

## Measured

Seven synthetic documents with known ground truth, worst edge error as a share of the card:

```
licence, centred            0.2%     A4 page, fills most        0.2%
licence, small in frame     0.7%     card on a busy desk        0.4%
licence, off to one side    0.2%     low contrast, grey on grey 0.2%
portrait phone shot         0.3%     blank frame                REFUSED, correctly
```

**End to end through the real capture path: 0.3% out.**

Nine adversarial cases:

| case | result |
|---|---|
| shadow gradient across the desk | exact |
| dark desk, white card | exact |
| finger resting at the frame edge | exact |
| card touching the frame edge | exact |
| card fills the whole frame | refuses — correct, there is no border to find |
| white card on a white desk | refuses — correct |
| tilted 8° | 7% loose — drag a corner |
| tilted 20° | 15% loose — drag a corner |
| heavy vignette | **28% loose** — the one weak case, see below |

**The honest weak spot.** A strong radial falloff still over-reaches vertically by about a quarter.
It is a big improvement on the 8% inset and the corners drag as they always did, but it is not
right. Fixing it properly means perspective detection — OpenCV.js and an 8MB download onto a phone
in a pharmacy — **and that should be bought with evidence that this is not enough, not before.**

**Tilt is a known limit, not a bug.** This finds an upright rectangle, not a perspective
quadrilateral. Held at a steep angle the box is honest but loose.

## Four wrong turns while building it, all caught by the tests

1. **The first detector locked onto the text block, not the card** — every one of the seven cases
   ~26% wrong. It thresholded edges against the frame's strongest gradient, and printed text is a
   far stronger gradient than a white card on a grey desk, so the card's own border was thresholded
   away. Replaced with the background method.
2. **The curved surface term overfitted** where there was no vignette, bending the fitted desk
   toward white in the middle and cutting a card on a busy desk to two-thirds its height. It now has
   to earn its place — the flat fit is used unless the curved one explains the ring markedly better.
3. **One single row broke a card in half.** Shrinking to 320px blends a dark text line into the white
   around it; where that average landed on the desk's own grey, one row read as background — a
   one-pixel slit straight across the card. The run was split and the top two-thirds handed back,
   confidently. Short gaps are now bridged.
4. **A card touching the frame edge contaminated the surface fit** and lost a third of its height.
   The fit now throws away its worst tenth and fits again.

**And one wrong turn in the test harness itself**, worth recording because it produced a green-looking
run that proved nothing: the fake camera was installed as `() => {…}` passed to `add_init_script`,
which evaluates a function and never calls it. The real `getUserMedia` answered `NotFoundError`, the
camera never opened, and the layout assertions were measuring a hidden element.

## Try it

```
deploy_kits\S207_SCANNER\host.html    open in a browser, choose a photo of a licence
```

`host.html` carries the Asset Register's own stylesheet, so what you see is what staff would see.

## Tests

```
python t_detect.py    7 documents, ground truth
python t_hard.py      9 adversarial cases
python t_regress.py   37 checks -- every v1 feature
python t_layout.py    3 phone sizes, portrait camera stream
```

They need Playwright and Chromium. `t_regress.py` drives a real browser through capture, add page,
whole image, reset, retake, all three modes, and the save bar, and asserts **nothing threw at any
point**.

## What I could not test

**Whether it feels right pointing a real phone at a real licence.** Everything above is synthetic.
Try it on one document before this goes anywhere near the live path.

## Install, when you want it

Replace `/root/assetapp/scanner_widget.js` with this file. No host page changes — the styles are
injected by the widget and `SCANNER_CONFIG` is unchanged, so Asset Register and Casepack both keep
working. **`BASELINE.md5` records the file this was cut from**, so the rollback is exact.
