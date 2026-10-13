# S545_SCANNER_FINDS_PAPER — the smart scanner finds the bill in the hand, and saves it upright (F-890)

*Scan App project, S314, 13-Oct-2026. A correction of S523 (D711: the smart scanner is the phone's own browser, on for
every phone). Built by BUILD_NORM_v1 (D704). One file. No database change. No switch: it rides the existing `scan.cv`
setting (on since the owner's tap of 11-Oct).*

## Why (the real cause, measured)
On 12-Oct reception scanned 11 papers (B-0146 … B-0156). **8 were saved as the whole camera photo** — hand, desk,
keyboard in the PDF — although every one went through the smart path (OpenCV ready, the switch on, 2400-px output).
The cause is in `cvFindQuad` (`scanner_widget.js` 65127fcb):
- a bill **held in the hand**: the fingers break the paper's outline into 5–10 corners, not convex — refused by the
  four-corner test (`ap.rows === 4 && isContourConvex`);
- a bill **touching the photo's edge**: refused as "the frame" (three corners within 1.5 % of the border);
- a bill on a **light table**: the brightness split takes the table with the paper (98–99 % of the frame) — refused by
  the 90 % cap;
- then line 1359 keeps the whole frame.
And **every wide bill shot with the phone upright is stored sideways** — nothing anywhere turns a page.

## What the kit does
Inside the S523 smart-path block only (the scan app's intake is the one surface that switches it on):
1. **Step 3 — the paper by its colour** (`quadFromPaper`), tried only when steps 1 and 2 find nothing (so every scan that
   is cut well today is cut exactly as today): paper is bright and has almost no colour; skin, wood and trays have
   colour, keyboards are dark. On a light table the bright side is split once more (paper is the brightest large
   thing). **A region must carry print** — a blank wall, cabinet or white board never does, so it is never taken for
   the bill (the independent read's finding). The largest such region's hull; four corners that keep **at least 97 %**
   of it, else a box round it. A paper **may touch the photo's edges**; refused only when the box *is* the frame. **Every side not
   on the frame's border must be a sharp step in brightness** — a real paper edge, not a shadow or uneven light.
2. **Upright** (`cvUpright`): after the cut, when the lines of print run up the page and not across it, the page is
   turned a quarter — towards the heavier end (the bill's heading) as the top. Applied after every smart capture and
   after Adjust, so a page cut well today may now be turned; a bill whose foot is heavier than its head (a dense terms
   block) can come out upside-down — readable, and the reading (Sarvam) is not affected. Proven on made-up pages only.
3. `window.__scannerS545` (version `S545.1`) for the after-check.

## Proven (walk/walk_results.txt)
- **Made-up photos** in Chromium with the live OpenCV 4.10.0 (md5 ff1e10e7): the OLD finder fails 5 cases (hand, frame
  edge, light table) — **the NEW passes all 5** (overlap 0.988–0.994, ≥ 98.8 % of the paper kept); the 3 cases the old
  one already cut well are cut identically; a blank bright wall bigger than the bill is never taken for it (step 3
  alone, scenes L and M: the bill); a thumb over a corner is unchanged (95.7 % kept by both); a paper filling
  the photo keeps the whole photo as before. 30–50 ms per photo at the detection size.
- **Upright:** 7 of 7 (wide bill upright, turned either way, portrait page, ruled tables).
- **Memory:** 600 passes of the live outline (≈ 3 minutes of camera) and 100 upright turns — the OpenCV heap does not
  grow (every channel and contour the new code takes is released); about 8 ms a live pass (the old: 4–5 ms).
- **The seven surfaces:** the finance app's five and the asset page render **byte-identical** with no error; the
  intake (smart) finds a frame-edge bill the old one cannot.
- **On the box** (`walk_box_s545.py`): the built file carries every piece inside the smart-path block — 7 green; the
  live file 6 red (the control).
- **Not proven here:** real colour photos from reception's phone — the first staff scans after the install are read the
  next morning (a dated check).

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/assetapp/scanner_widget.js` | `65127fcb` (S531) | `PIN_TO_scanner_widget.txt` — backup `.bak_S545_65127fcb` |

`make_s545.py` (four counted edits, refuses any other FROM) · `s545_block.js` (the new functions) · `install_s545.sh` ·
`walk_box_s545.py` · `walk/` (the browser bench, its scenes, the seven-surface walk, the results).

## Install (the owner's one line, after the publish)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S545_SCANNER_FINDS_PAPER/install_s545.sh`

Order: gates → pin → rebuild on the box → walk + control → backup → place → health (`/healthz` 200 and the served
widget carries `S545.1`; red → the backup put back by itself). No restart: the app serves the file from disk with an
mtime version, so each phone takes it the next time the intake page opens. A second run says ALREADY INSTALLED.
Rehearsed on a made-up root four ways (fresh · second run · health red → restored · wrong FROM → refused).

## Undo (one line)
`cp -p /root/assetapp/scanner_widget.js.bak_S545_65127fcb /root/assetapp/scanner_widget.js`
