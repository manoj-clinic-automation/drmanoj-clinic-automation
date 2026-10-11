# S528_AMIR_PAGE — Amir's screens say only what to do; the verdict is the owner's; renames by identity

Kit S528 · rulings **D706 D708 D709** · faults **F-851 F-852 F-853 F-854** · audit lines A1, A16, B2, B3, B11, B12, B24, §7 of the stock_app map ·
brief `claude_code_briefs/S528_AMIR_PAGE.md` (Sanjeevni chat, session 308, 11-Oct-2026, v3). Built under `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md`
v1.1. Kit 2 of three on Amir's page (Kit 1 = S524, the judgment; Kit 3 = the page rebuilt whole, briefed from `S528_KIT3_DEFERRED.md`).

## What and why

**3.1 "Wrong" only inside both reaches (F-851, charter 1b).** `_s524_table` now names **N**, the newest clean closing captured after the vouchers,
and what the spine's reach lacks for it (`N_short`: sale | pur). A key is **wrong** only when it is not proven at any try and N itself, inside the
reach, reads False; a key that read False at an earlier try while N is not yet judgeable is **pending_reach** (an `unseen` row, `why = reach_sale |
reach_pur`), never wrong; a key absent at N keeps its own why (R1-C2). When any of the proof's keys is pending, `_s488_why` is asked about N, so the
owner's ending says what it waits for (the purchase export → `pur_behind` → Amir's one do-this line *Purchase report nikaaliye*; the sale export →
`no_figure`). The cache key already carries `sp_meta.built`: a new export re-judges by itself. **The window (R3-1):** `_s446_window` gives every
entered batch the moment of its FIRST entry; `_s446_proof` and the per-key table count a batch by that moment, so a take-back by the checker (a wrong
Marg number) followed by Amir's fresh entry never moves R past a closing that already carries the voucher. (The brief's parenthetical "MIN(at) over
the rows after the newest empty row" would re-open the window on every take-back — the very fault R3-1 names; its own words "judged from his first
entry" and walk 2 decide: the first entry, whatever clears came between.) `_s446_entered` is widened to `(no, at, on, by)`; its older readers use
`[0]`/`[1]` only.

