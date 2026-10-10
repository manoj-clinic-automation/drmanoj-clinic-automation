# S521_AMIR_BOARD_STAGE_PROOF — Amir's stock-check board says the same thing as his card about his vouchers

Kit S521 · fault **F-838** · brief `claude_code_briefs/S521_AMIR_BOARD_STAGE_PROOF.md` (Sanjeevni chat, session 303, 11-Oct-2026 05:05 IST).
Built under `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md`.

## What and why

After S520 Amir's card (every step of `/finance/amir/step/N`) says **Orthotic: sab sahi ✓ · Naam badlo: 22 naam — kholiye**, and the link
opens his board. Section 2 of the board (*Voucher ke baad — Closing stock nikaaliye*, the line *Marg = shelf?*) then said
**Marg = shelf: 26 of 28 · 2 to correct: ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST** — two items Amir put right in Marg on 08-Oct.
The board's line came from `_proof_state` (the whole count's proof on the FIRST closing after the vouchers, through `_s436_board_extra`); his
card reads `amir_stage` / `_s446_proof` (S520: proven on the first OR the newest closing). Two judgments of one fact (charter rule 2). Had Amir
followed the board he would have changed two items that are right and spoiled Marg.

**The edit — `stock_app.py`, three anchored edits, nothing else moves:**

1. `api_pad_amir_board`: one line after `_s446_board_filter(...)` — `b = _s521_stage_proof(con, b)`, **for every login**, so the owner's
   board says the same as Amir's.
2. `_s444_renames` (his step-6 rename duty, read by `amir_duties`): ONLY the line that computed `ready` — now `amir_stage(con, cid)` says
   stage B, C or done (None or a raise → False, as before). Its 10-minute cache and its `n_open` count are unchanged.
3. A new S521 block at the end of the file: `_s521_stage_proof(con, b)` and two helpers. It reads `st = amir_stage(con, b["count_id"])` once;
   `st` None, or anything raising → `b` exactly as it came (the values are built in local variables and assigned at the end).

