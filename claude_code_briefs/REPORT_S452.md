# REPORT S452 — S452_AMIR_PANEL_FIXES (F-686 · F-687; serves D650 · D648) · installed 02-Oct-2026 23:51 IST · published

## For the owner

- **Amir's bill list now shows only bills Marg does not have: 2 to enter (B-0007, B-0018, both Yuvika Surgicals). The other 12 are held
  back** with one grey line, "12 scan abhi reception ki jaanch mein hain — Marg mein mat daaliye". They come to him once reception answers
  them in Scan ka kaam. The five with the shop's own name as supplier are among the 12. Each file name now starts with its stamp
  (for example `B-0007_YUVIKA_SURGICALS_09-09-2026.pdf`).
- **The reception phone has a new key; only you can see it.** The setup page now opens only for your login, and every showing is
  recorded. The old key stopped working at 23:51. *Your one step:* on the reception phone, sign in as yourself and open the setup page
  below. Long-press the key, copy it into the macro's two HTTP steps, then sign out. The page's top line will then say "jawab 200" once the
  phone asks, and the 18 August messages go out by themselves.
- **Amir's step 7 and his stock board are now in Roman Hindi**, the board has no Hindi script left, and step 6 shows its heading once.
  Step 7 now reads, for example, "Bill daalne ki pushti baaki hai … Ginti #1: 7 orthotic voucher Marg mein daalne baaki (din band karne se
  nahi rukta)". His card also says "2 item ka rate Marg mein daalna hai — kholiye". That line goes by itself once Marg carries the rates.
- **NEFT: for August Amir sees one line, "NEFT August 2026 — payment 24-09 ko ho gaya (Doctor sahab ne darj kiya)", and "Paid NEFT sheet
  (PDF)".** He no longer sees supplier names, and he gets no Excel. A month you have not entered, and whose bank SMS has not been read, shows
  him nothing.
- **Medicine vouchers: 12 a visit (was 5), plus an "Aur voucher kholiye" button that opens 12 more at once.** That starts once the orthotic
  stages are verified, in the order you set.
- **It works.** It was tested on a copy of today's records (54 of 54 checks), alongside the five earlier tests it touches. It was checked
  again after it went live.

```
https://followup.dr-manoj.in/finance/amir/day
```

```
https://followup.dr-manoj.in/finance/purchase/page/phone-setup
```

## For the chat

### The kit and the timeline
**Kit** `deploy_kits/S452_AMIR_PANEL_FIXES/`, 16 files:
- `make_s452.py` (the anchored patcher, 80 edits, each anchor exactly once);
- its blocks `purchase_block_s452.py`, `amir_block_s452.py`, `supplier_block_s452.py`, `stock_block_s452.py`;
- the board's 46 line edits `board_edits_s452.txt`;
- `walk_s452.py`, `walks_old_s452.py`, `plan_old_s452.py`, `apply_s452.py`;
- `install_S452_AMIR_PANEL_FIXES.sh`, `README.md`, `KIT_ID.txt`, `SUMS.md5`, `DUTY_MAP.md`, `DUTY_MAP.json`.

**Timeline (IST, read from the logs and file times):**

| When | What |
|---|---|
| 22:02 | Pins read live; all six = the brief's FROM. Lock free. |
| 22:40–23:10 | DRY runs 1–3: the kit's walk green from the 2nd run; the earlier walks' adjustments and named reds settled (below). |
| 23:14:41 | Build lock taken, owner `S452_AMIR_PANEL_FIXES`. |
| 23:14–23:16 | A first live run, **stopped by me in its walks, before anything was placed**: I had found that the rate line could never clear (decision 5). Read back after the stop: the six files at FROM, no `.bak_S452`, clinic-finance active, healthz 200. |
| 23:34:59–23:41:28 | DRY run with the fix and the real TO pins: everything green. |
| 23:45:11 | Live install from the uploaded kit copy (`KITS=/root/deploy/repo/deploy_kits`, `DUTYMAP_OLD=/root/deploy/repo/claude_code_briefs/DUTY_MAP.json`). The kit's SUMS were checked on the box first. |
| 23:51:36 | `finance.db.bak_S452_20261002_234511` written; files placed; `clinic-finance` restarted (journal: stopped/started 23:51:36). |
| 23:51:45 | Data step done; installer `DONE`. |
| 23:52:32 | Read back: md5s, health, the duty's SQL on the live database (below). |

