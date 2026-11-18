# S872_HUB_TWO_TAP — the Hub's three asking buttons fire in the built-in browser — Sanjeevni session 482, 18-Nov-2026

**His word, 13:26:** "Mark all Received is not working in your browser. Individual received for Dr Bhawna button is working."
**Cause (proved in the Claude app's built-in browser):** `window.confirm()` returns false in 3 ms — the pane answers every dialog with No by itself.
S869's *Mark all N received*, *Accept (write off)* and *remove* (an entry) asked first, so they never fired there. The single Received button never asked.
**Fix:** the Hub's own two-tap (as the Returns card's Approve): first tap turns the button into "Tap again to …" for 5 s, the second tap sends. No dialog anywhere in the S869 block.

| file | FROM | TO | how |
|---|---|---|---|
| `/root/finance/finance_ui/finance_approvals.html` | 7253dc9f | see TO_PINS.md5 | 5 exact anchors (make_s872.py) |

Proof: `synth_s872.js` (node, in the chat: arm / send / reset for the three buttons, 10/10; control red) and `synth_s872.py` (markers, run by the installer on the box, 6/6; control red). `rehearse_s872.sh` 8 paths. Install: his publish + one server line (header of the installer). Undo: `undo_s872.sh`.
