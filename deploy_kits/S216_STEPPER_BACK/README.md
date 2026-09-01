# S216_STEPPER_BACK — a way back from stage 2

**Page only.** `casepack_portal.py` unchanged and NOT installed.

## It was never a missing button

`cpSetStage(1)` already worked — it closes the modal and returns to Enquiry.
**The button that calls it was simply unreachable.** `#cpStepper` sits in the
page body; stage 2 opens `#caseModal`, which is `position:fixed; inset:0;
z-index:20` with a dark backdrop covering the whole page, stepper included.

The only exit was `#closeCase` — a button at the very **bottom** of a very long
modal, past the entire consent form and the fracture grid. From the top of
stage 2 there was no way back at all.

## The fix

While the modal is open the stepper becomes a fixed bar at the top of the
viewport, above the modal, on a solid background. There is still only ONE
stepper, so it cannot disagree with itself, and the original Close button keeps
working.

**The space the modal leaves for it is measured, not assumed.** The first draft
hard-coded 74px — the bar is 77px on a wide screen but wraps to **143px at
420px wide**, so on a phone it would have hidden the top of the form. `cpBarFit()`
reads the bar's real height into `--cpbar` on open and on resize.

## Proof

| gate | result |
|---|---|
| `BACK_WALK.py` (new) | **12/12** — includes the clear-space check at 900, 560 and 420px |
| `selftest` · `render` · `guard` · `contrast` · `naming` | 32/32 · 17/17 · 19/19 · 9/9 · 14/14, all unchanged |

`BACK_WALK.py` uses `document.elementFromPoint` to prove the control is actually
the topmost element at its own coordinates — not merely present in the DOM.
That is the exact distinction the bug turned on.

## Install

    cd /root/deploy/repo && git pull && bash deploy_kits/S216_STEPPER_BACK/install_back.sh

Base `af850a87…` → new `7de1f5c3…`.