### Live files, FROM → TO, md5 read back on the box (23:52:32)
| file | FROM | TO (read back) |
|---|---|---|
| /root/finance/purchase_app.py | 176fc6eac35c7a3e7d052cba96ca873e | 341c663e52076f0ee264c356b49cf49e |
| /root/finance/amir_day.py | cd8f4659cb828c09e9455d1b7543cfbd | 85f208d0d64def40fb5a02e02c531284 |
| /root/finance/supplier_msg.py | 02b4a9edc4ff6bc42ed896e7f260be72 | 5cc35d2af444b5ab1996f636db8e54cf |
| /root/finance/stock_app.py | ec6b1ce80d46b808d034b23cab032dc9 | f14a1cfaf9a47b1199a0763ac47d1006 |
| /root/finance/stock_amir.html | 1ec8663dbbad397fe46f093966352e0a | 2e41e406e3b2ef9d7ed75f9f24b923b8 |
| /root/finance/packs.py (the parent's: one edit, Amir's NEFT route) | 6a1cf6ceec4a58260df7352e48cdefe5 | 23fda41a19a6d4be398922e906d06702 |

**Not touched.** The installer read these at its start and again after placing; each was unchanged:
- porders.py 3620b374;
- finance_app.py a92baae4;
- sanjeevni_approvals.py 792f4a9a;
- darpan_kal.py 377ffd63;
- portal.py 1a9fb99d;
- clinic_sso.py 6344e09c;
- tile_grants.json f9441311;
- the crontab and the medical PC.

`finance_app.py` was e8dbf77e when I first read the box (22:02:20). **S453 placed it at 22:02:25** (its `.bak_S453_e8dbf77e`) — before my lock and
not by this kit.

### Backups
- **Database:** `/root/finance/finance.db.bak_S452_20261002_234511` (backup API).
- **Files:** `.bak_S452_<from8>` beside each of the six:
  - `purchase_app.py.bak_S452_176fc6ea`
  - `amir_day.py.bak_S452_cd8f4659`
  - `supplier_msg.py.bak_S452_02b4a9ed`
  - `stock_app.py.bak_S452_ec6b1ce8`
  - `stock_amir.html.bak_S452_1ec8663d`
  - `packs.py.bak_S452_6a1cf6ce`

### Services and health
- `clinic-finance` only was restarted.
- healthz 200, locally and publicly.
- These answer 302 (the login gate): `/finance/amir/day`, phone-setup, `/finance/stock/page/amir`, Amir's NEFT route and the scan-files zip.
- Nothing "NOT mounted"; the journal since 23:45 holds no traceback and no error line.

### The data step (live, after placing)
- **`amir.vouchers_per_visit`:** 5 → 12.
- **`stock_rate_marg` made:** it holds 2 rows, FINGER COT SPILNT REMEDE and SOFT COLLAR BODY AID S. Each reads S.RATE 0.0 and MRP 0.0 as on
  01-Oct.
- **The phone key:** renewed. `purchase_audit` holds `phone_token_renewed` (23:51:44). The key was compared with the backup's ("changed") and
  never shown.
- **Amir's step 2:** 2 to enter and 12 held.
  - To enter:
    - B-0007, YUVIKA SURGICALS, scan 09-09, bill 09-09-2026;
    - B-0018, YUVIKA SURGICALS, scan 29-09, bill 29-09-2026.
  - Held:

    | Reason | Scans |
    |---|---|
    | near-match | B-0033, B-0041, B-0042, B-0048, B-0078, B-0080, B-0082, B-0088 |
    | supplier unread | B-0054, B-0079, B-0100 |
    | second scan | B-0044 |

