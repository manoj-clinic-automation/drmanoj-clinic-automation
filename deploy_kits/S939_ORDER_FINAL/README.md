# S939_ORDER_FINAL · Sanjeevni session 509 · 23-Nov-2026 · D1053 (the owner's "Mockup okay", 18:52 IST)

The purchase order flow, part 1 — **Darpan makes the day's list final**. Mock-up: https://claude.ai/artifact/4zjaEK7xSi91y8e9kGVjWG

* **`/root/finance/order_d1053.py`** (new) — the logic. Switch: setting `order.d1053` (`1` on; anything else: every screen and door as before).
  * **The old-line step.** The old lines (`order_s778.red_lines`) are Darpan's questions on his tab: आज के ऑर्डर में जोड़ो · आउट ऑफ़ स्टॉक → डॉक्टर साहब (leaves the order at once; the doctor's word follows and never holds the flow) · अभी नहीं चाहिए (asked again on the next Marg sheet).
  * **F-1623.** A line whose goods came leaves by itself: a Marg purchase line of the medicine from that dealer on or after the line's day, on a bill other than its own order's (Amir's export); or, for a line of Marg's open order ordered here, its order's bill scan.
  * **Reception only raises.** "Dealer ke paas nahi → Darpan ko" on a card line and on a late order of her strip; her Out of stock, Dobara and remove are refused (409 `raise_only`). Darpan answers रहने दो · आउट ऑफ़ स्टॉक · इस बार हटाओ (the S619 `dealer_no` removal).
  * **F-1624.** On `order.source = marg_sheet` Darpan's tab shows reception's cards, never the engine's proposals beside them.
  * **सूची पक्की करो** once every question is answered (Darpan, or the doctor); until then WhatsApp all — the page's button, the confirm screen and `POST /finance/porders/api/s454/whatsapp` — is locked (409 `not_final`). Call and Order done stay open. Final is per Marg sheet.
  * **The sent record.** Reception's "Ho chuke" becomes "BHEJA GAYA — maal aane tak yahin dikhega": each order of the last 7 days not yet arrived, with its WhatsApp / call time and the day its goods are due.
* **`/root/finance/porders_s454.py`** — the S939 block appended (the wraps above; door `POST /finance/porders/api/d1053/raise`).
* **`/root/finance/darpan_kal.py`** — the S939 block appended (`_s485_payload` carries `d1053`; door `POST /finance/darpan/kal/api/order/d1053` {do: decide | final}).
* **`/root/finance/darpan_kal.html`** — the tab draws the questions, the final, the one list and what went (three exact anchors; `make_s939.py`).
* **After the install** `s939_on.py` sets `order.d1053 = 1` and marks Marg's newest sheet (today's, already ordered) final by `install`, so tonight's screens are not locked; the next sheet is the first one Darpan makes final.

Walk: `walk_s939.py` through the real porders and darpan_kal blueprints on a copy of the database (29 checks: the one list, F-1623 with a made-up Marg purchase and the carry's own bill, the lock on all three doors, the raise and the refused remove / Out of stock, each answer, the refused and the accepted final, the open door after it, the sent record, the switch off). CONTROL (the FROM files) red.
Install: one server line (the installer's header). Undo: `undo_s939.sh` (the flow off, the files back, `order_d1053.py` moved aside).
