# S402 ORDER LIST PLAN — the owner's asks of 07-Nov-2026 (14:32 – 14:45 IST) on the order list, for the next Sanjeevni build

*Written at the S402 close (the Sanjeevni chat, 08-Nov-2026). PLAN ONLY — nothing built. Decision D862; faults F-1176, F-1177. The page read live as manoj at 14:3x IST 07-Nov (read only, a sub-agent); the cause of B-0237 read from the 07-Nov database copy in the device VM. This plan supersedes the working note `03_WORKING_PAPERS\S402\S402_OWNER_ASKS.md`.*

**The page:** `https://followup.dr-manoj.in/finance/porders/s454/track` — drawn by `/root/finance/order_track_page.py` on `order_track.py`; the scan-to-order tie is made in `order_sheet.py` (`_tie`, how = `scan`).
**FROM bytes (the 08-Nov bundle, 03:15 IST):** `order_sheet.py` 53abf461 · `order_track.py` 6f4746c5 · `order_track_page.py` 4e6bd715 · `porders_s454.py` 37c4f3bf. Read whole before patching (F-472).

## 1 · Retire an old incomplete order (D862 item 1)
- The owner can **retire** an order that will never come, from its card on the order list (his login only).
- A retired order leaves *Not arrived* and *Came short*. Its missing lines are **never re-ordered by itself**. It is shown once under *Complete / retired* with who and when; *Undo* for a day.
- First cases: **SHIVAAZ 12-10** (TOLTRIS PLUS — replaced by a new product); **YUVIKA 20-10** (ANKLE BINDER BAMBOO M, RIB BELT — never came; RIB BELT re-ordered 04-11).

## 2 · A dealer's replacement product counts (D862 item 2)
- The owner names a replacement once: **KEDAR FLACORT 6 → FLEMCORT 6**; **SHIVAAZ TOLTRIS PLUS → TOLIVANT PLUS** (his voice "Taliban Plus"; confirm the name with him on the mock).
- A replaced name that comes as its replacement is *came*, not *short*. The re-order of the old name stops.
- **The same rule for another pack size** (F-1177 e): LINVIZ 600 came as 36 and 60 tablets — a medicine that came in another pack size is *came*, never *short*.

## 3 · Scans already with reception stay in his view (D862 item 3)
- The owner (14:45): keep them, so he sees what is pending and gets it done. **No change** to the *Scan problems* section; *Check all scans one by one* keeps them. At most, each card says plainly *with reception, N days*.

## 4 · The Yuvika mis-tie must not recur (D862 item 4; F-1176)
**What happened:** B-0237 — Yuvika bill 774 of 28-10, ₹2,550 — is in Marg and paired to its scan. When it was scanned (28-10 17:15) two Yuvika orders were waiting: order 54 (20-10: ANKLE BINDER BAMBOO M, RIB BELT UNIVERSAL) and order 63 (28-10 17:14: L S BELT L, TENNIS ELBOW). The reading could not pick (the bill says L S BELT **XXL**, the order **L**), so the rule fell back to **the oldest order** and tied B-0237 to order 54. Bill 774 carries none of order 54's items (it carries L S BELT XXL / XL ×2 / M and KNEE IMMOBILIZER XL — order 1's line, billed 0774). The order list therefore shows order 54 as *Bill scanned, not in Marg yet*.
**The fix:**
- (a) When the reading cannot pick between two waiting orders, **never fall back to the oldest** — the scan waits for Marg.
- (b) Once Marg's purchase lines for the bill arrive, **the tie follows the items**: the scan belongs to the order(s) whose medicines are on that Marg bill; a wrong tie is moved by itself (audited); one bill may close lines of several orders.
- (c) An order none of whose items came on any bill stays *Not arrived* (or is retired, §1) — never *not in Marg yet*.
- (d) **A size difference (L / XL / XXL / M) is a different item**, never a match.
- Re-read under the new rule at the build: B-0262 (Yuvika, scanned 06-11, tied to order 63) and B-0174 (§5).

## 5 · The order list's other faults (F-1177)
- a. **VERMA 20-10** — "arrived, nothing on it came" yet *Bill not scanned* asks reception for a scan. Nothing came = no bill: the card goes.
- b. **B-0174** is *Complete* under two Yuvika orders (12-10 and 16-10). One tie is wrong (the §4 rule settles it).
- c. **DAANSHI 12-10** shows the same bill twice (B-0151, B-0151) — show a scan once.
- d. **MANNAT 04-11 and ESSENTIAL 02-11** sit in *Not in Marg yet* with no bill number ("·"); MANNAT 04-11 is also in *Bill not scanned*. A card with no scan never sits in *Not in Marg yet*.
- e. another pack size counted short — §2.
- f. the page's "1 days" → "1 day".

## 6 · For the owner, not the build (told 07-Nov)
- **PREGHYPE NT** (SHIVAAZ 02-11): staff tapped *Nahi mila*, Marg billed 12 strips — the shelf to be checked; if it is not there, Shivaaz owes a credit (this is a return case for S740's *Record a return* if confirmed).
- **RAVI 04-11** (DOLOGESIC SP) late; its WhatsApp shows no *sent* time — a call.
- **Kedar's** C2CALZ / LINVIZ 600 short four orders running — buy elsewhere (FLACORT is §2).
- Done by him 07-Nov: the Yuvika 0774 name question (*No*), B-0239's dealer.

## 7 · How it is built
One kit, on his "go": the mock first (a screen of his changes — the retire and replace buttons). Charter v1.1 and BUILD_NORM_v1; the walk with a control that goes red on the live files; a cold review until SAFE; a re-tie kit is installed only after its DRY on the box is read (F-1153).
