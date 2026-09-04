# S225_STAFF_ORDER — the staff order page

**What the owner asked for (04-Sep-2026, 11:45 IST, on seeing the first Orders page):** staff should see
*item, current stock and order quantity* and nothing else; quantities in the unit already decided (strips),
*rounded to 10 strips then multiples of 10*; the order goes to the stockist as a WhatsApp reading
`Sanjeevni Medicos, G 15 Rampur Garden, Bareilly` then item name with quantity; staff call the stockist by
tapping; staff print an A4 PDF of the order on the reception printer.

**What this kit does.** `purchase_app.py` rev 6 — a full-file replacement of rev 5 (`6366edb5…`), same mount,
`finance_app.py` untouched:

- `/finance/purchase/page/staff` — per stockist, three columns: **Item · Stock now · Order qty** (in strips /
  bottles / tubes / units by the item's Marg packing). Strips round UP to 10, then multiples of 10. Bottles and
  the like keep the engine's box quantity — a syrup is not ordered ten at a time by rule. No rates, values,
  cadence, cover, confidence or reasons: those stay on the doctor's Orders page, which is unchanged.
- **Send on WhatsApp** — one tap. The order is written as **sent**, by this person, at this minute, audited
  (`order_sent_whatsapp`), and the browser opens `wa.me` with exactly the dictated text: the header line, a
  blank line, `Item — qty unit` per line. Nothing else. The phone number is never printed on the page; it
  travels inside the link. A stockist with no number gets *"ask Dr Manoj"* and no order is written.
- **Call** — a `tel:` button per stockist.
- **Print A4** — `/finance/purchase/order/<id>/pdf`: header, stockist, Item / Qty / Unit, a signature line, who
  prepared it and when. No rates. Uses `clinic_day_pdf.py`'s writer (S224, already on the box).
- Any signed-in person of the medical unit (viewer, maker, checker) may open the page and send. Signed out → login.
- The **Order Medicines** tile (🛒), right after Marg Purchases, granted by name in `tile_grants.json` v8 to
  amir, shavez, darpan, alisha and shivani — the five who hold Marg Purchases. In `portal.py` it carries
  `roles ["doctor"]`, so a lost grants file leaves it with the owner alone (fail closed for staff).

**Proof.** `selftest_staff_order.py` runs the entire S224 selftest as regression and then 33 staff checks on
the real Marg archive: **261/261**. `selftest_staff_tile_s225.py` rebuilds the live `portal.py` from the
repository patch chain — landing EXACTLY on the box's read-back pin `d2803804…` — and applies the patcher:
**ALL PASS**, predicted new pin `7bc59115…`. `walk_staff_gate_s225.py` is the live-shape walk and runs on the
box inside the install line, before the restart, against a copy of the db through the real front gate.

**Not in this kit (§8 order, next):** the phone book with two numbers and owner-verified bank fields · the
arrival flow (acknowledge / supplied qty / short) with the scan button in context · the nightly cross-check ·
new-items log · salt list · stock snapshot on capture.