| stage and condition | `proof_state` | `proof_hi` |
|---|---|---|
| A, vouchers open | `wait` | *Abhi baaki — pehle orthotic voucher Marg mein daaliye* |
| A, proof `export` | `export` | *Abhi baaki — * + S488's reason tail (F-753); today's words when the tail is empty or raises |
| A, proof `wrong` | `wrong` | *Marg = shelf: N theek karna hai — names* (the proof's rows, the same his card lists; the page's chip reads *Aa gaya*) |
| B, or done | `done` | *Orthotic: sab sahi ✓* (the card's own words) |
| C, a wrong lot | `wrong` | *Marg = shelf: N theek karna hai — names* |
| C, a lot waiting | `export` | the export wording |
| C, else | `done` | *Ab tak ke voucher Marg mein sahi ✓* |

`renames_ready`, for every login: False in stage A (with `_s446_board_filter`'s wording *Naam badalna — orthotic voucher Marg mein sahi hone
ke baad*), True in B, C or done (and `renames_wait_hi` emptied). A checker skips the filter, so without this the owner's board said
*sab sahi ✓* and still held the renames behind `_proof_state`. For a maker in stages A and B this equals the filter's own value; **in stage C
the list shows (every row verified) where the filter alone hid it** — the brief's rule, so the board and his step-6 duty agree.

**Accepted:** the extra `amir_stage` call on an owner read. Its writes are the same once-only stage events Amir's own card already causes
(A or B verified, a C lot released by its own rule). `_proof_state` itself, the owner's hub (step 5), `stock_amir.html` and every other page
are not changed.

## Pins (server, `/root/finance`) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `stock_app.py` (+80 lines: one call, one line, one block) | 1f43f47ea288c8bba3750b78ba4cef9b (S520's TO) | c0f0623f7d540bbdedb4369aa459405a |

Must not move: `amir_day.py f1ce78e8…`, `reports_tile.py 01f67f4d…`, `order_rules.py 79f21c1e…`, `stock_watch.py c960f6c8…`, `stockmatch.py fc1caf44…`,
`stockmatch.html 02826136…`, `stock_amir.html 2e41e406…`, `finance_app.py 0d713b14…`, `portal.py`, `tile_grants.json`, the crontab.
**No database write by the kit.** `stock_app.py.bak_S521_1f43f47e` beside the file; `finance.db.bak_S521_<stamp>` by the backup API before
placing (rule 6). Restarts `clinic-finance` once. The installer reads the live board once as the owner and as amir after the restart and
reports what it says and whether the read wrote a stage event.

## The walk (`walk_s521.py`) — on backup-API copies, every control red on the OLD file

1. **The live case** through the board's own route (`GET /finance/stock/api/pad/amir/<root>`), signed in through a walk-only portal as amir
   and as the owner: NEW — `proof_state` done, `proof_hi` *Orthotic: sab sahi ✓* naming neither item; `renames_ready` true, `renames_wait_hi`
   empty, all of `item_alias.rows` listed; the board's planned count = the card's `B.open`; `made.vouchers_flat` empty; the owner's board the
   same line and `renames_ready` true; the read wrote no stage event. **C:** OLD as amir names both items under *2 to correct*; OLD as the
   owner `renames_ready` False. His step 6 (stage B) still shows *Naam badlo: 22 naam — kholiye*; `_s444_renames` asked directly: NEW ready True
   / open 22, **C:** OLD ready False.
2. **Synthetic W521 counts** (ids beyond any real one, their own copies): stage A open → `wait`, no exception; a wrong stage-A proof → `wrong`
   with the card's names in the card's order; an export-waiting proof → the S488 tail (`no_figure`), the same tail the card reads; one wrong C
   lot → `wrong` with its name; a C lot waiting → `export`; C with nothing wrong (the next lot opened) → the done line; stage done → the
   card's words; a count with no stage → `b` as it came.
3. **Render check on the PC** (`render_s521.py`): the live `stock_amir.html` booted as amir with the NEW board JSON the walk saved, opened at
   375 px: section 2 reads *Orthotic: sab sahi ✓* with the green chip *Mil gaye ✓*; (c) *Naam badlo (23)* lists 22 *Marg mein badal diya*
   buttons; no voucher card (*Abhi koi voucher nahi.*). **C:** the same page with the OLD words — chip *Aa gaya*, both names — goes red.
4. `py_compile` under both pythons (the installer); one restart; `/finance/healthz` 200.

## Charter (S303)

**Retired:** the board's second judgment of Amir's vouchers — section 2's `_proof_state` line and the renames gate's `_proof_state` test (now
the stage's, for every login), and `_s444_renames`'s `_proof_state` test. DUTY_MAP: no duty is added, moved or removed (the rename duty's
door is unchanged: stage B of his card → the board's (c)); not changed.
**Left for later / seen, not touched:** (1) `_s436_board_extra` still computes `_proof_state` twice per board read (two report reads) only
for S521 to overwrite the result for every login — a dead computation; (2) `_s444_renames` still reads `_pad_report_data` for its
`d is not None` guard, and since S446 no screen reads `amir_duties`' renames value at all (`_s444_card/_left/_summary_rows` all route to the
S446 card, which asks the stage) — a report read per step render for nothing; (3) `stockmatch.ortho_run`'s close-by-rule test c3 still
judges the orthotic vouchers by `_proof_state`, so the orthotic section cannot close by rule while the stage says *sab sahi*; (4) the owner's
hub step 5 (`proof=_proof_state`) — not changed, as the brief says; (5) `_s446_proof`'s five-minute cache (rule 4), as before.

Undo: put back `stock_app.py.bak_S521_1f43f47e`, restart `clinic-finance`, healthz 200, read the md5 back. The database backup is used only
if the owner says so (the kit wrote nothing).

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S521_AMIR_BOARD_STAGE_PROOF/install_S521_AMIR_BOARD_STAGE_PROOF.sh
```
