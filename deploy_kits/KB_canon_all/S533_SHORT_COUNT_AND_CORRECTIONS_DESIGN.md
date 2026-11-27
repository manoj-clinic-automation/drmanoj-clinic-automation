# S533 — SHORT IN THE COUNT, AND AMIR'S CORRECTIONS BY THEMSELVES — the design for the next Sanjeevni build (27-Nov-2026)

*Written at the S533 close (the Sanjeevni chat, Opus 5.5, EOS-light, no code changed). His words are from the chat (26-Nov 21:40 → 27-Nov 09:25 IST). Every figure was read live this session by sub-agents (counts and item names only; Stock check rows, `/finance/stockcheck/api/vouchers`, the item ledgers — Marg's closing of 25-11). No patient or party name is in this paper.*

**His "ok" (09:25 IST 27-Nov) is on mock-up v9 — the one page:** `https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF` (also on `https://claude.ai/artifact/TSYKdNSvNNUYFKWHm47B6s`; copy `03_WORKING_PAPERS\S533\S533_STOCKCHECK_MOCK_v9.html`, md5 104ee265). D1090, D1091.

## 1 · His words, in order

- 26-Nov 21:34 (board) / 21:40: NORTIMER TAB needs a Stock Issue, as do other goods; every item Darpan's count finds short of Marg needs a proper flow to settle it promptly — his one tap (Write off as a Stock Issue / Pursue), small shortages within the allowance one tap for the group, the Stock Issue on Amir's card with nothing typed, Amir keys and taps done, his next Stock Issue export closes it (asked on his list when Amir tapped done and no newer export came). Mock-up first.
- 27-Nov 08:08: keep a provision to add stock vouchers by scanning printed ones when needed; scans for all vouchers, or only where the item is not clear from the report's cut name? — a dependable way with minimal staff workload.
- 08:12: how is reception told (a notification?); a voucher Amir claims to have made that the system does not show goes back to him by itself — he makes it, or if already made, its hard copy is scanned by reception or himself; "instead of me raising these every time to Amir, I only see these things and his work automatically gets populated".
- 08:28: later vouchers (e.g. 25-10) may already settle an older ask — the system must analyse that before raising anything, or confusion follows; in future Amir is told to make no voucher unless the system asks.
- 08:36: a voucher made without a system ask needs a better flow than a red mark — an inquiry and reconciliation path, as automated as possible.
- 08:49: all voucher lines inline, collapsed, expandable; the full flow on this one page; the item ledger opening here too, collapsed — every inquiry from the single page.
- 09:25: "ok" on v9; the build in a fresh chat.

## 2 · The page (Stock check, on top; mock v9)

Five boxes: **1 Short in the count — your call** · **Within the allowance** (one group button) · **2 On its way to Marg** · **3 Old corrections, re-judged on the whole item** · **4 Voucher nobody asked for — inquiry** (+ the month's tally) · **Settled in Marg** (folded). Every row is folded and opens IN PLACE to: **Path** (each step so far and the next) · **Voucher lines** (Marg's voucher no., date, kind, qty, batch, verdict; **Voucher ▾** opens all its lines) · **Item ledger** (newest lines; **Full ledger / a date range ▾** inside — the ledger page's content, no navigation; counts shown as rows). Actions on the row: Write off · Pursue · Reverse · Close — each two taps, no confirm dialog (his 18-Nov rule). Owner page English; staff cards Hindi (Roman), "do this" lines only, no figure typed, no judgment (11-Oct rule).

## 3 · The rules

**3.1 Short in the count.** A count lands here when the gap below Marg comes from a FRESH count (an old count carried forward is never a write-off — "count first", his 22-Nov rule). Within the allowance (`loss_piles` settings `stock.allowance_pct` 1.0 % of the item's own sales since its last count, floor `stock.allowance_min_strips` 1 — as `stock_watch.allowance_units` computes today) → the group box. **Write off** → one Stock Issue line (item, quantity, batch named by the system from Marg's batch stock, nearest expiry first) on Amir's card; the day's write-offs ride one card (one Marg voucher); a card Amir has tapped done never grows. **Pursue** → a recount on Darpan's next morning list; the row comes back with both counts.

**3.2 Closing.** The voucher judge (S965) matches every ask to Marg's own report lines. Amir tapped done and no newer report → ONE line on his list: take Marg's Stock Issue + Stock Receive (01-10 → today), once, however many lines wait. A newer report that still lacks it → back on Amir's card by itself: *Ab bana diya* · *Pehle bana chuka hoon* → print the voucher → scanned by reception or by Amir from his card. The scan read shows the item on that voucher → closed; not on it → back to Amir as *bana dijiye*. Still unsettled after Amir's second answer and the next report → one line on his list.

**3.3 Nothing old reaches Amir before the whole item is re-judged.** Marg now against the latest count and every bill, sale, voucher and rename since:
1. Marg = shelf → the old ask closes "settled by later entries", nothing to Amir.
2. Shelf only from an old count → recount first on Darpan's next list; the old ask closes as overtaken.
3. A fresh count still differs → ONE correction for TODAY's gap (not the old figure) — via the desk (3.1) or Amir's card.
4. Only a batch is wrong, the total right (wrong batch, a batch fix keyed twice) → nothing now; Marg's monthly Batch Stock export decides; a fix only if the batches are still off then. A wrong-batch card is first checked against Marg's batch stock.

Today's 13 cards (27-11 live): GLI-ME SR1 · GEN D3 NANO · DOLONEX 2 ML INJ · G DRESS 10 · JAKMAC 5 · PATOPAN DSR · PEMZOLE D → (1) / batch part (4). KNEE SUPPORT L HINGED · KNEE SUPPORT M HINGED (the 06-Sep asks were on the combined item, before Marg's 10-10 size split; Marg 2 = ledger 2 each) · CAST SHOE L TYNOR · CAST SHOE M TYNOR · KNEE IMMOBILIZER L UNISON · CCM → (2). KT ROS DT 7:11 (on Amir's card since 26-11) · TRAMATEE P TAB 15T 2:12 · NORTIMER TAB 6:0 → (3). VINBACTUM DS → held (his "ignore for now", D1077).

**3.4 Voucher scans — only on need.** Of 254 report lines (26-Nov) only AD00010's two cut names fit several items. A printed voucher is asked only (a) when a cut name fits more than one item, (b) for a claim a newer report lacks (3.2). Reception scans it on the pharmacy lane like a bill; Amir may scan it himself from his card (phone camera). Reception is told by a line on its own bill-scan screen and one phone notification when Amir taps *Print diya* — no new tile. The reader recognises a stock voucher (not a bill), files it by its voucher number, reads items / batches / quantities. Any stock voucher may be scanned at any time (the provision); only the unclear ones are asked. This replaces the one-item Stock Register as the FIRST route for a cut name (the register stays the fallback, D1088's route kept second).

**3.5 A voucher nobody asked for — from the rule date (a setting he sets when he tells Amir).** (a) The system looks first, nobody involved: an open ask it fits (keyed early or under another number) · an issue and receive that cancel (same item, batch, quantity, within `cancel window` 7 days) · a batch move between two batches of one item · Marg still equal to the shelf after it → explained, closed, folded, counted. (b) Not explained → a question on Amir's card, one tap: *Galti se bana* · *Ginti mein farak tha* · *Batch theek kiya* · *Kharab / expiry* · *Pata nahi*. (c) Each answer its own check: mistake → the exact reversing voucher on his card, closed by the next report · count difference → a recount on Darpan's next list (agrees with the voucher → explained; does not → the reversal to Amir) · batch → the next Batch Stock export · damaged / expiry → his Write off desk, one tap. (d) His list only when the path ends unsettled: *Pata nahi*, no answer in 2 days, or a check disagrees → red, **Reverse** (the reversal on Amir's card) or **Close** (his OK, optional reason). (e) The tally (his only): unasked vouchers this month — explained / reversed / closed by him / open. Before the rule date: history, judged by the same whole-item test, folded.

**3.6 Settings on the page (no code to change):** the rule date · days before a question or card reaches his list (2) · the cancel window (7 days) · the wrong-batch check against Marg's batch stock (on) · the allowance (the existing `loss_piles` keys).

## 4 · Faults to fix in the build

- **F-1706** — KT ROS DT reads "Amir said done — not in Marg" though re-asked 26-11 (S957 `S957:ktros:7-11`): the new ask claims the 19-11 done mark (done before asked). A done mark older than its ask is never that ask's.
- **F-1707** — the item ledger carries no count lines (Darpan's 23-11 counts absent on NORTIMER TAB, KT ROS DT, PANTAVIN 40, TRAMATEE P TAB 15T): counts are rows on the ledger.
- **F-1708** — PANTAVIN 40's ledger notes on 05-11 and 08-11 name bill 4043 where 4100 is meant; two stored batch numbers lose their prefix ("T-260753", "-260753A" against the scan's "JT-260753", "JT-260753A"). Assess in the build; read the ledger code first.

## 5 · Live figures (27-Nov, Stock check rows; Marg's closing of 25-11)

| item | Marg | shelf | gap | latest count |
|---|---|---|---|---|
| NORTIMER TAB | 6:2 | 0:2 | −6:0 | Darpan 23-11 (0:2) |
| KT ROS DT | 27:10 | 19:14 | −7:11 | Darpan 23-11 (6:11 of 06-09 + 1:0) |
| PANTAVIN 40 | 42:9 | 40:9 | −2:0 | Darpan 23-11 |
| CROCAL | 18:6 | 16:5 | −2:1 | Darpan 23-11 |
| ZUPRINOR 5 | 10 pcs | 8 pcs | −2 | Darpan 26-11 (and 23-11) |
| TRAMATEE P TAB 15T | 25:1 | 22:4 | −2:12 | Darpan 23-11 |
| PRETOL-4 | 17:5 | 16:7 | −0:8 (allowance) | Darpan 18-11 |
| TYRO BR | 28:6 | 28:5 | −0:1 (allowance) | Darpan 23-11 |
| ZIBON EXTRA / GEMCAL XT | agree | | | L000037 (22-11) settled them |

Voucher facts: AD00010 (25-10 RECEIVE: KNEE IMMOBILIZER L UNISON 1, KNEE IMMOBILIZER M TYNOR 1, CAST SHOE M TYNOR 1, ENZOMAC OINTMENT 2, NORTIMER TAB 9:0 batch 24006 — Marg had run to −0:9) · L000031 (25-10 ISSUE: KNEE SUPPORT L HINGED 1, CAST SHOE L TYNOR 1) · AD00012 (11-11, ROSIKA FORTE 1:2 unasked) · AD00016 / L000038 (22-11, TRAMATEE 2:8 each, asked 1:7) · L000037 (22-11, GEMCAL XT 0:4, ZIBON EXTRA 15:3, asked).

## 6 · The build — order and files

Read the live bytes from the newest bundle first (F-472); a file patched often is read whole (drift). Sanjeevni's own: `/root/finance/voucher_judge.py` · `stock_check.py` / `stock_check.html` · `item_ledger.py` · `stock_watch.py` · `record_judges.py` · Amir's card (`amir_day.py` / `stock_amir.html`, the `amir_job` kinds) · Darpan's next list (`stock_watch` / `stockmatch.html`) · `loss_piles.py` (settings reused, not changed). The pharmacy lane reader and the reception bill-scan screen: read the ownership map first — `scanner_widget.js` and `/root/assetapp/` are the Scan App's (a PLANNED line on `board/_numbers` before touching, D646).

- **Kit A — the one page:** the desk (3.1), the re-judge (3.3), the inline folds (path · voucher lines · ledger with counts), F-1706, F-1707, F-1708. Proof: the 13 cards' outcomes as §3.3 lists; the live-shape on the 27-Nov database copy.
- **Kit B — Amir by himself:** the write-off card, the claimed-not-in-report card, the export line on his list, the inquiry (3.5) with its settings and tally.
- **Kit C — voucher scans:** the stock-voucher kind on the pharmacy lane, reception's line + one notification, Amir's own scan, the cut-name route ahead of the register.

## 7 · Open with him

The rule date (he tells Amir; he sets it on the page). NORTIMER TAB: his one Write off tap of 6:0 settles Marg to the shelf (AD00010's 9:0 stays as history).
