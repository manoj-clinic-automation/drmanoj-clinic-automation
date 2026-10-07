# Claude Code brief — S494_AMIR_JOBS_NOTICE_FLAGS (Amir's one-time Marg jobs on his own card; the order sheet's arrival notice sent by the process that can send it; a stock flag judged again when its reports arrive; one spot-count line, not one a day)

Written 07-Oct-2026 by the Sanjeevni chat (session 299), from the owner's *"Yes"* of 08:31 IST 07-Oct to the wording shown him (§4.4 — those words are the words), his three notes of 24-Sep on the System Board, and this morning's read of the 07-Oct 01:35 bundle (`ecc20451`) and database. An independent agent read the first draft against the code and the database (2 blockers, 8 corrections, 8 notes) and then the corrected text (2 blockers, 7 corrections); this text carries all of them. Read `CLAUDE.md` first. `claude_code_briefs/S488_DATES_AND_WAITS.md` is the shape to keep.

**Kit S494 · D686 · faults F-765, F-767, F-771** (numbers given here; mint none).
D686 (the owner, 07-Oct) = Amir's one-time Marg jobs live on his own *Marg sudhar* card, each line gone when its work is done.
F-767 = the notice *"Darpan ki order sheet aa gayi"* failed on every send on 06-Oct 15:40:43 (`order_sheet` row 3: shavez 0 sent / 1 failed, shivani 0 / 2, alisha 0 / 1) while every timed reminder reached (`order_notice` rows 1–14).
F-765 = `shelf_figure.record_gaps` judges a closing once, when the closing-stock report lands — often before that day's sale or purchase report has reached the spine — and a flag then stays until the item is counted again. Measured on the 07-Oct database: 52 first flags at the 04-10 closing; 55 first flags and 22 carried at 05-10 (the owner's line reads 77).
F-771 = the owner's Needs-you list prints the spot-count line once for every day it was raised (two identical lines on 07-Oct).

**What this kit is NOT.** No screen changes its layout. No ordering logic moves: nothing of the buying model (S486, parked) is built here, and `order.source` is not written. No count page, no proof rule, no voucher flow, no gate of Amir's day. Nothing is written into Marg and no money row is written (the vendor sheet's own entry for Kedar is the owner's hand, outside this kit). **No parent file:** no `finance_app.py`, `portal.py`, `tile_grants.json`, `aaj_kaam.py`, `aaj_kaam.html`, `aaj_duties.json`, `owner_console.py`, `asset_register.py`, `ring_common.py`, `packs.py`, crontab, service unit.

**Runs on the live bytes** (pins §8; read each live before its first edit; a different md5 = STOP that file and report).

**Touches — PLANNED on the board (`_numbers` v309):**

- Server `/root/finance/`: `order_sheet.py` (Part A) · `stock_watch.py` (Part B, one block) · `shelf_figure.py` (Part C) · `amir_day.py` (Part D).
- Repository `claude_code_briefs/DUTY_MAP.json` (v8 → v9, one duty) and `DUTY_MAP.md` — edited in place (`.gitignore` already allows that path; carry no second copy of the `.json` in the kit folder, F-751).
- `finance.db`: one new table `amir_job` (eight rows seeded, `INSERT OR IGNORE`); three `setting` rows (`order.sheet_notice_max_min` by `order_sheet.ensure()` itself; the other two `INSERT OR IGNORE` into `setting(key, value, note)` by the installer, as S488's seeded its four); `s454_shelf_gap` rows judged again by Part C's own function at the first tick. **One backup by the backup API before the first data write.**
- **Read only (md5 before and after):** `order_rules.py`, `stock_app.py`, `purchase_app.py`, `sanjeevni_approvals.py`, `spine/spine_read.py`, `/root/portal/ring_common.py`, `/root/assetapp/asset_register.py`.

`order_sheet.py` is one of S486's twelve parked files (this chat's own line on the board); S486 is re-pinned on this kit's bytes at its re-read. Say the new md5 plainly in the report.

---

## 0 · The rules this build stands on