- **NEFT 2026-08 for Amir:** "NEFT August 2026 — payment 24-09 ko ho gaya (Doctor sahab ne darj kiya)".
- **His card:** "Orthotic voucher baaki: 7 — kholiye · 2 item ka rate Marg mein daalna hai — kholiye · Mahine ka pack — August 2026 · Paid
  NEFT sheet (PDF) · Yes Bank … · ICICI … · Dekh liya". Count #1 is at Stage A.

### What the chat asked to be read first (§2), read live
- **F-686.**
  - The 14 are the captured pharmacy scans with no `purchase_scan_link`, `dup_of` aside.
  - In `purchase_scan_state` they split as follows:

    | `why` | Scans |
    |---|---|
    | `no_digits` (Yuvika, no number or amount read) | B-0007, B-0018 |
    | `number_differs`, with a likely bill | B-0033, B-0041, B-0042, B-0048, B-0088 |
    | `amount_differs`, with a likely bill | B-0078, B-0080, B-0082 |
    | `vendor_unknown`, nothing chosen | B-0054, B-0079, B-0100 |
    | `dup` | B-0044 |

  - S440's "Marg ka intezaar" group (`porders.scan_work`) is exactly B-0007 and B-0018.
- **F-687 — why "shown once" did not hold for Amir.**
  - `page_phone_setup` admitted checker, maker and viewer. It showed the key when `supplier_msg.token_shown` was empty, or always to the
    checker, and on the first showing it set `token_shown`.
  - Nobody signed in had opened the page since S407: the three opens on 26-Sep answered 302 at the login gate. So the one showing went to
    whoever opened it first.
  - The app's access log and the portal's sign-ins show that the first opener was Amir's login:
    - 19:45:28: a sign-in whose `/portal` redirects, as Amir's day does.
    - 19:46:39: the setup page answered 3,855 bytes. That is the size with the key, and `token_shown` reads 2026-10-02T19:46:39.
    - 19:46:55: his second open answered 3,928 bytes, the "ek baar dikha diya" warning.
  - The opens at 19:48:33 and 20:53:24 also carried the key. They followed a fresh sign-in at 19:48:22 whose portal home is the size of
    the owner's (21,838 bytes, as at 19:44:45). These were most likely the owner's own login, which the old code always showed the key to.
  - So the once-rule held, but its one showing went to a staff login.
  - The key was readable at `/finance/api/supplier-msg/next`, which hands out full account numbers. The phone has not asked since its two
    401s on 26-Sep 09:08.
