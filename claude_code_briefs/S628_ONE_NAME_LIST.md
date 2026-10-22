# S628_ONE_NAME_LIST — brief v2 (S339, the Sanjeevni chat, 22-Oct-2026) — v1 + the independent read's corrections (§5)

**Ruling:** D761 (the combined build, approved at S338: "if all can be clubbed together, then we should do it that way"; "go"); D760 (a substitute
is only shown, never closes a line). Owner's "Start" 17:44 IST 22-Oct. Built IN THE CHAT (no API runner). Kit number S628 (board/_numbers v607).

**Why:** the owner's order list (`/finance/porders/s454/track`) said four medicines "did not come" that came, and put each back on the dealer's
next order by itself (S338 §15U: F-989 … F-996).

## 0 · Facts this brief rests on (read 22-Oct, offline, on rebuilt live code and copies of the data)

- Live code = the 22-Oct 01:35 bundle + the make_*.py of S613 → S618 → S619 → S626 → S625 → S627; every TO pin reproduced.
- Spine rebuilt offline from manojz's MargArchive (305 readings, the gate green, the 22-Oct 09:17 purchase export in it).
- finance.db = the 22-Oct 01:35 nightly; assets.db = the 22-Oct nightly (pharmacy scans: Sep 80 / 75 read by Claude; Oct 77 / 74).
- THIO Q AP (order 22, line 55): Marg holds TWO items — `THIO Q AP` (k20 THIO Q AP, 1*10, Deepam every month) and `THIO Q AP TAB`
  (new 15-10, 1*10, the same amount 2,743.20 for 10+2). Deepam's A000678 carries only the TAB one → `carried()` finds nothing (another key).
- LINVIZ 600 (order 38, line 89; 10 strips of 10): Marg holds `LINVIZ 600` (1*10) and `LINVIZ 600 6T` (1*6, new 18-10). Kedar's bill 216 has
  6 strips of **6** (36 tablets). Per tablet the rates agree (₹299.0 vs ₹303.3 for ten). **36 of 100 tablets came — 64 short, i.e. 7 strips of
  10 to carry, not 4** (S338's "4" counted strips of different sizes as equal; corrected here).
- ZUPRINOR 5 (order 24, line 62): JP23217 has two lines (seq 39: 2, seq 40: 4). Today's `carried()` sums them (6) — the stored 2 was written on
  15-10 09:30 by the code before S598 and `detect_supplies` never looks at a billed line again (`billed_qty IS NULL` only).
- POWERGESIC 100 PATCH (Deepam order 33, line 77): came on JANTA's 23672 (16-10, 5 pcs) → `carried()` rule (e); `detect_supplies` keeps (c)/(d) only.
- B-0157 (Kedar, total only, no number, 0 items) kept; B-0159 (the whole bill A000211, 3 items read) rejected as its duplicate (triple
  vendor+total, the oldest kept); B-0160 dup of B-0159. None of the three is linked to Marg's A000211 (the matcher skips rejected scans; B-0157 has
  no number). B-0150 and B-0154: Claude reads both as A000678 / ₹12,922 with the same two items; B-0150's header holds Sarvam's misread
  (A0006678, 2026-04-12, ₹615.32), so the duplicate guard never saw them as one.
- B-0161 (paper: Kedar A000213) saved under Shivaaz and tied to Shivaaz's order 28; B-0167 (paper: Mannat) saved under Yogendra.
  `order_sheet._resolver` already honours `s454_scan_answer(kind='vendor')` before the scan's own vendor.
- Wording: `of_came` prints (n, came) → "2 of 1 came"; the scans page prints `scan_quality.sent_by()` (Hindi) on the owner's English page.
- `s454_item_name` (69 rows) holds Sarvam-era pairings (e.g. "CHMSET DIT TAG" → ONKET DT): not fit to be trusted as a name list.

## 1 · What is built — seven parts, one kit

