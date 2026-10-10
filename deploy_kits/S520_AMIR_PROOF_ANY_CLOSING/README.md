# S520_AMIR_PROOF_ANY_CLOSING — Amir's voucher check: proven on the FIRST or the NEWEST closing after the vouchers

Kit S520 · fault **F-830** · brief `claude_code_briefs/S520_AMIR_PROOF_ANY_CLOSING.md` (Sanjeevni chat, session 303, 10-Oct-2026 23:1x IST).
Built under `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md`.

## What and why

Amir's card (every step, *Marg sudhar — abhi baaki*) told him to "correct" voucher 6 for L S BELT CONT GRAY UNISON L and XXL. Both were
keyed right: on the 04-10 closing — the first after his vouchers of 04-10 09:46–10:02 — each moved by exactly +1. Later Marg sold one L
(06-10) and gained one XXL (08-10); the PC's computed figure cannot follow those moves (the four belt sizes share one 20-letter name in
Marg's sale report). S500 (F-801) made the proof read the NEWEST closing after the vouchers — right for items Amir corrected later, wrong
for an item that sells or is bought after a voucher that was already right. Following the card would have spoiled Marg and kept his
renames closed.

**The rule (F-830, decided):** an item is **proven when the FIRST closing after the vouchers, or the NEWEST one, shows it moved by exactly
its vouchers.** Right on the first: keyed right, a later move is a sale or purchase. Right on the newest: corrected in Marg after a wrong
check (re-entering a voucher moves its entered stamp, so the closings counted start after the correction). **A middle closing alone never
passes an item** (a sale the PC's figure misses could cancel a real error there by coincidence, and a pass is recorded once). Otherwise
the item is still wrong and its row reads from the newest closing, as before. The same function checks the stage-C medicine lots; the
rule applies there on purpose.

**The edit** — `stock_app._s446_proof`, ONE span (S500's `R, L = before[-1], after[-1]` line and the block it opened, down to the
`res = dict(state=("done" …` line): `R = before[-1]`; `cands` = the closings in `after` on R's basis (`_proof_basis`); none → the
"re-based" answer naming R and `after[-1]`; `L = cands[-1]` (display, `as_after`, a still-wrong row's numbers); an item is ok if on
`after[0]` (only when it is itself on R's basis — never a later closing standing in for it) or on `cands[-1]` it is in `mR`, `eR`, `m_x`,
`e_x` and `(m_x − e_x) − (mR − eR) == need`; a row that is not ok is built from L exactly as before; `res` gains `proven_on = {item: x}`
(read only by the walk). The cache, `_s488_why` and everything else in the function are as they were. **Accepted change:** a later closing
on a different basis is now skipped where before it gave the *re-based* answer (it still gives that answer when EVERY closing after the
vouchers is re-based).

## Pins (server, `/root/finance`) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `stock_app.py` (+14 lines, one function) | bfc2a40bff0d8f0050078ea49f990eda (S500's TO) | 1f43f47ea288c8bba3750b78ba4cef9b |

Must not move: `amir_day.py f1ce78e8…`, `reports_tile.py 01f67f4d…`, `order_rules.py 79f21c1e…`, `finance_app.py` (as it is), S502's three
(`stock_watch.py c960f6c8…`, `stockmatch.py fc1caf44…`, `stockmatch.html 02826136…`), S500's three new files, `portal.py`, `tile_grants.json`,
the crontab. **No database write by the kit.** When the live card next renders a passed proof, the EXISTING code writes one
`stock_stage_event` (stage A `verified`, detail = `as_after`) and the card moves to stage B (the orthotic rename list); for a passed
medicine lot it writes the stage-C event and releases the next lot at once (the owner's decided order). The installer reads the live card
once, as the owner and as amir, after the restart (`finance.db.bak_S520_<stamp>` taken before it) and reports the event and what the card
shows. `stock_app.py.bak_S520_bfc2a40b` beside the file. Restarts `clinic-finance` once.

## Before building (read on the live database; STOP if it does not hold)

The seven orthotic batches of count 1 (rounds 3–4) entered on 04-10 between 09:46:22 and 10:02:28, none since; the 04-10 Marg closing is
`after[0]`; no Marg closing received after S500's install (22:56 IST 10-Oct), so no wrong correction could have been made. (Read at 23:39 IST.)

## The walk (`walk_s520.py`)

On backup-API copies: (1) the live case through the card's own path (`amir_stage` → `_s446_proof`): NEW — the two belts are not in the rows
and their `proven_on` is the 04-10 closing; **C:** OLD lists both; the NEW state reported, and whether the earlier two items remain;
(2) synthetic `W520` items on one before-closing and three after (first, middle, newest): always-wrong → wrong from the newest; right only on
the newest → ok; right only on the first → ok; **right only on the middle → wrong (the false-pass guard)**; a medicine lot the same; the
first closing re-based → skipped; every closing re-based → the "re-based" answer; **C:** OLD counts only the newest; (3) staff-eye as amir
through a walk-only portal: the block names neither belt on any step; **C:** OLD shows both; what the card now shows is printed.

## Charter (S303)

Retired: nothing on a screen. Retirement register: **the voucher proof moves onto the spine's Marg figure at 4b** — this proof still
rests on the PC's computed figure (`stock_expected` / `push_expected`), which the charter retires at rung 4b. Left out: nothing. Seen, not
touched: `_s446_proof`'s five-minute in-process cache (a stored conclusion keyed on its inputs' stamps, rule 4 — as before).

Undo: put back `stock_app.py.bak_S520_bfc2a40b`, restart `clinic-finance`, healthz 200, read the md5 back. A stage-A verified event the
live card wrote stays (it records a proof that passed under the decided rule); the database backup is used only if the owner says so.

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S520_AMIR_PROOF_ANY_CLOSING/install_S520_AMIR_PROOF_ANY_CLOSING.sh
```