- **The NEFT rows (§3.5).**
  - `purchase_neft_event` has one live row: month 2026-08, kind provisional, source `owner`, `sms_date` 2026-09-24. It was created
    2026-09-26 19:49 by manoj, with no `bank_line_id`.
  - No Yes Bank SMS event exists (`source='sms'`, S405's `bank_sms.py`). No statement line has confirmed it: `bank_line_id` is empty.
  - So **today Amir sees the first wording and the PDF.**

### The walk — `walk_s452.py`, run at install: **WALK_S452 GREEN — 54 of 54**
It ran on scratch copies of finance.db, assets.db and the spine, with its own rows keyed W452:
- a Marg bill W452-61234;
- scans W452-01, W452-02 and W452-03;
- an SMS-read NEFT for 2099-04.

The box's own 77 scan files were copied read-only for the downloads.

0. **Staff-eye walk** (a walk-only secret and user store; DUTY_MAP v3). Every due duty's door shows it:

   | Login | Duties | Due (count) |
   |---|---|---|
   | amir | 8 | bills_answer 1, own_correction 1, count_vouchers 37, **rate_entry 2**, purchase_exports 1 |
   | darpan | 7 | spot_count 4, desk_shelf_counts 48, desk_identity 30 |
   | shavez | 5 | month_reports 2, match_check 2, supplier_messages 18 |
   | manoj | 9 | approve_days 1, returns_ok 7, clinic_flags 5, slip_adjust 2, cash_received 2, physio_received 13, purchase_month_final 1 |

1. **The list, on the box's own scans.**
   - The listed scans are exactly S440's "Marg ka intezaar" scans, B-0007 and B-0018.
   - None of B-0054, B-0078, B-0079, B-0080 or B-0082 is listed.
   - Held 12 + listed 2 = the 14 of the list as it was.
   - Each line shows "scan: dd-mm, <who>" and a bill date within 60 days.
   - Every download name starts with its stamp; none contains "nobill".
2. **The crafted scans.**
   - The near-match W452-01 is held, and its download says "reception ki jaanch".
   - Reception's "Nahi" puts it on the list. A Marg bill that links it takes it off.
   - W452-02, with a bill date of 2023: "bill ki tareekh scan par saaf nahi", and the file carries the scan day
     (`W452-02_KEDWALK452_PHARMA_W45255555_02-10-2026.pdf`).
   - W452-03, with no number read: `W452-03_KEDWALK452_PHARMA_01-10-2026.pdf`.
   - The zip follows the same rule.
   - **The guard:** a scan linked after the page was drawn answers "Yeh bill Marg mein aa chuka hai", and it is gone on reload.
   - The owner's Scan links line is there.
3. **The key.**
   - amir and darpan get 403; reception gets 302.
   - The owner gets 200 with the key on each open, and each showing writes one audit row (+2).
   - The page's first line read the access log's 401 before anything was recorded.
   - The data step makes a new key, which is in no line of its output.
   - The old key gets 401 and the new one 200. The page's line follows: 401, then 200.
   - The probe stops red if a key string reaches its output.
4. **Step 7.**
   - As amir: no "not confirmed / not verified / not ticked / not entered". "Ginti #1: … (din band karne se nahi rukta)" stands apart.
   - As the owner (`/finance/amir/day`): English kept.
5. **The board.**
   - 0 Devanagari code points on the page and in its data.
   - The 7 vouchers and their buttons work: one entered → "Orthotic voucher baaki: 6".
   - "2 item ka rate Marg mein daalna hai" shows while due. It goes when a crafted Marg item export carries the rates: the card line, the
     board's (b), and `amir.rate_entry` reading 2 → 0.
   - LINVIZ 600 (done in Marg) has left block (a).
   - Step 6 carries one "Marg sudhar" heading.
6. **NEFT.**
   - August reads the first wording, with "Paid NEFT sheet (PDF)", on all seven steps.
   - None of the 18 supplier names, and no "baaki" or "bata diya", appears in his NEFT block.
   - The file is `NEFT_paid_2026-08.pdf` (`%PDF`). Its 19 rows equal the S408 sheet's, and so does its total, Rs 3,54,924.00 (the NEFT
     portion is Rs 3,53,455).
   - The crafted SMS month reads "NEFT April 2099 — bank ka kaam ho gaya, 30-09".
   - A month with neither: no line, and the route refuses amir (2099-06 and September). No sheet in a ready September pack (a walk-only
     patch of `packs.amir_pack`).
   - Shavez's and the owner's pay pages keep all 18 names, as before.
   - No address gives amir an .xlsx: Amir's route gives a PDF, the advice file 403, the owner's preview 302.
7. **Stage C.**
   - The setting is 12 after the data step. A copy where the owner had set 8 keeps 8.
   - Stage B (crafted A verified): the renames, and no "Dawa voucher".
   - Crafted B verified: 12 on the board, numbered 1..12; "Dawa voucher: aaj ke 12 (baaki 18)"; the button is offered.
   - An export with one wrong item names "ACILOC 300 Marg mein 39, hona chahiye 38 · voucher 2 theek kijiye".
   - One tap: 24 on the board, "aaj ke 12 (baaki 6)". One audit row: `{"by": "amir", "n": 12, "why": "more"}`.
   - The next visit opens the third lot: 30, and the button is gone. Another tap answers "none left" and writes nothing.
   - The owner's line: "Count #1: Stage C (medicine vouchers) 12/30 entered · 30 released · 0 verified".