### 1.1 The one name list — NEW `/root/finance/med_names.py`, table `med_name`
`med_name(id, kind 'marg'|'scan', supplier_norm ('' for marg), form, form_norm, item, item_norm, state 'sure'|'ask'|'yes'|'no', why JSON,
learnt_at, answered_by, answered_at, UNIQUE(kind, supplier_norm, form_norm, item_norm))`.
- **kind 'marg' — two Marg items that are one medicine** (THIO Q AP ≡ THIO Q AP TAB). Learnt from an order: an order line (since
  `order.track_since`) for which `carried()` finds no line, and its own dealer's bill dated from the order day − arrival.back_days to the order
  day + `names.window_days` (default 7) carries a line of ANOTHER key whose name, against the order name, differs ONLY by pack/form tokens
  (TAB, TABS, TABLET(S), CAP(S), CAPSULE(S), STRIP(S), `\d+T`, `\d+S`, `\d+\*\d+`, `1X\d+`), every other token equal and in order — so the
  strength numbers are equal by construction; and that bill line answers no other order line. **Sure** when, in addition, the two items' prices
  agree within 5 % per tablet (the order line's rate_p per its pack size against the bill line's amount per its packing; or the older item's last
  purchase in the spine). One candidate only. Anything weaker (one differing letter, a price that disagrees, two candidates) → **ask** — one line
  on the owner's track page: *"THIO Q AP TAB on Deepam's bill A000678 = THIO Q AP? Yes / No"*, asked once (a 'no' is never asked again).
- **kind 'scan' — a dealer's printed spelling of a Marg item.** Learnt from every pharmacy scan linked to a Marg bill (`purchase_scan_link`) that
  has a Claude reading (Sept and Oct now; every new one after): Claude's item lines against the spine's lines of that bill; a pair is **sure**
  when quantity agrees (qty, or qty+free), the rate agrees within 3 % (when both sides carry one), the names pass the loose test (§1.4) and the
  pairing is one-to-one. Only sure pairs are kept; a scan spelling is never asked (it moves no count — a decision, in the README).
- **Never:** a form across strengths or sizes outside the pack-token rule (the S598 sibling rule stands); a substitute (D760: FLACORT ≠ FLEMCORT —
  'FLEMCORT' differs by a letter → at most an 'ask', and a 'yes' is never taken from a substitute: the question says "the same medicine?").
- **Readers:** `forms(con, item, sn=None)` — the item, its 'marg' partners (sure/yes) and, for a dealer, its 'scan' spellings (sure);
  `same_items(con, item)` — the 'marg' partners only. `learn(con, sp, now)` — the one keyed, idempotent pass (writes `med_name` only), called at the
  head of `porders.detect_supplies` (fail-soft) and once by the installer (the September seed). `questions(con)`, `answer(con, id, yes, who)`.

### 1.2 The arrivals rule reads it — `stock_figure.py`
- `printed_forms()` adds `med_names.same_items()` (fail-soft) → `_line_forms`, `key_of`, `shelf_figure` and `order_track.forms_of` all see it.
- `_carried()`: the lines of the item's own key PLUS the lines of each partner's key (each with its own sib), in one date/bill/seq order;
  rule (b) reads the taken lines of every key in the group. The hit carries the bill line's `packing`.
- `_purchase_lines_of` selects `packing` too. Nothing else in stock_figure changes; the stock figure itself is per Marg item as today.

### 1.3 Marg's matching — `porders.detect_supplies`
- Calls `med_names.learn()` first (fail-soft).
- **Packs by tablets when the packings differ (LINVIZ):** came = floor((qty+free) × N_bill / order pack_size) when both packings read 1*N and
  differ; else qty+free as today. The line keeps `billed_units` (tablets / pieces came) beside it.
- **Two lines summed, again (F-990):** a billed line whose `billed_qty` is below its packs is looked at again by rule (a) on each pass; when the
  bill's matching lines now give more, `billed_qty` (and `supplied` if Marg wrote it) is raised and audited (`line_redetected`). Never lowered.
