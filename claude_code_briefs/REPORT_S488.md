# REPORT S488_DATES_AND_WAITS — installed 06-Oct-2026 14:18 IST, verified, published

**For the owner**
- **Stock now** and the stock lines show the right day again. They had been stuck on 30-09 all of October; they now read 05-10, the newest closing.
- **Amir's card now says what it is waiting for, since when, and whose turn it is.** He is no longer told to export a closing stock that has already arrived. Your own list says the same in English, and warns you once a proof has waited 48 hours.
- **Your two Marg lists are now your duties.** The weekly salt-wise list, and the monthly category-wise list and item list, show on your list only when one is late. Today all three are on time, so nothing shows.
- **A wrongly learnt item name can now be struck.** Open the Items check page and tap **Wrong**. **Put back** undoes it. Three names look doubtful:
  - Jubilee's "SHELLAC ST TAB GOLD" = SHELCAL XT
  - Ess Kay's "CHMSET DIT TAG" = ONKET DT
  - Kedar's "MIKO C/S" = MEG QCS

  Nothing has been struck; that is your call.
- **Filed stock vouchers are counted again.** 14 of the 66 "Marg and shelf moved apart" flags of 04-Oct were simply Amir's vouchers, and they are cleared.
- **The medical PC's file is packed and has not been sent.** It waits for the chat to read it, and then for your one PowerShell line.

---

## For the chat

Kit `deploy_kits/S488_DATES_AND_WAITS/` · faults F-753, F-754 · no D-number. Publish `a5996f1` (PUBLISH_ALL: verified on origin). Build lock taken 14:17:19 IST and released after this report. The installer ran from `/tmp/s488kit2/` and finished at exit 0, 14:18:21 IST. After the publish, the server's clone matched it byte for byte: `diff -r` showed no difference and SUMS.md5 is 0f0b09ea on both. Run from the repository, the installer answers **ALREADY INSTALLED**.

### Pins — FROM → TO, md5 read back on the box (14:21:37 IST)

