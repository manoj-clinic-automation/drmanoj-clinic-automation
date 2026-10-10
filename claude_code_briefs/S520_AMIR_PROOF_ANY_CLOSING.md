# Claude Code brief — S520_AMIR_PROOF_ANY_CLOSING (Amir's orthotic voucher check: proven when ANY closing after the vouchers shows the right move — so his card stops telling him to "correct" vouchers that were right)

Written 10-Oct-2026 23:1x IST by the Sanjeevni chat (session 303), after reading Amir's live card at 23:10 IST and the 10-Oct 03:12 nightly database. **Read `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md` first.** Kit **S520** · fault **F-830** (claimed on the board `_numbers` v339; numbers given here, mint none). Runs on its own, after S502 has finished and released the server build lock.

## Why — urgent before Amir's next visit

Amir's card (every step, the top block *Marg sudhar — abhi baaki*) now says:

> Orthotic: Marg mein yeh abhi sahi nahi hain — **L S BELT CONT GRAY UNISON L**: Marg mein 2, hona chahiye 3 · voucher 6 theek kijiye — **L S BELT CONT GRAY UNISON XXL**: Marg mein 3, hona chahiye 2 · voucher 6 theek kijiye

**Both vouchers were keyed right.** Marg minus the PC's computed figure, from `stock_snapshot` / `stock_expected` in the nightly copy:

| item | 02-10 | 04-10 (closing after the vouchers) | later |
|---|---|---|---|
| L (voucher +1) | 0 | **1, exactly +1** | 0 from 06-10, when Marg sold one L |
| XXL (voucher +1) | 1 | **2, exactly +1** | 3 on 08-10, when Marg gained one |

The PC's computed figure does not follow the later sale and purchase. The four LS belt sizes share one 20-letter name in Marg's sale report, so the computed figure cannot tell which size moved.

S500 (F-801) made the check read the **newest** closing after the vouchers instead of the first. That was right for items Amir corrected later (ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST). It is wrong for any item that sells or is bought after a voucher that was already right.

If Amir follows the card, he will change correct vouchers in Marg and spoil Marg. The renames also stay closed for no reason.