1. **Everything a staff member must do sits on that person's own page, and leaves it when done** (the owner, 01-Oct and 03-Oct). A line the system can prove goes by itself; a line it cannot prove goes by one tap; nothing asks him to type.
2. **A notice is sent by a process that can send it.** The web service runs `/usr/bin/python3`; the web-push library lives in the venv only. The ten-minute tick (`order_rules.py tick`, venv, 05:00–21:50) already runs `order_sheet.cron_pass` — it is the sender for anything the web process could not send. A notice is never sent on a later day, nor after it has gone stale.
3. **A flag is a statement about evidence, and is judged again when later evidence arrives.** The re-judge only clears: it removes a flag a later report explains and never raises one. One direction on purpose — the spine's evidence can shrink for a while (F-737: a one-supplier print can stand in for a whole period's purchase lines), and a flag once explained by a real report must not come back because of that.
4. **Every threshold is a setting row with its note** — three new keys (§1, §3, §4.6), each added where its file keeps its settings (`order_sheet.SETTINGS`, whose `ensure()` seeds its own row and note; the default beside `shelf_figure._setting`'s call; `amir_day`'s `_s444_setting` defaults), the last two also seeded by the installer. They are database rows for now, as S488's four are: the owner's settings card (`porders_s454.py`, parked) joins them when that file is next opened. Say so in the report.
5. **No walk or installer run can reach a real phone.** Every python the walk or the installer starts carries `ORDER_PUSH_STUB` (a scratch file) **and** a scratch `RING_PORTAL_DIR`, as `walk_s488.py` does — `order_rules._push` sends for real without them.
6. **Nothing live rebuilt; anchored edits (each anchor exactly once); a negative control on the OLD file for every walk section — the one positive assertion named in §5 for that section, since an invariant cannot go red; the walk's own rows keyed `W494`; no phone, account or patient detail in the repository; fixtures use invented names and non-numeric stand-ins for an account number or IFSC.**
7. **A staff line is Roman Hinglish, the owner's is English.** The words of §4.4 are the words the owner approved — do not improve them.

## 1 · PART A — the arrival notice (`order_sheet.py`; F-767)

