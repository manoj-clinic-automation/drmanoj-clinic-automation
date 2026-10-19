# REPORT S602_CUTOFF_LINE_AND_F943 — installed 19-Oct-2026, 19:56 IST

## For the owner

1. **Darpan's order tab now carries one grey line under its heading:** *"Marg में खरीद 18-10 के बिल तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में नहीं है"*. The date is read from the spine each time the tab is opened (today it says 18-10: the newest purchase-bill date Marg's purchases hold, read from the live files after placing) and moves by itself when Amir's next purchase export lands. It shows whenever the heading shows. The tab is not in use today (ordering is on Marg's sheet), so Darpan sees it the day the tab is switched on, or when he opens the tab to read it.
2. **The nightly stock witness no longer tries to write.** Run once on the live box after placing (19:56:47 IST, read-only, exactly as the night job runs it): no complaint line, the file written. Tonight's 23:58 run is its first real night.
3. **Nothing else changed:** every staff page (Darpan, reception, Amir, Shavez) and your pages read the same as before, every stock figure is the same, no order and no verdict moved.
4. **Installed and working:** `clinic-finance` restarted once at 19:56:43 IST, healthz 200, every page answering.

## For the chat

### Files, FROM → TO (read back on the box after placing, 19:56 IST; re-read 19:57:28 IST)

| file | FROM | TO |
|---|---|---|
| /root/finance/darpan_kal.py | 325d988c61e1c7408a2a4b687a4822bb | b28d7342469814e85129602ea35a7423 |
| /root/finance/darpan_kal.html | 75d5a5b51b017abd5ad3aa408609a1ff | 7c9391912cf62972a8d9e3a41e9e2ebb |
| /root/finance/spine/spine_read.py | 827b00402add288d028c910128084b90 | 10697b3869218151a75268e2259248d7 |
| /root/finance/stock_figure.py | cb577821d9e1eb40110312b4331df9ef | 51e1fc63ab3fb1ac21170cb214f15b6b |

Read-only pins printed at the open and unmoved: order_rules 8d078dbe, stock_watch 299c3ef7, order_sheet 1f1e85c1, porders e5a5c4d4, porders_s454 40f1755a, shelf_figure 23b2394a, stock_app 4f73d0b0, amir_day 3af992d9, spine/spine_build e3d3ed85. Proved unmoved by the installer: finance_app, portal.py, tile_grants.json, the crontab (84 lines, `# S577_WITNESS` once: `58 23 * * * … stock_figure.py witness >> …/stock_figure_witness.log 2>&1`), spine.db's schema (a66309303c25178a291ada6fb539fbe5 before and after). 11 anchored edits, each anchor exactly once; compiled on both pythons; the built html green under the JS check. The spine at install: passed 13/13, last success 2026-10-19T19:50:54+05:30 (4 min old). Settings: `order.source` marg_sheet, `order.darpan_list_time` 09:30. No DDL, no new table, no new setting, no data step; `DUTY_MAP` untouched (no duty added, moved or removed).

