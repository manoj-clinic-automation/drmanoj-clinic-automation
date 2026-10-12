# REPORT S533 — Amir's page rebuilt (kit S533_AMIR_DAY_PAGE, Kit 3 of D706)

**For the owner (12-Oct-2026, installed 05:48 IST — read from the installer's log):**

1. Amir's seven steps look the same, but every line on them now comes from one reading of the facts, so his card, his step-7 list and your English lines cannot disagree. Installed and read back on the live box; healthz 200.
2. This morning his card says **"Orthotic ke voucher: 1 baaki — board kholiye"** (voucher 29, ANKLE BINDER BAMBOO L, still to enter) and **"Scan hua bill Marg mein baaki: 1 — kholiye"** (a SHIVAAZ FORMULATIONS bill reception scanned on 03-10). No purchase bill is waiting for his tap (all 204 earlier answers carried over).
3. The two spellings are now Marg's own and verified by the 10-10 closing — **all 23 renames verified**. Nothing was asked of Amir.
4. The Yuvika goods tapped as arrived on 01-10: no scan of that bill exists on the box (every Yuvika scan is already matched to a Marg bill), so it reaches **your** Needs-you only: *"Goods tapped as arrived on 01-10 from YUVIKA SURGICALS: no bill scanned, nothing in Marg (11 days)"*. It is no longer on Amir's card.
5. One line for the chat to look at: your Needs-you also says *"Orthotics verified and renamed -- live orthotic ordering can start"* (the renames are all verified) while voucher 29 is still open.

---

## For the chat

### What ran, when (clock times read from `/root/deploy/kits/S533_install_.log` and the box)
- Build lock taken **05:41:48** IST by `S533_AMIR_DAY_PAGE`; `clinic-finance` restarted once at **05:48:40**; installer finished `S533_AMIR_DAY_PAGE: DONE` (log written 05:49).
- Order kept as §10: built in `_scratch\S533_AMIR_DAY_PAGE\` → `make_s533.py --print-to` against the four live files (read at their FROM pins) and the repository's DUTY_MAP → the walk on the server in DRY (`/tmp/s533kit`, two DRY runs: the first found 8 walk-side faults, fixed; the second **WALK_S533 GREEN (138 checks)**) → **published** (PUBLISH_ALL, origin HEAD 81ca81c; it carried the other chat's pending `S535_PUNCH_SOURCE_WATCH` too, as the charter expects) → kit folder copied by scp to `/root/deploy/kits/S533_AMIR_DAY_PAGE/` (SUMS.md5 9/9 OK) → installed (walk green again before placing) → this report → published again.
- **The pull (§10, R3-8) — said plainly:** the installer's own `git pull --ff-only` found "Already up to date": **another process pulled `/root/deploy/repo` at 05:43:44** (reflog), between my gate (05:41:48) and my data step (just before the 05:48:40 restart). So for about five minutes the live DUTY_MAP was v11 while `amir_bill_answer`, `purchase_bill.first_seen_day` and `amir_job.reopened_at` did not exist yet: `amir.bills_answer` / `amir.marg_jobs` read as errors (UNREAD on Aaj ka kaam, skipped by the console) in that window. Nothing was written by it; the data step closed the window. The map is at its v11 TO pin now and the repository's kit folder matches SUMS.md5.

### Live files FROM → TO (md5 read back on the box after placing)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/amir_day.py` (replaced whole) | f90df5b211c89dc8bdcd2671e163cf94 | **262b0b814ec2b840012cd1988e420097** |
| `/root/finance/stock_app.py` | 51620064e6849b02f0446b859a722638 | **c626a46acf371b3a767756dc35743d57** |
| `/root/finance/purchase_app.py` | c29050c18795a059e3cfbfae252efc21 | **147201dd288d291323023a764df3411e** |
| `/root/finance/stockmatch.py` | 4a2f9fcdfe969a0ca577c34536dbf9a2 | **10e30d28053aca3090e193502b67b1e0** |
| `/root/deploy/repo/claude_code_briefs/DUTY_MAP.json` | 7aa2f935677928e470454c355553210b (v10) | **69b8f56b17da263b932426b87a7abc1c** (v11) |
| `/root/deploy/repo/claude_code_briefs/DUTY_MAP.md` | 4888a228282d37133bb888e474d2d63c | **553398f3a21541e688d3f3c72e585748** |

Every placed file was byte-identical to the walk's NEW copy (`cmp`). The must-not-move list (item_alias 111a8e48, stock_amir.html 8dd65e64, stock_watch c960f6c8, qty_words 706db7cc, sanjeevni_approvals 792f4a9a, stock_hub.html a710a98a, finance_approvals.html b32da7ff, amir_salts, packs, supplier_msg, scan_register, porders, returns_kinds, reports_tile, aaj_seed, aaj_kaam, owner_console, stock_statement, finance_app, portal.py, tile_grants.json, spine_build, marg_read, spine_read, marg_take) and the crontab: unchanged across the install.

### Gates at install (charter 1b)
Spine passed 13/13 (last success 2026-10-11T23:50:41, built after the collector's newest take); the collector's `last_run.json` 1–2 min old (0 failed), newest take 18 h before (Amir's last visit 11-10). `AMIR_BILLS_FROM` in `clinic-finance`'s environment: **no** (the literal 2026-09-01 changes nothing).

### The walk (`walk_s533.py`; on scratch copies; NEW = the built files on a data-step copy, OLD = the box as it was; signed in through a walk-only portal secret and user store)
**WALK_S533 GREEN (138 checks)**, 15 controls red on the old files. The checks, condensed (full text in the installer's log):
- **10 greps:** every retired name (47, word-bounded) gone from the NEW finance folder and the portal, the kit's three comment lines aside — **RED control:** the OLD folder carries 126 hits. No .py reads `amir_step` / `amir_bill_disposition`. The new amir_day has no DELETE, no S494_JOBS, no rupee figure, no `stock_stage_event` write, no second salts door — **RED control:** the old one DELETEs on reopen, carries the rupee seed and the second door. `selftest_spine.py` SELFTEST OK (45 checks). After placing, the installer's grep over `/root/finance` and `/root/portal`: **GREP CLEAN (0 hits)**.
- **8/9 data step on copies:** clean; history copied; a second run writes nothing (no respelt, no copy, "already verified"); a closing lacking the spellings → each row skipped with its line; `_follow`'s spine alias rows carry the new spellings; two `respelt` events. **RED control:** the closing on the box does not verify the two rows under their old new_name (both stay `done`).
- **0 live state by key:** amir's medical role viewer, the owner's checker; root #1 stage A (7 of 8); events A verified + 3 rechecks (+ B verified after the spellings).
- **7 the map:** v11's three due_sql == `amir_day.DUTY_SQL` byte for byte; aaj_seed's REWRITE piece `AND b.bill_date >= '2026-09-01' AND` occurs once; `amir.marg_jobs` reads amir_day's `S494_OPEN`; each SQL runs after the schema step (schema-only copy: bills_answer (114, 2026-10-11) — before the history copy, as expected; full copy: (0, None) ×3). Staff eye on the busy copy: bills_answer 3, own_correction 1, salt_list 1, count_vouchers 1, marg_jobs 1 — each door_marker seen on its door as amir. `amir.arrival_bill_entry` not due, not unread on the owner's console; Aaj ka kaam's floored reads clean.
- **1 one read, one word** (states: empty day, busy day, a bad report, ready to close): Amir's step 7 prints every `hi`, the owner's `/finance/amir/day` the same `en` line, the visit summary's `left[]` and `steps[7].note` the same strings, Needs-you `Count #1: Stage A: 7 of 8 entered`; per request amir_stage 1, `_s521_stage_words` 1, `scans_for_amir` 1, the page's own assets.db opening ≤ 1. **RED control:** with a one-time category job not yet shown the old file asked amir_stage 2× on a step and 2× on Needs-you (new: 1 and 1). *(The brief's "old: 3–4" does not occur on today's data: on a plain step the old file read it once; the extra reads happen only in that job state and when the root has no open voucher.)*
- **2 append-only:** step 1 twice → two rows, the second replaces the first, the summary says "no punch" (**RED:** old overwrote, 1 row); a bill answered twice → two rows, claim raised then settled, audited (**RED:** old 1 row); close / reopen / close → three step-7 rows chained, a fourth tap writes nothing, `amir_day.closed_at` never written (**RED:** old reopen DELETEs the step-7 row, 1 → 0). Self-clear: (i) `marg_matches` with a system row replacing his, his row untouched, audited, a second read idle; (i-b) `marg_changed`; the same export not later → not cleared; (ii) `left_export`; the R1-1 rule control (a bill in the live September export, October present) → NOT cleared; (iii) `answered ok`, no system row (**RED:** the old self-clear rewrote his row `self/amir` → `ok/S444 auto`).
- **3 bills:** the four states by key; a later push moves `bw_md5` and keeps the first sight, a new bill's first sight is its export's day; the three counts 2 · 1 · 1 equal on step 5, step 7 and the owner's page; no raw ISO date; the paper line "Marg (export 12-10 07:30): ₹1,482 · Kaagaz (scan 10-10): ₹1,482 · mil gaya" (**RED R2-25:** the old list put the bill first seen yesterday under *today*).
- **4 gate:** nothing of his on the card → step 6 done without a tap, step 7 ready while the salt list is owed; owner reads "OPEN — ready to close" / "not holding: SALT WISE ITEM LIST not received" (**RED:** old lists "salt and name list not ticked", not ready).
- **5 D712:** an arrival 5 days old with no scan → no *Maal aa gaya* on his card, one owner line; a held scan of that vendor → no line; a listed one within the grace → no line, one before it → the line; card N == step 2's heading N in both modes, id `scans` (**RED:** old card says *Maal aa gaya, Marg mein bill baaki*).
- **6 salt:** one rule (a VERIFIED list received after the tick → not owed; **RED:** old rule A still owed by the Marg stamp while rule B was not); the card once on step 6, step 7, the owner's day and amir_salts' page; "2 visit" / "aaj ke tick ke baad"; the hub's four keys; the salts door only with open rows (**RED:** old step 6 says the sentence twice).
- **8 stockmatch c4:** B present 21/23 → "2 of 23 renames not yet verified (2 ticked, 0 not yet seen in Marg)", `renames_wait_stage_a` False; no 'A verified' event (removed on the walk's copy) → "renames wait for stage A — the orthotic vouchers' proof", True; hub, statement, page 200 (**RED:** old still "2 of 23 … not yet verified").
- **10/11 not broken:** a second identical GET writes nothing; Needs-you shapes; visit summary 17 top keys = old, literals kept, refused to amir; `/finance/amir/day` 08-10 CLOSED at 09:47, 22-09 reopened, a day with no rows OPEN; amir_salts 200; packs' seen → 303 /finance/amir; healthz `S533_AMIR_DAY_PAGE`; the jobs card byte-equal but the category heading (new reads the proved label **'ORTHOTICS'**, the old typed *ORTHOTIC*); light board and hub JSON byte-equal old vs new (stamps dropped; the one key 5.2 adds, `renames_wait_stage_a`, aside).
- **12/13 words and weight:** steps 1–7 as amir in both entry modes — no forbidden word, every *kholiye* a door's verb, exemptions listed per page (Signed in:, biometric punch, Download, Save kijiye, his two reason labels, SALT WISE ITEM LIST, Text ya Excel); every page under 100 KB (7.3–12.5 KB) (**RED:** the old pages carry 11 hits — jaanch, rows, server, wapas, Excel). Times (scratch, NEW / OLD): step 1 **4381 ms** / 4122 ms (the cold first read: the stage's report build, the same in the old file), steps 2–7 545–622 ms / 548–831 ms; Needs-you 5408 / 5262 ms.

### The data step on the live database (its lines)
```
1 first_seen_day filled on 579 bill(s) (1 of them from the bill date: no bill-wise export named)
1 first sight for the 579 bills already on the box is the day of the newest export that carried them -- the only day the data held; from today on it is the true first sight
2 amir_self_wait.bill_id: 1 matched, 0 unmatched
3 amir_step_log: 42 step row(s) copied + 1 reopen row(s)      (the brief expected 38 + 1 on the 11-Oct copy; 11-Oct's visit added 4)
3 a day reopened and closed again keeps its close row only; its reopen stays in amir_day.reopened_at: 2026-09-17
4 amir_bill_answer: 204 copied, 0 with no single bill; all 'ok'   (the brief expected 193; 11-Oct added 11)
6 L S BELT CONT GRAY UNISON XXX: L S BELT 3XL CONT GRAY UNISON -> L S BELT XXXL CONT GRAY UNISO (respelt; section inherited Orthotics; spine alias on item 185)
6 TYNOR WRIST SPLINT LF M ELAS: TYNOR WRIST SPL LF M ELASTIC -> TYNOR WRIST SPL LF M ELAS T (respelt; section inherited Orthotics; spine alias on item 342)
6 sight_closing (closing captured 2026-10-11T10:35:20, printed for 10-10, 382 names, the archive .xls): both verified; renames now 23 of 23
7 amir.salt_owed_days' note in visit days; S444 settings 0 new
duty amir.bills_answer (0, None) · amir.own_correction (0, None) · amir.salt_list (0, None)
committed
```

### The install-day state (charter 7), printed by the installer
- **Before** (old files): card *Marg sudhar — abhi baaki · Orthotic ke voucher: 1 baaki — board kholiye · Naam badal diye ✓ · Maal aa gaya, Marg mein bill baaki: 1 — kholiye*; B 21 of 23.
- **After** (new files): stage A 7 of 8 (voucher 29 open, no orthotic line pending), B 23/23 verified; bills: *Aaj aaye bill 0 · Pichhle dinon ke baaki 0 · Flag kiye hue 0*, his corrections waiting 0 (§4.3: no bill pending, so the back-fill's today/carry split shows nothing on install day); scans: 1 listed (SHIVAAZ FORMULATIONS, scanned 03-10), 10 held for reception (5 near-match, 3 supplier unread, 1 second scan, 1 unread paper).
  **Amir's card:** *Orthotic ke voucher: 1 baaki — board kholiye* | *Scan hua bill Marg mein baaki: 1 — kholiye*. **Step 7 holding:** Bill daalne ki pushti baaki hai; the two reports *abhi nikaali nahi gayi*; *Marg sudhar: 'Aaj ke item theek kar diye' dabana baaki*; **not holding:** the voucher line. **Owner's day:** "OPEN — holding: bills not confirmed entered; Item-detail purchase report not received; Bill-wise purchase report not received; Marg corrections not confirmed / not holding: Stage A: 7 of 8 entered".
  **Needs-you (Amir's part):** Count #1: Stage A: 7 of 8 entered · Orthotics verified and renamed -- live orthotic ordering can start (count #1, 12-10) · Goods tapped as arrived on 01-10 from YUVIKA SURGICALS (D712) · three vendor bank-detail lines (S494, unchanged) · Sarvam ×2 · 2 unrecognised refused files.
- **§4.4 differs from the brief:** the brief expected the Yuvika 01-10 bill as *scanned, not in Marg* (the card's D712 count). The box holds no unmatched Yuvika scan (its scans are matched to Marg bills of 18-09, 28-09 and 07-10), so the bill sits on the owner's D712 line, not on Amir's card or step 2, and not on step 5 (Marg's export does not carry it). The card's count of 1 is the Shivaaz scan.
- **Read-back** (after the restart, through a walk-only portal session — the owner's day page, the visit summary `kit S533_AMIR_DAY_PAGE`, Needs-you 200 / 22 lines; Amir's steps 1, 6, 7 200 at 6.3–6.8 KB): **READ_BACK OK**. Amir's step GETs ran the page's own settle (nothing to settle).

### Backups, restart
`/root/finance/{amir_day,stock_app,purchase_app,stockmatch}.py.bak_S533_<from8>` (read back = FROM); `/root/finance/finance.db.bak_S533_20261012_054148` (backup API, 35,840,000 bytes). Restarted `clinic-finance` only, once.

### Charter
- **Retired:** listed in the kit README (rule A of the salt list; the S444/S446/S452/S454 shims and dead code; S488's copies; `S494_JOBS` and `s494_seed_jobs`; `MARK_KIT` and the S243/S246 tags; the DELETE on reopen; the INSERT OR REPLACE writes; the second salts door; the arrival line on his card; `AMIR_BILLS_FROM`; `stock_app.amir_duties`, `_s444_renames`, `_S444_RENAMES_CACHE`; `purchase_app.scans_to_enter`). Proven by the greps (walk and live).
- **Left for later:** rung 4b (F-862), S486 Part A/B, F-802, the five `reports.*` settings, F-726a, F-777, F-794; the seed line `amir.arrival_bill_entry` in `aaj_seed.PEOPLE["amir"]` (parent) can be turned off — it now reads never-due.
- **Charter: left out** — nothing the brief ordered was left out.
- **Product calls kept:** the two dates typed on step 3; *Din phir se kholiye* (recorded as a row).
- **Dependency state at install:** spine passed 13/13 (built 2026-10-11 23:50, after the newest take); collector alive (last run minutes before, 0 failed).

### Decisions made by the builder (named)
1. `amir.marg_jobs`' due_sql now reads the same "said" rule as the card (a job the category list reopens is due again) — §2.3 changes the reopen; leaving v10's SQL would have split the map from the page (charter 13). The walk asserts the map carries `amir_day.S494_OPEN`.
2. DUTY_MAP.md rows naming the retired tables (`amir_step`, `amir_bill_disposition`, `amir_day.closed_at`) and the old held-scan words re-worded beside the rows the brief listed.
3. The collector's liveness is `marg_ingest/last_run.json` (the job runs every 5 minutes; its `logs/ingest.log` is 4 days old, so it cannot be the signal) plus a newest take within 72 hours (S528's 24 hours passes today at 18 h but would refuse after any two-day gap between Amir's visits); the spine must be built after the newest take.
4. Step 7's not-ready screen prints the three bill counts too (§2.4 names them on step 7); the visit summary's `bills` adds `flagged` and `waiting` (nested; all top-level keys kept).
5. Step 1 "no punch" reads `not done` in the visit summary with the note "no punch -- he tapped 'Punch nahi ho paya' HH:MM"; "punched" reads `done`.
6. The S285 warning names the item before the brief's statement ("<item>: yeh item pehle <usual> se aata tha (N bill); is bill mein <supplier> hai.").

### Seen, not touched (for the chat)
- **"Orthotics verified and renamed -- live orthotic ordering can start"** now shows on Needs-you (kept line, 2371–2373: it fires on B verified within 2 days) while stage A has voucher 29 open — B was verified today by the data step's closing. Whether it should wait for stage A is the chat's call.
- **Aaj ka kaam is switched off** on the box (`/finance/aaj/api/list` answers `{"ok":…, "error":"off"}`); the walk proved the floored reads through `aaj_kaam.build_all` instead.
- The stage's first read in a fresh process takes ~4.4 s (the report build; the old file the same) — over charter 14's 2 s on the first page of a cold process only; warm pages 0.55–0.62 s. Needs-you ~5.4 s (old 5.3 s).
- item_alias `_follow` closes only an OPEN `marg_task` rename (the S229 tasks were closed at tick time, so their answer keeps the old spelling) and leaves the old spelling's spine alias active beside the new one.
- The brief's other "seen, not touched" items stand as listed in the README (`reports_tile._salt_row`, `scans_for_amir`'s write on read, `amir_view`'s Spine never closed, `_s452_marg_rates`' mirror write, `_report_cached` 600 s, S524's release-on-any-read, `_newest_root` vs `_s446_root`, `#rest` with no target, A18, the 17-09 reopen in `amir_day.reopened_at`).
- Something outside the brief: a `git pull` of `/root/deploy/repo` ran at 05:43:44 while this kit held the build lock (not from this installer) — see "The pull" above.

### Undo
Put back the four `.bak_S533_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. The new tables and columns stay (the old files never read them); answers Amir gives after the install live only in `amir_bill_answer` / `amir_step_log` — an undo should be followed by a copy-back step if he has tapped. The spellings' reverse and the database backup are in the kit README; the backup is used only if the chat orders the data change reversed.
