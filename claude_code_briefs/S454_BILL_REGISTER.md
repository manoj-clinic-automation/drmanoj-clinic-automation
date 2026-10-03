> **HOLD — DO NOT BUILD (03-Oct-2026, 07:43 IST).** The owner changed the design after this text was written: the order now comes from Darpan's Marg order sheet, WhatsApp goes to all suppliers in one tap, September is parked, a printed order sheet is added, and the items screen and the medical PC's refusal note join the build. This text is superseded and is being rewritten from `S283_PURCHASE_FLOW_DECISIONS_03OCT.md`. **If you were handed this file, stop and tell the owner.**

# Claude Code brief — S454_BILL_REGISTER (the pharmacy's purchase flow at reception as one simple screen: order by phone, arrival, bill scan, and one question at a time; scans paired with Marg on the fields a scan reads well; the owner's month register; Amir left as he is)

Written 03-Oct-2026 by the Sanjeevni chat (S283 post-close), after a full day's discussion with the owner and two independent reads of this text against his words. **This text replaces every earlier text of this file** (their hashes began e43cb026, 979c3cec, edecf773, 5f8d091c). Read `CLAUDE.md` first.

**Kit S454 · faults F-690, F-691, F-695 · decisions:** D665 (the live flow at reception: §3, §5, §6) · D662 (pairing and the month register: §4, §7) · D663 (Vendor payments: §8). It serves D650 (Marg's entry is final and overrules the scan's reading), D640 (a tap per line for staff), D643 (the scanner is asked nothing while scanning), D648 (every duty has a door) and D626 (the buying rules).

**The mock: `claude_code_briefs\S454_BILL_REGISTER_MOCK.html`. Read it before §3.** The owner saw these screens on a canvas over several rounds. Screens 8, 9, 10, 11 and 13 were corrected to his rulings after his last look; he is told so, and §13 asks you to show him the built ones. The staff screens (1 to 12) bind you in their words, their order and their buttons. Screen 13, the owner's register, binds you in the names of its states and its shape. Its counts are examples. The screens the mock does not show are listed in §3.8.

**Runs on S452's files** (live 02-Oct 23:51 IST; its pins equal the 03-Oct 03:12 nightly bundle, §11).

