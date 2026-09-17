# S292_DESK_PAIRS — the "over" card stops being a wall of text

**Session 264 (Sanjeevni project), after its close · 17-Sep-2026 · from the owner's screenshot of the desk.**

## What he saw

The card *"3 items over"* carried one paragraph naming **every same-salt pair in the whole count** —
twenty-odd pairs run together, most of them nothing to do with the three items on the card. The
sentence was 580 characters of names before the first button. His word: *"the formatting of this
page needs improvement."*

## The change — the page only

Four anchored edits, two helpers and one stylesheet rule in `stock_desk.html`, over the S288 bytes.
No server code, no restart.

- The over card's sentence loses the pair dump and says *"Each item's own partner is listed below."*
- Under it, **Each item and its partner**: one line per item **on the card** — `PARI CR 12.5 18 strips
  3 tabs over — against ETOZOX 90 short 46 strips 9 tabs · same salt ETORICOXIB 90`; an unpaired item
  says *no same-salt pair found*.
- A closed toggle, **Show all N same-salt pairs in this count**, opens the full list one pair per line.
- A real-loss item card names its own partner under the facts: *Same salt ETORICOXIB 90 — PARI CR 12.5
  is 18 strips 3 tabs over — a billing swap is the usual answer, not a loss.* (This is the ETOZOX 90
  card the owner sat on this afternoon.)

## The proof

`selftest_s292.py`, **24 checks, 0 failed**: anchors once on the S288 bytes; a wrong `--from` refused;
idempotent; backup is the live bytes; the script parses. Then both pages driven in headless Chromium
over a mocked report with three real-shaped pairs: the control still dumps the pairs into the
sentence and has no block; the patched card's sentence is 316 characters, lists its three items with
partners, the toggle opens all three pairs, the ETOZOX 90 loss card names PARI CR 12.5, S288's four
buttons are still there, no console errors. Screenshot in `EVIDENCE_shot_s292.png`.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S292_DESK_PAIRS/install_S292_DESK_PAIRS.sh
```

Rollback: `\cp -p /root/finance/stock_desk.html.bak_S292_16b9a234 /root/finance/stock_desk.html`.