| file | FROM (brief = live before) | TO, read back |
|---|---|---|
| /root/finance/stock_app.py | 7e159de737c0ec03cea890053f1bcd58 | cc06dac9e3ab60a85d76e2409815b5af |
| /root/finance/darpan_app.py | 5bfabbecf1e0fbf86ff142e3cd07543e | a55ecbed4bbe1230b24565b4185b8755 |
| /root/finance/owner_sheets.py (**the parent's**: the one statement of A.8) | 8b1aea31fc1d7dd231fbb45f87c2c6d2 | baa7ccc405a78bdbbd8b2485c00dc9a0 |
| /root/finance/stock_watch.py (A.9: one line, line count unchanged) | 6d4d660f20a0e441fb1082597e5fd96c | 4fc0f6017825975e75ebacfdc2f122d2 |
| /root/finance/shelf_figure.py | 23c34ebb1149996e1053c26573077460 | 0d836de54672f3e624fcc763311ab22c |
| /root/finance/amir_day.py | 709f20c1078cbcb36fc1108e452c40c1 | 08d058a765278d6e119e70f8f0adeedd |
| /root/finance/item_check.py | 9000e3768086e0935d88bec8c8b1cd07 | 6f3faf899df5120af6ee51167604d457 |
| /root/finance/purchase_app.py (the Items check block only) | 254b77939ca40d20e46509a678bcb5d8 | c29050c18795a059e3cfbfae252efc21 |
| /root/finance/reports_tile.py | ea15aacbb6a00131d3f02664b0c1df42 | 6f7cf490c949495e3e714b7dd688b7af |
| claude_code_briefs/DUTY_MAP.json (v7 → v8) | 1595520d9c287efc6ecdcd16310041ae | f27423b61e50857875bb8f7ba4e5c57c (the server's clone, read back) |
| claude_code_briefs/DUTY_MAP.md | d50a6f4eedd78a2ba892706398f78249 | cb78fe54f4d09fb4733dc1bac268cf9e (the server's clone, read back) |
| medical PC `D:\SendToClinic\marg_watch.py` — **packed, not placed** | 58b54f37865cb487720b95eaa4aedde5 | 0a78ae15be60d8a0293b96ecfa38f35b (kit file) |
| Drive `ToMedical\_kit\KIT_MANIFEST.txt` — packed, not placed | ea2b437a… (CRLF) | a1bf114fd9e6940befe74592ffa78322 on Drive (CRLF), made by deliver_S488 from the kit's LF copy 59b31641 |

**Read only, the same before and after:**
- aaj_kaam.py d65e0bf4, owner_console.py 4819eceb, order_rules.py ee17c187.
- finance_app.py bff362c3, portal.py 63df9d49, tile_grants.json f9441311.
- The rest of S486's twelve parked files and the crontab: checked by the installer, step 12.

**Part F:** `/root/marg_ingest/marg_ingest.py` is 828c4dad6b159207b034d8129aed3ab7, the pin. That confirms S482 closed both lines the pending paper listed. Nothing was edited.

**Backups** (in /root/finance):
- `finance.db.bak_S488_20261006_141719`: 31,920,128 bytes, made with the backup API before the first data write.
- The nine file backups, each read back at its FROM md5: `amir_day.py.bak_S488_709f20c1`, `darpan_app.py.bak_S488_5bfabbec`, `item_check.py.bak_S488_9000e376`, `owner_sheets.py.bak_S488_8b1aea31`, `purchase_app.py.bak_S488_254b7793`, `reports_tile.py.bak_S488_ea15aacb`, `shelf_figure.py.bak_S488_23c34ebb`, `stock_app.py.bak_S488_7e159de7`, `stock_watch.py.bak_S488_6d4d660f`.

**Services:** `clinic-finance` was restarted once, at 14:18:10.
- `/finance/healthz` answers 200.
- `/finance/stock/page/now`, `/finance/stock/api/now`, `/finance/purchase/page/items` and `/finance/amir` all answer 302. That is the login gate, as expected.
- No Traceback appeared in the journal since the restart.

### The data, as written
- **The four settings** (INSERT OR IGNORE, 4 new of 4):

  | key | value | note |
  |---|---|---|
  | `amir.proof_wait_hours` | 48 | "S488: hours a count's voucher proof may wait before the owner's warn line" |
  | `amir.refused_keep_hours` | 36 | "S488: hours a refused report stays on the owner's Needs-you list (kept past midnight)" |
  | `owner.salt_list_days` | 8 | "S488: days after which the owner's salt-wise list from Marg is overdue" |
  | `owner.item_lists_days` | 35 | "S488: days after which his category-wise list or item list from Marg is overdue" |

  The owner's settings card (`porders_s454.py`, parked) lists only the keys it knows. The four rows join it when that file is next opened.
- **`s454_item_name_struck`** was made by `item_check.ensure` on the live database before the restart. It holds 37 learnt names, 0 struck.
- **The re-judge of `s454_shelf_gap`** ran once, after the backup. 27 rows were written. The first filed voucher's day is 2026-10-04.

  | closing | items with a filed voucher in the window | flagged before → after | pass 1 | pass 2 |
  |---|---|---|---|---|
  | 2026-10-04 | 28, in (02-10, 04-10] | 66 → **52** | 14 cleared | — |
  | 2026-10-05 (a closing newer than the brief's bundle) | 0, in (04-10, 05-10] | 90 → **77** | — | 13 carries of the 14 cleared |

  This matches the brief's expectation for 04-10 exactly: 28 items, 14 cleared, 52 stay.
  - Cleared at 04-10: ANKLE BINDER L TYNOR, ANKLE BINDER M TYNOR, ARM SLING XL UNISON, CERVICAL COLLAR SOFT HOPE L, CLAVICAL BRACE M UNISON, CLAVICAL BRACE S UNISON, DYNA WRIST BRACE REVER LONG, FINGER COT M, FINGER COT M TYNOR, FINGER COT SPILNT REMEDE, KNEE CAP UNISON L LYCRA, KNEE CAP UNISON M LYCRA, RIB BELT S TYNOR, SOFT COLLAR BODY AID S.
  - At 05-10, the same items were cleared by pass 2, except ARM SLING XL UNISON. At 05-10 that item's flag is a new one of its own ("on 2026-10-05"), not a carry.
  - A second run writes nothing. The walk proved this on its copy.
- **Shelf figures that moved.** `figures()` was run before and after on the server, for all 28 items with a filed voucher. One moved: **TYNOR WRIST SPLINT RT M ELAST 4 → 2**. Its boundary of 2 → 0: the filed RECEIVE voucher's gain is no longer mistaken for a purchase dated before the count.
- **The 52 that stay at 04-10** (said, not fixed). Their stored moves run from −138 to +416, 33 of them negative, as the brief measured. I worked them out again against the spine as it is now, with the same window and the new voucher figure:
  - **37 of the 52 are now explained by sales or purchases that reached the spine after the closing was recorded.** 15 are not, with residuals from 0 to +500.
  - At 05-10, all **55** first-flagged rows that stay (moves −124 to +30, 51 negative) are explained by the spine now. The other 22 of the 77 are carries.

  `record_gaps` judges once, with whatever the spine held at that moment, and never looks again. Nothing was changed for this.
- **The stock-ahead warning at install: it shows, true by the rule.** "The stock figure is for 05-10-2026 but purchases are known only to 04-10-2026." The 05-10 closing arrived at 09:51 today; no purchase export yet reaches 05-10. The brief expected no warning on the 01:35 copy (stock 04-10, reach 04-10), and the day has moved on since. A day with no purchase looks the same as a day not yet exported. Nothing was built for this.

### The duty map v8 — as placed, and its two statements on the LIVE database (read only)
- **`manoj.salt_list`**: person manoj; tile "Marg"; door null; door_marker null; coded null; allowed_days 0.
  - duty: "Export Marg's SALT WISE ITEM LIST (weekly)"
  - owner_line: "Your salt list from Marg is overdue -- due since {since}"
  - due_sql: the brief's statement, letter for letter.
  - On the live database at 14:00:09: **(0, None)**. After install, from the clone's map: **(0, None)**.
- **`manoj.item_lists`**: the same fields.
  - duty: "Export Marg's CATEGORY WISE ITEM LIST and the item list (monthly)"
  - owner_line: "Your monthly Marg lists are overdue: {n} of 2 (category list / item list) -- due since {since}"
  - On the live database: **(0, None)**, both times.
- The chat's test states, re-run on a scratch copy before writing them in:
  - a salt list 9 days old → (1, 2026-10-06)
  - setting "9x" → the default → (1, 2026-10-06)
  - setting "10" → (0, None)
  - an item list 36 days old with no category list → (2, 2026-10-06)
- `version` is 8, `kit` is S488_DATES_AND_WAITS, and one sentence was added to `_note`. DUTY_MAP.md gains:
  - the two rows in the owner's table
  - the history line
  - **no-door finding 10**
- **The no-door finding (CLAUDE.md "Every duty has a door").** These are the map's first duties with no door. The export is done in Marg, and no page of ours does it.
  - The owner is told by amir_day's orphan-duty lines and by his console. The walk shows both readers take v8 without an error.
  - The staff-eye walk exempts exactly these two ids from the door check.
  - When a list is late it will show in more than one place on the console. Left as the brief says.
- **v8 is live at the pull.** The map is read from `/root/deploy/repo`, so it took effect at the publish. Both statements read only `mi_file` and `setting` and fall back to the defaults without the setting rows.

### Part D — the strike
- Wrong / Put back sit on the Items check card `s454learnt`. Under the list is a collapsed *Struck: N*, and the sentence was added as worded.
- `POST /finance/purchase/api/items/strike` takes JSON `{supplier_norm, scan_norm, marg_item, do: strike | back}`. It is for the doctor only, by `_person("checker")` and `_is_doctor`.
- **The call is modelled on the salt list page's script.** Its `SALT_JS` (`saltDone` / `saltAnswer`) calls the page's shared `post(url, body)` helper from purchase_app's `JS`. The new `s488strike` does the same and reloads on the same month.
- After a strike or a put-back, the supplier's `purchase_sarvam_check` rows are deleted, as `sarvam_compare` does for a newly learnt name.
- Read back live: 37 Wrong buttons, "Struck: 0". As amir, the POST answers 403. **The kit struck nothing.**

### Part E — the medical PC (`marg_watch.py`): packed, not placed, not run
- **`_may_leave` admits exactly** PURCHASE, SALT, CATEGORY, ITEMS, VALUATION, EXPIRY and STOCK, by `_kind_of`'s words.
  - Each admitted spec in marg_txt S480 was read. None has a patient, doctor, customer, mobile or address column. PARTY / SUPPLIER NAME on a purchase is the supplier, as phi_scan reads it. **None dropped.**
  - Out: every sale shape, the sale return, the stock register (LEDGER), ORDER and an unrecognised text.
- phi_scan's patterns were copied letter for letter. The server's `/root/marg_ingest/phi_scan.py` has four compiled patterns: mobile, person words, the shop's Phone line, and Marg's footer.
- **The file's own selftest on manojz: SELFTEST OK, 61 checks.**
  - The S396.1 case was rewritten to the new rule.
  - The walk §7.6 cases were added, with W488 texts, invented names, and ten-digit runs built at runtime.
- **Negative control** (`control_s488e.py`, the same cases with the OLD `share_refused`): **7 of 9 red.**
  - The OLD file put all six bodies on Drive (sale, register, both lists, the ten-digit list, the planted one) and six whole-reason `.why.txt` files with their `from:` lines.
  - The 2 that stay green are expected: the shop's Phone-line list is admitted, and the local folder is untouched.
- **Function-level diff of 58b54f37 against the new file: FDIFF OK.**
  - Changed: the docstring, `share_refused` and `selftest`.
  - Added: the helpers `_may_leave`, `_read_or_none`, `_share_put`, `_safe_why`, `_withhold`, `_share_sweep` and `_s488_share_cases`, plus their constants.
  - Byte-identical: the capture and note path (`capture`, `capture_text`, `_keep_refused`, `_kind_of`, `_note_reason`, `retry_refused`, `publish_diagnostics`, `watch`, `main`, …).
- **Delivery.** `deliver_S488.ps1` was made from deliver_S480. Only marg_watch.py is replaced.
  - marg_txt.py 14b75012 and marg_push.py 566e189e are pin-only.
  - KIT_MANIFEST goes ea2b437a → a1bf114f (CRLF on Drive), with the S488 comment.
  - It keeps `.superseded` backups, reads the md5s back, and restores on red. It parses with 0 errors.
  - **Not run.** `walk_s454p4c.py` was not run as a gate, as the brief says.
- **Drive keeps its own bin for 30 days.** A body or a whole-reason `.why.txt` that the first sweep removes stays there for that long.

### The walk (`walk_s488.py`) — as it ran inside the installer, on scratch copies (backup API), its rows keyed W488

```
  ok   the v8 map less S488's two duties reads back as the v7 map byte for byte (md5 1595520d = the brief's pin 1595520d)
  ok   both function probes ran to the end (NEW = the box + S488, OLD = the box as it is), each on its own copies
-- 1  dates as dates (F-753)
  ok   api_now with W488 closings of 30-09-2026 and 25-10-2026: NEW answers 25-10-2026; control OLD answers 30-09-2026
  ok   _r_stock (the readiness line 'Marg's closing stock: as on ...'): NEW 25-10-2026; control OLD 30-09-2026
  ok   api_drift: the W488 item's days end on the October day (NEW ['30-09-2026', '25-10-2026']), its feeds list begins with it (NEW ['25-10-2026', '25-10-2026']); control OLD ['25-10-2026', '30-09-2026'] / ['30-09-2026', '30-09-2026']
  ok   readiness, NEW: warns when the stock day is past the purchase exports' reach and is silent when the reach covers it, on the 5th and on the 25th: {'05|covered': False, '05|short': True, '25|covered': False, '25|short': True}
  ok   control OLD: silent on the 5th whatever the reach, warning on the 25th whatever the reach: {'05|covered': False, '05|short': False, '25|covered': True, '25|short': True}
  ok   api_losses with ISO from/to (October 2030): NEW returns the W488 loss inside the range and not the one outside (['W488 LOSS IN']); control OLD []
  ok   darpan_app's pipeline leg: the newest snapshot NEW 25-10-2026; control OLD 30-09-2026
  ok   stock_watch.item_info (no spine): the October snapshot row, packing 1*15 (NEW); control OLD 1*10
  ok   owner_sheets.consumable_items with stock_item_section emptied: NEW reads the October snapshot (1 item(s): ['W488 SNAP']); control OLD the September one (378 items)
  ok   text check: each OLD statement of A.1-A.10 (11) is in the OLD file and absent from the NEW one   [[]]
-- 2  the filed vouchers (F-754)
  ok   filed_vouchers(item, 2026-10-02, 2026-10-04): a batch entered 04-10-2026 -> 6 (control OLD 0); free-text entered_on falls back to the day of `at` -> 3; a day outside the window -> 0; a batch whose newest row has an empty number -> 0; entered twice -> counted once 2   [OLD: 0, 0, 0, 0, and 4 for the batch entered twice]
  ok   boundary_purchases for a W488 item with a filed RECEIVE voucher and a purchase two days before the base day: NEW 0; control OLD 6 (the voucher's gain mistaken for a late-dated purchase)
   re-judge on the copy (first run): flagged before {'2026-10-04': 66, '2026-10-05': 90, '2031-03-01': 1, '2031-03-03': 3, '2031-03-05': 2} -> after {'2026-10-04': 52, '2026-10-05': 77, '2031-03-01': 1, '2031-03-03': 2, '2031-03-05': 1}; cleared by pass 1 / 2 {'2026-10-04': [14, 0], '2026-10-05': [0, 13], '2031-03-03': [1, 0], '2031-03-05': [0, 1]}
  ok   W488 rows: a first-flagged row its voucher explains is cleared (G1 at 03-03: 0); one it does not explain stays (G2: 1); a carried flag of an earlier closing with a small move is NOT cleared by pass 1 (G3: 1); the carry of a cleared row is cleared by pass 2 (G1 at 05-03: 0) and the carry of an uncleared one stays (G2 at 05-03: 1)
  ok   a second run writes nothing (written 0; flagged per closing the same: {'2026-10-04': 52, '2026-10-05': 77, '2031-03-01': 1, '2031-03-03': 2, '2031-03-05': 1})
  ok   control OLD: its filed_vouchers over (01-03, 03-03] for G1 is 0 -- |5 - 0| >= 1, so the OLD rule would clear nothing
-- 3  the card (B)
  ok   _s446_proof on W488 feeds: why / closing_day / closing_at per state {'no_closing': ('no_closing', None, None), 'no_figure': ('no_figure', '11-03-2031', '2031-03-11T10:31:00'), 'pur_behind': ('pur_behind', '11-03-2031', '2031-03-11T10:31:00'), 'reach_covers': ('no_figure', '11-03-2031', '2031-03-11T10:31:00'), 'no_before': ('no_before', ...), 'rebased': ('rebased', ...), 'later_pairs_no_before': ('no_before', '12-03-2031', '2031-03-12T10:40:00'), 'later_pairs_rebased': ('rebased', '12-03-2031', '2031-03-12T10:40:00')} (the earliest push, with a 22:30 re-push present)
  ok   the same state as the OLD function in every case (export; done; wrong), and OLD carries no reason (control)
  ok   a later day pairs while the first Marg day after the vouchers has no figure: no_before / rebased, never no_figure
  ok   Amir's card, stage A and stage C, each row of B.2 letter for letter (closing_day printed dd-mm)   [{}]
  ok   control OLD: every reason renders today's words ('Ab closing stock export kijiye' even when the closing has come)
  ok   a result without the key renders today's words; a done and a wrong proof render byte-equal OLD and NEW
  ok   B.2b: his day's two lines (stage A, stage C) and the voucher board's proof line say the same reason; no_closing keeps today's words   [{}]
  ok   control OLD: the three places say an export is awaited in every state
  ok   the owner's lines: each ending (stage A's line and sentence; stage C's sentence once the lot is entered -- unchanged while some of it is left)   [{}]
  ok   control OLD: the owner's stage A line ends 'waiting for the closing-stock export'; the left sentence names the export
  ok   the warn line: absent at 47 hours, present at 48 -- stage A ['Count #948803: the voucher proof has waited 48 hours — waiting for a closing-stock export since 04-10 14:16 (Amir / Shavez)']; a stage-C lot [the same]; amir.proof_wait_hours 72 moves it ([])
  ok   control OLD: no warn line at 48 hours
-- 4  refusals (B.4)
  ok   a W488 refusal at 23:30 yesterday is shown this morning (09:00): ['Report refused 10-03 23:30: W488_REPORT -- W488 test reason (Shavez / Amir to export it again)']; control OLD shows none of it: []
  ok   fifteen unrecognised refusals (NULL, '' and _UNKNOWN mixed) make ONE line: ['15 unrecognised file(s) refused since 10-03 20:00 (newest 22:38)']; control OLD on their own evening: 10 lines
  ok   still there at 35 hours; gone at 37 (the window 36); amir.refused_keep_hours 40 brings it back at 37
  ok   it goes when a VERIFIED file of its type arrives later
-- 5  the owner's lists (C)
  ok   both due_sql on the copy: {'manoj.salt_list': [0, None], 'manoj.item_lists': [0, None]}; with the newest verified list moved 9 / 36 days back (no category list): {'manoj.salt_list': [1, '2026-10-06'], 'manoj.item_lists': [2, '2026-10-06']}
  ok   _s444_duty_lines raises each owner_line exactly as worded: ['Your salt list from Marg is overdue -- due since 06-10', 'Your monthly Marg lists are overdue: 2 of 2 (category list / item list) -- due since 06-10']
  ok   ... also when since is NULL (no salt list ever): [1, None] ['Your salt list from Marg is overdue -- due since -']
  ok   control: with the v7 map no such line
  ok   owner_lists at the default settings returns what the OLD function returns
  ok   it follows a changed setting (salt 3 -> limit 3; '9x' -> the constant 35): [['SALT_WISE_ITEM_LIST', 3], ['CATEGORY_WISE_ITEM_LIST', 35], ['ITEM_MASTER', 35]]; control OLD [['SALT_WISE_ITEM_LIST', 8], ['CATEGORY_WISE_ITEM_LIST', 35], ['ITEM_MASTER', 35]]
  ok   and survives a database with no setting table: [['SALT_WISE_ITEM_LIST', 8], ['CATEGORY_WISE_ITEM_LIST', 35], ['ITEM_MASTER', 35]]
  ok   the v8 map loads in aaj_kaam.load_defs ([None, 8, None]) and in owner_console's reader ([8, {'manoj.salt_list': [0, None], 'manoj.item_lists': [0, None]}, 0]) without an error
  ok   for every staff login amir, darpan, shavez, alisha, shivani, reception, bhati, sukhveer the list cut with the v7 map and with the v8 map is identical; only manoj gains the two (['manoj.item_lists', 'manoj.salt_list'])
-- 6  the strike (D)
  ok   learn pairs the W488 printed name with Marg's item (['W488 ALPHA TABLET']); learnt_line returns it (W488 ALPHA TABLET)
  ok   Wrong (strike): ok; learnt_line no longer returns it (None) and learn over the same pairing does not bring it back ([], None)
  ok   control, the OLD design (a delete is the only way back): learn brings the same pair back at once (['W488 ALPHA TABLET'], W488 ALPHA TABLET)
  ok   a different item for the same printed name is learnt (['W488 ALPHA FORTE']); strike that too, and neither returns ([] / []); both listed struck ['W488 ALPHA FORTE', 'W488 ALPHA TABLET']
  ok   Put back restores one at once without a learn ([True, 'Put back: it is used again.'] -> W488 ALPHA TABLET); the other is refused while it holds the name: 'Another item is learnt for this name — tap Wrong on that one first.'
  ok   the route: a staff login is refused (amir: 403); the doctor strikes ([200, True]) and puts back ([200, True]); control OLD: no route ([404, None])
  ok   the Items check page: every learnt name has a Wrong button (37), a collapsed 'Struck: N' with Put back (1), the sentence, the script
  ok   control OLD page: no button
-- 7  staff-eye (D648): amir, darpan, shavez, reception and the owner, signed in on scratch copies (a walk-only store and secret)
   (eye, NEW copy) closing 2026-10-04: flagged 66 -> 52 (pass 1 cleared 14) | closing 2026-10-05: flagged 90 -> 77 (pass 2 cleared 13)
  ok   both staff-eye probes ran to the end (NEW: re-judged on its own copy; OLD: the copy as it is)
  ok   on the live copy with no W488 row: api_now's day 05-10-2026 equals the newest day by date in stock_feed itself (05-10-2026); control OLD 30-09-2026
   [as_is]
  ok   amir (as_is): signs in (200), 3 tiles; 7 pages compared NEW vs OLD; differences: none
  ok      amir: 9 duties in the map, 2 due now -- each due one visible (its tile on the home, its marker on its door) as on the OLD side
  ok   darpan (as_is): signs in (200), 8 tiles; 4 pages compared NEW vs OLD; differences: none
  ok      darpan: 9 duties in the map, 4 due now -- each due one visible as on the OLD side
  ok   shavez (as_is): signs in (200), 19 tiles; 4 pages compared NEW vs OLD; differences: none
  ok      shavez: 6 duties in the map, 2 due now -- each due one visible as on the OLD side; NOT visible on either side, before this kit too: ['shavez.match_check'] (a finding, below)
  ok   reception (as_is): signs in (200), 7 tiles; 2 pages compared NEW vs OLD; differences: none
  ok      reception: 4 duties in the map, 2 due now -- each due one visible as on the OLD side
  ok   manoj (as_is): signs in (200), 54 tiles; 15 pages compared NEW vs OLD; differences: ['/finance/darpan/api/pipeline (A.7)', '/finance/purchase/page/items (D)', '/finance/stock/api/drift (A.1-A.3)', '/finance/stock/api/now (A.5)', '/finance/stock/api/readiness (A.3 / A.4)']
  ok      manoj: 11 duties in the map, 5 due now -- each due one visible as on the OLD side; the two door-less duties of S488 exempt by id
   the owner's Needs-you, NEW only: ['Report refused today 13:48: ORDER_PENDING -- the medical PC refused it: the reader refused it (line 21) (Shavez / Amir to export it again)']
   the owner's Needs-you, OLD only: ['Report refused today: ORDER_PENDING at 13:48 -- the medical PC refused it: the reader refused it (line 21) (Shavez / Amir to export it again)']
   [waiting]
  ok   amir (waiting): 7 pages compared; differences: ['/finance/amir (B.2)', '/finance/amir/step/3 (B.2)', '/finance/amir/step/5 (B.2)', '/finance/amir/step/6 (B.2)', '/finance/amir/step/7 (B.2 / B.2b)', '/finance/stock/api/pad/amir/1 (B.2b)']
  ok   darpan (waiting): differences: none · shavez (waiting): none · reception (waiting): none   [each with every due duty visible as on the OLD side]
  ok   manoj (waiting): differences: ['/finance/amir/day (B.3)', the five A / D pages above]
   the owner's Needs-you, NEW only: ["Count #1: Stage A: all 7 orthotic vouchers entered -- Marg's closing of 06-10 arrived 06-10 23:59; waiting for our own figure for that day (made when its sale report lands — Shavez; on a no-sale day, the empty report)", "Count #1: the voucher proof has waited 52 hours — Marg's closing of 06-10 arrived 06-10 23:59; ...", the refusal line in its new words]
   the owner's Needs-you, OLD only: ['Count #1: Stage A: all 7 orthotic vouchers entered -- waiting for the closing-stock export', the refusal line in its old words]
  ok   the W488 waiting state (the closings after the vouchers set aside; a Marg push of 06-10 with no figure of ours): Amir's home card says 'Closing stock aa gaya' and nothing is asked of him (NEW ['Closing stock aa gaya ✓ (06-10 23:59)', 'Server ka 06-10 ka apna hisaab abhi nahi bana — yeh bikri report ke baad banta hai. Aapko abhi kuch nahi karna.']); control OLD tells him to export (['Ab closing stock export kijiye'])
  ok   ... and the voucher board's line (as amir): NEW 'Abhi baaki — closing stock aa gaya — server ka hisaab banna baaki (bikri report ke baad)'; control OLD 'Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye'
  ok   the owner's stage-A line in that state names the arrival
   FINDING (not this kit's; the same on the box as it is): a due duty whose marker is not on its door page -- {'shavez.match_check': ['/finance/clinic/match', '2026-09-24']}
WALK_S488 GREEN -- 75 checks
```

(Lines above are the log's own, shortened where they repeat. The full log stays at `/tmp/s488kit2/install.log` on the box until /tmp is cleared.)

**Each staff-eye difference, named:**
- **As it is today:** the owner's five pages of A and D only: Stock now, readiness, drift, the pipeline and Items check.
  - The live proof is in state `wrong`, so Amir's card does not change today.
  - Darpan's spot-count roster (`/finance/stockmatch`) rendered the same: that page draws its list by script.
  - The owner's Needs-you shows the shelf-gap line with the new count. The refusal line is in its new words.
- **With the W488 waiting state:** Amir's home, steps 3, 5, 6 and 7, and the voucher board's line. The owner also sees his view of Amir's day.

### What I did NOT do, and why
- **Not placed and not run:** `deliver_S488.ps1` and `marg_watch.py`. The chat reads the file first; then the owner gets the one PowerShell line.
- No learnt name was struck. Which one is wrong is the owner's call.
- No flow gate was moved. The stock-ahead warning on no-purchase days is reported, not built for.
- No staff list was touched. The walk's §5 proves every staff login's list is byte-equal under v7 and v8.
- **None of S486's twelve parked files was touched.** S486's pins of `purchase_app.py` and `stock_watch.py` are now stale (254b7793 → c29050c1, 6d4d660f → 4fc0f601). They are refreshed at the Fable re-read. Its cited lines of `stock_watch.py` survive: A.9 stayed one line.

### Outside the brief — noticed, or done to make the kit publishable
1. **`.gitignore` gained one exception line**, `!deploy_kits/S488_DATES_AND_WAITS/DUTY_MAP.json`. The kit's v8 map must be in the repository, as in S482 and S485. Without the line, `*.json` would have dropped it silently.
2. **Staff-eye finding: `shavez.match_check` is due but not visible.**
   - The day has been `maker_done` since 2026-09-24.
   - The "first pass" marker is not on `/finance/clinic/match`, before this kit and after it.
   - Most likely No-door finding 7 again: the page opens yesterday only. That is the parent's side (clinic_money), and nothing was done.
3. **Part E concern, from the build:** check whether manojz runs its own copy of the watcher with Drive mounted before the line is given. `marg_watch.py`'s S381 comment says manojz runs one.
   - If it does, that copy's sweep would see the medical PC's admitted list bodies as "local source gone" and withhold them. The medical PC would copy them back at its next pass.
   - It fails closed (nothing leaks), but the folder would churn.
4. **Two old warnings, both harmless on the server's Python 3.9 and both left alone (outside the edit lists):**
   - `purchase_app.py` header line 33: `"\D" invalid escape`, a SyntaxWarning on Python 3.14 only.
   - `marg_watch.py` capture message: `"\h"`, the same kind.
5. **The watcher's start line still says "marg_watch S480 starting".** Changing it means editing `main()`, which is outside E.4's list. The heartbeat's md5 is the proof of the version.
6. The new `S488_ITEMS_JS` and the route sit inside the S454 part 5 block of `purchase_app.py`. Nothing outside the Items check block moved.