**Touches (declared, all Sanjeevni's):** `/root/finance/porders.py`, `porders.html`, `order_rules.py`, `purchase_app.py`, `amir_day.py`, `reports_tile.py`, `sanjeevni_approvals.py`, `supplier_msg.py` (§8 only), `claude_code_briefs/DUTY_MAP.md` + `.json`. A new template or module beside `porders.html` is allowed; pin it.

**READ ONLY:** `assets.db` and the asset app (its intake link and its re-lane route are called as they are; `asset_register.py` is not edited), the stock-count tables, `item_alias.py`, `packs.py`, `darpan_kal.py`.

**No parent file:** not `finance_app.py`, `portal.py`, `tile_grants.json`, `finance_approvals.html`, `asset_register.py`. If one turns out to be needed, stop and report; do not edit it.

## 0 · The rules this build stands on

1. **A staff screen shows only what that person has to do.** The owner, 03-Oct: "They should only see what they need to do. What has already been accepted by the system is not a part of their flow. They should get it in very simple terms. The sections are nice but the arrangement seems very overwhelming." One task on the screen at a time. No counts of settled things, no day counts, no tags, no explanations.
2. **Staff pages in Roman Hindi; the owner's in English.** Phone width first. Buttons at least 44 px. Typing only where a number on the paper must be given.
3. **Amir is asked nothing new.** The owner: "A soft start is what I want for Amir. Abruptly we cannot change the system. We will keep both the flows." No new kind of line reaches any list of his from this kit.
4. **September is practice.** The owner: "The backlog is only for the assessment and training and not for any real accountancy or accountability work." Alerts, day counts and the accept-without-paper tap start with October (`purchase.register_from`). A practice month's lines stay in the staff's lists so they can practise, and its register shows its states and counts for the owner's assessment. **Nothing new of a practice month reaches Amir.** What S440 already puts on his *Marg sudhar* today (a bill entered twice in Marg; an amount already answered) stays as it is; this kit pulls nothing off his lists and adds nothing to them.
5. **Every threshold is a setting the owner can change on his screen** (§10).
6. **The old page stays one tap away** (§3.7) until a later kit removes it. There is no timer.
7. **Build in the order of the parts and walk each part.** One kit. If the whole cannot be made clean in one kit, install §3 to §6 and §8 as S454, keep what §3.4 and §3.5 record for the register in their tables and show it as plain lines on today's Scan links page, say plainly what of §7 and §9 is left, and stop there.
8. **"REPORT" means: write it in `REPORT_S454.md`.** It never means wait for the owner. The only stops are the ones this brief names.

## 1 · How this came

The owner asked what the net result was of September: the staff had scanned the bills, Amir had keyed every purchase into Marg. The chat read his live pages: 63 of 81 Marg bills had their scan, and the scan list had stood untouched since 30-Sep. A first brief was written for a month register. He then saw the staff screen as a mock, found it too heavy, and widened the question to the everyday flow: the reception staff order the medicines, receive them and scan the bill, and the system pairs the scan with Marg when Amir enters the bill. His rulings, in his words:

- **The regular flow:** "The goods come with the bill and the bill is scanned then or within a day." September's bills were all scanned at the month's end; that was a one-time catch-up. From here on the scan comes first, Amir's Marg entry follows on his next visit (two to three days), and the system pairs the two when his export arrives.
- **Ordering:** "The default is calling the supplier. One card per supplier will be 'order karo'. They call from there only; the click to call should exist. That should terminate with a confirmation, because sometimes the call is not picked or the number is busy. They should have a tap, 'order ho gaya'. If they do not tap, we keep it posted as a pending order to be made by the reception staff." And: "The ordering should be first the automated WhatsApp, after we set the reception mobile for that."
- **Out of stock at the stockist:** "Leave it as such."
- **Arrival:** all received unless tapped otherwise. "The bill scan there needs to be optional and not compulsory, because staff might be busy at that time and might do the work later."
- **Stock basis:** "You have the 6 September stock report and can work out the shortages using that, till the vouchers of the loss and extra medicines are filed."
- **Amir:** "All purchases are entered in a physical register with the date, bill number, vendor name, items. Amir writes the Marg number there whenever he enters those bills. That is his current flow and it will take time to shift him." Reception scans; the system matches "as those bills are entered". Only "once this flow is established and running" do scans go into Marg's digital entry without waiting for his visit: "that might take one or two months."
- **Two slips:** two Yuvika papers shown as "not in Marg" were handwritten estimate slips for the procedure room. "These slips are not of pharmacy purchase. They are for the direct purchases in the consumption zone, not related to the Marg pipeline. They are only scanned as all documents are scanned at the reception." And of such papers: "Later on I can assign lanes for such purchases, or Shavez can assign."
- **Vendor payments:** "The vendor payment sheet should be limited to me and Shavez."

## 2 · What the chat read — REPORT the same facts first, as they stand on your day

**Scans against Marg** (`/finance/purchase/page/scans`, `/finance/purchase/page/sarvam?month=2026-09`, as the owner, 03-Oct):

- September: 81 Marg bills · 63 linked to a scan · 18 with no scan · 12 scans with no Marg bill.
- *Scan ka kaam*: To scan 11 · Is this the bill? 8 · Choose the supplier 3 · Match the amount 4 · Waiting for Marg 0 · second scans 1 · S441's questions 6.
- **F-691:** those counts are what they were on 30-Sep. Nobody worked the list and nothing told anyone. Say from `audit_log` when the last tap was, and whose.
- Of the 18, six probably have a scan read differently (bills 75904, 78354, EP002243, IP006767, KEDAR 189, A.A. 416). KEDAR 163 is in Marg twice.
- **F-690, the Sarvam page miscounts.** It says of the 63 linked bills: supplier wrong 13, bill number 7, date 9, total 10. Read cell by cell, in substance: supplier wrong 3, bill number 4, date 9, total 10. The rest are a full stop, a bracket or a prefix ("PVT. LTD." against "PVT LTD"; a printed number with its series and financial year against Marg's short number). All of supplier, bill number and date are right on 47 of 63. Item lines: 28 of 158 read right (batch 67, name 36, rate 33, quantity 22, expiry 21 wrong).
- **F-695:** scans B-0007 and B-0018 (Yuvika, no number and no amount read) were on Amir's list as bills Marg does not have. They are estimate slips. Yuvika's four September bills in Marg all have their scans. On 03-Oct both were moved to the clinic lane in the owner's login; Amir's list reads 0.

**Ordering** (`/finance/porders/api/state`, as the owner, 03-Oct; and the 03-Oct nightly copy of `finance.db`):

- The ordering screen is live: 18 suppliers, 39 lines planned, the rules approved by the owner on 26-Sep.
- **No medicine order has ever been sent through it.** `purchase_order` holds one row: the owner's test order to Yuvika of 26-Sep; its first line cleared itself against Yuvika's bill of 28-Sep. `order_proposal`: 9 merged, 1 open. The order days of 28-Sep (8 suppliers) and 02-Oct (Kedar) were merged forward to Monday 05-Oct by `nightly()`.
- **Stock basis.** `order_rules` takes a medicine's shelf from Marg's snapshot (`_latest_snapshot`, `s["qty"]`). The orthotic side (`porders.ortho_items`) takes it from the count: counted + purchases since − sales since + returns.
- **The count is all there.** `stock_count` id 1 (06-Sep): `stock_count_item` holds 373 items, every one with `counted_qty`: Medicines 284, Orthotics 69, Consumables 20. Of the 377 items in Marg's newest snapshot, 372 have a count row; 5 do not.
- The two differ a great deal. MEG QCS: counted 640 on 06-Sep, Marg 477 on 30-Sep. PATOPAN DSR: 314 and 43. TYRO BR: 470 and 57. The count's loss and extra vouchers are not in Marg yet.
- RAVI MEDICAL AGENCY has no phone in the phone book. Two planned items have no supplier on record.

## 3 · PART A — the reception screen (`/finance/porders`), one task at a time

For every login in `porders.senders` (manoj, darpan, shavez, shivani, alisha, reception). The owner sees the same screens with the same buttons, in English. A viewer (`porders.viewers`) keeps the old page. S441's "who is working" on the shared reception login stays, and that name is the person on every record below.

### 3.1 The home — "Aaj ka kaam"

- A large button first, always, on the finished screen too: **"Naya bill scan karo"**. It opens the asset app's intake with the pharmacy lane and this month set, and comes back here (S403's link, S440's `from`).
- Then one row for each kind of work, **shown only when its count is above zero**: a big tappable row with its count and its name, nothing else.
  1. **"Order karna hai"** — the suppliers to be ordered from today (§3.2).
  2. **"Maal aaya?"** — the orders made and not yet received (§3.3).
  3. **"Bill scan karna hai"** — the papers still to be scanned (§3.4).
  4. **"Photo dekh kar bataiye"** — the questions about scans (§3.5).
- When no row has work: under the button, one green card, **"Sab kaam ho gaya"**, and "Naya bill aate hi yahan dikhega."
- Nothing else is on the staff's page: no keep-in-stock numbers, no rules, no stock, no cover days, no history.
- **The doors stay as they are:** the portal's Purchase orders tile; and the line on Darpan's *Kal ka hisaab* card, which comes from `order_rules.day_summary` and keeps counting what it counts today, the orders not yet made. `darpan_kal.py` is not edited.

### 3.2 Order karna hai — by phone, ended by one tap

- **The list.** One card per supplier with an open proposal for today: the supplier's name, how many medicines, and **"Order karo"**. Four at a time, then "Baaki N supplier dikhaiye". A held proposal (under the minimum, paused) is not the staff's work and is not listed.
- **One supplier.** The medicines and the quantity of each in the order's own unit (S417's words: strip, tube, bottle). No stock figure, no cover. Then:
  - **"Call karo"** — a `tel:` link to the supplier's number from the phone book (`_phone_for`). The tap is recorded (who, when). The number is also shown in small text under the button, for a desk that cannot dial (not drawn in the mock).
  - "Baat ho gayi? Tab yeh dabaiye. Phone nahi laga to BACK, order yahin baaki rahega."
  - **"Order ho gaya"** — this makes the purchase order exactly as `send_proposal` makes it today (the same tables, the same ten-minute repeat guard), with `note` saying it went by call, and marks the proposal ordered by this person. No WhatsApp window opens.
  - A small text button **"Quantity badalni hai?"** opens S410's own plus, minus and remove on each line; what is changed goes with "Order ho gaya".
- **There is no tap for a call that failed.** Leaving the screen without "Order ho gaya" is all it takes: the proposal stays open. If "Call karo" was tapped and the order was not made, the supplier's card in the list reads "call kiya tha, order baaki".
- **No phone in the phone book:** no Call button; the line "Is supplier ka phone number yahan nahi hai"; "Order ho gaya" still works.
- **If the stockist says on the call that an item is not there**, nothing new is tapped. The order is made as it is, and that item is answered "Nahi mila" at arrival, as today. (The owner: out of stock, "leave it as such".)
- **Pending stays posted.** The cadence still decides the day a supplier's proposal is first made. Today `nightly()` merges an unmade proposal into the supplier's next order day, which can be a week away. Change it: an open proposal of an earlier day is carried to **the next working day** (a blocked day or a holiday is skipped), as that supplier's one proposal, its lines planned again on that morning's stock, `carried_from` kept. If the fresh plan is empty the proposal closes itself. Never two proposals for one supplier on one day: the interim check skips a supplier that already has an open proposal that day. The nine rows already merged into 05-Oct are left as they are; say what they became.
- **The channel is a setting**, `order.channel`:
  - `call` — the default, as above.
  - `whatsapp_tap` — today's one-tap wa.me order, kept whole: the supplier screen shows today's "…ko order bhejo", which makes the order and opens WhatsApp as it does today; "Order ho gaya" is not shown; "Call karo" stays below as a plain link.
  - `whatsapp_auto` — the reception mobile sending by itself. **Not built here.** The setting refuses the value with one line saying so. It is the owner's first choice once that phone is set up.
- **Untouched:** the owner's approval of the rules, the freeze, a supplier's pause, holidays, blocked days, the minimum order, the cadence, the repeat guard. When ordering is frozen the row is not shown.
- **Orthotics** keep their own rules (S403). When that section offers an order, it is one more supplier card in this list, ended the same way.
- **The notices** at 12:00, 15:00 and 17:00 keep going to `order.notice_to`, counting the suppliers still to be ordered.

### 3.3 Maal aaya? — everything received unless tapped; the bill scan optional

- One order on the screen. With more than one waiting, a list first: supplier and order date, one tap each.
- The medicines and quantities, each shown as received. Above them: "Jo kam aaya ya nahi mila, us par tap kijiye."
- Tapping a line opens the three answers the page has today: **"Kam aaya"** (one box, "Kitna aaya?"), **"Nahi mila"**, **"Aa gaya"**.
- **"Maal aa gaya"** saves it through `api_arrive`'s own rules: untouched lines as received, the tapped ones as answered. **"Abhi nahi aaya"** leaves, saving nothing.
- Then one screen: a green "Maal darj ho gaya", and **"Bill abhi scan karna hai?"** with two buttons of equal weight:
  - **"Bill scan karo"** — the intake, with the supplier, the pharmacy lane and the month filled in.
  - **"Baad mein"** — home. The line under it: "Baad mein karenge to yeh 'Bill scan karna hai' mein milega."
- **One paper, one line.** An arrived order whose bill is not scanned waits under "Bill scan karna hai" as "<supplier> · <dd-mm> ka maal". It leaves when the first of these happens:
  - a pharmacy-lane scan of that supplier, **scanned at or after the time the order was made** and not tied to another order, is tied to it (so a bill scanned the evening before the arrival tap counts);
  - a Marg bill of that supplier, **dated on or after the day the order was made**, appears with no scan: that bill's own line (§3.4) takes the order's place, never both;
  - `purchase.arrival_scan_days` (7) pass from the arrival. After that only the Marg bill, once entered, can ask for the paper.
  - With two arrived orders of one supplier, the older order is served first.
- Keep the tie between an order and its scan in a table on the finance side; the asset app is not edited. Say how you tied them.
- Marg's purchase still clears an order by itself, as today.
- Goods that came without an order in the system have no line here; the staff use "Naya bill scan karo".

### 3.4 Bill scan karna hai — a short list by supplier

- **What is in it:** arrived orders with no bill scan (§3.3), and Marg bills with no scan and no likely scan (today's "Scan karo" group).
- **Grouped by supplier**, as the papers are filed: "KEDAR PHARMACEUTICAL · 3 bill". Under it one line per paper: the bill number (or "<dd-mm> ka maal"), the date, the amount, and **"Scan karo"** (the pre-filled intake). Five lines at a time, oldest first, then **"Agle 5 dikhaiye"**.
- A small text button at the foot, **"Koi paper nahi mil raha?"**: the Marg-bill lines with a tick each and one button "Paper nahi mila". It is recorded (who, when); the line leaves the staff's list and shows on the owner's register (§7.1). An arrived-order line has no such tick; it only waits.

### 3.5 Photo dekh kar bataiye — one question on the screen

A queue, oldest scan first. Each card: a bar with **"Sawaal i / N"** and a thin progress line; the scan's first page, large (tap opens the file); one line saying which paper (supplier, and the bill number where it is not the thing being asked); the question in one line; big buttons; **"Baad mein"**, which sends the card to the end of the queue for this sitting. After the last card: "Sab kaam ho gaya".

The kinds, and their words:

1. **Is this the bill?** (S440's confirm, for a scan not yet paired) "Kya yeh <SUPPLIER> ka bill <number> hai?" with "<dd-mm> · <amount>" under it. **Haan / Nahi**, with today's meaning. Where that bill already has a scan: "Kya yeh <SUPPLIER> ke bill <number> ka doosra scan hai?"
2. **The amount differs** (S440's amount, for a paired scan). "Bill par total amount kya likha hai?" Two buttons with the two amounts, **not labelled as Marg's or the scan's**, and "Koi aur amount" with one box.
   - In a month from `purchase.register_from` on: what follows the answer is what follows today. That path is not changed.
   - In a practice month: the answer is recorded on the register only. Nothing goes to Amir.
3. **The supplier is not known** (S440's vendor, for a scan not yet paired). "Yeh bill kis supplier ka hai?" Up to three likely suppliers as buttons, then "Koi aur" with today's list.
4. **Is it a pharmacy bill?** (new, F-695; §3.6).
5. **S441's questions** ("Dobara scan?", "Galat lane?") join the queue as cards with their own words and their own answer routes.

**No card is made for a date or a bill number that differs on a paired scan.** Marg's entry stands (D650); the scan's reading is counted as a misreading (§4, §7.4).

### 3.6 A paper with no bill number and no amount is never Amir's (F-695)

**The supplier never decides the lane.** Yuvika sells the pharmacy its orthotics on printed bills, which are in Marg, and the procedure room its plaster on handwritten slips, which are not. The paper decides.

- A pharmacy-lane scan on which neither a bill number nor an amount was read (S440's `no_digits`), or whose reading is headed Estimate, Challan or Quotation, is never in *Marg ka intezaar*, never on Amir's list or in its count, and never counted on the register as waiting for Marg.
- It is a card in §3.5: **"Kya yeh dawa (pharmacy) ka bill hai?"** with two buttons and nothing to type:
  - **"Haan, pharmacy ka bill"** — the scan stays in the pharmacy lane and leaves this card (if its supplier is not known, the supplier card comes next).
    - If figures were read on it (an Estimate or Challan heading with a number or an amount), it is matched by §4 like any scan.
    - If nothing was read, it is an **unread pharmacy paper**. **It never pairs by itself.** When exactly one unscanned Marg bill of that supplier is dated within `purchase.unread_pair_days` (7) either side of the scan day, now or later, a kind-1 card is asked: "Kya yeh <SUPPLIER> ka bill <number> hai?" — reception reads the number on the paper. "Haan" pairs it; the row reads "Has its scan" with the note "paired by reception; nothing was read on the paper". "Nahi", or two such bills, or none: it waits.
    - Until it is paired it shows on the register as "unread pharmacy paper", where a checker may complete it in the asset app as today.
  - **"Nahi, pharmacy ka nahi"** — the scan leaves the pharmacy lane for the asset app's clinic lane, through the asset app's existing re-lane route (`/bills/<id>/lane`, the one S440's "Galat lane" uses). Its exact lane is set there later by Shavez or the owner; reception is not asked. If that route cannot be called from here, the button opens the asset app's own control for that scan; say which you built.
- S440's line "Number / amount nahi padha gaya — manager isse theek karega" goes.
- **Not here, the parent project's (D664):** how clinic consumables are grouped, one PDF for a bill and its warranty cards, the Dr MK expense lane.

### 3.7 The old page stays one tap away

- `porders.simple` = 1 serves these screens. Set to 0, everyone is back on today's page.
- With it on, `/finance/porders?old=1` serves today's page. A small link at the foot of the home, "Purana page", for the owner and Shavez only.
- Today's routes keep working; the new screens call them where they can.

### 3.8 Screens the mock does not show — build them in the same pattern

The supplier card of §3.5; the second-scan wording of kind 1; S441's cards; the tick list of "Koi paper nahi mil raha?"; an arrived order's line in the scan list; the list of orders when more than one waits in "Maal aaya?"; a supplier with no phone; `order.channel=whatsapp_tap`; the owner's English. Put a picture of each (a saved page from the walk) in the kit and name them in the report, so the owner can look.

## 4 · PART B — a scan is paired with its Marg bill on what a scan reads well (`purchase_app.py`)

One set of rules, in one function, used by the matcher, the staff's questions, the register and the Sarvam counter. Two pages must not be able to disagree about a bill.

**How a field agrees**

- **Supplier:** start from what `_vendor_match` and `supplier_key` do today, and add only this: punctuation and brackets are dropped; "&" equals "AND"; the standalone words PVT, LTD, P, CO and M/S are dropped (never a letter inside a name); a trailing BAREILLY is dropped. Then the learnt spellings (`purchase_scan_alias`). The shop's own name, or a heading such as "WHOLE SALE CHEMIST & DRUGGIST", is never a supplier: the field is "not read".
- **Bill number:** Marg's number, leading zeros dropped, equals **one whole run of digits** in the scan's reading. A run that is the financial year, and any reading shaped like a drug-licence number (ending "/BLY" or the like), is never the bill number. Letters in Marg's number are compared by their digit run, as S439 does.
- **Date:** the day and the month agree. A year other than Marg's is a misreading and is ignored.
- **Total:** within Rs 1 is equal (paise; fixed, not a setting). Up to `purchase.total_noise_rs` (10) agrees, with the difference shown (the D622 rule). More differs.

**The states of a Marg bill that has a scan — each bill in exactly one**

- **Amount differs:** paired, and the total differs by more than the noise. One card (§3.5, kind 2). After the answer the row is Verified or Has its scan (the paper agreed with Marg), or it stays here and says "the paper reads <amount>".
- **Verified:** the total agrees, the bill number agrees, and at least one of supplier and date agrees. This is how the matcher pairs by itself. If the other of the two was read differently or not read, the row is still Verified and carries one note saying what the scan read.
- **Has its scan:** paired, the total agrees or was not read, and the row is not Verified: the bill number was read differently or not read, or neither supplier nor date agrees. Such a pair comes from reception's "Haan" (§3.5 kind 1, §3.6) or from the auto-link below. Marg's entry stands. The row carries one note saying what the scan read. Nobody is asked.

A link that exists today is never undone by these rules; they only give it its state.

**What is already known is not asked — only if the record shows it.** REPORT what the intake link (S403, S440's `from`) leaves on a scan's record today. Then:

- If the record shows the scan was made from a line of this screen (§3.3, §3.4): its supplier is taken from that line, the supplier card is not asked, and the §3.6 card is not asked (it is a pharmacy paper). **It settles nothing by itself:** the scan still pairs only by §4's rules or by reception's "Haan". A wrong paper scanned from a line must not settle that line's bill.
- If the record shows nothing of the kind: nothing changes; the scan is treated as any other. The asset app is not edited to make it show.

**The system asks less (auto-link).** Before a kind-1 card is made: if the supplier agrees, the amount is within Rs 1, and **exactly one** unscanned bill of that supplier carries that amount, pair them with no card (audit `auto_link`). Two candidates: a card.

Each Verified bill teaches the supplier's printed spelling, as today.

**Before anything else of this part is placed**, run the rules on September on a copy and REPORT: how many of the 12 unlinked scans now pair by themselves, each by stamp and bill; how many of the 63 are Verified; how many questions are left for reception; every row whose state changes. **If a rule pairs a wrong scan and bill on the copy, stop and report.**

## 5 · PART C — orders are worked out from the count, not from Marg's stock (`order_rules.py`)

- `order.stock_basis` = `count` (the default) or `marg`.
- On `count`, a medicine's shelf is: **its counted quantity at its newest count** (count 1 of 06-Sep; a later spot or full count of that item replaces it) **+ purchases since − sales since + returns**, from the same sources and the same boundary the orthotic shelf uses (`porders.ortho_items`), plus what is marked arrived on an order and is not yet in Marg (today's in-transit rule).
- An item with no count row keeps Marg's figure. A result below zero is taken as zero and named. If a later spot count is not stored as a quantity for the item, say so and use the full count.
- The staff see only the quantity to order. Both figures, where they differ, go into `owner_state`'s data and onto the old page. If drawing them on the owner's approvals page would need an edit to `finance_approvals.html`, do not edit it: the old page is enough; say so.
- When the count's vouchers are filed in Marg the two figures agree by themselves. Nothing has to be switched.
- REPORT: for every line of today's plan, both figures and what changes in the proposal (lines added, dropped, quantity changed); the five items with no count row; and, since purchases reach Marg two to three days late, how many planned lines have a delivery in that gap that no arrival tap covers.

## 6 · PART D — Amir: nothing new is asked of him (`amir_day.py`, `purchase_app.py`)

**The stage of his soft start is one setting,** `purchase.entry_mode`: `paper` (the default: he enters from the paper bill and the physical register, as today) → `both` (he may also use the scanned file) → `digital` (scans go into Marg's digital entry without waiting for his visit; Marg takes a photo and a PDF, both). The owner moves it when he chooses.

- **On `paper`:** his step 2 card is headed **"Scan ho chuke bill (N)"** and reads: "Reception ne jo bill scan kiye hain aur Marg mein abhi nahi hain, woh yahan dikhenge. Aap apne register se jaise daalte hain, waise hi daaliye. Chahein to bill ki file yahan se le sakte hain." The downloads stay. The line "N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye" is not shown. His step 7 never lists these as work. No reminder and no Needs-you line comes from them. The duty-map row has no due state.
- **On `both`:** S452's words and its grey line return. Nothing else changes yet.
- **`digital` is not built.** The setting refuses the value with one line saying so.
- His list never holds an unread paper (§3.6).
- **Nothing in this kit adds a new kind of line to *Marg sudhar*, to his board or to his step 7.** What reaches him today for a counted month (the amount path of S440, the double entry of S440) reaches him as today. For a practice month, nothing new reaches him at all.
- The physical purchase register stays the lock against double entry while both flows run: nothing here replaces it.

## 7 · PART E — the owner (`purchase_app.py`, `sanjeevni_approvals.py`, `reports_tile.py`)

### 7.1 The month's register — the Scan links page

`/finance/purchase/page/scans?month=YYYY-MM`, default the newest month. No second page.

- **One row per Marg purchase bill of the month**, in exactly one state:
  - **Verified** (§4).
  - **Has its scan** — with its note (§4).
  - **Amount differs** — both amounts, and "waiting for reception" or "the paper reads <amount>".
  - **No scan** — with the note "scan <stamp> is probably this bill" where a question is waiting at reception; "paper not found" where reception said so; the days waited, in a counted month only.
  - **Entered twice in Marg** — as S440 marks it today; nothing new. The two entries are one row; this state wins over every other, whether or not one of them has a scan.
  - **Accepted without paper** — the owner's own tap on a "paper not found" row, audited, undoable; only in a month from `purchase.register_from` on.
- **Under them, the scans with no Marg bill**, each in one state: probably a bill already in Marg · supplier not known · to be named by reception · unread pharmacy paper · waiting for Marg's entry · second scan.
- **The head line:** the count of each state, **Verified and Has its scan shown separately**, and "N of M settled" (Verified, Has its scan, Accepted without paper). It reads "M of M ✓" with its date when every bill is settled and no scan of the month is open. A practice month shows the same counts.
- **At the foot, one block:** the Sarvam counter's header figures for the month's linked bills (§7.4) and its item figure, with the line "Items are not judged from the scan", linking to the Sarvam page.
- **A month before `purchase.register_from` is headed "Practice month: nothing here raises an alert."** It has no accept-without-paper tap, no day counts, and raises no Needs-you line.
- The same one line on the owner's approvals page, Month section, through `sanjeevni_approvals`'s existing lines.
- Phone width: no sideways scroll; the sticky BACK bar and the up-arrow stay.

### 7.2 Is the new flow ready? — one line a week

On the register's head and in the Month section: **"Last 7 days: N bills entered in Marg · n had their scan before the entry · m paired with no tap."** This is what tells the owner when to move `purchase.entry_mode`. English, no alert.

### 7.3 What reaches a person — only for months from `purchase.register_from`

- **Shavez's morning page** (`reports_tile`): one line while a line of "Bill scan karna hai" waits that belongs to a counted month (a Marg bill of that month with no scan, or an order that arrived in it with no bill scan): "Bill scan baaki: N · sabse purana X din", with "Kholiye", opening the reception screen. September's lines stay in the staff's lists for practice and are not counted here.
- **The owner's Needs-you:**
  - the oldest counted line of "Bill scan karna hai" is older than `purchase.scan_wait_days` (3): the count and the age;
  - a paper reception could not find: his tap accepts it;
  - a scan in the state "waiting for Marg's entry" (a read pharmacy bill with no Marg bill and no likely one) for more than `purchase.entry_wait_days` (7): for his eyes only, never Amir's. An unread pharmacy paper and a scan with a question open are not counted;
  - a supplier on today's order list with no phone number.
- **`DUTY_MAP`:** rows for "order from today's suppliers", "say what arrived", "scan the bill", "answer the question about a scan", each with this screen as its door and due only for work of a counted month (ordering and arrival are always counted); Amir's scan list with no due state. The staff-eye walk asserts them.

### 7.4 The Sarvam counter, and the items

- **F-690:** the Sarvam page counts by §4's rules. Punctuation and prefixes are not misses. A date, a bill number or a supplier read differently on a paired scan is a miss here, and only here.
- **Item lines are not judged from the scan.** MEASURE and REPORT only, for August and September: for how many Marg bills do the lines' own value (quantity × rate, less discount, plus tax, from `purchase_line`) come to the bill's amount within the noise setting, and what the usual differences are. No screen is built from it in this kit.
- **Learning the suppliers' item names is deferred** to the kit that follows that measurement: it changes only the Sarvam item figure, and it should rest on the measured facts.
- Batch and expiry are not verified from a scan. They belong to the shelf (the arrival, the spot counts, near-expiry).

## 8 · PART F — Vendor payments: the owner and Shavez only (D663) (`purchase_app.py`, `supplier_msg.py`)

S452 closed the bank advice Excel to everyone but the senders. The Vendor payments page still opens for every medical login, and draws S265's annexure with every supplier's full account number and IFSC.

- **The Vendor payments page** (`/finance/purchase/page/pay` and its month pages), **the covering letter, the annexure, the bank advice and the payment pack** (S265, S380), on screen and in print, open only for the logins in `supplier_msg.senders` (today: manoj, shavez). Every other login gets the page's own refusal, and the "Vendor payments" link is not drawn for them.
- **No page a login opens under `/finance/purchase/` or `/finance/amir/` serves an account number or an IFSC to a login outside that list.** REPORT each address you closed.
- **Not touched: the reception phone's keyed message queue** (S407, `/finance/api/supplier-msg/next`). It is not a login; the suppliers' payment notices carry the account number and IFSC by the owner's own ruling.
- **Amir keeps what the owner ruled for him in S452, on his own pages:** the one NEFT line, and his month pack on step 2 ("Paid NEFT sheet (PDF)" and the two bank statements), once the month is confirmed. That is not the payment pack above and is not closed. His Paid NEFT sheet carries supplier and amount only; if it carries account numbers today, take them out of his copy.
- REPORT every link to the Vendor payments page from a staff screen, and that it is gone for those logins.

## 9 · PART G — one duty reads a wrong figure (`DUTY_MAP.json`)

`manoj.returns_ok` reads 7 in the staff-eye walks of S446 and S452 while the owner's own line reads 3. Its `due_sql` does not apply `returns.act_from` (02-Sep). Make it read the rule the owner's line reads. REPORT both figures before and after.

## 10 · The settings, all editable by the owner where he edits Sanjeevni's settings today

| key | default | what it does |
|---|---|---|
| `porders.simple` | 1 | the one-task screens; 0 returns the old page |
| `order.channel` | call | call, or whatsapp_tap; whatsapp_auto is refused |
| `order.stock_basis` | count | count, or marg |
| `purchase.entry_mode` | paper | paper, or both; digital is refused |
| `purchase.register_from` | 2026-10-01 | the first counted month; earlier months are practice |
| `purchase.total_noise_rs` | 10 | a total difference up to this is not a question |
| `purchase.scan_wait_days` | 3 | the owner hears of a bill waiting to be scanned after this |
| `purchase.entry_wait_days` | 7 | the owner sees a scan not yet entered in Marg after this |
| `purchase.arrival_scan_days` | 7 | how long an arrived order asks for its bill's scan |
| `purchase.unread_pair_days` | 7 | how near in date a Marg bill must be for reception to be asked whether an unread pharmacy paper is that bill |

Say in the report where each is edited. A key with no editing place today goes on the card where the order rules are edited, if that needs no parent file; otherwise on the old page.

## 11 · Pins — S452's TO, each equal to the 03-Oct 03:12 nightly bundle; read each live before its first edit

| file | pin |
|---|---|
| `purchase_app.py` | `341c663e` |
| `amir_day.py` | `85f208d0` |
| `supplier_msg.py` | `5cc35d2a` |
| `porders.py` | `3620b374` |
| `porders.html` | `7a6799ae` |
| `order_rules.py` | `00a60efb` |
| `reports_tile.py` | `8a987041` |
| `sanjeevni_approvals.py` | `792f4a9a` |

Not touched: `finance_app.py`, `portal.py`, `tile_grants.json`, `finance_approvals.html`, `asset_register.py`, `packs.py`, `stock_app.py`, `stock_amir.html`, `darpan_kal.py`, the medical PC, and the crontab except `order_rules`'s own lines if the carry needs one (declare it).

## 12 · Walk (scratch copies of `finance.db`, `assets.db` and the spine; rows keyed W454*; dates from today)

- **The home.** As the reception login with crafted work of each kind: the scan button and the four rows with their counts, no other text on a row. With one kind empty: that row is absent. With nothing: the button and "Sab kaam ho gaya". No stock, cover or rule figure in the served page. As the owner: the same screens in English.
- **Order.**
  - A crafted open proposal: its card; with six open, four cards and "Baaki 2 supplier dikhaiye". The supplier screen lists the lines in the order's unit; the Call link is a `tel:` link, the number shows under it, and its tap writes one audit row; "Order ho gaya" makes one order with its lines, marks the proposal ordered by the named person, and the card is gone. A second tap within ten minutes makes no second order.
  - Call tapped, the screen left: the proposal is open and the card reads "call kiya tha, order baaki".
  - A quantity changed by the text button goes into the order.
  - An unmade proposal: after `nightly()` it is on the next working day, once, with lines planned on that day's stock; a blocked day and a holiday are skipped; an interim proposal is not made beside it; when stock has arrived it closes itself.
  - A supplier with no phone: no Call button, the tap still works, the owner's Needs-you names it.
  - Frozen, paused, held and unapproved: nothing to order is shown; the routes refuse as today.
  - `order.channel=whatsapp_tap`: today's send button, no "Order ho gaya", and S410's walk passes on it. `whatsapp_auto` is refused with its line.
  - An orthotic shortage: its card in the same list, ended the same way.
  - The 12:00 notice counts the suppliers still to be ordered. Darpan's card line reads what it read before.
  - No phone number appears in the walk's output.
- **Arrival.** Two orders waiting: the list, then one order. All received in one tap. One line short with a quantity, one "Nahi mila": saved by today's rules, the short carries as today. "Abhi nahi aaya" saves nothing. After it: both buttons. "Baad mein" puts the order under "Bill scan karna hai". It leaves on a crafted scan of that supplier made after the order, the evening before the arrival tap included; on a crafted Marg bill, whose own line takes its place, the list's count unchanged; and on the eighth day. Two arrived orders of one supplier: the older is served first.
- **The scan list.** Grouped by supplier, five lines, "Agle 5". "Paper nahi mila" is offered on Marg-bill lines only, takes the line off the staff's list and puts it on the register.
- **The questions.** One card at a time with "Sawaal i / N". Kind 1 on a crafted case and on September's own, the second-scan wording included. Kind 2: the two amounts are not labelled; in a counted month the answer does exactly what S440's walk expects; in a practice month it is on the register only, and **no row is added to any list of Amir's** (count his *Marg sudhar*, his board and his step 7 before and after); the rows that were on his lists before the kit are still there. Kind 3 with three likely suppliers. S441's two questions as cards. A paired scan whose date or bill number differs makes **no card**. "Baad mein" moves the card to the end. After the last: finished.
- **Is it a pharmacy bill?** A crafted pharmacy scan with no number and no amount is a card, is not in *Marg ka intezaar*, not on Amir's list, not in his count; S440's "manager isse theek karega" line is in no served page. "Haan" with the supplier unknown: the supplier card comes next. "Haan" with nothing read: it shows on the register as an unread pharmacy paper and **pairs with nothing by itself**; with one crafted Marg bill of that supplier inside the window a kind-1 card is asked, and its "Haan" makes the row "Has its scan" with its note; with two such bills, or one outside the window, no card. "Haan" on an "Estimate" with a number and an amount read: matched by §4. "Nahi": it is in the clinic lane on the scratch `assets.db`. A scan headed "Estimate" with an amount read is caught too. Of two Yuvika papers, one printed and paired, one unread, only the unread one is asked about.
- **The rules.** "PVT. LTD.", "(EXTN)", "&" against "AND" and a trailing BAREILLY agree with Marg's spelling; a "P" inside a name is kept; the shop's own name is "not read". A printed number with its series and year agrees with Marg's short number; a licence-shaped reading agrees with nothing; a financial-year run alone pairs nothing. A wrong year agrees. A wrong month with the supplier, the number and the total agreeing is Verified with its note; a misread bill number with the rest agreeing is "Has its scan" with its note. No bill is in two states. Rs 6 off agrees; Rs 243 off is "Amount differs" with one card. The auto-link pairs one candidate, writes its `auto_link` audit row, and asks on two. Every link that existed before the run still exists after it. A bill entered twice is one row in that state, with or without a scan. A scan made from a line of the screen (if the record shows it) is not asked its supplier or the §3.6 card, and a wrong paper scanned from a line does not settle that line's bill. Two bills of one supplier with the same amount and neighbouring numbers stay apart.
- **Stock basis.** A crafted item: counted 100, 30 sold, 20 bought and 2 returned by a customer since: shelf 92 whatever Marg says; with 10 marked arrived and not in Marg: 102; with no count row: Marg's figure; with a later spot count: that count is the base; below zero: zero and named. Both figures in `owner_state` and on the old page, neither on a staff screen. On `marg` the plan equals today's plan line for line.
- **Amir.** On `paper`: the new heading and words, the downloads, no grey line; step 7 lists nothing of it; no Needs-you from it. On `both`: S452's walk passes on his step 2. `digital` is refused with its line. An unread paper never reaches him in either. His paid NEFT sheet holds no account number.
- **The register.** The head line's figures add up to the Marg bill count, Verified and Has its scan counted apart; the foot block's figures equal the Sarvam page's; every bill in one state; the same bill in the same state on every page; the same line in the approvals Month section. A practice month: the heading, no accept tap, no day counts, no Needs-you. A counted month: accept without paper settles the row and is undoable. The weekly line on crafted rows.
- **What reaches a person.** A crafted counted-month line four days old: Shavez's line and the owner's Needs-you show, and leave when the scan arrives. The same in a practice month: neither shows, and the line is still in the staff's list. A crafted read scan waiting for Marg's entry for eight days: the owner's line, nothing on Amir's pages; an unread pharmacy paper of the same age raises no line.
- **The settings.** Each of the ten is changed on the owner's screen and takes effect: the old page, the channel, the stock basis, the entry mode, the register's first month, the noise, the three waiting times, and the unread paper's pairing window.
- **The Sarvam page.** September's header figures equal §2's "in substance", or the difference is explained row by row.
- **Vendor payments.** As amir, darpan, bhati and the reception login: the page, the letter, the annexure, the sheet and the pack refuse; no "Vendor payments" link on their screens; no page they can open under `/finance/purchase/` or `/finance/amir/` holds a seeded account string. As shavez and the owner: unchanged. The phone's keyed queue answers as before.
- **The duty.** `manoj.returns_ok` equals the owner's returns line on the box's own data.
- **The old page.** `?old=1` and `porders.simple=0` serve today's page, and S440's and S410's walks pass on it. "Purana page" is on the home for the owner and Shavez, and for nobody else.
- **The pictures of §3.8** are in the kit, one saved page each.
- **Staff-eye walk** (CLAUDE.md, "Every duty has a door") for the reception login, darpan, shavez, amir and the owner, at phone width.
- **Earlier walks re-run:** S403, S410, S414, S417, S439, S440, S441's scan checks, S444, S446, S452 — each adjustment named.
- **Negative control** on the box as it is.

## 13 · Done means

Kit `deploy_kits\S454_BILL_REGISTER\` · installed · published · `claude_code_briefs\REPORT_S454.md`, owner lines first:

- What the reception staff now see, screen by screen, in their own words, and the pictures of the screens the mock did not show.
- How an order is made by phone, and what happens when the call does not go through.
- What the order quantities are worked out from now, and how the first day's proposals changed.
- September as the register reads it, and how many bills paired themselves under the new rules.
- That Amir's work is unchanged, and what his card says.
- That Vendor payments opens for you and Shavez only, and that Amir keeps only his own Paid NEFT sheet, with no account number on it.
- The built screens 8, 9, 10, 11 and 13 as pictures, since they were corrected after your last look at the canvas.
- The settings you can change, and where.
- **What is not built, and why.** At least: WhatsApp sent by the reception mobile by itself; scans going into Marg's digital entry without Amir; the items check as a screen; learning the suppliers' item names; the medical PC's refusal note.

Ending with:

```
https://followup.dr-manoj.in/finance/porders
```

```
https://followup.dr-manoj.in/finance/purchase/page/scans
```