**F-510, the clocks read, not estimated:** `/root/finance/spine/stock_figure_witness.log` (the crontab's `2>&1` target) **did not exist** at the open and still does not — the 23:58 job has not run since S594's install (19-Oct morning); the first real night is tonight. The newest witness file at the open was `stock_figure_witness_Mon.txt`, mtime 2026-10-19 08:27:48, header `stock_figure witness  2026-10-19T08:27:48 IST  (kit S587_MORNING_FLOW; …)` — S594's daytime rehearsal. The brief's "one stderr line a night" was therefore seen only at that rehearsal, never yet by the night job; the OLD-files walk reproduced the line on this box (below).

### The install (one run, one placement)

- **19:47, 19:49, 19:52, 19:54 IST** four DRY runs (every gate, the scratch sides, both walks, S598's walk twice). The first three found faults in the kit's own walk, fixed before anything was placed: (1) the OLD anchor `'</div>':'')+'</div>';` is consumed by the fragment (its tail is the Hindi string's `</div>`), so the walk now asserts the anchor count 0 and the heading's closing `</div>':'')+'</div>';` once; (2) the walk's proposal row collided with today's real proposal for that supplier (`UNIQUE(day, supplier_norm, kind)` — 98 proposals on the copy) — it now picks a live rule with no fixed proposal today (DAANSHI PHARMA, id 99); (3) the owner's `api/order` carries `editable: true` server-side — the browser alone makes his view read-only (`ro = j.me === "owner"`, line 418), so the control asserts `me: owner` and the key. The fourth DRY found the installer's S598-walk gate too strict (below) and was green end to end.
- **19:54:56** the build lock taken by S602; pins exact; the state BEFORE and as the NEW files read the same copy; backups; the four files placed by rename in one command (md5 read back = the TO pins, byte-identical to the walked files); **19:56:43** `clinic-finance` restarted — healthz 200; /finance/darpan/kal, its api/order, /porders, /stockmatch, /amir, /reports/aaj all 302 without a login (the gate, expected); journal clean (0 error lines since the restart, re-read 19:57); the state AFTER; the witness once on live (below); nothing else moved; `DOCTOR_AUTO_OFF` removed. DONE.
- The kit ran from `/tmp/s602kit` (SUMS checked on the box); the kit in the repository is the same bytes (SUMS re-checked in the clone after the publish, below).

### The walk on the box (the install run, 19:55)

`WALK OK S602: 58 checks, 20 controls green on the new files` · negative control: `every control red on the old files (18)` (two controls exist only against `--old-dump`, which the OLD run has none of). Every section green.

**Control 4 (first — the pages and APIs, no DOM rendered):** Darpan's `/finance/darpan/kal` (40988 bytes) and `api/day`, reception's `/finance/porders` and `/porders/s454/order`, Amir's `/finance/amir` and steps 1–7, Shavez's `/reports/aaj`, the owner's `/stock/api/now` (the stock proof, 99107 bytes) and `/sanjeevni/api/needs-you`: all 200, **every dump byte-equal to the OLD files' dump (0 differ)**; `api/order` (Darpan's and the owner's) byte-equal after `purchase_upto` is masked; `purchase_upto` absent on OLD, `2026-10-18` on NEW for both logins.

**Control 1 verbatim:**
```
direct SQL on the spine copy: MAX(date) of PURCHASE bills dated <= today = 2026-10-18; purchases_upto() = 2026-10-18
ok   C: spine_read.purchases_upto() on the copy equals the direct MAX(date) (an ISO day)
ok   C: on a spine copy with sp_purchase_bill emptied purchases_upto() is None (MAX over an empty table: one row, d None)
a synthetic bill dated 2026-10-20 on a second copy: raw MAX(date) 2026-10-20; purchases_upto() 2026-10-18
ok   C: a synthetic PURCHASE bill dated tomorrow leaves purchases_upto() unchanged (the future date ignored; raw MAX moved)
```

**Control 2 verbatim:**
```
payload keys: ['all_pakka', 'date', 'editable', 'frozen', 'list_time', 'me', 'n_lines', 'n_suppliers', 'ok', 'opened', 'order_day_names', 'purchase_upto', 'source', 'suppliers', 'yesterday', 'yesterday_date']
purchase_upto = 2026-10-18; spine handles opened by the payload: 1, closed after it: 1
ok   C: _s485_payload carries purchase_upto equal to control 1's day
ok   C: the payload opened a fresh spine handle for the read and CLOSED it (R1-B2: 1 opened, 1 closed)
ok   C: every other key of the payload equals the OLD files' payload, key by key (R1-C7: the one new key masked)
ok   the payload opened exactly one more spine handle than on the OLD files (1 vs 0)
with SPINE_DB at a missing file: purchase_upto = None; the rest equal: True
ok   C: with SPINE_DB pointed at a missing file the payload still answers, purchase_upto None and every other key equal (fail-soft, never a stand-in)
```

**Control 3 verbatim:**
```
the fragment occurs 1 time(s) at line 427; the OLD anchor "'</div>':'')+'</div>';" occurs 0 time(s) (consumed by the fragment on NEW), the heading's closing "</div>':'')+'</div>';" 1 time(s); the file has 478 lines
ok   C: (a) the exact fragment is in the built html exactly once, at line 427, inside renderOrder, as the tail of the heading's concatenation (the OLD anchor consumed, the heading's closing once)
the <script> block: 387 lines from line 89; tokenizer GREEN {'strings': 818, 'regex': 7, 'comments': 28, 'templates': 0}
ok   the page's one <script> block passes the Python tokenizer check (strings closed, brackets balanced; Node is not on the box)
ok   the checker can go red: the same block with one quote of the fragment dropped is RED (unclosed regex literal at line 339)
ok   the html has the same number of lines as the OLD file (one line changed, none added)
the walk's proposal: DAANSHI PHARMA (DAANSHI PHARMA, kind fixed, id 99) beside today's real proposals
Darpan's api/order (200): opened True, source darpan, suppliers ['A.A. Pharmaceuticals', 'Daanshi', 'Deepam', 'Drug Deal', 'Gunina', 'Janta', 'Kedar', 'L.K. Drug', 'Mannat', 'Shivaaz', 'Shraddha', 'Verma'], purchase_upto 2026-10-18; the owner's (200): me owner, editable True, purchase_upto 2026-10-18
ok   C: (b) /finance/darpan/kal/api/order as darpan with the list OPEN and a supplier present (the walk's W602 proposal, source darpan, ORDER_CLOCK 10:00) carries purchase_upto = control 1's day
ok   C: (b) the owner's call of the same API carries it too (me owner; his view is read-only in the browser: ro = j.me === 'owner')
ok   order.source restored on the copy
```
**The JS check:** Node is not on the box (`which node` empty) and not on this PC either, so the check is a Python tokenizer over the page's one `<script>` block (comments and regex literals skipped; every string closed on its line; `()[]{}` balanced) — green on the built file and on the OLD file, red with one quote of the fragment dropped. Not a parser: it proves quoting and bracketing, not JS semantics; the fragment's shape is the mock-up's and R1-C6's (the leading `+`, `esc` in scope).

**Control 5 (F-943) verbatim:**
```
the start capture: printed 2026-10-18 taken 2026-10-18T09:37:08 (6d718060); its row on the copy: {… 'verdict': 'pending', 'reason': 'pur_short', 'checked_at': '2026-10-19T19:55:40' …}
witness(con_ro, sp) in 0.5s -> stock_figure_witness_Mon.txt (689 lines); stderr: (empty)
header: stock_figure witness  2026-10-19T19:55:42 IST  (kit S602_CUTOFF_LINE_AND_F943; the old ways run beside the new for one week -- 4b-2 retires them)
ok   C: NEW: the witness on a mode=ro connection leaves stderr EMPTY of 'stays pending' (the judge stayed out: no write attempted)
ok   C: the stock_start_capture row is unchanged by the read-only run
ok   the witness file was written with its header and the capture line
ok   C: the witness file carries the SAME figures as the OLD files' run (every line after the header's timestamp equal) -- and the OLD run's stderr carried the line
captures(sp, Ctx(con_rw, sp)) in 0.0s: the row now {… 'verdict': 'pending', 'reason': 'pur_short', 'checked_at': '2026-10-19T19:55:42' …}
ok   the judge still runs on a WRITABLE copy connection: the pending capture's row written or re-checked (checked_at moved) -- equal on OLD and NEW
ok   the writable judge's verdict / reason equal the OLD files' (('pending', 'pur_short'))
```
On the OLD files the same read-only run printed `stock_figure: start capture 6d718060 (2026-10-18T09:37:08) stays pending: attempt to write a readonly database` — the fault reproduced on this box (sqlite 3.34.1 under both pythons; R1 verified the `CREATE TABLE IF NOT EXISTS`-passes behaviour on 3.45.1 — here too the ro run reaches the write), and the 688 figure lines of the OLD and NEW witness files are identical.

**Control 6:** `figures()` for 414 names (the master and the orthotic items) equal OLD vs NEW on the copy, 0 moved; `capture_at` the same capture (printed 2026-10-18, taken 2026-10-19T09:37:51, end 2026-10-18); the spine copy's schema and bytes unchanged; `selftest_spine` 50 checks OK; healthz 200. **Control 7 (greps):** `read_only` on 6 lines of stock_figure.py, all inside `Ctx.__init__`, `_may_write`, `witness` and the two docstrings; `_may_write(con, ctx)` once and `_may_write(` twice in all; `KIT = "S602`; `def purchases_upto` once in spine_read.py (2 mentions with the docstring line); `purchases_upto` once and `purchase_upto` once in darpan_kal.py; `purchase_upto` in darpan_kal.html in the one fragment only (three reads of the key inside it); nowhere else in the finance folder; `purchase_bill` count in darpan_kal.py 0 = OLD's 0; no ten-digit run; no write to an `sp_` table; a default Ctx writable, `_ctx()` unchanged.

**S598's walk whole (`walk_s598.py`, run by the installer on the NEW side and on the OLD side):** `WALK RED S598` on BOTH sides, 4 identical FAIL lines — the seven rows S593 marked are five today, lines 3 and 50 having been cleared on live by S598's own re-judge (19-Oct 09:54), so its controls 0, 1 (line 3 by rule a), 8 (re-judge / undo) are red on today's data on OLD and NEW alike — **not this kit's doing**; the other 57 check lines identical on both sides (0 moved figures, the screens, the greps). The only two lines that differ are the ones that must: Darpan's `/finance/darpan/kal` byte count 40792 → 40988 (the fragment) and S598's own `C: KIT = "S598 in stock_figure.py` (ok on OLD, FAIL on NEW: the kit line is S602's). The installer masks exactly those two and gates on the rest being equal. `walk_s593.py` was not run (R1-C8).

### The state before / after, and the witness on live (19:56)

- **BEFORE** (the OLD files on a copy): `api/order` keys without `purchase_upto`; the live spine's `purchases_upto` by direct SQL `2026-10-18`; the list open (19:5x ≥ 09:30), 11 suppliers, source marg_sheet. **As the NEW files read the same copy:** `purchase_upto = 2026-10-18`, every other key the same. **AFTER** (the live files on a fresh copy of the live database): `purchase_upto = 2026-10-18` = the live spine's day (asserted by the installer). A plain curl of the live `api/order` answers 302 (the login gate), so the date is quoted through the live files on a copy of the live database, not through a browser session.
- **The capture rows:** eight within LATE_DAYS, unchanged before / after and across the witness run — `6d718060` printed 2026-10-18 taken 09:37:08 → end 2026-10-17 `pending / pur_short` (checked 2026-10-19T19:50:03 by the day's tick, which judges on a writable connection as before).
- **The witness once on live, read-only, as the crontab runs it** (`cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness`): started 19:56:47, exit 0 at 19:56:48, **stderr EMPTY**, stdout `stock_figure witness written: /root/finance/spine/stock_figure_witness_Mon.txt`; the file's header `stock_figure witness  2026-10-19T19:56:47 IST  (kit S602_CUTOFF_LINE_AND_F943; …)`, its capture line `newest usable capture: printed 2026-10-18, taken 2026-10-19T09:37:51, stands for the end of 2026-10-18 (84d9df3a)`. It overwrote the 08:27 rehearsal file (65,519 bytes now; the rehearsal's was 99,410 — the newest usable capture moved from 16-10 to 18-10 during the day, as the 09:37:51 capture became usable); tonight's 23:58 run overwrites it again. Harmless, as the brief said.

### Backups, restarts, lock

- `finance.db.bak_S602_20261019_195456` (40,747,008 bytes, the backup API, mode 600); `darpan_kal.py.bak_S602_325d988c`, `darpan_kal.html.bak_S602_75d5a5b5`, `spine/spine_read.py.bak_S602_827b0040`, `stock_figure.py.bak_S602_cb577821` beside the files.
- `clinic-finance` restarted once at 19:56:43 IST (`ActiveEnterTimestamp` read back). Nothing else restarted.
- The build lock `/root/deploy/.claude_code_build.lock` taken 19:54:56 by S602, held until the publish; `/root/deploy/_off/DOCTOR_AUTO_OFF` absent; the installer's `/tmp/s602_inst_*` scratch removed on exit.

### Not done, decisions made, and findings outside the brief

- **Not done:** `DUTY_MAP.md` / `DUTY_MAP.json` are not changed (no duty added, moved or removed). `walk_s593.py` not re-run (R1-C8). No CSS change. No `VERSION` bump in stock_figure.py (stays 1.3: a fix, not a feature — the brief named the KIT line only; decided). The owner's `editable` flag and the Devanagari tab untouched.
- **Decided (the brief left it open or the box differed):**
  - **The JS check is a Python tokenizer, not Node** (not on the box, not on this PC) — said in the kit, above.
  - **S598's walk is red on today's data on both sides**; the brief asked for it "green on NEW". It cannot be green on any files today (its data controls read the pre-re-judge rows), so the kit's gate is the honest one: identical on OLD and NEW but for the page's byte count and its own KIT line. Stated here and in the installer's output.
  - The walk's proposal row goes under a live rule with no fixed proposal today (else a `darpan`-kind row of its own) — the UNIQUE key found by the first DRY.
  - `purchase_upto` in darpan_kal.html counts three (one fragment, the key read three times inside it) — the brief's "once" read as one fragment.
- **Finding — the witness is fast:** 0.5 s on the copy, 1 s on live (689 lines, 414 names); the brief's "wasted `verify_start` work" was real but small on this data (the capture is `pur_short`: `start_ready` says not ready before `verify_start` runs). Named, not a change.
- **Finding — the owner's view of the tab:** `_s485_payload` says `editable: true` for the owner (`who[0] in ("staff", "owner")`); the browser's `ro = OWNER_RO || j.me === "owner"` is what makes his view read-only (line 418). Pre-existing design (S485), seen, not touched.
- **Finding — the witness log:** F-943's one-line-a-night has never yet been written anywhere but the rehearsal; after tonight the log file will exist. The next reader should read its tail (the installer prints it).
- **Permissions:** nothing asked or refused on the server. On this PC: `git` is not on PowerShell's PATH (PUBLISH_ALL.bat finds its own); one of my ssh lines failed because PowerShell expanded `$(seq …)` locally — rewritten as a file, nothing lost. No memory note beyond what exists (one small addition on the ssh/wait shape).

### Charter

- **One fact, one place:** the cut-off day is `spine_read.purchases_upto()` (the spine), served by the tab's own payload, worded in the tab's own HTML. The two neighbouring "report reach" facts (`stock_figure.reach(sp)["last_pur"]` = MAX of `sp_export.date_to`; `stock_app._s488_purchase_reach` = `purchase_export.period_to`) are the REPORT PERIOD's reach, a different fact from the newest BILL DATE D746 named — both stand, named here. The read-only flag: `Ctx.read_only`, read by `_may_write` alone (the grep proves it).
- **Seen, not touched (named):** the tab is Devanagari (charter 8 says Roman Hindi) — pre-existing; `dd-mm` on the line against charter 11's `dd-mm-yyyy` — the owner's approved mock-up wins; the line appears only with the heading (an empty list, a closed tab or a frozen order day shows none — D746 asked for a line under the heading); the day is a bill DATE, not an entry moment (with F-948 corrected by Amir it is the newest paper date Marg holds); `verify-start` (the writable CLI) and the day's pages still judge as before (the tick re-checked `6d718060` at 19:50:03 and again after).
- **Retired:** nothing. **Left for later:** nothing new from this kit.
- **Behaviour changes (rule 4, 7):** one new line on Darpan's tab (whenever the heading shows); the witness no longer attempts a write and no longer runs `verify_start`'s work for nothing. No figure, no order, no verdict changes (controls 4, 5, 6).
- **Dependency state at install:** S593 and S598 live (the FROM pins); S594's witness line in the crontab (line 84, 23:58); the 18-10 09:37 start capture `pending / pur_short`; the spine 13/13 and 4 min old; `order.source = marg_sheet`; the witness log not yet written (first night tonight).