**3.2 The door (F-852, D708, charter 13).** `api_pad_vouchers_entered`: `clear` is the checker's alone (403 `checker_only`, *Yeh aapke liye nahi
hai.*); a non-checker POST on an already-entered key → 409 `already` (*Yeh voucher likha ja chuka hai.*) — no second entry by Amir; a new row's
`entered_on` is ISO (`now_iso()[:10]`, the request value is ignored; the page sends none); every reader prints a day through ONE `_dmy_any`
(`_voucher_state`'s `entered.on`, the finding's voucher list, the xlsx through `_voucher_state`). The replies are Hindi for every role: *Likh liya:
<title_hi> — Marg number <no>* / *Wapas le liya.* `api_pad_rename_tick`'s `clear` is the checker's the same way; the tick reply is *Tick ho gaya:
OLD → NEW.* (the promise about Marg's next export is gone, R2-6). `api_pad_marg_answer` is the checker's (the owner's pages keep the box).
**New door `POST /finance/stock/api/pad/rename/accept`** `{rename_id, seen_name}` (checker only): `item_alias.accept`.

**3.3 One source of the stage's words — `_s521_stage_words(con, st)`.** Returns `{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en,
owner_lines: [dict(cls, target, text)], wrong_rows, questions}`; `st None` → empty words. The composition rule (R3-3): the A/C line of the stage,
then the B line iff `renames_visible` (gone once B is verified); `card_hi = board_hi` = the lines joined with " · "; `owner_en` = the stage's English
+ the B line's English. The table of the brief (3.3) is the code: *Orthotic ke voucher: N baaki — board kholiye* (anchor vouchers) / *Orthotic voucher
daal diye ✓* (+ *· Purchase report nikaaliye* on `pur_behind`) / *Orthotic voucher ho gaye ✓* / *Naam badalna: N baaki — board kholiye* (anchor renames)
/ *Naam badal diye ✓* / *Dawa ke voucher: N — board kholiye* / *Dawa ke voucher daal diye ✓* / *Stock ke voucher poore ✓*; the owner's English per row,
with *· n orthotic line(s) not yet on a voucher (make the round on the hub)* in every A row with `pending > 0`. **3.4 The owner's lines** (`owner_lines`):
*Voucher <seq> (<kind>): <item> — by Marg's closing of dd-mm-yyyy Marg moved <words>, the voucher said <words>* (+ *(judged with its N sizes together)*);
*Rename: Marg prints '<seen>' — is it '<new>'? (Accept on Amir's board)*; *Rename: Marg prints both '<old>' and '<new>' — a new item was made instead of a
rename (no Accept)*; *Rename: '<old>' still printed by Marg after 2 closings*; *Marg voucher number <no> is written on vouchers <a> and <b>*. Read by
`_s524_hub_proof` (hub step 7: `text` = `owner_en`, `rows` with their why, `lines`), amir_day's `_s446_owner_lines` (*Count #N: <owner_en>* + the lines)
and the checker's board. A call made here: the stage-C row with nothing open, nothing waiting and nothing wrong (between lots) reads *Dawa ke voucher ho
gaye ✓* with the C counts — the table had no row for it.

**3.5 One light board — `_amir_board_light(con, root, u, st)`; `stock_amir.html` replaced whole (B3, F-853, charter 14).** The payload is exactly the
brief's: `count_id, day, you{user}, stage{stage, more, per}, vouchers[] (seq, kind, n, title_hi, round_no, batch_no, entered{no, on, by, at_text}|null,
can_clear, lines[{item, packing, from_hi, to_hi, change_sign, qty_hi}]), proof{state, hi}, renames{ready, wait_hi, verified, total, questions, rows},
salt_fix[], rate_tasks[], rest{plan, bill_pending, fixes}, last_closing{as_on, received_at_text}`, plus three fields so the page holds no words of its own:
`vouchers[].clear_hi` and `renames.rows[].clear_hi` (*Wapas lein* / *Wapas*, sent to the checker only), `renames.done_hi` (*Naam badal diye ✓*, the one
line once every row is ticked), `renames.questions[].event / .accept` (a `both` question has no Accept, R3-26), `last_closing.hi`. A non-checker sees the
stage's visible keys and the rename rows only while any is planned (each with the staff words of `item_alias.STATE_STAFF_HI`: *Badalna hai* / *Badal diya
✓* / *Marg mein dikh gaya ✓*); a checker every batch, every row (with `STATE_HI`) and the open questions. No `_pad_report_data`, no `_voucher_state`, no
`stockmatch.ortho_run`, no differences / lookups / tranches / pool / reasons / links. **Retired:** `_amir_board`, `_s436_board_extra`,
`_s452_board_roman` (and its `S452_REASONS_ROMAN`, read by nothing else), `_s446_board_filter`, `_s521_stage_proof`, `_s521_wrong_hi`, `_s521_export_hi`,
`S521_EXPORT_HI`, `S488_TAIL_HI` and `_s488_tail_hi` (stock_app's copies); `S521_RENAMES_WAIT_HI` stays as `renames.wait_hi`. The page keeps its look,
its ids, its three doors and the three strings the server depends on; the upload box, its route call and *Server ko bhejo* are gone; the lead reads *Jo
voucher yahan dikhen, unhe Marg mein daaliye aur Marg ka voucher number likhiye.*; card 3 is *Sudhar — Marg mein*; the questions block (*Marg mein '<seen>'
dikha — kya yahi '<new>' hai?* + Accept) renders for the checker only, from the server's list; the line *Aakhri closing stock jo server ko mila: dd-mm-yyyy
hh:mm* is the push's `received_at` (stock_feed's newest push_snapshot — that clock, R3-23). `moreBtn` for every login (the stage comes for every login).

**3.6 One number, one stage call.** `_voucher_seq(con, root)` → `{(round, kind, batch): (seq, kind)}` (ISSUE 1..N then RECEIVE 1..M over every round);
`_s437_flat(con, root, rounds)`, `_voucher_numbers` (the statement) and the light board read it; `amir_stage.numbers` is unchanged in shape (the walk proves it
equal). `amir_stage` is called once per request by the board route and passed down. `page_amir` opens `_s446_root` (the count whose vouchers Amir works;
`_newest_root` as the fallback — B22); the C comment says 12 (B23). `_s524_stage_b` gains `B["questions"]`. `api_snapshot` no longer calls
`item_alias.verify_closing` (a push carries no capture; `marg_take` is the one door — charter 6).

**4 item_alias.py v2.0 (D709, F-854; charter 5 / 12).** `verify_closing(con, names, as_on, md5, source, ts, captured)` — `captured` REQUIRED (a call without
it logs one line and returns). A row is judged by a closing captured after its tick (`captured[:19] > done_at[:19]`), whatever day it is printed for. Folds:
`pad_norm` (case, spacing, trailing dots), `spine_norm` (alnum only), `Kf = stock_watch._k20(pad_norm(name))`. **Seen** = a listed name with `pn == pn(new)`
(or the same 29-clip) and no `pn(old)` → events `seen` + `verified`, `verified_at = ts`, `verified_md5`, `verified_as_on`, `verified_captured`,
`verified_k20`. **Near-miss** → event `question` (state `question`, the owner's tap): `sn` equality (an inner dot, a hyphen), and — a call made here, read
on the 10-10 closing itself — a printed spelling that is a prefix of the new name or carries it as a prefix (the shorter at least 20 letters), the old name
gone: e.g. *TYNOR WRIST SPL RT L ELASTI* for *TYNOR WRIST SPL RT L ELASTIC*, *KNEE SUPPORT XXL HINGED UNISO* for *KNEE SUPPORT XXL HINGED*. **Both** printed
→ event `both` (no Accept). **Collision** → event `collision` only when `Kf(new)` equals the Kf of a listed name that is neither old nor new. `seen_n` counts
once per printed day (`last_seen_as_on`, as before — four captures of one day are one sighting). A questioned row is still judged on later closings: an exact
sighting verifies it (event `verified` closes the question). **Read-back (B12):** a row never ticked (or taken back) whose new name is listed and old name not,
captured after `planned_at` (or `undone_at`) → `done_by='marg'`, `done_at=captured`, the verified fields, `_follow`, event `read_back`. **States:** verified |
question | amber | done (ticked and not taken back) | planned; `STATE_HI["question"] = "Badal diya ✓"`, `STATE_EN["question"]`, `STATE_STAFF_HI` (the staff
words). `summary()` carries `question` and `questions`; `all_verified` unchanged (stockmatch c4). **Table/columns:** `marg_item_rename_event(id, rename_id,
event, seen_name, as_on, captured, md5, by_user, at, note)`; `marg_item_rename` gains `undone_at, verified_k20, verified_captured` (additive, in `ensure`).
`tick` re-ticks a taken-back row (new `tick` event; `undone_at` cleared — the one system mark cleared, R2-17); `untick` sets `undone_at` and writes `untick`,
never NULLs `done_*`; `accept(con, rename_id, seen_name, who)` needs an open question/collision naming that seen_name (never `both`); `questions(con)`;
`sight_closing(con, names, as_on, md5, stamp)` = the short-closing gate + stamp→ISO + `verify_closing` (one reader; `marg_take._rename_verify` keeps its own
gate call and passes `captured` as today — one gate function, two call paths, R3-17). `verified_k20` is a record, not a key to join on (R3-24).

**2 amir_day.py — four anchored edits, nothing else.** `_s446_state` builds `stage_words` beside the stage; `_s446_card` prints `sw["lines"]` (one `<div>`
per line, a board anchor when the line has one) — the A/B/C branch tree and `_s446_wrong_lines` are gone; `_s446_owner_lines` prints *Count #N: <owner_en>*
and `owner_lines`; `_s452_extra_hi` prints `card_hi`; `_s446_left` prints `owner_en`. **Dead, left for Kit 3 (R3-6b):** amir_day's `_s488_wait_html`,
`_s488_tail_hi`, `S488_TAIL_HI` (no caller after this kit); `_s488_proof`, `_s488_why`, `_s488_ending` still have callers (`_s488_wait_line`,
stock_app's `_s524_english_ending`). The salt rules, the S444 shims, `_s444_renames` / `amir_duties` / `amir_vouchers_open`, the bills' since-when,
DUTY_MAP v11, step 4's *jaanch* heading: Kit 3's.

**5 The data step (`data_s528.py`).** After the files are placed and before the restart: the newest VERIFIED `STOCK_CLOSING` row of `mi_file` (finance.db;
the brief's "mi_export" is this table) whose stamp is after `MAX(done_at)` of the ticked, unverified rows; its file under
`/root/marg_ingest/archive/STOCK_CLOSING/<yyyy-mm>/` read by `spine/marg_read.read_file` (the reading `/readings/<md5>.json` is the fallback); the KIT's
`item_alias.sight_closing` (the module copied out of the kit folder) on the live database; one line per ticked row; the summary after. Keyed and idempotent.
**Reverse** (only if the chat orders it; never DELETE): `UPDATE marg_item_rename SET verified_at=NULL, verified_md5=NULL, verified_as_on=NULL,
verified_captured=NULL, verified_k20=NULL WHERE verified_captured='<the capture printed by the step>'` — the event rows and the audit rows stay as records.

## Pins (server) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_app.py` (+118 lines) | b7e9880af7b81d38e7760b98d0a262b5 (S524's TO) | 51620064e6849b02f0446b859a722638 |
| `/root/finance/item_alias.py` (+191) | 5168c3c05df63a674a8dcab59f74365f | 111a8e4877035e5a02665dd586e01b06 |
| `/root/finance/amir_day.py` (−88; four places) | 7f9803d813b59df287e9175de06f6d36 (S524's TO) | f90df5b211c89dc8bdcd2671e163cf94 |
| `/root/finance/stock_amir.html` (whole) | 2e41e406e3b2ef9d7ed75f9f24b923b8 | 8dd65e64aa2315da6c74909fe50c31c7 |
| `finance.db` | additive: `marg_item_rename_event`, three columns on `marg_item_rename`; the data step's rows | backup `finance.db.bak_S528_<stamp>` first |

Read only, never edited (recorded by the installer, refused if they move during the install): `stockmatch.py 4a2f9fcd`, `shelf_figure.py 9be5eb88`,
`stock_watch.py c960f6c8`, `reports_watch.py a8bbd95e`, `qty_words.py 706db7cc`, `purchase_app.py c29050c1`, `amir_salts.py`, `sanjeevni_approvals.py
792f4a9a`, `stock_hub.html a710a98a`, `stock_report.html`, `stock_desk.html`, `finance_ui/finance_approvals.html b32da7ff`, `/root/marg_ingest/marg_take.py
5cad2d24`, `DUTY_MAP.json 7aa2f935` (v10 stands), `finance_app.py`, `portal.py`, `tile_grants.json`, the spine files, the crontab. Service: `clinic-finance`
restarted once. Backups: `<file>.bak_S528_<from8>` beside each of the four, `finance.db.bak_S528_<stamp>` by the backup API.

## The walk (`walk_s528.py`) — scratch copies of finance.db AND the live spine.db by the backup API; `SPINE_DB` at the scratch spine for the whole process;
a walk-only portal session (its own secret and user store); every control on the OLD files

0 the live state by key (a stage-A root, the 22 ticked rows, the roles) · 1 F-851 replayed on the live spine copy with the reach set back to the brief's
day (the TYNOR key *waiting*, `pur_behind`, *Purchase report nikaaliye*; a purchase export covering 10-Oct + `sp_meta.built` bumped → judged; the key
absent at N keeps its why; **control** old → wrong) · 2 R3-1 the window (the earliest key cleared by the owner and entered again after a synthetic clean
closing captured between its first entry and the next key's → the first time kept, the verdict unchanged; **control** old → wrong) · 3 F-854 by
identity on copies (21 verified + 1 not seen, the events, the key and the capture recorded, nothing judged twice; folds; the inner dot → question → Accept
→ verified, the chain; a later exact sighting supersedes; both; read-back; before the tick → nothing; no capture → refused; a 30 % list → skipped; a
collision; the prefix spelling → question; untick/re-tick; `section_state` on a question row; `api_snapshot`'s call gone; **control** old module → 0
verified) · 4 the words, one row of the table at a time (A open / wrong / export / done, B open / all ticked, C released / waiting / judged, done, None),
the dup-number line, the card, step 7's line, the owner's left line, the hub — three reads, one string; **control** old card/board words · 5 one number
(`_voucher_seq` = `_voucher_numbers` = `_s437_flat` = the payload for every batch; **control** old board renumbered amir's subset from 1) · 6 the light
board (< 100 KB, the fields, no take-back word for amir, can_clear for the owner; **control** old > 100 KB with the judgment words) · 7 Needs-you's shape, the
jobs card byte-equal · 8 the routes: the door (403 checker_only / 409 already / 403 not_released / 200 Hindi / the owner's clear / the fresh entry / the dup
line / ISO entered_on printed dd-mm-yyyy; **controls**), marg_answer (403 amir / 200 owner; **control**), the page (no file input, the bar, the rest id),
the board through the route (bytes, ms, one `amir_stage` call), the once-only events, the words in the kit's strings + every `kholiye` a door's verb, step 6's
marker, the staff-eye duties of the v10 map, the hub (text = `owner_en`), the orthotic section, the statement, Needs-you, the visit summary, amir_salts ·
10 the greps (every retired name gone from the NEW folder, comments included), `selftest_spine.py` green, amir_day writes no stage event.

## Charter (S303)

**Retired:** `_amir_board`, `_s436_board_extra`, `_s452_board_roman` + `S452_REASONS_ROMAN`, `_s446_board_filter`, `_s521_stage_proof`, `_s521_wrong_hi`,
`_s521_export_hi`, `S521_EXPORT_HI`, `S488_TAIL_HI` and `_s488_tail_hi` (stock_app); amir_day's `_s446_wrong_lines` and the stage branch tree of
`_s446_card`; the day rule and the exact-string match of `verify_closing`; `api_snapshot`'s rename call; the upload box on the staff board; the stage's
renumbering of a non-checker's vouchers; the take-back and the second entry on a staff screen; the "Marg ke agle stock export mein dikhna chahiye" promise.
**Dead, left for Kit 3:** amir_day `_s488_wait_html`, `_s488_tail_hi`, `S488_TAIL_HI` (R3-6b). **Left for Kit 3:** amir_day's rebuild (the two salt rules
F-839, the S444 shims and the rest of its dead code, `_s444_renames` / `amir_duties` / `amir_vouchers_open` which amir_day still calls, the bills' since-when,
DUTY_MAP v11, `_s454_returns_cache`'s stamp, step 4's *jaanch* heading, the step pages' other words listed by walk 9). **Seen, not touched:** stockmatch c4
on `item_alias.summary`; S524's release-on-any-read (B21); `_newest_root` vs `_s446_root` for the owner's pages; `amir_job.done_how='seen in Marg'` never
re-checked (R2-16); `marg_take`'s own stamp conversion and short gate beside `sight_closing` (R3-17); `marg_take` with `captured` from `now_ist()` when a file
name carries no stamp (R2-24); `last_closing`'s clock is the push's `received_at` (R3-23); the shelf gap's windows (rung 4b); `push_expected` on manojz.
**Calls made without asking:** the window = the FIRST entry (above); the prefix near-miss as a question (above); the stage-C "between lots" words; `seen_n`
once per printed day; `untick` leaves an open question open (the brief's state rule, literally); `_s437_flat` takes `(con, root, rounds)` (its one caller is
`_voucher_state`); the hub's `rows[].why` is the owner line's tail (one copy of the words); the xlsx prints "Batch n of m", not the sequence number — the one
number is proven across `_voucher_seq`, `_voucher_numbers`, `_s437_flat` and the payload.

## Run

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S528_AMIR_PAGE/install_S528_AMIR_PAGE.sh
```

Undo: put back the four `.bak_S528_<from8>` files, `systemctl restart clinic-finance`, healthz 200, read the md5s back; the database backup is used only if
the chat orders the data step reversed (the UPDATE above, or the backup — say so first).
