# REPORT S587_MORNING_FLOW — installed 18-Oct-2026, 17:56 IST

## For the owner

1. **Shavez's closing stock is now used whichever date he prints on it.** A closing printed as on today and taken before the first sale counts as the start of that day once the system has checked it item by item against that day's sale report and Amir's purchase export. The check ran on the eight such closings since 1-Oct: six are accepted and in use (04-10 10:22, 08-10 09:54, 09-10 09:48 twice, 15-10 10:05 and 10:22), one was set aside because a sale came before it (01-10 21:39, an evening print), and today's 09:37 closing is waiting for tomorrow morning's sale report and Amir's next export — it is never used on its own day.
2. **Your hub now says, for the four items Amir corrected this morning** (KT ROS DT, VINBACTUM DS, FOLITRAX 15 MG TAB, OSTOVAXL DM): *"Amir marked it done 18-10 09:2x — judged on the next closing taken after it"* instead of calling them wrong. The stage line reads *"2 items Amir marked done after Marg's closing of 16-10-2026 — judged on the next closing taken after it"*.
3. **Amir's purchase export covers until his next visit**, and a voucher that agrees with Marg is called right at once; only a disagreement waits for the purchase cover.
4. **Amir's page:** the banner now reads *1 Punch · 2 Bill entry · 3 Marg sudhar · 4 Export · 5 Check · 6 Bills · 7 Band*. If he enters a bill after exporting, a red line says *"Purchase report dobara nikaaliye — bill entry export ke baad hui hai"* and the day does not close until a fresh export. His other words are unchanged.
5. **Two new settings on your "Counts & watch" card:** the start-of-day rule (on) and how many unexplained item changes such a closing may carry (3). The stray column heading on the stock-now page (F-936) is fixed.
6. It is installed and working: healthz 200, every page answering, the service restarted once at 17:56:03 IST.

## For the chat

### Files, FROM → TO (read back on the box after placing, 17:56 IST)

| file | FROM | TO |
|---|---|---|
| /root/finance/stock_figure.py | 72b9135ab00db0af2fe8e54091147bb5 | 92367a196b360f0cded4cda6a5ded700 |
| /root/finance/shelf_figure.py | 14ef2c24e272ae8ea684615ae82b6cb5 | 23b2394a7a10a99ff0c30121087813f1 |
| /root/finance/stock_app.py | 1883807d7c0872b805f6101e92206878 | 4f73d0b02a167289d9439af7a35b5fa0 |
| /root/finance/amir_day.py | 3deca3b95380165d81ae4a8406a53d75 | 3af992d9e6b6c6050b1427e34757ca78 |
| /root/finance/stock_watch.py | 555202ce50b8df0b5111b5c56952efda | c5f3ce21a785c45df58f21932cf920e7 |
| /root/finance/stock_now.html | ff415eb22ee1ad94a95f2c87365341a3 | 9a840af4c4e0c39773e83625a14e421a |

Read-only pins printed at the open and unmoved: loss_piles 2b9023fd, stockmatch 623cb6f1, spine/spine_build e3d3ed85, spine/selftest_spine 7d0edb4a, spine/spine_read 712a1e4e, item_alias 111a8e48, reports_tile 535b5790, qty_words 706db7cc, DUTY_MAP.json 891defd8. Proved unmoved by the installer: finance_app, purchase_app, order_rules, porders_s454, portal.py, tile_grants.json, the crontab, spine.db's schema (a66309303c25178a291ada6fb539fbe5 before and after — no table added to the spine). 50 anchored edits, each anchor exactly once; compiled on both pythons.

### Two placements — the first undone (said plainly)

