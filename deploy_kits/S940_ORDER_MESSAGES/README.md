# S940_ORDER_MESSAGES · Sanjeevni session 509 · 23-Nov-2026 · D1053 (the owner's "Mockup okay", 18:52 IST) — after S939

The purchase order flow, part 2 — **the messages and his four steps**. Mock-up: https://claude.ai/artifact/4zjaEK7xSi91y8e9kGVjWG

* **`/root/finance/order_d1053_msg.py`** (new). Each message opens its own page; all are made and sent by order_rules' ten-minute tick (05:00 – 21:50; the web process cannot push, F-767), so a message lands within ten minutes of its moment:
  * **A** the Marg sheet came in → Darpan (Devanagari, his tab) and the ordering staff (`order.notice_to` less Darpan; Roman Hindi, the order screen). The doctor already has "Darpan's order sheet ✓" (owner_notice) — not sent twice. The old "Darpan ki order sheet aa gayi" push gives way to A while the flow is on (kept on the sheet as `replaced: d1053`).
  * **B** Darpan made it final → the staff ("WhatsApp bhejiye") and the doctor (what was added, what went to his word).
  * **C** the WhatsApps went → the doctor and Darpan, once every order message after the final has been answered by the phone (WhatsApp n · call n · failed n, named).
  * **D** each delivery entered (arrival tap, bill scan or Marg) → Darpan: "<dealer> का माल आया" — what came, what did not.
  * **His page** (`/finance/porders/flow`) opens with the day in four steps: sheet in · final · sent · arriving, and his out-of-stock words waiting (they never hold the order). While Darpan has not made it final, a link to Darpan's tab, where the doctor may decide and make it final himself.
  * Recipients are settings: `order.d1053_msg_darpan` (darpan), `order.d1053_msg_staff` (empty = `order.notice_to` less Darpan), `order.d1053_msg_owner` (manoj). Start: `order.d1053_msg_since` (the install). Table: `order_d1053_msg`.
* **`/root/finance/porders_s454.py`** — the S940 block appended (his page's steps; the old notice gives way in this process too).
* **`/root/finance/order_rules.py`** — the S940 block before its `__main__` line: the tick's S454 pass then `order_d1053_msg.tick`.
* **After the install** `s940_on.py`: the messages start now; nothing earlier is announced.

Walk: `walk_s940.py` on a copy, pushes into a stub file (never a phone): A to Darpan and the staff with their pages, the old notice not pushed, nothing twice; B after the final; C waits while a message is with the phone, then goes; D to Darpan, not twice; his page's steps; switched off nothing. CONTROL (S939 alone) red.
Undo: `undo_s940.sh` (the two files back, `order_d1053_msg.py` aside; S939 stays).
