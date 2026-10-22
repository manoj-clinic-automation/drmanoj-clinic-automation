# REPORT S613_S605_FOLLOWUP — 22-Oct-2026 (installed; clinic-finance restarted 08:59:29 IST, the box's clock)

**For you (Dr Manoj):**
1. The orthotic sizes' stock figures are right again. Each of the 22 sizes is now figured by its share of the family up to 10-Oct and by its own records after that. The old name and the new name now give the same figure. 5 sizes changed, each by +1: Knee support L and M, L S belt XL, Shoulder immobiliser M, Tynor wrist splint left L. No spot count was judged on the wrong figure.
2. Bills are matched to orthotic order lines by size only, before and after 10-Oct. A bill for one size never closes another size's order line (order 1's XL / XXL lines stay open against bill 672).
3. The old Purchase orders page can no longer order from Yuvika: its button and its size / quantity buttons are gone, and the server refuses the order. One more way remains, on the purchase page's staff send; it is named for a later build.
4. "Aaj ke order — call karo" now counts only today's orders that have not arrived yet.
5. WhatsApp orders: the 60-minute "not confirmed" wait now starts when the phone takes the message. If the phone says "could not send" after that hour, the order comes back to reception's card to call. After the phone's own "could not send", an order may be sent again, once per "no".
6. S604's test now uses its own made-up days and passes. Everything was tested on a copy first, and it is live and working.

---

## For the chat

### FROM → TO, read back on the box (`md5sum`, 08:59, after placing)
| file | FROM | TO (read back) |
|---|---|---|
| /root/finance/stock_figure.py | 51e1fc63ab3fb1ac21170cb214f15b6b | 8c66b6b1010b7f0942768fe04022fa27 |
| /root/finance/order_sheet.py | 17fa1fdbd34d07b0af0535375926c4fc | c7fe2561b22158f9dffa73b8c963e298 |
| /root/finance/porders_s454.py | 7ca91d4f8eabc5cdb10c9df55f2c080b | 34bab4648940f30d7fc57188398c51b4 |
| /root/finance/porders.py | e5a5c4d4dfa15c3ecd0b0cdf4786abcd | b1736494f6dc58683ccb9c0a4c3fe181 |
| /root/finance/porders.html | 7a6799ae3c8b41e783051cd1280a6964 | cbe1a46a72e0e82489c00397e303daab |

**Pins.** All five FROM pins matched at the open (08:05) and again at the installer's gate (08:53). Every read-only md5 also matched at both checks: supplier_msg 4e3911a7, stock_watch f0d9092a, shelf_figure 23b2394a, order_rules 8d078dbe, stock_app 40f2c922, purchase_app 447b745f, amir_day 1169a3d6, amir_salts fc5c1d16, darpan_kal.py d6ba4882, darpan_kal.html c0ddc0ea, order_sheet_pdf 7a6d47c0, marg_order_pdf bdcf2d00, item_alias 111a8e48, spine/spine_build 1cd20ead, spine/spine_read 10697b38, spine/spine_rules.json dd6c7616. finance_app.py, portal.py, tile_grants.json and the crontab (84 lines) were proved unmoved at the end.

**Kit folders.** S605's folder passes its SUMS, and SUMS itself is 018a68ad. S604's files pass their SUMS, KIT_MANIFEST.txt apart (F-958). Both folders were left untouched.

**Builder.** `make_s613.py` made 38 anchored edits on the live bytes, each anchor found exactly once. The kit in `deploy_kits/S613_S605_FOLLOWUP/` is byte-identical to `/tmp/s613kit`, which ran.

**Backups.** `finance.db.bak_S613_20261022_085348` was taken by the sqlite backup API (42,098,688 bytes). Each replaced file has its `.bak_S613_<from8>` beside it.

