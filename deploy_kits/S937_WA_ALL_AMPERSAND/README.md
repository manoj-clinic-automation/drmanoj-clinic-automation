# S937_WA_ALL_AMPERSAND · Sanjeevni session 508 · 23-Nov-2026

The owner (17:24 IST): "Today's Orders whatsapp messages are not going out, from reception mobile". (17:10 / 17:30): he could no longer reach and print the order sheet from his Purchase orders tile — "Go".

* **`/root/finance/porders_s454.py`** — the WhatsApp-all confirm screen wrote its supplier list into its `<script>` through `html.escape`. Inside a script no entity is decoded, so a dealer whose name carries `&` (RADHA MEDICAL & SCIENTIFIC, on 23-Nov's Marg order) reached the server as `&amp;`, never equalled the server's list, and every press answered 409 "List badal gayi" and reloaded — nothing queued, the phone never got a message (F-1619). Now the list is JSON with `& < >` written as `\u00XX` escapes (`_s937_js`), so the browser sends the true names. The phone, the queue and the server's own list check are unchanged.
* **`/root/finance/order_flow.py` v2.0 → v2.1** — a clear **"Today's order sheet — Print · WhatsApp →"** button under BACK on his Purchase orders page (`/finance/porders/flow`), to reception's To-order screen (`/finance/porders/s454/order`: Marg's open order, Print the order sheet, WhatsApp all). It is there all day — reception's own To-order row hides once every supplier is ordered.

Walk: `walk_s937.py` through the real porders blueprint in a Flask test app on a copy of the database — made-up dealers with `&`, an apostrophe, `< >` and `</script>`: the list the screen sends equals the server's, the press queues every one (the order door and the phone stubbed), a moved list is still refused; his page carries the button; the sheet opens for him. CONTROL (the live files) red on 5.
Install: one server line (the installer's header). Undo: `undo_s937.sh`.
