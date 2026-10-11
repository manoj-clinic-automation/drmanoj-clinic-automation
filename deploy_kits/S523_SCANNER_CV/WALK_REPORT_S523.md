# WALK REPORT — S523_SCANNER_CV — browser walk, 11-Oct-2026 (headless Chromium in the assistant's workspace, OpenCV 4.10.0)

Built files: scanner_widget.js cd9c6e6053d85895e8132eb021b63b6b · asset_register.py d3f1b64ee103efe22266426af9280fbe. Made-up images from walk/make_images.py (seed 523). 48 checks:

- GREEN **A1 cvScan switch seen by the widget**
- GREEN **A2 OpenCV.js loaded and ready** — why=
- GREEN **A3 outline on straight_wood** — max corner error 20 px (tol 82)
- GREEN **A3 outline on tilted12_wood** — max corner error 18 px (tol 82)
- GREEN **A3 outline on perspective_grey** — max corner error 17 px (tol 82)
- GREEN **A3 outline on near_edge_black** — max corner error 20 px (tol 82)
- GREEN **A3 outline on small_light** — max corner error 19 px (tol 82)
- GREEN **A3 outline on landscape_wood** — max corner error 8 px (tol 82)
- GREEN **A3 outline on phone_on_bill_wood** — max corner error 11 px (tol 82)
- GREEN **A3 outline on hand_holding_grey** — max corner error 12 px (tol 82)
- GREEN **A3 outline on shadow_across_light** — max corner error 20 px (tol 82)
- GREEN **A4 outline found on all made-up photos** — 9 of 9
- GREEN **B1 two chosen photos became two pages** — 2
- GREEN **B2 page 1 is 1231x1754 (the paper's own size, 1500-2400 long side; half-A4 shape; was 536x759 under the 1400 cap)**
- GREEN **B2 page 2 is 1196x1731 (the paper's own size, 1500-2400 long side; half-A4 shape; was 536x759 under the 1400 cap)**
- GREEN **B3 each page carries Retake and Adjust (4 buttons for 2 pages + 2 delete)** — 6
- GREEN **B4 the Adjust button is on the page** — ✕|Retake|Adjust|✕|Retake|Adjust
- GREEN **C1 Adjust opens the stage with 'Theek hai'** — block|✔ Theek hai — page 1
- GREEN **C2 'Theek hai' re-cuts the page at full size** — 1231x1754
- GREEN **C3 the stage closes and the adjust ends** — none|-1
- GREEN **C4 'Add whole image' in Adjust keeps the whole photo (4:3)** — 2400x1800
- GREEN **D1 deleting a page drops its kept original too** — 1 pages, 1 originals
- GREEN **E1 the live outline canvas is on the camera** — block
- GREEN **E2 Capture adds a page through the smart path** — pages=2 video=640
- GREEN **E3 the camera stays open after Capture (S441 kept)** — block
- GREEN **E4 Cancel stops the live outline** — none
- GREEN **F1 Save empties the pages and the kept originals** — 0, 0
- GREEN **F2 no page error in the smart path** — []
- GREEN **G1 without cvScan: switch off, no library requested** — [False, False]
- GREEN **G2 without cvScan a page is the S441 page (1400 px cap, as today)** — 1400x1050
- GREEN **G3 without cvScan no Adjust button** — ✕|Retake
- GREEN **G4 no page error without cvScan** — []
- GREEN **G5 a finance-shaped caller (no autoPage): the review stage as before** — block|✔ Add this page
- GREEN **G6 'Add this page' adds the page as before** — 1
- GREEN **G7 no page error on the finance-shaped caller** — []
- GREEN **H1 the old whole-photo scans (already flattened B&W, 1050 px -- the worst case): never a frame-hugging box; the rest refused, not guessed** — 7 of 33 outlined, 0 frame-hugging
- GREEN **P0 the app imports**
- GREEN **P1 /scan/opencv.js serves the gzip copy with a one-year cache** — 200 gzip public, max-age=31536000, immutable
- GREEN **P2 /scan/opencv.js serves the plain copy without gzip** — 200 10378215
- GREEN **P3 the seeded owner can log in on the throw-away database** — 302
- GREEN **P4 intake OFF by default: no cvScan in the scanner config** — 200
- GREEN **P5 /admin shows the switch card, OFF** — 200
- GREEN **P6 the owner's tap switches it ON** — 200
- GREEN **P7 intake ON: cvScan true and the library's versioned URL in the config** — 200
- GREEN **P8 switched OFF again: the intake is as today**
- GREEN **P9 ON but no library file on disk: the intake stays as today and /admin says so**
- GREEN **P10 /healthz answers** — 200
- GREEN **P11 the widget route serves the built widget**
## The negative control (the LIVE bytes e2bca602 / e774be89, same walk)
RED on: A1 cvScan switch seen, A2 OpenCV loaded, P1/P2 /scan/opencv.js (404), P5–P9 the admin switch and the intake config, P11 the widget served — 10 red of 14 run (the browser part stops at A2). The walk tells old from new.

## The app on a copy of the real database (walk_box_s523.py): 14 of 14 green; on the live bytes 5 red (control).

## The installer rehearsed on a made-up root (rehearse.sh): 1 green/DONE · 2 ALREADY INSTALLED · 3 drift refused · 4 no library refused before placing · 5 red-after-placing restored.