**Service.** clinic-finance only, restarted once at **2026-10-22 08:59:29**.
- healthz 200. `/finance/porders`, `/s454/order`, `?old=1`, `/amir` and `/darpan/kal` answer 302 (the login gate).
- The journal's one "ERROR" line is gunicorn's worker SIGTERM at the restart.
- `DOCTOR_AUTO_OFF` was written before the restart and removed after.
- The 09:00:13 order tick ran on the new code with `withdrawn 0, marg_lines 0` and no error.

**Data.** `finance.db`: no DDL, no DELETE, no hand edit, no setting. `spine.db`: not edited, not rebuilt.

**Witness.** Run once, read only: exit 0, stderr empty. It wrote `/root/finance/spine/stock_figure_witness_Thu.txt` at 08:59.

### The walk (walk_s613.py), on the box, scratch copies (backup API), 08:54–08:58 IST
Final lines:
- `WALK OK S613: 73 checks, 25 controls green on the new files`
- `WALK OK negative control S613: 25 controls red on the old files` (`RED on the old files: 25 of 25 controls`)

The 25 controls, verbatim. NEW: every one `ok`; the OLD run: every one red.
- `C: (1) split_of reads all 22 sizes (new key, old key, day 2026-10-10 from the spine's own note) and the old name gives the same row`
- `C: (1) shelf() by old and by new name give the same figure for each of the 22`
- Six per-size controls, each against the old run's figure:
  - `C: (1) by old name KNEE SUPPORT HINGED L: shelf's sold 5.6 / bought 4.0 = its share 0.4 of the old key's 9 / 10 to 10-10 + the new key's 2 / 0 since` (OLD: sold 3.6)
  - The same for KNEE SUPPORT HINGED M (4.6 vs OLD 3.6), L S BELT … L (3.25 vs 2.25), L S BELT … M (1.75 / 1.5 vs 0.75 / 0.5), L S BELT … XL (bought 2.0 vs 1.0) and TYNOR WRIST SPLINT LF L (1.5 / 1.0 vs 0.5 / 0.0).
- `C: (1) by old name (KNEE SUPPORT HINGED M) shelf() counts the walk's sale under the new key (sold +1)`. The walk laid one sale of its own under `KNEE SUPPORT M HINGE`, dated 22-10, on its own spine copy; the side's spine is md5-unchanged.
- `C: (1) marg() by old and by new name equal for each of the 22, the walk's sale after the newest capture included`
- `C: (1) order 20's L S BELT ... XXX: its family-bill words name bill 738 of 18-10 (the sibling sizes' new keys)`
- `C: (2) api/send as manoj -> 409 ortho_via_order_page ('Yuvika's order now goes from reception's order page, after Darpan's yes.'), nothing written`, and the same for darpan with the Roman Hindi words. OLD made an order.
- `C: (2) the old page has no send(), no 'Yuvika ko order bhejo', no -/+ (dq) and no size chips (ps)`
- `C: (3) the call row counts today's orders still awaited -- 2 (the walk's 2 + the copy's 0), never the received or yesterday's`. The OLD rule says 14.
- `C: (3) all of today's orders received -> no call row, and 'Sab kaam ho gaya' when nothing else stands`
- `C: (4) queued T, handed T+50, no done -> at T+60 still queued: not withdrawn, not unconfirmed (the wait runs from the hand-out)`
- `C: (4) a message the phone takes between withdraw_late's read and its write is not withdrawn (the guarded UPDATE)`
- `C: (4) a late ok:false on an unconfirmed order, nothing arrived -> a draft again (sent_by NULL), its line in_line, reception's card 'WhatsApp nahi gaya — call kijiye', audit row`
- `C: (4) after the phone's no on the unconfirmed order it may be queued again (not under wa_plan's 'call'; order_supplier 200, queued)`
- `C: (4) ... with a line arrived -> the order unchanged, the message skipped, the owner's line 'W613 SUPPLIER H — the reception phone said it could not send the order of 08:54, but goods have already come in on it. Nothing was changed.'`
- `C: (4) handed + the phone's ok:false -> wa_plan lists it to send again (not under 'call') and order_supplier re-queues it (once per no)`
- Three grep controls: one `split_of` and one `split_moves`; one rule `_s613_phone_said_no` read by `order_supplier` and `wa_plan`; `_done_today`'s numbers through `book_card`.

