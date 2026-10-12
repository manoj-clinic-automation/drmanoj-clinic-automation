# S539_NORTIMER_OUT — brief for Claude Code (v1) — a data-only kit, no code change

*Written 12-Oct-2026 by the Sanjeevni chat (session 310) at the owner's word of **08:42 IST**: "Remove NORTIMER for now from this, as a few strips were with me which I had handed over to Darpan; he is selling from that; we will incorporate whatever surplus later with a new stock issue voucher whenever possible." Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` and `CLAUDE.md` first. Model: `deploy_kits/S537_VOUCHER_GUARD/data_s537.py` (its `find`/`apply`/`print_after` shape, `--dry`, `DATA_S537:` lines) and its installer's data-step part. **No live file is edited.** Everything goes through S537's own doors (live since 08:08:09 12-Oct): `stock_voucher_void`, `stock_voucher_settle`, `stock_app._voucher_make`.*

## 0 · For the owner
1. **NORTIMER TAB leaves the 6-Sep count.** Voucher 11 (STOCK ISSUE, six medicines, held by the guard because of NORTIMER) is voided; NORTIMER is marked settled for this count, so it is never raised again by the count.
2. **The other five lines of voucher 11 go to Amir as a new voucher** — *NIMREX P −11 · NUROKIND LC −5 · NURVION LC TAB −38 · OLMETIME H 20 −45 · ONDEM MD 4 −35* (the same quantities as on 6-Sep, each checked by the guard against today's closing) — numbered after the last one (STOCK ISSUE 30 expected — the voided 29 keeps its number unseen; no other voucher changes its number); it reaches Amir with a coming lot of 12, like the rest. Checked by the chat on the 11-Oct copy: each of the five appears only in voucher 11, and Marg's closing of 09-10 holds NIMREX P 168, NUROKIND LC 14, NURVION LC TAB 282, OLMETIME H 20 157, ONDEM MD 4 90 — none goes below zero.
3. **The count can now finish** once Amir has entered all medicine vouchers and they are proven.
4. **NORTIMER later:** any surplus is put right by a new stock voucher from a fresh count of that item (the normal way) — nothing is built for it now.

**State on install:** count #1 stage C; 12 of 30 medicine vouchers released; voucher 11 (count 1, round 2, ISSUE, batch 10) not entered, held in `C["held"]`.

## 1 · Numbers and pins
- Kit **S539** (board `_numbers` v379 → v380). The owner's word 08:42 IST.
- **Read at their S537 TO pins, never edited:** `/root/finance/stock_app.py` **f58e09db**, `stock_watch.py` 0e6a42c4, `shelf_figure.py` 183c70fa, `loss_piles.py` 81ae481e, `stock_statement.py` a90f3413; the clone's `DUTY_MAP.json` **f499dd1f** (v12). A different byte = STOP.
- `finance.db`: rows only, through the doors above; `finance.db.bak_S539_<stamp>` first; never DELETE. **No restart** (no code moves); no pull.
- The build lock. Scratch `_scratch\S539_NORTIMER_OUT\` and the server's `/tmp`. No `.json` in the kit. F-185.

## 2 · `data_s539.py` (keyed, idempotent; `DATA_S539:` lines; `--dry` rolls back)
1. **Find voucher 11 by shape:** count 1, round 2, ISSUE, batch 10, six lines whose items are exactly {NIMREX P, NORTIMER TAB, NUROKIND LC, NURVION LC TAB, OLMETIME H 20, ONDEM MD 4}; not entered (newest `stock_voucher_entered` empty/absent); not already voided. Print its seq (expected 11). Anything else → `DATA_S539: STOP`, exit non-zero, nothing written. Already voided and NORTIMER settled and the five re-made → `ALREADY DONE`, exit 0.
2. In ONE transaction: INSERT `stock_voucher_void` (count 1, round 2, ISSUE, batch 10; by_user `manoj`; reason `owner 12-Oct 08:42: NORTIMER out of the count for now (strips with Darpan, being sold); the other five re-made`); INSERT `stock_voucher_settle` (count 1, `NORTIMER TAB`, by_user `manoj`, note `owner 12-Oct 08:42`). Commit.
3. Re-make the five through the door: `d = stock_app._pad_report_data(con, 1)`; `pend = stock_app._voucher_pending(con, d, items={the five})` must equal exactly those five with `change` = −11, −5, −38, −45, −35 (print each; any other figure, an extra item, or a held one → STOP before making, the void and settle stay and the report says so — the owner then decides); then `stock_app._voucher_make(con, d, {"user": "manoj"}, section=None, items={the five})` → print the new round, its batch(es) and seq number(s).
4. Print after: `amir_stage(con)` stage, `C` released / held (NORTIMER absent from held), Amir's board batch list (as amir: `_amir_board_light` visible keys), the owner's Needs-you lines naming Count / NORTIMER (none expected).

## 3 · The walk (`walk_s539.py` — short; on scratch copies by the backup API; controls red on the unchanged copy)
1. On a copy of the live finance.db (+ live spine.db): run `data_s539.py` → voucher 11 gone from `_s446_batches`, the board as amir and as the owner, `amir.count_vouchers` (v12 SQL); NORTIMER in `stock_voucher_settle`; one new ISSUE batch with exactly the five lines and their changes; `_voucher_seq` of every pre-existing batch unchanged; `C["held"]` empty; a second run → `ALREADY DONE`, no row written. Control: the untouched copy still holds voucher 11 in `C["held"]` and NORTIMER in Needs-you.
2. `--dry` writes nothing (row counts of `stock_voucher_void`, `stock_voucher_settle`, `stock_voucher_line` before/after).
3. A copy where voucher 11 carries an entry → STOP, nothing written.

## 4 · Install, publish, report
Gates → the six pins → `spine_state.json` passed (charter 1b) → walk (DRY stops) → `finance.db.bak_S539_<stamp>` → `data_s539.py` → state before/after (§2.4) → healthz 200 (no restart). Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` when final; run from the kit folder copied to the server; `claude_code_briefs/REPORT_S539.md` (3–5 plain lines on top: voucher 11 void, NORTIMER settled, the new voucher's number and its five lines, what Amir's card says now); publish again. Undo (if the chat orders it): a later void of the new batch and a settle-removal are not possible by design — the reverse is written in the README as the owner's decision.

**NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NO FIGURE TO TYPE, EVER.**
