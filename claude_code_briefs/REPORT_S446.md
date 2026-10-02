# REPORT S446 — S446_AMIR_STAGES_BILLS (D649 · D650 · F-673 F-674 F-679 F-680) · installed 02-Oct-2026 06:15 IST · published

## For the owner

**Amir's count work, in the order you decided.**
- From his next visit, "Amir ka kaam" shows only **"Orthotic voucher baaki: 7 — kholiye"**. His board lists just those 7.
- After he enters them, the card asks for a closing-stock export. The server then checks the orthotic figures in Marg itself and
  names any item still wrong.
- Only when they are right does he get the 22 renames. Only when Marg shows the new names do the medicine vouchers start,
  5 per visit. You get one line, "Orthotics verified and renamed — live orthotic ordering can start", when that point comes.
- Nothing stops his day closing.

**The card also shows:**
- the **August pack**, until he taps "Dekh liya";
- on step 2, **"Marg mein daalne ke bill (14)"**: each scanned bill to download as a PDF named supplier_billno_date, and today's as
  one zip. Only Amir and you can download them.

**The 30-Sep sale** is already on the server, from your Excel export of 01-Oct 12:56 (24 bills, Rs 23,598). The medical PC's reader
now understands Marg's "***" mark, so the same text export will not be refused again. The medical PC confirmed this at 06:17 today.
Nothing for you to do.

**Sarvam against Marg, September:** of 63 scanned bills, Sarvam read only 3 completely right. Marg's figures are what every page
uses. The comparison runs until 02-Dec, and you get one summary line each month.

**The 18 supplier messages** are not stuck on the server. The reception phone stopped collecting them on 26-Sep: it was using a wrong key.
- **Whose step:** someone at reception, with that phone.
- **What to do:** open https://followup.dr-manoj.in/finance/purchase/page/phone-setup and set up the MacroDroid macro again from it.
  After that, the 18 messages go out by themselves.

**Also new:**
- Darpan sees Amir's supplier claims on "Kal ka hisaab", with two taps.
- Shavez's Vendor payments says "Pichhle mahine ka baaki: 18".
- Your counter-returns line now counts every open month: 3 waiting, oldest 02-Sep.

**It works.** Every change was tested on a copy of today's records (41 of 41), alongside the earlier tests, and checked again after it
went live.

```
https://followup.dr-manoj.in/finance/amir/day
```

```
https://followup.dr-manoj.in/finance/approvals
```

## For the chat

### The kit and the timeline
**Kit** `deploy_kits/S446_AMIR_STAGES_BILLS/`, 22 files:
- `make_s446.py` and its 5 blocks: `amir_block_s446.py`, `stock_block_s446.py`, `purchase_block_s446.py`, `darpan_block_s446.py`,
  `approvals_block_s446.py`;
- `walk_s446.py`, `walks_old_s446.py`, `plan_old_s446.py`, `apply_s446.py`;
- `install_S446_AMIR_STAGES_BILLS.sh`, `README.md`, `KIT_ID.txt`, `SUMS.md5`;
- `DUTY_MAP.md` and `DUTY_MAP.json`;
- `medical/`: `marg_txt.py`, `make_marg_txt_s446.py`, `prove_s446.py`, `PROVE_S446_RESULT.txt`, `KIT_MANIFEST.txt`, `README.md`.

**Timeline (IST, read):**

| When | What |
|---|---|
| 05:50–06:01 | DRY run green |
| 06:01:16 | Build lock `/root/deploy/.claude_code_build.lock` taken (owner `S446_AMIR_STAGES_BILLS`) |
| 06:15:37 | Live install from the uploaded kit copy (`KITS=/root/deploy/repo/deploy_kits`); data step |
| 06:15:38 | `clinic-finance` restarted |
| 06:16:54 | Medical files written to Drive `ToMedical\_kit` |
| — | PUBLISH_ALL → `76ac7f2` |
| 06:17:38 | Medical heartbeat: `marg_txt.py up to date (70f920c4)` |
| 06:17:51 | On the box: `git pull` → `diff -r` of the repository's kit against the copy that ran: **byte-identical**. `claude_code_briefs/DUTY_MAP.md/.json` = the kit's. The repository installer answers **"ALREADY INSTALLED"** |