**Prove the cause on the box first, and say the result in the report:** `/usr/bin/python3 -c "import pywebpush"` and `/root/wa/venv/bin/python3 -c "import pywebpush"`. Expected: the first fails, the second succeeds. `ring_common.send_push` imports `pywebpush` inside its `try` (≈216), so in the web process every subscription returns *failed* with no exception — exactly the stored counts. **If the system python DOES import it, the cause is elsewhere: build nothing of Part A, report what you read (the service's journal for 06-Oct 15:40, the push answer codes), and carry on with Parts B–D.**

`_sheet_notice` is reached in the web process from `marg_take.py` (the door, ≈192), `porders_s454.py` (≈503, ≈1383) and `darpan_kal.py` (≈1264) through `load_file` / `load_pending`, and in the venv from the tick's `cron_pass`. Nothing else reads `order_sheet.notice`.

- **A.1 `_can_push()`** (new, module level), in this order: `False` when `ORDER_PUSH_NONE` is set (the walk's "web process" switch); else `True` when `ORDER_PUSH_STUB` is set; else `True` only if `import pywebpush` succeeds.
- **A.2 `_sheet_notice(con, sid)`:** build `text` as today. **If `not _can_push()`:** write `notice = {"text": text, "pending": true, "at": now_iso()}` on the row, commit, return — no send attempted. Otherwise as today (the sending branch's bytes unchanged).
- **A.3 `send_pending_notices(con)`** (new). Candidates: `order_sheet` rows whose `notice` JSON has `pending` true, or has `sent` with every login at `sent == 0`, at least one `failed > 0`, and no `retried`, `lapsed` or `dropped` key. For each, in this order:
  - `substr(taken_at,1,10) != today().isoformat()` (`taken_at` is naive `YYYY-MM-DDTHH:MM:SS`; `today()` is the file's own, which honours `ORDER_TODAY`) → add `lapsed: true`, `pending: false`; never send;
  - `now() - _dtm(taken_at)` (the file's own helpers, ≈107 and ≈159) greater than `order.sheet_notice_max_min` minutes → the same `lapsed`. The key is added to the file's `SETTINGS` (≈54) with default `60` and the note *"Order sheet arrived: minutes after which the arrival notice is no longer sent"* — `int_setting` raises on a key that is not there, and `ensure()` then seeds the row itself;
  - `source(con) != "marg_sheet"` → add `dropped: "source"`, `pending: false`;
  - `not _can_push()` → leave it untouched (this process cannot; the tick will);
  - else send **the stored `text`** (do not recompute it — `day_order` falls when a later sheet reprints lines) to `order.notice_to` with the payload `_sheet_notice` builds, and write `{"text", "sent", "at": now_iso(), "first_at": <the old at>, "pending": false}` plus `"retried": true` when the candidate was the failed shape. A pending row whose first send fails everywhere is thereby the failed shape and is tried once more: two attempts at most, ever.
  Returns the number of rows sent. Fail-soft per row.
- **A.4 `cron_pass`:** add `("notices", send_pending_notices)` to the tuple **after** `("sheets", load_pending)`.
- Nothing else in the file moves: `load_file`'s condition (`not as_ordered and n_new and source(con) == "marg_sheet"`) stays; `order_rules._push` is called, not edited. The 06-Oct row is marked `lapsed` at the first tick and never sent. A sheet taken after the day's last tick lapses unsent — true to rule 2; say it in the report.

## 2 · PART B — one spot-count line (`stock_watch.py`; F-771)

`needs_you_lines` (≈1563–1565): the loop `for n in notices(con, "owner"):` appends every `spot_missed` notice of the last seven days; `once_key` is per day, so a week of misses is up to seven identical lines. `notices()` returns newest first (`ORDER BY id DESC`). **Mend, in that loop only:** the first `spot_missed` is appended, any further one is skipped. The other kinds (`cadence`, `plan_lapsed`, `trace_unexplained`, `close_watch`, `ortho_closed`) are left exactly as they are — each of those is a different event. One anchored block. Nothing else in `stock_watch.py`.

## 3 · PART C — a flag is judged again (`shelf_figure.py`; F-765)

`record_gaps` writes one set of rows per closing and returns 0 ever after for that closing. Add **`rejudge(con, sp=None)`** and call it **at the top of `record_gaps`, before the early return, inside its own `try` (fail-soft; `record_gaps`'s return value and what `order_rules` prints are unchanged)** — the tick already calls `record_gaps` every ten minutes, so no other file moves. This is a new standing judgement, not `rejudge_s488.py` (that one-time pass kept each stored `marg_move` and recounted only the vouchers); read it for the table's shape, not as the rule.

`s454_shelf_gap.as_on` and `.at` are ISO. On the 07-Oct database every first flag has its previous closing's row, and no `approx` or rebased row is flagged.

- **Window:** closings with `as_on >=` (the newest `as_on` in the table minus `stock.gap_rejudge_days` days; setting, default `7`, note *"Stock flags: days a first flag is judged again as later reports arrive"*).
- **An ORIGIN row** = a row with `flagged = 1` whose `why` begins `Marg moved ` and contains ` on <its own as_on>` (the format string writes the closing's own day; a carried copy holds its origin's day, which differs from its own `as_on`). Its **copies** = the same item's rows at later closings with `flagged = 1` and `why` equal to the origin's `why`.
- **Pass 1 — each origin row in the window, oldest closing first:** `prev` = the newest `as_on` below it; the item's row at `prev` must exist with `marg` not NULL, and `sp.ok`, else skip. Recompute as `record_gaps` does, from the stored rows and today's spine: `move = marg(D) - marg(prev) - (bought - sold + ret)` with `movements(sp, item, prev, D, incl_from=False)`; `vch = filed_vouchers(con, item, prev, D)`; `thr = mins * (pack if pack > 1 else 1)`, `mins` from `stock.gap_min_packs` as today. **If `abs(move - vch) < thr`:** `flagged = 0`, `marg_move = move`, `voucher = vch`, `why = "explained by a report that arrived later (first flagged <the row's at as dd-mm HH:MM>; judged again <now as dd-mm HH:MM>)"`. Otherwise leave the row byte-for-byte.
- **Pass 2:** for every origin cleared in pass 1, each of its copies (matched on the origin's `why` as it stood BEFORE pass 1 changed it) → `flagged = 0` and the same new `why` (a copy's own `marg_move` and `voucher` are that closing's figures and stay). `record_gaps` carries a flag only from the previous closing's `flagged`, so a cleared flag is not carried into the next closing.
- Never raises a flag (rule 3); never touches a row that is not flagged, an `approx` row, or a flag whose origin lies before the window. Writes nothing when nothing clears (a second call is a no-op); one `commit` at the end. Returns the number of rows cleared, for the walk.
- **The installer** seeds the setting row and nothing else for Part C: the first tick after the restart does the work on the live database. **The walk does it on the copy first and prints, per closing in the window, first flags and carried flags before → after.** That table goes in the report, with one more measure, **counted only, mended nowhere:** of the first flags that remain with `move > 0`, how many have a PURCHASE of the same item in `sp_move` dated within the seven days up to and including that flag's own `prev` whose units equal the move within `thr` (a bill Amir keyed later than its date).
- Cleared flags leave Darpan's spot-count roster reasons (`stock_watch` ≈924 reads `gap_flag`) — expected; name it in the staff-eye differences.

## 4 · PART D — Amir's one-time Marg jobs (`amir_day.py`; D686)

### 4.1 The table (`_s494_ensure(cx)`, called only inside `_s494_refresh` and `_s494_jobs`)

```
CREATE TABLE IF NOT EXISTS amir_job (
  id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,   -- 'category' | 'vendor_bill' | 'tap'
  subject TEXT NOT NULL,      -- the item, the vendor, or the entry's name
  text_hi TEXT, sub_hi TEXT,  -- used by kind 'tap' only (the line and its small line)
  created_at TEXT NOT NULL, created_by TEXT,
  show_from TEXT,             -- NULL = not yet on his card
  said_at TEXT, said_by TEXT, said_what TEXT,   -- a tap: 'done' | 'not_found'
  done_at TEXT, done_how TEXT)                  -- 'seen in Marg' | 'scan linked' | 'bank details on record' | 'tap'
```

Every stamp the code or the installer writes is `_stamp()`'s IST form — never SQL `datetime('now')`.

### 4.2 The eight rows the installer seeds (`INSERT OR IGNORE` by `key`; `created_by = 'S494'`)

| key | kind | subject | show_from |
|---|---|---|---|
| `cat:BRACE TYLOR UNISON` · `cat:SKIN TRACTION HOPE` · `cat:TENNIS ELBOW L HOPE` · `cat:TENNIS ELBOW M HOPE` | `category` | the item name | NULL (set by 4.3) |
| `vbill:AGARWAL SURGICALS AND MEDICALS` · `vbill:RAMA MEDICOSE` · `vbill:KUSHAGRA MEDICAL AGENCY` | `vendor_bill` | the vendor's `supplier_norm` | now |
| `pay:KEDAR-JULY` | `tap` | `KEDAR PHARMACEUTICAL` | now |

The `tap` row's `text_hi` = `KEDAR PHARMACEUTICAL: ₹310 cash payment ki entry Marg mein kijiye.` and `sub_hi` = `July 2026 ka purana balance band karne ke liye.` The four item names stand exactly so in `stock_item_section.item` (section `Orthotics`) and the three vendor names in `purchase_bill.supplier_norm` on the 07-Oct database — **read each on the box before seeding; a name not found there is not seeded and is named in the report.** After the `INSERT OR IGNORE`, the seed step also sets `show_from = now` on any `S494` row of kind `vendor_bill` or `tap` that is unsaid, not done and has `show_from` NULL — a re-install after a restore (§8) must bring them back.

### 4.3 `_s494_refresh(cx)` — the system's own part; called at the two places `_s444_self_clear` is called (the work build ≈580 and `needs_you_lines` ≈2128); fail-soft, idempotent, writes only when a row changes

- **`category` rows.**
  - *Show:* `st = stock_app.amir_stage(cx)` returns `None` (no count, or no vouchers) or a dict whose `stage` is `A`, `B`, `C` or `done`. When `st and st["stage"] in ("B", "C", "done")`, a row with `show_from IS NULL` gets `show_from = now` — the lines appear **together with his rename list**, never before the orthotic vouchers are proved. `None` or `A` = not shown. (It is `A` today.)
  - *Marg's category for an item:* through `stock_watch.Spine().q` (fail-soft; never `spine_read.Spine`, whose constructor raises when the spine is missing), an exact-name read of `sp_item_fact(name, packing, fact, value, as_on, source_md5)`: `fact = 'category'`, `name = <the item>`, newest `as_on`. Not by the 20-letter key — 51 of the 69 orthotic names are longer than 20 letters and 8 keys are shared.
  - *The orthotic label* = the most common newest category among the names in `stock_item_section` with `section = 'Orthotics'`, the four excluded; with fewer than ten such names carrying a category there is no label and nothing is proved or reopened.
  - *The newest list:* in `mi_file`, the row of `type = 'CATEGORY_WISE_ITEM_LIST'`, `verdict = 'VERIFIED'` with the latest `received_at` — its `md5` and time. **The spine has read it** when a category fact with `source_md5 =` that md5 exists. (A list's `as_on` is its export day and is often earlier than the day it was received — judge by the md5, not by days.)
  - *Prove:* an item whose category in the newest list the spine has read (else, with no such list, its newest by `as_on`) equals the label → `done_at = now`, `done_how = 'seen in Marg'` (whether or not he tapped).
  - *Reopen:* for a row with `said_at` set, when the newest list was received after `said_at` — **both stamps through `_norm_ts()` (≈282) before comparing: `received_at` is `YYYY-MM-DDTHH:MM:SS+05:30`, `_stamp()` is `YYYY-MM-DD HH:MM:SS`, and as raw text every same-day list reads "later"** — and the spine has read it: the item carries a category in that list (a fact with that `source_md5`) that differs from the label → `said_at`, `said_by`, `said_what` back to NULL (it returns to his card); the item carries no fact from that list at all → the row stays said and the owner gets the line of §4.6.
- **`vendor_bill` rows.** Done when the vendor has both an account number and an IFSC in `purchase_vendor_contact` (`acct_no`, `ifsc`; `done_how = 'bank details on record'`), or when a scan is linked to any Marg bill of that vendor — `EXISTS (SELECT 1 FROM purchase_scan_link l JOIN purchase_bill b ON b.id = l.bill_id WHERE b.supplier_norm = ?)` (`done_how = 'scan linked'`). **Expected on the live data at the first refresh: the AGARWAL row closes at once** (its bill of 07-Sep is linked since 30-Sep), **the other two stay open** — their newest bills (22-Aug, 15-Jun) are older than `porders.scan_from`, so a scan of them may never link; that is why the row also has a tap (4.4).
- **`tap` rows.** Nothing: the tap closes them (4.5).

### 4.4 His card (`_s446_card` — `_work` always sets `s446`, so the `_s444_card` branch is not touched) — the owner's approved words

State: `_s446_state` gains `jobs = _s494_jobs(cx)` — the rows with `show_from` set, `done_at IS NULL`, `said_at IS NULL`, grouped by kind. **`_s494_jobs` returns `[]` on any error: `_s446_state` builds its dict with no `try`, and a raise there would take all seven steps down, *Din band* included.** When any job is open, these lines are appended to the card's `lines` **after the count's own lines and before the monthly packs**, under one small heading line whose text is exactly `Ek baar ke kaam` (it is the duty's `door_marker`):

- **Category (one line for all open rows):**
  `In {n} item ki category Marg mein ORTHOTIC kijiye` (n = 1: `Is item ki category Marg mein ORTHOTIC kijiye`)
  small line: the open item names joined with ` · `
  small line, only when the label of 4.3 is known and is not the word `ORTHOTIC`: `Marg mein is category ka naam: {label}`
  one button `Kar diya` → every open category row gets `said_at`, `said_what = 'done'`.
- **Vendor bills (one line for all open rows):**
  `In {n} vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye` (n = 1: `Is vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye`)
  small line: `Bill nikaal kar reception (Alisha / Shivani) se scan karwaiye.`
  then per vendor: `{VENDOR} — bill {bill_no} ({dd-mm-yyyy})` naming that vendor's newest bill in `purchase_bill` (so he finds it in his register), with a button `Scan ho gaya` → that row's `said_at`, `said_what = 'done'`, and a quiet button `Bill nahi mila` → `said_at`, `said_what = 'not_found'`.
  **No scan button on his card:** the owner's own grant file masks the Scan tile for Amir, and scanning is reception's work.
- **Tap rows (one line each):** `text_hi` as the big line, `sub_hi` as the small line, one button `Kar diya` → `said_at`, `said_what = 'done'`, **and** `done_at = now`, `done_how = 'tap'`.

Nothing else on the card moves; with no open job the card's HTML is byte-equal to today's. Amir's step-7 words come from `_s446_summary_rows`, which already says *"Marg sudhar abhi baaki hai — upar wala card dekhiye"* whenever the card is non-empty — leave it. `_s446_left` is the OWNER's English (it feeds `/finance/amir/day` and the visit summary on the approvals page): it gains one line when jobs are open — `one-time Marg jobs: {n} open`. The lines are advisory like the rest of *Marg sudhar*: **`GATE_STEPS`, `_ready_to_close` and the day's close are untouched.**

### 4.5 The tap — the existing step POST, one form field

No new route (a new path would need the parent's gate; there is no CSRF token on these forms). In `step(n)`'s POST block, **test `request.form.get("job")` FIRST, before `if n == 5:` (≈1236), for every n** — step 4's branch returns early and would swallow it otherwise. Values: `cat` (all shown, open category rows), `scan:<id>` and `nf:<id>` (a row of kind `vendor_bill` only), `tap:<id>` (a row of kind `tap` only). A value for a row that is not shown, not open, of another kind, or not a number changes nothing. On a change: one audit row through `_s444_audit(cx, who, "job", <the row's key>, <what was tapped>)`, commit. Then `return _go(n)` — he stays on the step he was on. Each button is its own small `<form method=post>` posting to the step being shown (the card is drawn on every step). Any login the page admits may tap (the owner can answer for Amir, as on the rest of this page); the row records who.

### 4.6 The owner's lines (`_s494_owner_lines(con)`, appended in `needs_you_lines` right after `out.extend(_s446_owner_lines(con))`) — English, `target = "checks-marg"`, each gone by itself

- For each `vendor_bill` row done by `scan linked` while the vendor has no account number and IFSC on record: `Bank details to type for {VENDOR} -- its bill is scanned` (`cls = "warn"`). Expected at install: one line, AGARWAL SURGICALS AND MEDICALS. For a row said `done` (his `Scan ho gaya`) and not yet proved: `Bank details to type for {VENDOR} -- Amir says its bill is scanned` (`warn`). Either line goes when the details are on record.
- For each `vendor_bill` row said `not_found`: `Amir could not find a bill of {VENDOR} -- its bank details are still needed` (`warn`).
- For each `category` row said `done` whose item is not on the newest category list (4.3): `{ITEM} is not on Marg's category list of {dd-mm} -- its category could not be proved` (`info`).
- When shown, unsaid, open rows have waited `amir.job_wait_days` days or more (setting, default `10`, note *"Amir's one-time Marg jobs: days before your Needs-you list names them"*; Amir visits about twice a week): **one** line — `Amir's one-time Marg jobs not done: {n} -- since {dd-mm} ({days} days): {the first three subjects}` (`warn`).
- Nothing for a category row he has said *done* and that is on the list: Marg's next category list proves or reopens it, and that list is already the owner's own duty (`manoj.item_lists`).

The owner's console lists every due duty under its person from the first day, whatever `allowed_days` says (`owner_console.py` ≈778–793) — so *Amir: one-time Marg jobs* shows there at once. That is the console's own rule; only the Needs-you line waits ten days.

### 4.7 The duty map (`claude_code_briefs/DUTY_MAP.json` v8 → v9, `DUTY_MAP.md`) — ONE duty added, nothing else moved

```
{"id": "amir.marg_jobs", "person": "amir",
 "duty": "One-time Marg jobs the owner sets for him (D686): an item's category, a vendor's bill to scan for its bank details, a payment entry -- each a line on his Marg sudhar card until done",
 "duty_hi": "Ek baar ke Marg ke kaam", "tile": "Amir ka kaam", "door": "/finance/amir/step/6", "door_marker": "Ek baar ke kaam",
 "due_sql": "SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE done_at IS NULL AND said_at IS NULL AND show_from IS NOT NULL",
 "allowed_days": 10, "owner_line": "Amir's one-time Marg jobs not done: {n} -- since {since} ({days} days)", "coded": "amir_day._s494_owner_lines"}
```

`version` 9, `kit` `S494_AMIR_JOBS_NOTICE_FLAGS`.

**The map is live the moment the server pulls** — `amir_day.py`, `aaj_kaam.py` and `owner_console.py` all read `/root/deploy/repo/claude_code_briefs/DUTY_MAP.json`. Until the table exists the new `due_sql` raises *no such table* in each reader (caught: skipped by `amir_day`; Amir's list never "all done" in `aaj_kaam`; "Not read just now" on the console). **So this installer's order is a ruled deviation from `CLAUDE.md`'s usual one: step 1 the lock, step 2 the database backup (backup API), step 3 `CREATE TABLE IF NOT EXISTS amir_job (...)` on the live database — and only then the gates, the pin check, the compile and the walk (whose copies are taken after step 3).** An empty table reads as `(0, NULL)` and harms nothing if the install later stops. If step 1 or 2 itself exits, the map's new line reads *"Not read just now"* on the console until the re-run — say so in the report. Prove the `due_sql` on the walk's copy; after seeding and one `_s494_refresh` on the live database print its result — **expected `(3, <today>)`** (two vendors and the Kedar entry; AGARWAL closed by its linked scan; the four category rows not yet shown). For every login but `amir` the duties before and after are identical — the walk proves it.

## 5 · Walk (`walk_s494.py`) — on a scratch `finance.db` (backup API), a scratch spine, `ORDER_PUSH_STUB` and a scratch `RING_PORTAL_DIR` set for every run; the kit's own rows keyed `W494`; each section's **control** is run on the OLD file and must go red

1. **The notice.** (Run without `ORDER_TODAY` — `now()` ignores it. The `W494` sheet has at least one new line, `as_ordered` false, and `order.source` is `marg_sheet` on the copy, so OLD does call `_sheet_notice`.) With `ORDER_PUSH_NONE=1` and the sheet loaded through `load_file`: the row's notice is `pending` and the stub file is empty — **control: on OLD (which ignores the switch) the stub holds one payload per login at load.** Then `cron_pass` without the switch: the stub holds one payload per login of `order.notice_to` carrying the stored text, the row reads `pending: false` with `sent` filled and `first_at` kept; a second `cron_pass` sends nothing. A `W494` row in the 06-Oct shape (all `sent 0`, some `failed`) taken now is retried once and carries `retried`; the same shape dated yesterday → `lapsed`, not sent; taken today but older than the setting's minutes → `lapsed`; with `order.source` moved off `marg_sheet` on the copy → `dropped`. Without the switch `_sheet_notice` sends at once as today.
2. **One spot-count line.** Three `W494` `spot_missed` notices on three days of the last week → `needs_you_lines` carries exactly one such line, the newest — **control: OLD gives three.** Two `trace_unexplained` notices still make two lines.
3. **The re-judge.** `W494` items over three `W494` closings on a scratch spine: a first flag whose window's sale is added to the spine after the flag → cleared, its two copies with it — **control: on OLD the three rows stay flagged after `record_gaps` is called again.** Removing that sale from the scratch spine again changes nothing — cleared stays cleared (rule 3) — and a fourth `W494` closing recorded after the clear does not carry the flag. A first flag nothing explains stays, byte-equal; a carried flag whose origin is outside the window stays; an unflagged row is never flagged; an `approx` row is untouched; a second call writes nothing; with the spine absent nothing changes and nothing raises. **Then on the copy of the live rows, no `W494`:** the table of §3 printed.
4. **His card.** (`stock_app.amir_stage` is stubbed for the stage — a stage cannot be keyed `W494`.) Seeded `W494` jobs of all three kinds: at stage `A` or `None` the card shows the heading, the vendor block (each vendor with its newest bill's number and date) and the tap line, and **not** the category line — **control: OLD shows none of them**; at stage `B` the category line appears with its names. Each line letter for letter as §4.4. `Kar diya` on the tap line → gone, the row `done`; `Kar diya` on the category line → gone from his card, rows `said`; a `W494` category list received later the SAME day that still differs → back on his card (the stamps normalised); one that equals the label → `done`, `seen in Marg`; an item absent from that list → stays said, the owner's line present; a list whose export day is earlier than the day it was received is still honoured (judged by its md5). `Scan ho gaya` → that vendor's line gone and the owner's *Bank details to type … Amir says its bill is scanned* line present; with a (non-numeric) account and IFSC on the copy the row is `done` and the line gone. `Bill nahi mila` → line gone, the owner's *could not find* line present. A `W494` scan link → `done`, `scan linked`. **Posted from step 4, step 5 and step 7 each tap lands and he stays on that step.** A `job` value for a row not shown, of the wrong kind, or a made-up id changes nothing. With no open job the card's HTML equals the OLD file's. The day closes exactly as before with jobs open. `_s494_jobs` with the table dropped on the copy → every step still renders.
5. **The duty.** `due_sql` on the copy: the count and day expected — **control: with the v8 map the duty is absent**; `(0, NULL)` when all are done or said. The map loads in copies of `aaj_kaam.load_defs` and `owner_console`'s reader without an error; **for every login but `amir` (`darpan`, `shavez`, `alisha`, `shivani`, `reception`, `bhati`, `sukhveer`, `manoj`) the list cut with the v8 map and with the v9 map is identical.**
6. **Staff-eye (D648):** amir, darpan, shavez, a reception login and the owner — every home and door page equal before and after **except, and name each difference found:** Amir's card on each step (the jobs) and his own `/finance/aaj` line; the owner's Needs-you (the spot line once; the shelf-gap count; the lines of §4.6), `/finance/amir/day` and the visit summary on the approvals page (the `_s446_left` line), and the console's by-person block (the new duty under Amir); Darpan's spot-count roster (fewer *flagged* reasons). Amir's home shows the tile, and step 6 shows `Ek baar ke kaam` while the duty is due.

## 6 · Done means

- An order sheet that reaches the server through the web door is announced to the ordering team at the next tick (ten minutes at most, between 05:00 and 21:50) the same day; never on a later day, never after it is stale, never more than twice.
- The owner's list carries one spot-count line.
- A first flag of the last seven days leaves when the report that explains it arrives, its later copies with it, and is not carried into the next closing; nothing is ever flagged by the re-judge; the report gives the before → after table and the count of late-keyed purchases.
- Amir's *Marg sudhar* card carries his one-time jobs in the owner's words, each gone when proved or tapped; the category line arrives with his rename list; the day's close is untouched and no step can fail because of the jobs.
- The owner is told only what needs him: bank details to type once a bill is scanned, a bill Amir could not find, an item the category list does not carry, jobs left ten days.
- The map has the one new duty; no other login's list changed; the table exists before any reader can ask for it.
- Every walk section green on NEW, its control red on OLD; both pythons compile every changed file; healthz 200; the lock taken and released; the publish gate clean (`NO_PHONE_NUMBERS.py` over every added file; `.gitignore` read against each).

## 7 · Report — `claude_code_briefs\REPORT_S494.md`

For the owner (3–6 lines): reception is now told when Darpan's order sheet arrives; Amir's page carries his one-time Marg jobs and they leave when done; your list shows the spot-count line once; the stock flags fell from N to M because the rest were reports that arrived later; what needs you (the bank details line, by vendor name). **No patient's name, no phone or account number, no line of a sale or register text.**

For the chat: the two `import pywebpush` results; every pin FROM → TO read back on the box; the walk whole with its controls; the re-judge table per closing and the late-keyed-purchase count; after the first live tick, the count of rows whose `why` begins `explained by a report` and the tick's own log line (`notices`, `gaps`); the eight seeded rows as they stand after the first refresh (which closed, how); the orthotic label read from the spine and the number of names it rests on (or that there is none yet); the `due_sql` result on the live database; the three settings as seeded (and by what); each staff-eye difference; anything outside the brief you noticed.

## 8 · Pins — the 07-Oct 01:35 bundle; read each live before its first edit; STOP that file if different

| file | FROM |
|---|---|
| `/root/finance/order_sheet.py` | `16f21a6515a1317e1f6e31cb0a280513` |
| `/root/finance/stock_watch.py` | `4fc0f6017825975e75ebacfdc2f122d2` |
| `/root/finance/shelf_figure.py` | `0d836de54672f3e624fcc763311ab22c` |
| `/root/finance/amir_day.py` | `08d058a765278d6e119e70f8f0adeedd` |
| `claude_code_briefs/DUTY_MAP.json` · `DUTY_MAP.md` | `f27423b61e50857875bb8f7ba4e5c57c` · `cb78fe54f4d09fb4733dc1bac268cf9e` |
| read only — `/root/finance/order_rules.py` `ee17c1872acd0c440868a915fa5014df` · `stock_app.py` `cc06dac9e3ab60a85d76e2409815b5af` · `purchase_app.py` `c29050c18795a059e3cfbfae252efc21` · `sanjeevni_approvals.py` `792f4a9af1728c76e8d5a656f5662421` · `spine/spine_read.py` `712a1e4ef827f6be4e8b23415c3ceb62` · `/root/portal/ring_common.py` `4344b59277d94b2d11d8d7cc23328677` · `/root/assetapp/asset_register.py` `e774be89193472dfa4b142d85bdcc46c` (md5 before and after) | |

The clinic chat's S493_LISTS_2 is in flight on `aaj_kaam.py` / `aaj_kaam.html` — none of its files is edited here. If `aaj_kaam.py` or `owner_console.py` has moved since the bundle, walk section 5 runs on a copy of whatever is live, and the report says which bytes it read.

Backups beside every file replaced (`<file>.bak_S494_<from8>`); `finance.db.bak_S494_<stamp>` by the backup API before the first data write (the empty table of §4.7 included). Restart `clinic-finance` once; `/finance/healthz` 200. The lock taken and released. A red step after placing: every file back byte-identical, restart, healthz, report (the database backup stays; the table stays, and the restore sets `show_from = NULL` on every row with `created_by = 'S494'`, so the map's `due_sql` reads `(0, NULL)` while no page shows the jobs — say so in the report).

## 9 · The server line, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S494_AMIR_JOBS_NOTICE_FLAGS/install_S494_AMIR_JOBS_NOTICE_FLAGS.sh
```