- **17:48:34** lock taken; **17:50:15** the six files placed and `clinic-finance` restarted; verify-start wrote the first verdicts (eight rows, below). The state AFTER showed the owner's stage line falling back to S488's *"waiting for our own figure for that day"* for lots whose only unseen rows are `pending_fix` — wrong text (charter 8), produced by F-933 itself. I added the missing English in the kit (`_s524_verdict` says `why='pending_fix'` with the judged closing's day; `_s521_stage_words.fix_en`), re-ran both walks locally (36/36 red on the old files; 105 checks, 68 controls green on the new).
- **17:54:17** the six `.bak_S587` files put back byte-identically (md5s read back = FROM), one restart, healthz 200 (`DOCTOR_AUTO_OFF` around it). The one journal line matching "Error" since then is gunicorn's normal `Worker was sent SIGTERM` at that restart.
- **17:54:21** the amended kit's installer: pins exact (the files were back at FROM), the spine 13/13 and 3 min old, both walks green on the box, backups, **17:56:03** placed and restarted, healthz 200, pages 302, journal clean, verify-start (the record already held the seven final verdicts; the pending one re-checked), state AFTER green. The kit in the repository is the amended one, byte-identical to what ran (SUMS checked on the box).

### The walk on the box (the amended kit, 17:54 run)

`WALK OK S587: 105 checks, 68 controls green on the new files` · negative control: `every control red on the old files (36)`. All 15 sections green; the staff screens word for word except the banner's order and *"Step N of 7"* (set apart), the stage's proof day on Darpan's state JSON (16-10 → 18-10, the accepted start capture being the newest try) and the owner's pages.

**Control 1 (the proof identical where nothing changed):** 198 items, old → new: 194 proven / 4 changed, every one named — FOLITRAX 15 MG TAB, KT ROS DT, OSTOVAXL DM, VINBACTUM DS: `wrong → unseen/pending_fix` (F-933, his corrections 18-10 09:23–09:25 after the judged 17-10 09:20 capture). 0 unexplained.

**Control 2 (the real 18-10 09:37 capture) verbatim:**
```
pending / sale_short with 18-10's sale report absent (never set aside)
pending / pur_short with the sale report in but no purchase export after the 09:35 tap (R1-B3)
VERDICT of the real 18-10 09:37 capture on this copy (18-10 sale report in, a purchase export after the 09:35 tap, the same bills): accepted; keys 372, excluded 47, unexplained 0; the previous verified capture 7f4d5832 2026-10-17T09:20:35
excluded by cause: {'bill_new': 39, 'consume': 5, 'fix': 4, 'purchase': 38, 'vouchers': 0}
the four 'fix:' items among the excluded: ['FOLITRAX 15 MG TAB', 'KT ROS DT', 'OSTOVAXL DM', 'VINBACTUM DS']
purchases dated 18-10 excluded: 38 key(s); bills first seen on or after the previous capture's day: 39 key(s); the consumption list: 5; vouchers in the window: 0
deciding keys -- a sale before it: []     deciding keys -- unexplained: []
excluded keys that moved (the morning's known work): APRO SYP +6, ARSEODEO +120, AXIMAL 200 +390, BIO D3 MAX +300, CALFLIP CQ +240, CCM +5, CHEXID D +200, CLAVICAL BRACE M UNISON +1, COVCAINE GEL SYP +12, DEFVAX 6 +240, DOLONEX 2 ML INJ +77, FENARIC T4 TAB +100, FERONES HD +300, FLORA BC CAP +120, FOLITRAX 15 MG TAB -6, GEMCAL XT TABLETS +150
```
No 18-10 sale lines exist yet (the report lands 19-10 morning): the walk's reach is synthetic (a SALE_BILLWISE export row and a purchase export stamped 09:45 on the copies). The live verdict is the server's tomorrow.

**Control 8 (visit cover, the real days, the reach as each day ended) verbatim:**
```
02-10 taken 03-10 07:25 -> end 02-10: cover c (visit 01-10, last bill-entry tap 08:57:26, export 09:00:57) | old rule (a only): False
04-10 taken 04-10 10:22 START -> end 03-10: cover c (visit 04-10, tap 10:10:20, export 10:11:47) | old: False
05-10 / 06-10 x2 (taken 06-10 09:46, 07-10 09:39): cover c (visit 04-10, export 05-10 07:59:55) | old: False
07-10 taken 08-10 06:00: cover a | old: True
08-10 taken 08-10 09:54 START -> end 07-10: cover None (the 09:48 re-tap after the 09:03 exports) | old: False
09-10 x2 START, 09-10 taken 10-10 09:01: cover None | old: False
10-10 taken 11-10 07:11: cover a | old: True;  10-10 taken 11-10 09:39 / 09:52 / 10:35, 12-10, 13-10: cover None | old: False
15-10 10:05 START, 15-10 10:22 START -> end 14-10: cover None (the re-taps 10:05 / 10:06 came after the 09:10 export) | old: False
15-10 taken 16-10 05:17: cover a | old: True
16-10 taken 17-10 09:20 -> end 16-10: cover c (visit 15-10, last tap 15-10 10:06:54, export 16-10 13:04:27, identical to the visit's own export) | old: False
18-10 taken 18-10 09:37 START -> end 17-10: cover None (tap 09:35 after the 09:25 / 09:27 exports) | old: False
a closing on 16-10 14:00 (end 15-10): {'clause': 'c', 'visit': '2026-10-15', 't2': '2026-10-15 10:06:54', 'at': '2026-10-16 13:04:27', 'identical': True}
tryable() of the 17-10 closing with the reach as 17-10 ended: the new rule (True, ''), the old rule (reach only) False; with con None (False, 'pur')
```

**Control 9 / 10:** a voucher agreeing on the 09:37 capture (purchase cover withdrawn) → proven at once; a disagreeing one `pending_reach` (why reach_pur) until N is inside both reaches, then `wrong`; with a `fix:` row done 18-10 10:00 → `pending_fix`, the owner's line *"ALCOXIB 120: Amir marked it done 18-10 10:00 — judged on the next closing taken after it"*, the stage's English *"1 item Amir marked done after Marg's closing of 18-10-2026 — judged on the next closing taken after it"*, Amir's card unchanged old vs new; with a synthetic 22:00 capture after his tap → judged normally (wrong again). **Controls 11–12:** banner, *Step 3 of 7* on /step/6, *Step 4 of 7* on /step/3, the export screen word for word, taps on positions 2/3/4 write ids 2/6/3, the redirect by position; the gate line, the red band on position 6 (none on 2), the owner's *"re-export due since hh:mm"*, cleared by a step-3 tap or a landed VERIFIED export. **Control 15:** selftest_spine 50 checks OK; no spine write by any new code.

### The first verdicts written on the live database (`stock_figure.py verify-start`, 17:50:18 IST; the 09:37 row re-checked 17:56:07)

```
681d7975 printed 01-10 taken 01-10 21:39:02 -> end of 30-09: set_aside / sale_before (keys 363, excluded 138, unexplained 0; the previous capture 86075074, taken 30-09 at 22:10)
   a sale came before it: CALBERT K27 -10 (sold 10), COCYP T SYP -1, DOLOGESIC SP -20, DYTOR 10 -7, NAPROVIN D -10, RIFAVAX 550 -14, ROVIC DSR -20, TAPEASE NS SPRAY -1
3193e01b printed 04-10 taken 04-10 10:22:10 -> end of 03-10: accepted (keys 364, excluded 150 [bill_new 134, consume 5, vouchers 20], unexplained 0; the previous capture becf9008, taken 03-10 at 07:25)
46c49e84 printed 08-10 taken 08-10 09:54:36 -> end of 07-10: accepted (keys 367, excluded 141, unexplained 0; the previous capture 63b8e3fb, taken 08-10 at 06:00)
9d44ce5d printed 09-10 taken 09-10 09:48:02 -> end of 08-10: accepted (keys 366, excluded 141, unexplained 0; prev 46c49e84)
11e8564c printed 09-10 taken 09-10 09:48:41 -> end of 08-10: accepted (keys 366, excluded 141, unexplained 0; prev 9d44ce5d)
4ee1b8ca printed 15-10 taken 15-10 10:05:40 -> end of 14-10: accepted (keys 370, excluded 182 [bill_new 56, consume 5, purchase 23, vouchers 167], unexplained 2: XGESIC LA -15, ZERODOL P -1; the previous capture c21b2597, taken 14-10 at 09:23)
07713bac printed 15-10 taken 15-10 10:22:38 -> end of 14-10: accepted (keys 370, excluded 61, unexplained 0; prev 4ee1b8ca)
6d718060 printed 18-10 taken 18-10 09:37:08 -> end of 17-10: pending / sale_short (judged when 18-10's sale report and a purchase export after the 09:35 tap are in)
```
Live effect today: `capture_at(today)` stays the 17-10 09:20 capture (the 09:37 is pending); `capture_for(14-10)` is now the 15-10 10:22 start capture (no other capture stood for 14-10); 07-10 and 08-10 are now stood for by the accepted morning captures (newest by stamp — the morning's Marg work in them). The stage: `proof state export why pending_fix; 0 wrong rows, 3 lots waiting`; before: `4 wrong rows`.

### Backups, restarts, lock

- `finance.db.bak_S587_20261018_174834` (40,263,680 bytes) and `finance.db.bak_S587_20261018_175421` (40,325,120 bytes), both by the backup API; `<file>.bak_S587_<from8>` for the six files (= FROM, used once for the undo at 17:54).
- `clinic-finance` restarted at 17:50:15 (first placement), 17:54:17 (undo), 17:56:03 (final). Nothing else restarted.
- The build lock `/root/deploy/.claude_code_build.lock` taken 17:48:34 by S587, released after this report; `/tmp/s587*` removed.

### Not done, and findings outside the brief

- **Not done:** no DUTY_MAP.json change (no duty added/moved/removed; the door is the route id). DUTY_MAP.md's purchase-export row wording updated (positions since S587, the re-export line). No data step beyond the record table and its first verdicts.
- **Finding — `purchase_bill.first_seen_day` backfill:** S533 set `first_seen_day` on 11-10 to the export day of each bill's then bill-wise export, so on the start captures before 11-10 the `bill_new` exclusion covers 133–136 keys (most purchased items) — those verifications were lenient by construction. From 11-10 on the exclusion is right-sized (39–56 keys). For the chat's register.
- **Finding — the brief's "16 keys"** of the visit summary are 17 on the live JSON; the walk asserts the key set unchanged.
- **Finding — the stage's `pending_fix` count** in the English sentence is the first waiting lot's (2 items for lot 3); the four owner lines cover all lots.
- **Permissions:** one PowerShell command (`Remove-Item -Recurse -Force` on my own scratch folder) was refused here; I used python for scratch cleanup instead. A stray empty file I wrote by mistake to `D:\Users\placeholder_ignore.txt` was removed at once.

### Charter

- **Retired:** `_s524_closings` / `close_of` by printed day; `early_bill`; the single purchase-cover clause inside `tryable`; `_s524_table`'s first-or-newest tries.
- **Left (named):** the spine's own build and gate (a start capture is verified beside the spine); an accepted start capture is not re-judged when the nightly rebuild moves `bal()` under it (`built` recorded); amir_day Kit 3; the D712 gap; `porders.detect_supplies` / `order_rules._s470_arrivals`.
- **Seen, not touched:** `shelf_figure.record_gaps` / `rejudge`; `_s488_ending` / `_s488_wait_line`; the sealed findings' frozen words; `stockmatch.KIT` (S502).
- **Dependency state at install:** the spine 13/13, 3 min old; `count.start_capture` on, `count.start_unexplained_max` 3 (defaults, no rows); count #1 at stage C, lot 3, the four corrected items `pending_fix`; Amir's next visit day unknown.