- **Another dealer's bill (F-991):** rule (e) within `names.window_days` of the order day and not taken by an order line of that dealer → the line
  gets `other_supplier, other_bill_no, other_date, other_qty` (new columns); it is NOT marked billed (D743 stands: stock only).

### 1.4 The order list's lines — `order_track.py`
- A line with `other_*` and no own bill: state **came** (how 'other'), note *"came from Janta (bill 23672)"*; never short, never carried.
- `carry_pass`: an open carry whose line's short changed is set to the new short (LINVIZ 10 → 7), audited; dropped as 'came' as today.
- `name_score` loosened (F-996): pack/form tokens dropped before comparing ("TAB ORICOX-P 10*10" = ORICOX P); a token subset of ≥ 2 letters-words
  where the shorter side's tokens all appear ("NASO B12 NASAL SPRY" = NASO B12); one letter apart stays the 0.8 rule. Numbers that remain must agree.
- `forms_of` reads `med_names.forms(con, item, sn)`; `s454_item_name` is no longer read here.
- `Ctx.head()` — the CLEARER scan of a duplicate family (most items read, then the earliest) for the thumb and the notes; `same_paper()` — two
  usable scans of one dealer whose Claude readings agree on bill number and total → one note naming both.
- `wrong_dealer()` skips a scan whose dealer was corrected (§1.6).

### 1.5 Send back on every pharmacy scan (F-993) — `porders_s454.py`
- On the track page every scan an order card names carries the three chips (blurred / cut off / not a bill), unless already asked (then "sent back
  ✓ — Withdraw"). The 'asks' section of the track page gets *Withdraw* too.
- The scans page (`/finance/porders/s454/scans`) gains a folded section *"Every pharmacy scan, last 14 days"* — each with the chips.
- `api_rescan` already accepts any pharmacy scan not set aside; unchanged.

### 1.6 Wrong dealer (F-993 rest) — `porders_s454.py`
- Each *Saved under another dealer* card gets ONE button *"Change dealer to KEDAR PHARMACEUTICAL"* (the owner and Shavez only). POST
  `/finance/porders/api/s454/dealer_fix {scan}`: re-derives the paper's dealer server-side (never from the browser); writes
  `s454_scan_answer(kind='vendor', answer='chosen', value=<the paper's supplier key>)`; deletes the scan's `order_scan_tie` to an order of the
  other dealer and ties it to the paper dealer's newest order made before the scan moment within 7 days that has no tie (else none); audited.
  The scan app's own record keeps its vendor text (the scan app's Edit can change it — said on the card after the tap).

### 1.7 The owner's words (F-995) — `porders_s454.py`
- "came X of Y" the right way round (English); Roman Hindi pages keep "Y mein se X aayi".
- The owner's pages are English only: the scans page's *sent by* line in English ("sent back by you" / "by Shavez").
- An arrived order whose lines all did not come: *"arrived — nothing on it came"*.
- The owner's name questions (§1.1) on the track page, top, one line each, Yes / No.

### 1.8 WITHDRAWN at v2 (R1-2) — the scan app's duplicate guard is NOT touched by this kit
B-0159 was set aside by the owner's own S441 answer (`/root/shared/scan_checks_s441.py answer()`, which keeps the older scan), not by
`asset_register._dup_after_ocr`; its total (₹5,360) is not Marg's A000211 (₹5,470), so a swap would not link it either. The rule "keep the
clearer scan" goes to the Scan App chat (both files are theirs). This kit reads the clearer scan of every duplicate family on the order list
(order_track `Ctx.head`). The v1 text follows for the record only:
- `_dup_after_ocr`: when the triple finds an earlier scan that has NO item lines while the new one has some, and the earlier one is not approved,
  the EARLIER one is set aside as the duplicate of the new one (the new keeps its own number) — one anchored edit, audited `duplicate_swapped`.
- `heal_s628.py` (run once by the installer, assets.db backed up first): the same swap for the families of the last 30 days (B-0157 → set aside as
  B-0159's duplicate; B-0160 stays B-0159's); order 25's tie moves to B-0159. The matcher then links B-0159 to Marg's A000211 on its next pass.