**F-830 — the rule, decided:** an item's voucher is **proven when the FIRST closing after the vouchers, or the NEWEST one, shows it moved by exactly its vouchers.**
- Right on the first closing: the voucher was keyed right, and a later move is a sale or purchase.
- Right on the newest: Amir corrected it in Marg after a wrong check (S500's F-801 case). Re-entering a voucher moves its entered stamp, so the closings counted start after his correction.
- A middle closing alone never passes an item. A sale the PC's figure misses could cancel a real error there by coincidence, and a pass is recorded once and never re-checked.

Otherwise the item is still wrong, and its row reads from the newest closing, as now. **The same function also checks Amir's stage-C medicine voucher lots; the rule applies there too, on purpose.**

## The edit — `/root/finance/stock_app.py` (FROM `bfc2a40bff0d8f0050078ea49f990eda`, S500's TO), function `_s446_proof` only

The anchor is S500's line:

```
        R, L = before[-1], after[-1]                              # S500 (F-801): the NEWEST closing after the vouchers -- a correction made in Marg after a wrong check is seen
```

Replace that line and the block it opens, down to the `res = dict(state=("done" if not wrong else "wrong"), …)` line inclusive, with a version that does the following:

1. `R = before[-1]`.
2. `cands` = the closings in `after` whose `_proof_basis` of the expected source equals R's. If `cands` is empty, keep today's "re-based" answer, naming `R` and `after[-1]`.
3. `L = cands[-1]` (the newest, used for display, `as_after`, and the numbers of a still-wrong row, exactly as now).
4. For each item in `need`, it is `ok` if, for `x` = `after[0]` **(only when `after[0]` itself is on R's basis — never a later closing standing in for it)** **or** `x` = `cands[-1]` (only these two), the item is in `mR`, `eR`, `m_x` and `e_x`, and `(m_x − e_x) − (mR − eR) == need[item]`. An item missing from R, or from both of those closings, is never ok.
5. A row that is not ok is built from `L` exactly as today: `moved`, `marg`, `should`, `keys`, and the `None` form when the item is missing from L.
6. `res` as today, plus `proven_on = {item: x}` for the ok items, which is new and only read by the walk.

Leave the cache, `_s488_why` and everything else in the function as it is. Mark the edit with a one-line comment: `S520 (F-830): proven on the first or the newest closing after the vouchers`. Note: a later closing on a different basis is now skipped, where before it gave the *re-based* answer. That is accepted; say it in the README.

## Before building — read on the live database (read-only), STOP if it does not hold

- `stock_voucher_entered` for count 1, rounds 3–4 (the orthotic batches): the chat read seven rows on the 10-Oct 03:12 copy, all on 04-10 between 09:46:22 and 10:02:28 (`last_at` = 10:02:28). The 04-10 Marg closing (`push_snapshot`) was first received at 10:31:44 that day. So `after[0]` is the 04-10 closing, where both belts moved exactly by their vouchers.
- **If any orthotic batch has been entered again since then** (a newer `at`), `after[0]` moves past 04-10. Then STOP this kit, change nothing, and report: the rule would need a per-voucher stamp.
- **Wrong-correction check:** list every Marg closing received after S500's install (22:56 IST 10-Oct). For L S BELT CONT GRAY UNISON L and XXL, report any day-on-day move of L +1 / XXL −1 that the PC's figure does not explain. That would mean Amir followed the old card and changed voucher 6 in Marg. If one is found, do not install; report it to the owner in the first line.

## Walk (`walk_s520.py`) — on a backup-API copy of the live `finance.db`, taken at install time; never the live database

1. **The live case:** call the same function Amir's card calls for his orthotic stage-A proof (`_s446_proof` with the card's own keys, entered stamps and batches, through the card's own path), on the copy.
   - NEW: L S BELT CONT GRAY UNISON L and XXL are not in `rows`, and their `proven_on` is the 04-10 closing.
   - **Control:** OLD (`bfc2a40b`) lists them both (red).
   - Report the NEW state: `done`, or `wrong` with the rows that remain. If ANKLE BINDER BAMBOO M or TYNOR WRIST SPLINT RT M ELAST remain, say so plainly. Do not force anything.
2. **Synthetic, rows keyed W520:**
   - an item wrong on every closing after its vouchers → `wrong`, with the row from the newest closing;
   - an item right only on the newest → ok;
   - an item right only on the first → ok;
   - **an item right only on a middle closing → wrong (the false-pass guard)**;
   - **one stage-C medicine lot** case → ok and wrong as above.
   - Clear `_S446_PROOF_CACHE` between the OLD and NEW runs if both load in one process.
3. **Staff-eye, on the SCRATCH copy only:** as `amir` (walk-only session), GET his card's step pages.
   - The *Orthotic: Marg mein yeh abhi sahi nahi hain* block no longer names the two belts.
   - If the proof is now `done`, the next stage his card already shows after a passed proof (the orthotic rename list) appears, by the existing code. Report what it shows.
   - **Control:** OLD shows the two belts.
4. `py_compile` under both pythons; one restart of `clinic-finance`; `/finance/healthz` 200 (only that route).

## Installer, pins, report

- Installer: `install_S500_REPORT_CHECK.sh` is the model. Lock → FROM pin → compile → walk on scratch → `stock_app.py.bak_S520_bfc2a40b` → place → md5 read-back → restart `clinic-finance` → healthz → release lock. Restore on red.
- No database write by the kit. When the live card next renders a passed proof, the existing code writes one `stock_stage_event` (stage A verified, detail = `as_after`); for a passed medicine lot it writes the stage-C event, **and the next medicine lot is then released to Amir at once** (the existing code, ~7908–7913). Say how many lots this releases on the live card. That is the intended effect (the owner's decided order: vouchers verified, then renames). After the install, read the live card once as the owner (`/finance/amir/step/6`), and report the event it wrote and what the card now shows (expected: *Orthotic: sab sahi* and *Naam badlo: N naam*).
- **Must not move:** `amir_day.py` (`f1ce78e8…`), `reports_tile.py` (`01f67f4d…`), `order_rules.py` (`79f21c1e…`), `finance_app.py`, and S502's files as S502 left them.
- Publish with `PUBLISH_ALL.bat`.
- Report in `claude_code_briefs\REPORT_S520.md`, with owner lines first: whether Amir's card now asks him for nothing wrong, and whether his renames have opened.
- **Charter:** this proof still rests on the PC's computed figure, which the charter retires at rung 4b. Enter it as *"the voucher proof moves onto the spine's Marg figure at 4b"*.

*Written 10-Oct-2026, session 303 (Sanjeevni). Kit S520; F-830.*
