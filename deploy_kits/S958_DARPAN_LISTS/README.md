# S958_DARPAN_LISTS · Sanjeevni session 522 · 26-Nov-2026 — his word 10:22 / 10:24 ("build"; next list every day: "yes")

**What he saw.** Darpan's call list still showed Shivaaz's TOLTRIS PLUS of 12-Oct though he had stopped it; Darpan's "Abhi nahi chahiye" did not reach his Purchase orders page; YUVIKA's knee support (XL) showed pending though it came; the counts he sent never reached Darpan's phone or Aaj ka kaam; the next-list counts waited for Mon / Wed / Sat; Darpan's alerts did not land on the place.

**One not-needed rule (`order_track.gone`).** A line or carry is no longer awaited once he stopped it (or the same medicine came), Darpan said "Ab nahi milta" (his word awaited), or Darpan tapped "Abhi nahi chahiye". It stays on its order, settled and marked *not needed* on the order cards, and is on no list: the call list, Maal aaya, the purani dawa box, the carry, the tiles, Darpan's line. His "keep" brings it back (a carry re-opens on the next pass). **A bill's extra packs** fill the same item's other line on the order (the XL ordered twice, both on bill 842's first line).

**Counts.** His next-list asks go on Darpan's list the next morning, every day (a non-spot morning holds only his asks; a page opened later in the day never writes it). His Count now, and a morning list holding his asks, push to Darpan's phone and open his count screen. Aaj ka kaam's count line also counts his open Count-now asks (the parent's `aaj_seed.py`, DUE only). At the install: today's list of his waiting asks written now.

**Alerts.** The order notices open Darpan's own page for him. His page follows `#order` when already open; the app's worker (the parent's `portal_sw.js`) brings up his open page and tells it where to go.

**Files** (10): finance/order_track.py · stock_watch.py · stock_check.py · order_rules.py · darpan_kal.html · stockmatch.html · porders_s454.py · order_track_page.py · aaj_seed.py (the parent's) · portal/portal_sw.js (the parent's). **Walk** `walk_s958.py CODE COPY FROM_DIR` — 25 checks, twice on one copy; CONTROL red by the rules (19). **Undo** `undo_s958.sh`.

**Known, not built:** the duty-map SQL for reception's / Shavez's late-order lines (`reception.order_arrival`, `shavez.order_followup`, the parent's DUTY_MAP) does not know the not-needed rule — their Aaj ka kaam line can stay lit for an order whose open lines are all not needed (named to the parent).