### Live files, FROM → TO, md5 read back on the box (06:17:51)
| file | FROM | TO (read back) |
|---|---|---|
| /root/finance/amir_day.py | 2b497142efdb1a3d1b84e9f05cbf59ac | cd8f4659cb828c09e9455d1b7543cfbd |
| /root/finance/stock_app.py | c0120fb67c78105fe797982fcb6ab644 | ec6b1ce80d46b808d034b23cab032dc9 |
| /root/finance/sanjeevni_approvals.py | d2c550401ebfb7716126d24a09fae78f | 792f4a9af1728c76e8d5a656f5662421 |
| /root/finance/purchase_app.py | a51fe90eaa2922ba4e2b4db6388f797a | 176fc6eac35c7a3e7d052cba96ca873e |
| /root/finance/darpan_kal.py | 803970bd04c7203632b98d9659923b3b | 377ffd63786261cef4a6113482d43bb5 |
| /root/finance/darpan_kal.html | a4eecb21a88f793ab5c81b75dab20a51 | 9269afb04a454b626895a27666032752 |
| packs.py (READ ONLY) | 6a1cf6ce… | 6a1cf6ceec4a58260df7352e48cdefe5 (unchanged) |
| Drive `_kit\marg_txt.py` (medical PC) | 38d85298f1627ab22b59c9f3459d8764 | 70f920c445ec82fc8c1e069f1f758efb; the agent confirmed it in the heartbeat |
| Drive `_kit\KIT_MANIFEST.txt` | 8230562e3dc08d5b07b458198086c68d | bdd277686cb76f944d4569e666a9d89f (CRLF; the repository copy is LF, 60992cf0…) |
| medical `marg_watch.py` | 81145aa7 | **unchanged, not delivered**; the watcher is still pid 2448 |

**Not touched**, read before and after by the installer and again at 06:17:51: porders.py 3620b374, portal.py ba61e35a, clinic_sso.py 6344e09c,
tile_grants.json 392e6d89, finance_app.py, crontab.

### Backups
- **Database:** `/root/finance/finance.db.bak_S446_20261002_060116` (backup API).
- **Files:** `.bak_S446_<from8>` beside each of the six: `amir_day.py.bak_S446_2b497142`, `stock_app.py.bak_S446_c0120fb6`,
  `sanjeevni_approvals.py.bak_S446_d2c55040`, `purchase_app.py.bak_S446_a51fe90e`, `darpan_kal.py.bak_S446_803970bd`,
  `darpan_kal.html.bak_S446_a4eecb21`.
- **Drive:** `marg_txt_S397.py.superseded` and `KIT_MANIFEST_S397.txt.superseded` beside the new ones.

### Services and health
- `clinic-finance` only was restarted.
- healthz 200, local and public.
- `/finance/amir/day`, `/finance/approvals`, `/finance/darpan/kal`, `/finance/purchase/page/pay` and the scan-files zip each answer
  302 (the login gate).
- Nothing "NOT mounted".
- The journal since the restart holds one "ERROR" line: gunicorn's own "Worker … was sent SIGTERM!" from the OLD process during the
  restart. No traceback.

### The data step (live, after placing)
**Settings added** (INSERT OR IGNORE): `amir.vouchers_per_visit=5`, `purchase.sarvam_trial_until=2026-12-02`, `purchase.scan_file_users=amir`.

**Sarvam:** 63 linked scans compared → September 2026:

| Bills | Agreed fully | Supplier wrong | Bill no. wrong | Date wrong | Total wrong | Items wrong |
|---|---|---|---|---|---|---|
| 63 | 3 | 13 | 7 | 9 | 10 | 57 (of 63 with items read) |

**Amir's card as he sees it:** "Marg sudhar · Orthotic voucher baaki: 7 — kholiye · Mahine ka pack — August 2026 · … · Dekh liya".
- Count #1 is at Stage A, 0/7 entered. His board lists 7, numbered 1..7.
- Step 2 lists 14 bills to put into Marg, the oldest B-0007 from 09-Sep. None was scanned today.

**The owner's new lines:**
- "Count #1: Stage A (orthotic vouchers) 0/7 entered" (info);
- the Sarvam monthly summary (info, links to /finance/porders).

