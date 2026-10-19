# S602_CUTOFF_LINE_AND_F943 — the cut-off line on Darpan's order tab (D746); the witness never judges (F-943)

**Brief:** `claude_code_briefs/S602_CUTOFF_LINE_AND_F943.md` (v2, Sanjeevni session 332, 19-Oct-2026), at the owner's word of 18:09 IST
("Darpan, amir and f 943 now") and his "Yes" of 18:01 IST to the mock-up of one grey line under the heading of Darpan's order tab. The
independent read R1 (`03_WORKING_PAPERS/S332/S602_R1_REVIEW.md`: three blockers, ten corrections) is folded in. Rides **D746**; closes
**F-943**. No new D or F. **Charter:** `SANJEEVNI_BUILD_CHARTER.md` v1.1. Four Sanjeevni files, no new file placed, no new table, no new
setting, no data step, no staff word beyond the one new line. Kit shape: S598's. One restart.

## What it does

- **`spine/spine_read.py` (3.1) — `Spine.purchases_upto()`**, one method after `purchases_by_supplier`: `MAX(date)` of `sp_purchase_bill`
  rows with `direction='PURCHASE'` and `date <= today` — the ISO day, or None when the spine holds no purchase bill (MAX over an empty table
  yields one row with `d=None`). `date <= today` keeps a mis-keyed future bill date (F-948's class) off the tab. One line in the module
  docstring's usage list. Nothing else.
- **`darpan_kal.py` (3.2) — the payload carries the day.** In `_s485_payload`, after `live = …` and before the return: a fresh spine handle
  through the engine's own door (`order_rules._s470_spine()`), `purchases_upto()` read, the handle **closed** in `finally` (R1-B2: every
  caller of `_s470_spine` closes what it opens), the whole inside a fail-soft `except Exception` — a spine that cannot be opened leaves
  `purchase_upto` None and the line out, never a stand-in. The return dict gains **`purchase_upto`**. The S485 block's header comment
  names S602 / D746. No read of `purchase_bill` (charter 1). Every tap of the tab (five routes) serves it.
- **`darpan_kal.html` (3.3) — the one fragment.** At line 427, the closing `'</div>':'')+'</div>';` of the `.ohead` block (once in the file)
  becomes `'</div>':'')+(j.purchase_upto?'<div class="muted">Marg में खरीद '+esc(dd-mm)+' के बिल तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में
  नहीं है</div>':'')+'</div>';` — the leading `+` joins the existing concatenation (R1-C6), `esc` is in scope (one `<script>` block), no `'`
  or `\` in the Hindi. `dd-mm` as the mock-up the owner approved. No CSS change (`.muted` exists). The line shows whenever the heading shows.
- **`stock_figure.py` (3.4) — F-943.** `Ctx.__init__(self, con=None, sp=None, read_only=False)` keeps `self.read_only`; `_may_write(con,
  ctx=None)` answers False first when `ctx.read_only` (its docstring says so); `_start_apply`'s one call becomes `_may_write(con, ctx)`;
  `witness()` builds `Ctx(con, sp, read_only=True)`. The judge stays out of the witness's `mode=ro` run — no `attempt to write a readonly
  database`, no stderr line, and `verify_start`'s work is no longer done for nothing before the INSERT raises. `_ctx()` unchanged: a default
  Ctx is writable, so the day's pages and `verify-start` judge as before. `KIT = "S602_CUTOFF_LINE_AND_F943"`, the history extended;
  `VERSION` stays 1.3 (a fix, not a feature — decided).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/darpan_kal.py` | 325d988c61e1c7408a2a4b687a4822bb | b28d7342469814e85129602ea35a7423 |
| `/root/finance/darpan_kal.html` | 75d5a5b51b017abd5ad3aa408609a1ff | 7c9391912cf62972a8d9e3a41e9e2ebb |
| `/root/finance/spine/spine_read.py` | 827b00402add288d028c910128084b90 | 10697b3869218151a75268e2259248d7 |
| `/root/finance/stock_figure.py` | cb577821d9e1eb40110312b4331df9ef | 51e1fc63ab3fb1ac21170cb214f15b6b |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `order_rules.py` 8d078dbe, `stock_watch.py` 299c3ef7,
`order_sheet.py` 1f1e85c1, `porders.py` e5a5c4d4, `porders_s454.py` 40f1755a, `shelf_figure.py` 23b2394a, `stock_app.py` 4f73d0b0,
`amir_day.py` 3af992d9, `spine/spine_build.py` e3d3ed85; proved unmoved: `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (84
lines, `# S577_WITNESS` once), `spine.db`'s schema. Service `clinic-finance`, restarted once. Window 08:00–23:49 IST, the spine green and
under 30 minutes old; `DOCTOR_AUTO_OFF` around the restart. No duty added, moved or removed: `DUTY_MAP` untouched.