Plain checks, green:
- `key_of` is byte-equal OLD vs NEW over 413 names: the newest usable capture ebbb09fb, the 6-Sep count, and count 1's vouchers.
- Amir's count-voucher proof (`amir_stage`) is equal OLD vs NEW: `{'stage': 'C', 'proof': 'done', 'pending': 0}`.
- Every other name is byte-equal OLD vs NEW: 369 names (shelf + marg) and 92 order lines (carried), KNEE IMMOBILISER UNISON M among them.
- The witness reads the same: 675 lines, 0 differ.
- Never-handed messages are withdrawn at T+60.
- At T+50+61 an order is unconfirmed.
- Two cycles (no → re-queued → handed → silence) end unconfirmed and never re-queueable.
- A late ok:true makes the message sent.
- Payment and test messages behave as before.
- `counts()` and the *Ho chuke* list (10 lines, numbers via `book_card`) are equal OLD vs NEW.

**Staff-eye.** The walk ran on its own portal secret and user store.
- Reception, the shared login: its name cookie gives "reception · Alisha". Two duties were due on the copy: `reception.bill_scan` (tile *Purchase orders*, door "Bill scan karna hai") and `reception.order_arrival` ("Maal aaya?"). Both were seen on the home and the door.
- Amir: his portal home renders (*Amir ka kaam*), but none of his 11 duties was due on the copy (each `due_sql` n = 0). No door could be asserted for him today; his page dump is byte-equal OLD vs NEW.
- **DUTY_MAP: no change.** No duty was added, moved or removed (the clone's DUTY_MAP.json stays v17, ef42b155).

**Page dumps, OLD vs NEW** (Darpan's day and his order tab, reception's home / order list / supplier / maal / scan / photo pages, Amir's page, the approvals Needs-you, the pay page, Bhati's sale check): byte-equal except this kit's own lines, printed both ways:
- Reception's home: `- 10` / `- Aaj ke order — call karo` are gone. The call row counts today's awaited orders, and the copy holds none today.
- Needs-you: `(its bill YS…##### of 07-10 carried L S BELT XXL CONT GRAY UNI, not this size)` → `(its bill 738 of 18-10 carried L S BELT M CONT GRAY UNISON, L S BELT XL CONT GRAY UNIS, not this size)`.

**F-957: walk_s604_v2.py**
- On the NEW files: `WALK OK S604v2: 50 checks, 33 controls green on the new files`.
- On S604's own OLD purchase_app (60f2d846): `WALK OK negative control S604v2: 33 controls red on the old files`.
- It lays its own January-2030 suppliers, bills 9001–9006, export payloads and twin rows, found by key.
- Not re-walked:
  - the reader-side controls (`marg_txt.py`): their OLD (a59a222f) is the medical PC's reader and is not on the box;
  - `data_s604.py`: a one-time step, done on 20-Oct;
  - the live months' figures.

**S605's three walks (brief §4.6),** on the OLD (live) and the NEW side, check lines compared:
- **walk_s605.** OLD `WALK RED S605: 4 failure(s)`, NEW 6. The only lines that differ are the two this kit changes on purpose:
  - `C: (2) ... and a send-all never queues again a message the phone was handed (call instead)` (R1-B4: the re-queue after a phone-no);
  - `C: (4) nothing left to order -> 'Aaj ke order — call karo' with the Ho chuke count (10)` (F-962).

  The 4 lines red on both sides are its section 1 (Darpan's हाँ … on the live day's copy), not this kit; see below.
- **walk_s603.** OLD `WALK OK S603: 79 checks, 32 controls green`; NEW differs in one line only: `stock_figure.py untouched (md5 51e1fc63)`. Its pin on the file this kit edits.
- **walk_s598.** OLD `WALK OK S598: 62 checks, 25 controls green`; NEW differs in one line only. That line is S605's own expectation that XXX's clause names 07-10's bill; this kit returns it to bill 738 (R1-C4).

### The 22 sizes, before → after (live, read only)
Before is 08:53:48, the S605 files; after is 08:59:32, the S613 files. Both read the same spine build of 08:50:46. Marg is unchanged for every size.

| size (new name) | key | Marg | shelf before → after | approx before → after |
|---|---|---|---|---|
| KNEE SUPPORT L HINGED | KNEE SUPPORT L HINGE | 4 | **2 → 3** | False → True |
| KNEE SUPPORT M HINGED | KNEE SUPPORT M HINGE | 3 | **3 → 4** | False → True |
| KNEE SUPPORT XL HINGED | KNEE SUPPORT XL HING | 1 | 1 → 1 | False → True |
| KNEE SUPPORT XXL HINGED | KNEE SUPPORT HINGED | 1 | 1 → 1 | True → True |
| L S BELT L CONT GRAY UNISON | L S BELT L CONT GRAY | 1 | 2 → 2 | False → True |
| L S BELT M CONT GRAY UNISON | L S BELT M CONT GRAY | 2 | 1 → 1 | False → True |
| L S BELT XL CONT GRAY UNISON | L S BELT CONT GRAY U | 2 | **2 → 3** | True → True |
| L S BELT XXL CONT GRAY UNISON | L S BELT CONT GRAY U | 2 | 2 → 2 | True → True |
| L S BELT XXXL CONT GRAY UNISO | L S BELT XXXL CONT G | 0 | 0 → 0 | False → True |
| SHOULDER IMMOB L UNISON | SHOULDER IMMOB L UNI | 1 | 1 → 1 | False → True |
| SHOULDER IMMOB M UNISON | SHOULDER IMMOB M UNI | 3 | **3 → 4** | False → True |
| SHOULDER IMMOB XL UNISON | SHOULDER IMMOB XL UN | 1 | 0 → 0 | False → True |
| TYNOR WRIST SPL LF L ELASTIC | TYNOR WRIST SPLINT L | 3 | **2 → 3** | True → True |
| TYNOR WRIST SPL LF M ELAS T | TYNOR WRIST SPL LF M | 2 | 2 → 2 | False → True |
| TYNOR WRIST SPL RT L ELASTIC | TYNOR WRIST SPLINT R | 2 | 2 → 2 | True → True |
| TYNOR WRIST SPL RT M ELASTIC | TYNOR WRIST SPLINT R | 1 | 2 → 2 | True → True |
| KNEE IMMOBILIZER L UNISON | KNEE IMMOBILIZER L U | 2 | 1 → 1 | False → True |
| KNEE IMMOBILIZER XL UNISON | KNEE IMMOBILIZER XL | 0 | 1 → 1 | False → True |
| ANKLE BINDER L BAMBOO | ANKLE BINDER L BAMBO | 0 | 0 → 0 | False → True |
| ANKLE BINDER M BAMBOO | ANKLE BINDER M BAMBO | 1 | 0 → 0 | False → True |
| BLING PELVIC L TRACTION BELT | BLING PELVIC L TRACT | 1 | 1 → 1 | False → True |
| BLING PELVIC XL TRACTION BELT | BLING PELVIC XL TRAC | 1 | 1 → 1 | False → True |

- 5 shelf figures changed, each by +1. All 22 are now `approx` (the base is the 6-Sep count, before the split day); 16 of them turned from False to True.
- `key` is the `key_of` answer, unchanged by design. That is why the six printed-name rows above still show the old key; `shelf` and `marg` use `split_of`'s new key.

### split_of's rows (live, after placing)
22 rows, all `split 2026-10-10`:
- KNEE SUPPORT L / M / XL / XXL (`… HINGE`) ← `KNEE SUPPORT HINGED`
- L S BELT L / M / XL / XXL / XXXL ← `L S BELT CONT GRAY U`
- SHOULDER IMMOB L / M / XL ← `SHOULDER IMMOBILISE`
- TYNOR WRIST SPL LF L / LF M ← `TYNOR WRIST SPLINT L`
- TYNOR WRIST SPL RT L / RT M ← `TYNOR WRIST SPLINT R`
- KNEE IMMOBILIZER L U / XL ← `KNEE IMMOBILI?ER UNI (family)`. The note's clip is 'KNEE IMMOBILIZER UNI'; the rules-family key comes through sp_item.
- ANKLE BINDER L / M ← `ANKLE BINDER BAMBOO`
- BLING PELVIC L / XL ← `BLING PELVIC TRACTIO`

Every note was parsed by `\(split (\d{4}-\d{2}-\d{2}) from ` and agreed with the old key's `RENAME_SPLIT` date. No stderr line.

The 10-10 split captures (printed 10-10):
- 64f60c9e, taken 11-10 07:11, a morning capture;
- 9e99d952, taken 09:39;
- 14995473, taken 09:52;
- 76eb46af, taken 10:35.

All stand for the end of 10-10.

### The families' conservation (scratch)
Σ of the sizes' NEW shelf before the clamp, against the family's total by S605's OLD builder (spine_build.py.bak_S605_e3d3ed85 on a scratch spine), one member set:

| family | members | OLD builder total | NEW sum |
|---|---|---|---|
| ANKLE BINDER BAMBOO | 2 | 0 − 2 + 0 + 2 = 0.00 | 0.00 |
| BLING PELVIC TRACTIO | 2 | 2.00 | 2.00 |
| KNEE SUPPORT HINGED | 4 | 10 − 12 + 1 + 10 = 9.00 | 9.00 |
| L S BELT CONT GRAY U | 5 | 8 − 8 + 1 + 6 = 7.00 | 7.00 |
| SHOULDER IMMOBILISE | 3 | 4 + 1 = 5.00 | 5.00 |
| TYNOR WRIST SPLINT L | 2 | 4 − 2 + 2 + 1 = 5.00 | 5.00 |
| TYNOR WRIST SPLINT R | 2 | 4 − 1 = 3.00 | 3.00 |

**KNEE IMMOBILI?ER UNI (family)** was left out, as R1-C3 allows. Its old key also carries KNEE IMMOBILISER UNISON M (not one of the 22), whose own share is taken over the newest capture's members, so the 22's shares cannot sum to 1.

### The open old-name lines: carried bill and family-bill words (NEW; OLD where different)
- Order 54, ANKLE BINDER BAMBOO M: carried None; family bill None (both).
- Order 20:
  - ANKLE BINDER BAMBOO L: carried None; family bill YS…##### of 07-10 (ANKLE BINDER M BAMBOO), both.
  - L S BELT CONT GRAY UNISON XXX: carried None; family bill **738 of 18-10** (L S BELT M CONT GRAY UNISON, L S BELT XL CONT GRAY UNIS). OLD named 07-10's YS…##### (L S BELT XXL CONT GRAY UNI).
  - KNEE IMMOBILISER UNISON M: carried None; family bill None (read, named, nothing changed).
- Order 1:
  - KNEE SUPPORT HINGED XL and XXL UNISO: carried None. The family bill is 672 of 28-09 (KNEE SUPPORT M HINGED, KNEE SUPPORT L HINGED): never carried by it.
  - KNEE IMMOBILIZER UNISON XL: carried None; family bill 672 (KNEE IMMOBILIZER L UNISON).
  - SHOULDER IMMOBILISE UNISON XL: carried None; family bill None.
  - L S BELT … XXX (billed 672): branch (a) bill 672, units None, equal to OLD.

### detect_supplies' writes
- On a copy of the quiet copy: none on the OLD files, none on the NEW.
- On live since placing (08:59:29 to 08:59:3x): no `line_detected` audit row and no `detected_at`. The 09:00 tick logged `marg_lines 0`.

### Calls I made (the brief left them open), and why
1. **The share's members (R1-C3).** The brief says "the last capture on or before the split day". The newest such capture that prints the SHOULDER IMMOBILISE key (11-10 09:52) prints `SHOULDER IMMOBILISE L/M/XL UNISON`. No count holds those spellings, and they are not in the rename memory. So `split_members` takes the newest capture on or before the split day **whose every member reaches a counted item**, else the newest printing the key.
   - Without this, each shoulder size took the whole family's history. S605's live figure has the same fault: by old name, each shoulder size got the 18-09 purchase in full.
   - The conservation control proves the shoulder family now sums to 5.00.
2. **A late "could not send" on an unconfirmed order whose goods came in.** `_s613_unconfirmed_now` accepts the order `received` as well as `sent`. A bill-scan tie makes it `received`. The brief's arrived branch (no change; the owner's line) is the right outcome for that case too, rather than the old silent withdrawal.
3. **The call row's count** uses `order_via<>'paper'` exactly as `_done_today` does, so that N matches the not-yet-arrived lines of today in *Ho chuke*.
4. **walk_s604_v2's "own synthetic export text".** It is the push payloads the purchase page receives, not a text file run through `marg_txt.py`, because the reader is not what is tested there (its OLD is not on the box).
5. **The old page's orthotic table** shows the short quantity as plain text where the −/+ were.

