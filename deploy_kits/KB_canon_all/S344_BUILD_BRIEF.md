# S344 BUILD BRIEF — the Sanjeevni chat · 23-Oct-2026 06:47 IST → 24-Oct-2026 20:33 IST

*The one paper for the next chat (session 348) and for you. Part A is for you, in plain words. Part B adds to the build's specification in `S340_BUILD_BRIEF.md` Part B. The detail is in the Archive §S344 and the Book §15X.*

## PART A — for you

### What you asked, and what happened

1. **September's supplier payments (23-Oct).** The bank's SMS of 22-Oct (₹4,29,019) matched the September sheet's NEFT total to the rupee. The page had no button for an SMS-seen NEFT (F-1014), so the messages were released through the page's own route. **18 of 20 went** from the reception phone (9:50–10:08). **A.A. Pharmaceuticals and Deepam Pharma are unconfirmed.** Bass Pharma's message goes when its cheque is marked handed.
2. **The bank's alert e-mail:** nothing reads it, and at your word nothing will (D779).
3. **The expiry build — your additions (D777):** the dump list in two parts, orthotics first, then medicines; **New products this month** on your page; **Out of stock, waiting / Arrived again**. Still one build, the mock-up first.
4. **Shivani's "Maal nahi aaya" screen** showed no medicine names when nothing on an order came (F-1015). Repair in the same build.
5. **24-Oct morning reports:** the pickup program on the medical PC had been running only inside your SET login since 21-Oct (F-1016). Your login ended overnight, so Shavez's exports were lost; you exported both yourself. **You fixed it at the counter at 15:35** (the enable in "user"). The start-with-the-PC fix goes into the build.
6. **Shivani the fallback for the morning reports (D778)** — her app gets the tile in the build.
7. **Darpan's order sheet** of 23-Oct and his two of 24-Oct never became files. His re-export at 15:45 came through (12 dealers, 28 medicines).

### Yours

1. The publish (this close's record):

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Reception phone:** check the WhatsApp chats with A.A. Pharmaceuticals and Deepam Pharma. If the September payment message isn't there, tap *Bhejo* next to them on this page, on the reception phone:

```
https://followup.dr-manoj.in/finance/purchase/page/pay/2026-09
```

3. **Give Shivani** the Marg reports-only login ID and password.
4. **Before 1-Nov:** REEBORN D, RIFAVAX 550, VOM L. **Before 1-Dec:** INTACOXIA-60, DOLOGESIC SP.
5. Still from before: Ram Singh's report buttons; the two LINVIZ messages; *Change dealer* on B-0161 / B-0167; Flemcort 6 with Kedar.

### Next

1. **The expiry build (D771 + D777)**, the mock-up first.
2. Kit II, the buying model.
3. On Monday morning I read whether the pickup program now runs from "user".

## PART B — D777, added to the D771 specification

**Files to read whole before any edit (beyond S340's list):** `/root/finance/purchase_app.py` (`_log_new_items`, `_new_items_card`, `purchase_new_item`) · `/root/finance/porders_s454.py` (`_s619_late_card`, `_s619_rows`) · `/root/finance/order_track.py` (lines, `short_words`) · `/root/finance/supplier_msg.py` (`pay_card`, `neft_done`, `state`) · `/root/finance/bank_sms.py` (`neft_event_decide`, `needs_you_lines`) · `/root/finance/sanjeevni_approvals.py` (the Needs-you OK route) · `/root/finance/reports_tile.py` (the roles) · `/root/portal/tile_grants.json` (**the parent's file** — the kit's README says so) · the medical PC's `D:\SendToClinic\agent_guard.py`, `START_AGENT.cmd`, `ENABLE_AGENT_THIS_ACCOUNT.bat` (copies on manojz in `D:\Downloads\margsync\medical_SendToClinic\`).

1. **Dump in two parts:** orthotic = the category the order screens already use for orthotics (the sizes by their own codes, S613); orthotics first, each line with item, size, stock and last sale date; then medicines.
2. **New products this month:** the owner's Sanjeevni page reads `purchase_new_item` for the month (first seen, where seen, stockist, packing); the monthly ITEM_MASTER becomes a third source (a name never seen in a purchase or a closing). No staff line.
3. **Out of stock — waiting / Arrived again:** *waiting* = an order line short or missing (`purchase_order_line.short`, `order_carry`) for an item whose newest closing is zero; the day it went short, the stockist, the times re-ordered. *Arrived again* = the first purchase line for that item after it; date, stockist, quantity; shown seven days. Read-only.
4. **F-1015:** `_s619_late_card` lists every awaited line (`state in open, part`) with its quantity for a wholly late order too; the reception page changes in nothing else.
5. **F-1014:** the pay card offers the confirm for an unconfirmed SMS event (the same `neft_done` call); `neft_event_decide('ok')` queues through `supplier_msg.queue_neft`; idempotent; audited. Proof on a copy of the database: a fresh SMS event → OK → twenty rows; a second OK → nothing new.
6. **F-1016, the permanent half:** an installer run once in the SET account over RDP — a Windows scheduled task at the PC's start (no sign-in needed) that starts the guard; the guard's lock rules unchanged; read back by the task's own query and the heartbeat. Proof: after a restart, before anyone signs in, the heartbeat says ALIVE.
7. **D778:** `tile_grants.json` — Shivani's `extra` gains "Aaj ki reports"; her login opens `/finance/reports/aaj` with the same steps; proved by rendering as her.

**The proof before the publish (S340's, plus):** each staff screen rendered as its staff login; the stock figures byte-identical; a cold read by an independent agent.
