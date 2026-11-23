# S941_ORDER_ADDINS · Sanjeevni session 509 · 23-Nov-2026 · the owner's "YES FOR ALL" (20:01 IST) — after S940

The four add-ins of the purchase order flow's mock-up (https://claude.ai/artifact/4zjaEK7xSi91y8e9kGVjWG), made and sent by order_rules' ten-minute tick; nothing from before the messages began (`order.d1053_msg_since`) is announced.

* **E — late:** an order of the flow not come by its due evening → Darpan (his tab) and the staff (the late page), once, from `order.d1053_late_hour` (09) the next morning.
* **F — reminders:** the sheet not final `order.d1053_nudge_final_min` (45) after it came → Darpan; final but nothing gone `order.d1053_nudge_send_min` (30) after → reception; the doctor only if still stuck `order.d1053_nudge_owner_min` (30) after the reminder.
* **G — 20:00 summary:** once a day at `order.d1053_summary_at` (20:00) → the doctor and Darpan: ordered · arrived · short · late · waiting for his word.
* **H — wrong bill:** a scanned bill tied to an order of the flow names a medicine the order did not carry (and no other order of that dealer in 30 days), or more strips than ordered → the doctor and Darpan; it opens `/finance/porders/d1053/bill/<scan>`: each line **Keep / Send back** (two taps; the doctor or Darpan). A Send back is reception's "Wapas bhejna hai" on her order screen until she taps **Wapas kar diya**.
* **His page:** step 1 counts Marg's open order (as reception's screen); a sheet made final by the install counts the day's orders as sent.

Files: `/root/finance/order_d1053_msg.py` v1.0 → v1.1 (whole) · `/root/finance/porders_s454.py` (the S941 block appended). Tables (new): `order_d1053_billq`, `order_d1053_billseen`.
Walk: `walk_s941.py` on a copy + a made-up assets database (no patient paper), pushes into a stub file. CONTROL (S940) red. Undo: `undo_s941.sh`.