`stock_stage_event` is empty: nothing is verified yet.

### The walk — `walk_s446.py`, run at install: **WALK_S446 GREEN — 41 of 41**
It ran on scratch copies of finance.db and assets.db, with its own rows keyed W446*:
- scan W446-01 (today, unlinked);
- scan W446-02 (linked to Marg bill W446B; Sarvam Rs 1,240.56 against Marg Rs 1,234.56; item BETA qty 7 against 5);
- claim W446C;
- its own feeds `push_snapshot W446` / `push_expected base=W446`.

**0. Staff-eye walk** (a walk-only secret and user store; DUTY_MAP v2). Every due duty's door shows it:

| Login | Duties | Due duties whose doors show them (count due) |
|---|---|---|
| amir | 7 | bills_answer 1, own_correction 1, count_vouchers 37, purchase_exports 1 |
| darpan | 7 | cash_handover 1, amir_claims 1, spot_count 4, desk_shelf_counts 48, desk_identity 30 |
| shavez | 5 | month_reports 2, match_check 2, supplier_messages 18 |
| manoj | 9 | approve_days 1, returns_ok 7, clinic_flags 5, slip_adjust 2, cash_received 1, physio_received 12, purchase_month_final 1 |

**1. Stage A.**
- Steps 1–7 show only "Orthotic voucher baaki: 7". Amir's board shows the 7 orthotic vouchers in the order 3|ISSUE|1, 3|ISSUE|2,
  4|ISSUE|1, 4|ISSUE|2, 3|RECEIVE|1, 3|RECEIVE|2, 4|RECEIVE|1, numbered 1..7, with no renames. The owner's board still lists 37.
- Din band is offered.
- All 7 marked → "Ab closing stock export kijiye".
- One orthotic item wrong on a crafted export → that item is named, with Marg's figure, the figure it should be, and its voucher.
  No rename is shown.
- A clean export → "Orthotic: sab sahi ✓" and "Naam badlo: 22 naam". Still no medicine voucher.

**2. Stage B → C.**
- 22 renames ticked; the export with the new names verifies them.
- "Orthotic poora ✓" and "Dawa voucher: aaj ke 5 (baaki 25)". The board shows 5, numbered 1..5, oldest round first.
- The owner's line comes exactly once, plus "Count #1: Stage C … 0/30 entered, 5 released".
- A lot verified → the next 5 ("baaki 20").
- A lot left unverified → the next 5 after 2 visits; the unverified lot stays listed (10 on the board).
- Din band is offered.

**3. Packs.**
- August shows until "dekh liya".
- A crafted ready September appears (a walk-only patch of `packs.amir_pack`).
- The foot card is gone.

**4. Files and Sarvam.**
- The step-2 list = the unlinked captured pharmacy scans.
- A download carries the new name and the stored bytes (md5 equal). The zip holds today's file.
- Another staff login gets 403/403; the owner gets 200.
- The crafted linked scan's comparison row: supplier, bill number and date agree; the total is wrong; 1 of 2 items is wrong.
- The summary adds up.
- The Scan links page line and the Needs-you summary are there.
- Amir's bill line reads "Marg: Rs 1,235 · Kaagaz (scan): Rs 1,241": Marg's figure is the bill's.

**5. Doors.**
- The card's three door lines (Sunday, arrived-goods bills, trace fixes) show while due and only then (a walk-only patch of
  `stock_watch.amir_view`).
- Darpan lists W446C. "Supplier se baat ho gayi" → contacted; "Credit / maal mil gaya" → settled (`darpan_received`), and the claim
  leaves the list.
- Shavez sees "Pichhle mahine ka baaki: 18 — August 2026".
- The returns line: "Counter returns waiting for your OK: 3, 2,491 (oldest 02-Sep)".

**6. NEGATIVE CONTROL.** The same walk on the box as it is (the old files) goes red at every point:
- the old card "Stock voucher baaki: 7 orthotic, 30 dawa";
- the old board giving Amir all 37;
- no August pack, no bills list, and the file door 404;
- no claims on Darpan's page, no earlier-month card, no Sarvam (`purchase_app` has no `sarvam_compare`);
- the old returns line "1 return of 1,110 needs your OK" (this month only).

