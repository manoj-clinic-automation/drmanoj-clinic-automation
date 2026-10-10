# Claude Code brief — S521_AMIR_BOARD_STAGE_PROOF (Amir's stock-check board says the same thing as his card about his vouchers)

Written 11-Oct-2026 at about 05:05 IST by the Sanjeevni chat (session 303). The chat read Amir's live card and board after S520, at 04:50 IST. **Read `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md` first.** Kit **S521**, fault **F-838**, both claimed on the board `_numbers` v341. The numbers are given here; mint none.

## Why — before Amir's next visit

His card (every step of `/finance/amir/step/N`) now says **"Orthotic: sab sahi ✓ · Naam badlo: 22 naam — kholiye"**, which is right after S520. The link opens his board (`/finance/stock/page/amir?count=1#renames`). Section 2 of the board, *Voucher ke baad — Closing stock nikaaliye*, then says:

> Marg = shelf? — **Marg = shelf: 26 of 28 · 2 to correct: ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST**

Amir put those two items right in Marg on 08-Oct. The board line comes from a different judgment: `stock_app._proof_state(con, d)`, the whole-count proof read on the first closing after the vouchers, through `_s436_board_extra`. The card reads `amir_stage(...)` and `_s446_proof`. That is two judgments of one fact (charter rule 2).

If Amir follows the board, he will change two items that are now right and spoil Marg. `_s446_board_filter` already gives a non-checker login only the stage's vouchers and renames. It does not touch `proof_hi` / `proof_state`.

## The edit — `/root/finance/stock_app.py` (FROM = S520's TO, as S520's report read it back)

**Add a function `_s521_stage_proof(con, b)`** and call it in `api_pad_amir_board` right after `_s446_board_filter(...)`, **for every login**, so the owner's board says the same as Amir's.

It reads `st = amir_stage(con, b.get("count_id"))` once. If `st` is None, or anything raises, it leaves `b` exactly as it came. Otherwise:

- **`proof_state` / `proof_hi`** — let `A = st["A"]`, `AP = A.get("proof") or {}` (it is None while vouchers are open) and `C = st.get("C") or {}`.
  - The *export* wording keeps S488's reason (F-753): `"Abhi baaki — " + _s488_tail_hi(_s488_stage_proof(st))`. Fall back to *"Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"* only when that tail is empty or raises.
  - The *wrong* wording starts with `"Marg = shelf: "`, so the page's chip reads *Aa gaya*, as it does today for a judged closing.

| stage and condition | `proof_state` | `proof_hi` |
|---|---|---|
| A, `A["open"] > 0` | `wait` | *"Abhi baaki — pehle orthotic voucher Marg mein daaliye"* |
| A, `AP.get("state") == "export"` | `export` | the export wording |
| A, `AP.get("state") == "wrong"` | `wrong` | *"Marg = shelf: %d theek karna hai — " + names*, from `AP["rows"]` (the same rows as his card) |
| B, or done | `done` | *"Orthotic: sab sahi ✓"*, the card's own words |
| C, `C.get("wrong")` | `wrong` | *"Marg = shelf: %d theek karna hai — " + names* |
| C, else `C.get("waiting_export")` | `export` | the export wording |
| C, else | `done` | *"Ab tak ke voucher Marg mein sahi ✓"* |

- **Build the new values in local variables and assign them to `b` only at the end**, so a failure part-way leaves `b` untouched.
- **`renames_ready`, for every login:** False in stage A (for the owner too — set it, and give `renames_wait_hi` the filter's wording *"Naam badalna — orthotic voucher Marg mein sahi hone ke baad"*); True when `st["stage"]` is B, C or done; when it is True, empty `renames_wait_hi`. A checker skips `_s446_board_filter`, so without this the owner's board would say *sab sahi ✓* and still hold the renames back behind `_proof_state`. For a maker this equals the filter's own value.
- **The extra `amir_stage` call on an owner read is accepted.** Its writes are the same once-only stage events Amir's own card already causes (A or B verified, a C lot released by its own rule). Say so in the README.
- **The same rule for Amir's step-6 rename duty:** `_s444_renames(con, cid)` (stock_app.py ~7640–7665, read by `amir_duties` → his step 6) computes `ready` from `_proof_state`. Change only that line: `ready` = `amir_stage(con, cid)` says stage B, C or done (None or a raise → False, as now). Keep its 10-minute cache and its `n_open` count unchanged. That removes the second judgment of the same fact; the walk checks that step 6's rename line still shows in stage B.
- `stock_amir.html` is not changed.
- `_proof_state` itself, the owner's hub (step 5) and every other page are **not** changed.
- Mark the edit with a comment: `S521 (F-838): the board's proof line and renames gate are the stage's, as on his card`.

## Walk (`walk_s521.py`) — on a backup-API copy of the live `finance.db`; never the live database

1. **Live case, on the copy, as `amir`** (walk-only session): `GET /finance/stock/api/pad/amir/1`.
   - `proof_state == "done"`; `proof_hi` contains *Orthotic: sab sahi*; it does not contain *ANKLE BINDER* or *TYNOR*.
   - `renames_ready` is true and the renames rows are listed (all of `item_alias.rows`, 22 still to do).
   - `made.vouchers_flat` is empty, since stage B lists no voucher.
   - **Control:** the OLD file gives *2 to correct: ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST* (red).
   - Also GET it as the owner: the same `proof_hi`, and `renames_ready` true.
2. **Synthetic stage A / C cases (W520-style rows keyed W521):**
   - stage A with open vouchers → `wait`, and no exception (A's proof is None);
   - a wrong stage-A proof → `wrong` with the names its card would show;
   - an export-waiting case → the S488 reason tail in the line;
   - one wrong C lot → `wrong` with its names;
   - nothing wrong → the right `done` line.
3. **Render check at build time on the PC:** Amir's board page with the live JSON at phone width. Section 2 reads *Orthotic: sab sahi ✓* with the green chip; section 3 (c) lists the renames with *Marg mein badal diya* buttons; no medicine voucher card shows. Assert on the rendered text.
4. `py_compile` under both pythons; one restart of `clinic-finance`; `/finance/healthz` 200.

## Installer, pins, report

- `install_S520_…sh` is the model. Lock → FROM pin → compile → walk on scratch → `stock_app.py.bak_S521_<from8>` → place → read-back → restart → healthz → release. Restore on red. The kit writes nothing to the database.
- **Must not move:** `amir_day.py`, `reports_tile.py`, `order_rules.py`, `stock_watch.py`, `stockmatch.py`, `stockmatch.html`, `stock_amir.html`, `finance_app.py`.
- Publish with `PUBLISH_ALL.bat`. Report in `claude_code_briefs\REPORT_S521.md`, with owner lines first: what Amir's board now says, and that it matches his card.
- **Charter:** this kit retires the board's second judgment of Amir's vouchers. Under *"Charter: seen, not touched"*, name the other places `_proof_state` still feeds a staff-visible line, if any.

*Written 11-Oct-2026, session 303 (Sanjeevni). Kit S521; F-838.*