8. **NEGATIVE CONTROL** — the same walk on the box as it is goes red at each point:
   - the 14-line list, the shop's own name in it;
   - the near-match listed, a 2023 file name, "nobill";
   - the setup page 200 to amir;
   - English step 7;
   - 1,075 Devanagari code points on the board;
   - supplier names with "baaki" in his NEFT block, and the .xlsx;
   - "aaj ke 5 (baaki 25)" and no "more" door (404).

### The earlier walks — `walks_old_s452.py`: **WALKS_OLD_S452 GREEN**
Each walk ran twice on fresh scratch copies: once unadjusted on the box as it is (the baseline), and once adjusted on the box + S452.

| Walk | Baseline | Patched | Reds on the patched files |
|---|---|---|---|
| S446 | GREEN 41/41 | GREEN 41/41 | none |
| S444 | 56/59 | 56/59 | the same 3 as the baseline, accepted by name |
| S407 (the NEFT card, the setup page) | 20/27 | 20/27 | the same 7, accepted by name |
| S408 (Amir's pack route) | 18/27 | 18/27 | the same 9, accepted by name. **The Amir-pack check is green on both**: the route answers 200 (the PDF on the patched files); bhati is refused |
| S434 | WALK OK | WALK OK | — |

**S444's three reds:**
- KEDAR 195's claim was settled at S444's own install.
- Amir's board was opened as amir at 19:47:10 and 19:47:45 today (the chat's walk). So `stock_board_open` already holds rows, and line (d)
  is not due.

**S407's seven reds:**
- its negative control, the box before S407, no longer exists: both runs use the box as it is;
- the 18 live August messages, queued since 26-Sep, answer the queue door before the walk's own message, and keep the Needs-you count at
  19 and then 18.

**S408's nine reds:**
- its control, the box before S408, no longer exists;
- the portal is at v32 now;
- the walk's statement fixtures meet the real statements filed since 26-Sep: the cells, the ICICI fixture, the electricity line, the lab
  bundle, the split send.

**Adjustments, each anchored on a scratch copy** (the kit folders are never edited):

| Code | Walk | Adjustment |
|---|---|---|
| B1–B3 | walk_s444 | S446's own adjustments, now on **both** runs, since the box is S446. |
| A1–A2 | walk_s408 | On **both** runs: S446's card in place of S408's foot card — "Mahine ka pack — August 2026", gone once "Dekh liya". |
| C1–C4 | walk_s446 | Stage C at 12 a visit: the patched copy gets S452's data step first, as the live box did. Card, then board: 12 (baaki 18); 12 (baaki 6) / 12; the next visit opens the next lot (1 visit, was 2), so 18 (baaki 0) / 18. |
| F1–F3 | walk_s446 | The crafted W446-01 read "W446A". Its digits (446) and supplier are those of the crafted bill W446B, already linked to W446-02, so S452 rightly holds it as a second scan. It is crafted as "W9446A", and the zip's name is matched by its end (the names now start with the stamp). |
| P1–P3 | walk_s407 | The setup page's two opens are the owner's: the key on both, and no "ek baar". Shavez's pay page has no setup link. Amir's page has no "bata diya". |

### What I decided, and why
1. **"Supplier known".** A wait-group scan is listed only if its supplier is a chosen supplier, or the matcher reads its vendor as exact,
   learned or similar to a Marg supplier. The buyer's own name and unknown vendors are held. On today's data this makes no difference:
   B-0007 and B-0018 both resolve to YUVIKA SURGICALS.