### The earlier walks — `walks_old_s446.py`: **WALKS_OLD_S446 GREEN**
Each walk ran twice on fresh scratch copies: once unadjusted on the box as it is (the baseline), and once adjusted on the box + S446.
Each walk's control is its own `.bak` files.

| Walk | Baseline (box as is) | Patched (box + S446) | Reds on the patched files |
|---|---|---|---|
| S436's walk (S437's copy), on the board | GREEN 48/48 | GREEN 48/48 | none |
| S437's walk | RED 3/42 | RED 3/42 | the SAME 3 reds as the baseline, all today's data: S437's rule and round 5 already ran on the live database on 28-Sep ("ONE run of kind receive_close", "exactly ONE STOCK RECEIVE line on round 5", "the statement reads 'Marg corrected'"). Accepted by name. |
| S444's walk | 57/59 | 58/59 | only "NEGATIVE: KEDAR 195's claim stays open on the box as it is": S444's own rule settled claim #1 at its install on 01-Oct. Accepted by name; red on the baseline too. |

The baseline's other S444 red ("shavez … supplier_messages unseen") was the v2 duty map read against the old files. S446 adds that door,
and on the patched files it is green. The brief said "S444 60/60"; the walk without the `--live-*` arguments has 59 checks.

**Adjustments, each anchored on a scratch copy** (the kit folders are never edited):

| Code | Walk | Adjustment |
|---|---|---|
| D1 | walk_s437 | `amir()` reads the board as the owner. Amir now sees only his stage; the whole board is the owner's and the checker's view, which the walk asserts. |
| D2 | walk_s436_s437 | the same as D1 |
| B1, B1b, B1c, B1d | walk_s444 | The card is staged: "Orthotic voucher baaki: N", read as [orthotic, 0]. |
| B2, B2b | walk_s444 | The renames' gate is Stage A's own proof, so the crafted green proof patches it too. |
| B3 | walk_s444 | Line (d) reads "Count vouchers waiting (Stage A, orthotic): N". |

### What I decided, and why
1. **Count #1 has 37 vouchers, not 39.**
   - Stage A is the 7 batches whose items are all orthotics.
   - Stage C is the other 30: medicine and consumables, rounds 1, 2 and 5.
   - The card's "baaki 25" is 30 minus the first 5.
2. **The returns line counts from `returns.act_from` (02-Sep), not August.** This corrects REPORT_S444, finding F-680.
   - The 7 counter returns of 03–19 Aug are older than `returns.act_from` (2026-09-02, the code default, no setting row). S219's
     rule is "the past is accepted", so the existing S406 rule never counted them.
   - The line now counts every open month from that date: 3 waiting, oldest 02-Sep. My statement in REPORT_S444 that 7 August
     returns wait was wrong.
   - If the owner wants August counted, that is one setting row (`returns.act_from`) and a chat decision. I did not move it.
3. **The scanned-bill list counts 14, oldest 09-Sep.**
   - It lists captured pharmacy scans that have no Marg bill linked. Duplicates (`dup_of`) are left out.
   - The downloads read the asset store read-only, by the stored upload's path. No asset-app file was touched.
4. **Sarvam's 3 of 63 is the comparison as built,** and it is strict:
   - the supplier, alias-aware;
   - the bill-number digit tail;
   - the date;
   - the total within Rs 1;
   - every item, matched by name similarity ≥ 0.6 and then quantity, rate, batch and expiry.

   57 bills have at least one item different. The page `/finance/purchase/page/sarvam?month=2026-09` shows each bill field by field.
5. **The medical delivery is the reader only.**
   - The 30-Sep sale is already VERIFIED on the server: `mi_file` eec4e41d, stamp 20261001-125631, SALE_BILLWISE DETAIL
     30-Sep→30-Sep, received 01-Oct 12:56:35.
   - Not changing `marg_watch.py` means the agent does not restart the watcher. So the refused 30-Sep/01-Oct texts are not offered to
     the reader again, and the server keeps one copy of that sale.
   - The texts age out of the watcher's retry window around 03-Oct 22:10 (the 30-Sep copies) and 04-Oct 12:55 (the 01-Oct copy).
     A PC restart before then would bring in two more `.XLS` of the same sale: `7818a331` and `72bfdba1`. The server's own duplicate
     handling would then meet them.
