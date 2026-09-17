# S288_DESK_PARKED — the desk gets the word it was missing

**Session 264 (Sanjeevni project), after its close · 17-Sep-2026 · built while the owner sat at the desk.**

## What happened

Step 0 of the stock-check sequence is the owner's word on the lines he already knows the answer to —
the injection in the fridge, the tablet boxes with him. He opened the decision desk for count #1,
tapped something on the first, reached ETOZOX 90 and said: *"I find no way of saying that it is with
me and it is not lost."*

He was right. The server has accepted **PARKED — kept elsewhere** for any line since S227
(`LANE_ACTIONS` in `stock_app.py`), but the desk offered that button only on the *"Your word —
adjustment stock"* cards. A *Real shelf loss* card had three words — Pursue · Write off · Darpan counts
again — and none of them was his. And a word once given could be undone only in the next breath
(the Undo link on the Done card); after that, the find box said *"already decided … see the full
report"* and stopped.

## The change — the page only

Three anchored edits and one click handler in `stock_desk.html`. No server code, no table, no
setting, **no restart** — the page is read from disk on every request, so the new words are there on
the next reload.

1. Every *Real shelf loss* card gets a fourth button: **Kept elsewhere — with me, not lost** (PARKED,
   amber). Parked lines leave every list until a spot count finds them — exactly S227's lane.
2. Every per-item row inside a lane list gets the same word.
3. The find box: an item that already carries a word shows it (*your word: written off*) and offers
   **Change this word** — which reopens the line (OPEN, the same append-only layer) and lands on its
   card, where the new word is one tap.

## The proof

`selftest_s288.py`, **29 checks, 0 failed**: the three anchors and the handler anchor hit exactly once
on the live bytes (`54aeda96…`); a wrong `--from` is refused; the patch is idempotent; the backup is the
live bytes; the page's script parses (`node --check`). Then **both the untouched and the patched page
were driven in headless Chromium against a mocked report**: the untouched page shows no PARKED on the
loss card and no way to change a word (the control); the patched page shows PARKED as the fourth
button, tapping it POSTs `action=PARKED` for that item, the find box names the word already given,
*Change this word* POSTs `OPEN` and lands on the item's card, lane rows carry *Kept elsewhere*, and no
console error is raised on either page.

Predicted md5 of the patched page: `16b9a234b71150b19c8d2ef883eb5f08` — the installer refuses
anything else and restores byte-identically.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S288_DESK_PARKED/install_S288_DESK_PARKED.sh
```

Rollback: `\cp -p /root/finance/stock_desk.html.bak_S288_54aeda96 /root/finance/stock_desk.html`.

## Then, for the owner, on the desk

Type the item in the find box → tap it → if it already carries a word, *Change this word* → on its
card, **Kept elsewhere — with me, not lost**. For a line not yet decided, the button is on the card.
