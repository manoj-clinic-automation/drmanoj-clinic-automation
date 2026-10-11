# S523_SCANNER_CV — the smart outline (OpenCV.js) for the bill intake · installed SWITCHED OFF

*Scan App project, S306, 11-Oct-2026. The owner's word of 05:48 IST: "8 mb app can be easily installed in most current
android mobiles … keep the flow friction less for staff phones". Built by BUILD_NORM_v1 (D704).*

## The real cause (F-842)
Measured on the 11-Oct 02:30 `assetapp_nightly` backup, the last 40 scans (01–10 Oct): the intake's light outline finder
found **no outline on 33 of 40** real scans — the whole photo (desk, keyboard, phone, hand) went into the PDF — and one of
the seven outlined is cut off. And `scanner_widget.js` shrinks every photo to **1400 px** on its long side before it is
looked at (`autoAdd`, `loadImage`), so no PDF ever carried the camera's resolution. Reception's "no crop" is S441's
no-wait flow: the corner handles exist, but the intake never shows them.

## What the kit does — all of it behind ONE new opt-in switch of `SCANNER_CONFIG` (`cvScan` + `cvUrl`), as S441's four
Only the bill intake sets it, and only when the owner has switched `scan.cv` ON on `/scanapp/admin`. The asset pages and
the finance app's five scan surfaces never set it: for them the widget behaves exactly as before (walk G1–G7).
- the camera is asked for 8 MP (3264×2448) instead of 2.7 MP;
- a **live green outline** is drawn on the camera preview while aiming (every 300 ms, on a 360-px copy);
- each capture is read at **full size** (up to 3300 px): the paper found as a true four-cornered shape (edges first, a
  brightness pass second; a box that hugs the frame is refused, the brighter-inside candidate wins), straightened by
  perspective, kept at the paper's own pixel size up to 2400 px, the B&W flattening done by the same arithmetic as
  `enhanceGray` but in the library; the light finder is the second opinion; the whole photo is the honest third;
- the original photo of every page is kept until Save, so a page can be **Adjusted**: the existing corner handles open on
  it, **✔ Theek hai** re-cuts it at full size; *Add whole image* keeps the whole photo; *Retake* as before;
- a phone that cannot carry it (deviceMemory < 2 GB, Data Saver on, or the download never arrives) keeps today's path
  unchanged — `autoAddCV` hands straight to `autoAdd`;
- the library (OpenCV 4.10.0, `dist/opencv.js` of the npm package `@techstark/opencv-js` 4.10.0-release.1, Apache-2.0,
  md5 `ff1e10e7…`) is served by our own app at `/scanapp/scan/opencv.js` — the gzip copy (3.4 MB, not 10) when the
  browser takes it, cached a year under its `?v=` stamp, so each phone downloads it once.

## Files
| file | FROM (live, pinned) | TO (the installer's read-back) |
|---|---|---|
| `/root/assetapp/scanner_widget.js` (seven surfaces, two apps) | `e2bca602` | `PIN_TO_widget.txt` |
| `/root/assetapp/asset_register.py` | `e774be89` | `PIN_TO_app.txt` |
| NEW `/root/assetapp/static/opencv.js` + `.gz` | — | `ff1e10e7…` (downloaded on the box, pinned) |

Edits (counted, anchored, by `make_s523.py` on the box): widget W1–W12 (the flag beside S441's; the camera's 8 MP; live
start/stop with the stream; Capture and a chosen photo go to the smart path; the stage's two buttons finish an Adjust;
delete drops the kept original; the Adjust button beside Retake; the stage's Retake cancels an Adjust; Save clears the
originals; the S523 block before the buttons are wired). App A1–A6 (the intake's config pair behind `_scan_cv_on()`;
the library route with gzip and a one-year cache; the admin action and card; the admin context; `scanner_opencv_js`
named in `RECEPTION_OK`, A-D21). Not touched: `clinic_papers.py`, `scan_checks_s441.py`, `sarvam_ocr.py`, the service
unit, the database (no column, no row — `scan.cv` is written only by the owner's tap).

## Proof
- `walk/walk_s523.py` in headless Chromium on nine made-up 8 MP desk photos with known corners (a tilted bill, a
  perspective shot, near the frame edge, a small bill on a light desk, a landscape sheet, a phone lying on the bill, a
  hand holding its edge, a shadow across it): **48 of 48 green**, max corner error 8–20 px of 3264 (tol 82). The same walk
  on the LIVE bytes: RED on 10 checks (the control). The old whole-photo scans of the backup (already flattened B&W,
  1050 px — the worst case): no frame-hugging box, 7 of 33 outlined, the rest refused rather than guessed.
- `walk_box_s523.py` — the app on a copy of the real database: 14 of 14 green; on the live bytes 5 red (the control).
- The installer rehearsed on a made-up root five ways: green/DONE · again → ALREADY INSTALLED · a moved live file →
  refused, nothing placed · the library not reachable → refused before placing · health red after placing → both files
  restored from their backups, `static/` removed.

## Install (the owner's one line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S523_SCANNER_CV/install_s523.sh
```
Order: gates → pins → the library (the kit folder's `opencv.js` if present, else the pinned npm package) → rebuild on the
box → walk on a copy of the database + the control on the live files → backups `.bak_S523_<from8>` → place →
`systemctl restart assetapp` only → `/healthz` and `/scan/opencv.js` → data step none → the owner's words → the undo line.

## After the install
Nothing changes for anyone until the owner's tap: `https://followup.dr-manoj.in/scanapp/admin` → *Scanner — smart
outline (OpenCV)* → **Switch ON**. Then the bill intake on a phone that can carry it shows the live outline, keeps the
full resolution and offers **Adjust** on every page. Proven in this order: the owner's Galaxy Z Fold, Shavez's S21 FE,
reception's Galaxy A07 5G.

## Undo (one line)
```
cp -p /root/assetapp/scanner_widget.js.bak_S523_e2bca602 /root/assetapp/scanner_widget.js && cp -p /root/assetapp/asset_register.py.bak_S523_e774be89 /root/assetapp/asset_register.py && systemctl restart assetapp
```
(`static/opencv.js` may stay; nothing reads it without the switch, and the switch is off without the new app.)