- Placed only when `asset_register.py` is still at 2bb28600 (S627's TO); otherwise this part alone is skipped and named in the report.

## 2 · What is NOT touched
Staff screens (Darpan, reception, Amir) — unchanged in look; their counts follow the corrected lines. `scan_quality.py`, `claude_reader.py`,
`item_check.py`, `s454_item_name` (left as it is), `finance_app.py`, the crontab, DUTY_MAP (no duty added or moved).

## 3 · Pins (FROM → TO at build)
/root/finance/stock_figure.py 8c66b6b1 · order_track.py a8c46700 · porders.py b1736494 · porders_s454.py 53ef850f · NEW med_names.py ·
/root/assetapp/asset_register.py 2bb28600. READ: order_sheet.py 1bba95ab, stock_watch.py f0d9092a, purchase_app.py 447b745f, shelf_figure.py
23b2394a, /root/shared/scan_quality.py 16fb2402.

## 4 · The walk (on copies; its own rows by key 'W628 …'; negative control on the OLD files)
1. The four cases on the copy: THIO Q AP came 12 (10+2) from A000678; ZUPRINOR 5 came 6; POWERGESIC 100 PATCH came from Janta 23672, not
   short, not carried; LINVIZ 600 short 7 (36 tablets of 100), its carry 7. C2CALZ and XGESIC LA still short.
2. The September seed: the count of sure 'scan' pairs; none across strengths (a planted 'W628 FOO 500' vs 'W628 FOO 650' never pairs);
   a planted substitute never sure; a planted 'one letter' → ask, Yes → the line came; No → never asked again.
3. Duplicates: on the copy the heal sets B-0157 aside, keeps B-0159; a planted pair (empty first, full second) swaps; a planted pair (both
   with items) does not.
4. Send back: chips on B-0181 and B-0188; the asks carry Withdraw; refused for Darpan (403).
5. Wrong dealer: B-0161 → Kedar; Shivaaz order 28's tie gone; refused for reception and Darpan; a scan of the right dealer → 409.
6. Words: "came 1 of 2"; no Hindi on the owner's track and scans pages; a planted all-missing order says "arrived — nothing on it came".
7. Every page the kit touches renders 200 for the owner and Shavez, and the staff pages (reception's order list, Darpan's tab) unchanged in text
   except counts.


## 5 · The independent read (R1, a fresh sub-agent, 22-Oct) — and what v2 does
1. BLOCKER `printed_forms` feeds closings, counts, splits and the shelf → partners added in a NEW `arrival_forms()` read only by `_line_forms`;
   the stock figure of all 1,045 spine items walked byte-identical.
2. BLOCKER §1.8 → withdrawn (above).
3. BLOCKER THIO's price → the ordered item's LAST THREE purchases (₹2,743.20 on bills 83, 427, 505 = A000678); sure.
4. BLOCKER the pack-word rule merged sizes → `N*M` is never a pack word between Marg items; only TAB/CAP/STRIP words and `\d+T`; sure also needs
   both packings strips (1*N, N>1) or equal; variant words (FORTE, PLUS, DSR, SR …) never fold in the scan test.
5. BLOCKER re-detect → the tablets conversion on both paths; own dealer only (rule a reads a number across dealers); never lowered; supplied and
   short follow only where Marg wrote them.
6. other-dealer credit → own dealer first (`own_only`); lines credited to another dealer join rule (b); the 'other' state before the short rule.
7. the dealer door → also `purchase_scan_state.chosen_vendor` through `porders._s440_put` and `_rematch` (no alias learnt). Order 28 (Shivaaz,
   TOLTRIS PLUS) has no other arrival — after the fix it reads not arrived, which is the truth (Marg has no TOLTRIS PLUS from anyone).
8. heal → withdrawn with §1.8.
9. `learn()` throttled (10 min) — `detect_supplies` runs on page views.
10. carries: the partners count in `_ordered_since` / `_marg_items`.
11. `part_sub` English fixed; 'its first scan is' → 'a copy; the clearer scan is'.