### What I did not do, and why
- walk_s605 / walk_s603 / walk_s598 (S605's folder) are **not "green on NEW"** in the brief's literal sense. Each differs from its run on the live files only in this kit's intended lines, listed above, and the installer gated on exactly that.
- walk_s605's section 1 (Darpan's हाँ, 4 controls) is **red on the live files too**, identically on both sides. It reads the live day's orthotic list (the F-957 class).
- **For the chat:** walk_s605 needs the F-957 repair in a later kit.

### Anything outside the brief I noticed
- **`s577_shelf_gap`** holds rows at end-day **16-10** for 16 of the 22 new names: all but KNEE SUPPORT XXL, L S BELT XL / XXL, and TYNOR LF L / RT L / RT M. These are pre-existing; the table's newest end_day is 16-10. They were most likely written by `record_gaps` while S605 showed the new names as exact. Nothing newer exists.
- **An untracked kit appeared** in the PC's repository at 08:04: `deploy_kits/S620_PCS_JOBS_LINE_NIGHT/` (session S336, setup_notes.py; not a file of this kit). PUBLISH_ALL publishes everything pending, so it goes out with this publish. I did not touch it.
- **Seen, not touched** (brief §7):
  - `stock_watch.Spine.key` / `spine_read.Spine.key` (expected_units, allowance_units, open_trace, watch_list), `loss_piles` / `stock_statement`, and `shelf_figure.movements` / `boundary_purchases` still resolve an old name to the old key.
  - Reception's order page and the approvals card write on a GET (F-925).
  - The MacroDroid macro posts `ok:true` whatever happened.
  - `reception.medicine_orders`' due_sql and the orthotic card.
  - The purchase page's `staff_send` (purchase_app 1773–1776), a third door to Yuvika.
  - The split day as a spine column.
  - A re-key of the 22 at the next orthotic count.

### Cost
The runner writes its own cost line when the run closes (`run_build.py S613_S605_FOLLOWUP --budget 60`; log `D:\Downloads\_kbtools\agent_build\logs\S613_S605_FOLLOWUP_20261022_0804.log`). When this report was written, about **$17 of the $60** budget had been used.

### Lock
`/root/deploy/.claude_code_build.lock` was taken at 08:53:48 IST by S613_S605_FOLLOWUP. It is released after this report and the publish with `rm -f /root/deploy/.claude_code_build.lock/owner; rmdir /root/deploy/.claude_code_build.lock`.