## The install (`install_S602_CUTOFF_LINE_AND_F943.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS, S598's kit present and whole) → the FROM pins and the read-only md5s, the crontab → the spine green
→ the witness log's tail (`/root/finance/spine/stock_figure_witness.log`, the crontab's `2>&1` target; "not yet written" when it does not
exist — F-510, no clock estimated) and the newest witness file's header → build from the live bytes (11 anchored edits, each anchor exactly
once) → compile on both pythons; the JS check of the built html (a Python tokenizer over the page's one `<script>` block — Node is not on
the box) → scratch (the finance folder twice, finance.db / assets.db / spine.db by the backup API) → the walk on the OLD files (every control
red) then on the NEW files → **S598's walk whole on the NEW files and on the OLD files, its check lines identical** → DRY stops → the state
BEFORE and as the NEW files read the same copy (`purchase_upto` = the live spine's day) → backups (`finance.db.bak_S602_<stamp>`,
`<file>.bak_S602_<from8>` ×4) → `DOCTOR_AUTO_OFF` → the four files staged and renamed in ONE command → one restart → healthz 200, the pages
302 → journal clean → the state AFTER (the live files on a fresh copy: `purchase_upto` present and equal to the live spine's day; the
capture rows unchanged) → **the witness ONCE on live, read-only**, as the crontab runs it (stderr must be empty; its file's header quoted; it
overwrites today's `stock_figure_witness_<Day>.txt`, which 23:58 overwrites again) → nothing else moved → md5 read-back → the off-switch
removed. Red after placing: the four files back in one command, one restart, healthz.

## The walk (`walk_s602.py`)

On scratch copies only (the real app in one process, the walk's own header session for Darpan, reception, Amir, Shavez and the owner; its own
rows by key `W602 …`; the spine copy never written by the code under test — the emptied / future-bill spines are second copies). **No DOM is
rendered anywhere (R1-B1):** the page route is `send_file`, `renderOrder` runs only in a browser, and the page dumps strip `<script>`.
Controls as the brief's §4: (4, first) Darpan's tab page and day API, reception's order pages, Amir's steps, Shavez's, the owner's stock-now
and needs-you dumped and byte-equal OLD vs NEW; `api/order` (Darpan's and the owner's) carries `purchase_upto` and is byte-equal after that
key is masked; (1) `purchases_upto()` on the copy = the direct `MAX(date)`; None on an emptied copy; a synthetic bill dated tomorrow ignored;
(2) `_s485_payload` carries the day, opened exactly one fresh spine handle and closed it (the Spine class wrapped to count), every other key
equal to OLD's, and with `SPINE_DB` at a missing file: None and the rest equal; (3) the fragment exactly once at line 427 inside
`renderOrder`, the `<script>` block green under the tokenizer (and RED with one quote of the fragment dropped — the checker can fail);
`/finance/darpan/kal/api/order` with the list OPEN (source darpan, `ORDER_CLOCK=10:00`, a W602 proposal on a live rule) carries the day for
Darpan and for the owner's read-only view; (5) F-943: the newest start capture within LATE_DAYS (set back to pending on the copy if it was
final), `witness(con_ro, sp)` on a `mode=ro` connection: stderr empty of `stays pending`, the row unchanged, the file's figures equal to the
OLD run's (every line after the header's timestamp); then `captures(sp, Ctx(con_rw, sp))` on a writable copy connection still judges
(checked_at moves; verdict / reason equal OLD vs NEW); (6) `figures()` for every master and orthotic item and `capture_at` equal OLD vs NEW;
the spine copy's schema and bytes unchanged; `selftest_spine` green; healthz; (7) the greps of §3.4 (`read_only` only in `Ctx.__init__`,
`_may_write`, `witness` and the docstrings; `_may_write(con, ctx)` once; `purchases_upto` / `purchase_upto` where the brief says and nowhere
else; `purchase_bill` count in `darpan_kal.py` unchanged; `KIT = "S602`; no ten-digit run; no write to an `sp_` table). `--expect-red` is the
negative control (8); `--state` prints the install-day state; `--jscheck FILE` is the tokenizer alone.

## Charter

- **One fact, one place:** the cut-off day is `spine_read.purchases_upto()` (the spine), served by the tab's own payload, worded in the tab's
  own HTML like every other staff line. The two neighbouring "report reach" facts (`stock_figure.reach(sp)["last_pur"]` = MAX of
  `sp_export.date_to`; `stock_app._s488_purchase_reach` = `purchase_export.period_to`) are the REPORT PERIOD's reach, a different fact from
  the newest BILL DATE D746 named — both stay. A read-only caller: `Ctx.read_only`, read by `_may_write` only.
- **Seen, not touched (named):** the tab is Devanagari (charter 8 says Roman Hindi) — pre-existing; `dd-mm` on the line against charter 11's
  `dd-mm-yyyy` — the owner's approved mock-up wins; the line appears only with the heading (an empty list or a closed tab shows none, as
  D746 asked); the day is a bill DATE, not an entry moment; `verify-start` (the writable CLI) and the day's pages still judge as before.
- **Retired:** nothing. **Left:** nothing new.
- **Behaviour changes (rule 4, 7):** one new line on Darpan's tab; the witness no longer attempts a write (and no longer runs
  `verify_start`'s work for nothing). No figure, no order, no verdict changes.
- **Dependency state at install:** S593 and S598 live (the FROM pins), S594's witness line in the crontab, the 18-10 09:37 start capture
  `pending` (`pur_short`, re-checked by the day's tick), the spine green.
