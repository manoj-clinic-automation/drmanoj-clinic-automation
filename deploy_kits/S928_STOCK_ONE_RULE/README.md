# S928_STOCK_ONE_RULE · Sanjeevni session 503 · 22-Nov-2026

The owner (22-Nov 07:01 IST, D1036): "the scanned bill's quantity is relied on over reception's arrival taps, and the same rule must apply
everywhere in the system"; (07:49 IST, D1037, mock-up v5): every count Darpan writes reaches him. The stock plan's steps 1 and 2
(`S501_STOCK_PAGES_CONSOLIDATION.md` §7; F-1565, F-1564).

* **`/root/finance/stock_figure.py` cc1cef5d → v1.6** (make_s928.py, 9 exact anchors + the S928 block):
  * **THE ONE ARRIVALS RULE counts a delivery by the dealer's SCANNED BILL** (`bill_units` / `_count_units`): when the order has a usable,
    Claude-read scan tied to it, every order line is matched one-to-one against the bill's read lines by the tracker's own matcher
    (`order_track.match_lines`, as S825 judges "on the bill"; one match per order, cached), the medicine's batch lines summed, free goods
    added; the line counts `bill quantity × the order line's pack size`. A tapped medicine the bill does not carry counts **nothing**; a bill
    above the tap counts the bill; **a tap above the bill is a short supply** (`short_supplies()` — read by the Stock check page, S929; the
    purchase flow's next order). No usable read scan, or a quantity not read → the tap stands as before (charter 1b). `taps()`,
    `scan_arrivals()` and `expect_for_point` (an uncounted item is now judged WITH its scan-tied delivery, provisional until Marg carries
    it) all go through it. The switch: `arrival.bill_over_tap` (stock_watch.settings, on).
  * **A spot count by its time** (`evening_count`): a stock point saved on its own day at or after `count.evening_hour` (17) is the END of its
    day — its day's sales are not taken off again (TYRO BR, Darpan 12-10 19:49). Its scan arrivals count from its moment. The full count's
    rows are never read as evening (their `at` is the entry moment). `shelf()` reports `base_evening`.
  * `s825_bill_judged` and `bill_units` share ONE `order_track.Ctx` per `stock_figure.Ctx` (one load of the scan store per page).
* **`/root/finance/stock_watch.py` 5acf3cf0 (S927's) → v1.9**: two settings rows on his page (`arrival.bill_over_tap` on/off,
  `count.evening_hour`); **every spot / darpan count writes the day's ONE line on his Needs-you** (`_s928_count_day`: notice kind
  `count_day`, once_key `counted:<day>`, rewritten as the newest notice after each count or correction; information unless an item is
  below the records, `_s928_cls`); `needs_you_lines` carries it.

Walk: `synth_s928.py <files> <COPY of finance.db>` — a scratch database with the copy's schema and NO rows of its own, a made-up spine
(spine_build.SCHEMA), made-up scans and orders of 'W928 PHARMA': 32 checks (two batch lines summed, s825 and the bill rule read the ONE match per order, free goods, two sizes on one order
matched one-to-one, not on the bill = 0, no scan = the tap stands, the switch, the evening count, the full count never evening, the
day's line, the settings); the control (the live files) goes red on 23. `regress_s928.py` — the figures of record on COPIES of the live
finance.db and spine.db, old files vs new: every difference must be explained by the bill over the tap or an evening spot count, else
the install stops. The earlier proofs run too (walk_s927, synth_s894: never worse). Cold review: NOT SAFE (3 MUST) → fixed → second look SAFE; its 2 SHOULD + 1 LOW built in (s825 reads the one match; the regress knows "a delivery inside the count"; the marg branch reads the scan arrivals once).
Install: one server line (the installer's header). Undo: `undo_s928.sh`.