2. **The held count includes the second scan B-0044.** That way held + listed = the old 14, as the brief's walk reads.
3. **Bank confirmation.**
   - A Yes Bank **statement** line confirming the NEFT also reads "bank ka kaam ho gaya, <date of the line>". The bank has then done its
     work, as with the SMS.
   - The owner's entry without either reads the first wording.
   - Months shown: those with a live event of the last 45 days (S407's window).
4. **Amir's NEFT route no longer waits for both statements to be on the shelf.** It answers by confirmation alone. In the month's pack, the
   PDF link appears only once confirmed.
5. **The rate line clears on Marg's own figure.**
   - This is why I stopped the first live run. `stock_rate` is filled only by the server's computed feed (202 rows, all `push_expected`).
     Marg's stock export carries no rates. So an item would never leave after Amir put the rate in Marg.
   - Marg's item export does carry S.RATE and MRP into the spine (`sp_item_fact`, 3,379 items, newest 01-Oct). Both items read 0.0 there.
   - So an item leaves when the spine's newest S.RATE or MRP is above 0, or `stock_rate` has a rate.
   - The spine is another database, so what it says is mirrored into `stock_rate_marg` (finance.db) whenever the list is read. That keeps
     `amir.rate_entry`'s one SELECT and the card in step.
6. **The bank's NEFT advice file (`/page/pay/<m>/advice.xlsx`)** is now the owner's and the senders' only (`supplier_msg.senders`: manoj,
   shavez). It carries full account numbers, it answered every medical login including Amir's, and the brief's walk requires that no
   address give him an .xlsx. Darpan (medical maker) loses it too.
7. **Shavez's pay page no longer links the setup page,** which he cannot open now. The owner's link stays.
8. **The card's "aaj ke N" counts what is open on his board,** so after a tap it reads 24 on the board and "aaj ke 12 (baaki 6)".
   - A lot is still released when the previous lot is proved, as in S446.
   - It is also released on his next visit (1 visit, was 2), proved or not.
   - Each export proves whatever is entered so far and names a wrong item.
9. **The phone's last ask** is recorded from now in `supplier_msg.phone_last`. Before S452 nothing recorded it, so the page reads the newest
   queue-door line of `/root/finance/access.log`. On the live box I **did not call the queue door** to prove the keys, so that the page's
   line stays true. Old key 401 and new key 200 were proved on the scratch copy; live, the key was compared with the backup's.
10. **The earlier walks S407 and S408** were written against a box before their kit, which no longer exists. Both runs use the box as it
    is, and each of their reds is named and is red on the baseline too.
11. **`.gitignore` got one exact-path line,** `!deploy_kits/S452_AMIR_PANEL_FIXES/DUTY_MAP.json`, as S446 did. The kit's walk and installer
    ran with that file, and SUMS covers it.
12. **The duty map is v3** (`claude_code_briefs/DUTY_MAP.md` and `.json` = the kit's):
    - `amir.rate_entry` added. Its door is `/finance/amir`, marker "item ka rate Marg mein daalna hai". Its `due_sql` read **2** (since
      28-09 13:29) on the live database: before the install, and again at 23:52:32 with the mirror table.
    - `amir.count_vouchers` now reads 12 a visit, more on request.
    - The scanned-bills row has the S452 rule.
    - A NEFT-payments row: no due state, so it is not in the JSON.

### What I did NOT do
- **The medical PC's refusal note** (the brief puts it in its own kit, after 04-Oct).
- **I did not call the live queue door** (decision 9).
- **I did not set the phone up.** That needs your login on the reception phone.
- **I did not touch** porders.py, portal.py, clinic_sso.py, tile_grants.json, finance_app.py, sanjeevni_approvals.py, darpan_kal.py,
  the crontab or the medical PC.

### Outside the brief, noticed
- **B-0018 may already be in Marg.** It is Yuvika, scanned 29-Sep with no number or amount read. Marg holds Yuvika bill 672 dated 28-Sep.
  The matcher cannot tell with nothing read, so by the brief's rule it is on Amir's list. B-0007 (09-Sep) has no Yuvika bill that close.
  Worth reception reading both papers before Amir uploads them: Scan ka kaam already says "manager isse theek karega" for no-digit scans.
- **The pay page** (`/finance/purchase/page/pay`) still carries S265's bank advice annexure, with full account numbers, for every medical
  login, Amir's included. S452 closed only the Excel file. Whether staff should see that annexure is the owner's call.
- **The 18 August supplier messages** wait for the phone's new key (the owner's step above).
- **S408's and S407's walks no longer match the live box.** The statement shelf has real files and the queue has live rows. A refresh would
  be a new kit, if they are to guard anything again.
- **S453 changed `finance_app.py` at 22:02:25 IST**, while this build was being prepared. It did not hold the build lock then: the lock was
  free at 22:02:20.