6. **The refusal note does NOT travel — named, not built.**
   - The only route is `marg_push` → `/finance/api/marg-file` → `marg_take.take()`. It refuses anything that is not
     `.xls/.xlsx/.pdf`, with matching magic bytes, before it opens the database.
   - So a note leaves no row and no log line. Carrying one needs a note branch in `marg_door`/`marg_take`: a new door.
   - The brief says to report that and deliver the reader fix alone, which is what I did. Details are in `medical/README.md`.
7. **`.gitignore` got one exact-path line.** `!deploy_kits/S446_AMIR_STAGES_BILLS/DUTY_MAP.json`.
   - The kit's walk and installer ran with that file, and `SUMS.md5` covers it.
   - PUBLISH_ALL refused the first publish because the blanket `*.json` rule hid it.
   - This follows the file's own rule ("any new kit whose payload is a .json needs its line here") and S444's line for
     `claude_code_briefs/DUTY_MAP.json`.
8. **The duty map is v2 (`claude_code_briefs/DUTY_MAP.md` and `.json`, `kit: S446_AMIR_STAGES_BILLS`).**

   | Duty | Door | Marker |
   |---|---|---|
   | `amir.count_vouchers` | — | "Marg sudhar" |
   | `amir.full_count_sunday` | /finance/amir | "Poori ginti ka Sunday" |
   | `amir.arrival_bill_entry` | /finance/amir | "Marg mein bill baaki" |
   | `darpan.amir_claims` | /finance/darpan/kal | "Amir ke claim" |
   | `shavez.supplier_messages` | /finance/purchase/page/pay | "Pichhle mahine ka baaki" |
   | `manoj.returns_ok` | — | note: every open month from `returns.act_from` |

   Each `due_sql` is one read-only SELECT, and each was run on the live database before it was written in.

### The 18 supplier messages (REPORT only; the fault is not on the server)
- **The queue:** `supplier_msg` holds 18 rows (August, queued 26-Sep 19:49), none sent, 0 fetch attempts.
- **The queue door's access log:** exactly 2 requests, both on 26-Sep at 09:08 and both 401 (a wrong token). Both came before the
  messages were queued. Nothing has come since.
- **So:** the reception phone's MacroDroid macro is not fetching with the current token.
- **The step on the phone:** open `/finance/purchase/page/phone-setup` (owner / checker), which issues a new token, and set the macro
  up again from it. No server change is needed.
- **Who sees it:** Shavez's Vendor payments now shows the count ("Pichhle mahine ka baaki: 18").

### Spine tasks (REPORT only: kinds and ages)
`marg_task`: 48 open, with no page and no person.

| Kind | Open | Dates |
|---|---|---|
| ambiguous | 9 | all 07-Sep |
| merge | 2 | 07-Sep |
| name_clash | 1 | 11-Sep |
| question | 12 | 07-Sep to 01-Oct |
| rename | 24 | 07-Sep |

### Door states today
- No full-count Sunday is open (`stock_count_plan` is empty).
- There are 0 arrived-but-unbilled lines.
- `stock_trace` has 28 `first_count` lines open, but `amir_view` reports 0 fixes for Amir.

So none of the card's three new door lines shows today. The walk proves each appears while due.

### What I did NOT do
- The refusal-note route (6 above): it needs a new door.
- `marg_watch.py`: no change, by design (5 above).
- `returns.act_from`: not moved (2 above).
- No change to porders, portal, clinic_sso, tile_grants or crontab.

### Outside the brief, noticed
- **The medical PC's heartbeat** says "6 kit backup files are lying about — the prune is not working". This predates S446.
- **Marg's server backup** is noted in the heartbeat as on D: (as before).
- **Sarvam's supplier mismatches (13 of 63)** are probably supplier names Sarvam reads differently from Marg's ledger names. An alias
  list would lift the figure. Worth a look before the trial ends on 02-Dec.
- **`item_alias` holds the 22 renames for Stage B.** Their "verified" state comes from `verify_closing` on a closing-stock export,
  which is S437's code, unchanged.
