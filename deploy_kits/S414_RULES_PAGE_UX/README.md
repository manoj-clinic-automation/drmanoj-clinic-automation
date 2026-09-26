# S414_RULES_PAGE_UX — the buying-rules block: no redraw on a tap, real editors, ticks that stay (F-635)

**Session 283 · 26-Sep-2026 · follow-up to S410 · OWNER: PARENT (clinic).** The owner: "I clicked one item in never-reorder, the list
closed and it shows only the item I clicked; the other items vanished." Read from the live page: every tap ended in `loadPORules()`,
which rebuilt the whole block by innerHTML with every `<details>` closed again; the supplier editor was a `prompt()` asking for a field
name; pause / freeze / approve used `prompt()` / `confirm()`. The server (order_rules.py, S410) was fine.

## What was built
1. **`finance_ui/finance_approvals.html`** (clinic file, declared; anchored — the S410 JS block replaced between its two markers, one CSS
   insert, the card's words): **nothing redraws on a tap.** A tick, a supplier edit, a pause / resume, the freeze and the approval patch the
   DOM in place from the API's answer. A full draw (`loadPORules`, on the block's open) goes through `poKeepOpen`, which remembers every
   open `<details>` (by id) and the scroll and restores them; the first draw opens the two candidate lists and the item rules, keeps the
   suppliers and "last changes" folded. **The candidate lists are check-lists that stay put:** a checkbox per row, tick = saved at once
   (a green "✓ saved" fades in, the row stays where it is, greyed, with its rule name), untick = removed, no dialog; a count "N of M ticked";
   **Tick all shown / Untick all shown** (one call per row, a running "saving k of n…"); a filter box (every typed word must be in the
   name); sort by stock (never list) / unit value (on-demand list) or by name; "show ticked only". Rows already ticked (from
   `item_rules`) are merged INTO their list as ticked rows, so his ticks are visible in the same list, never only in another block.
   **The supplier editor is an inline form** under the supplier's line: cadence · order days Mon–Sat · Thursday ok · Sunday blocked ·
   lead · safety · cover cap · single-source extra · review date + target · pause + reason · note — every field with a one-line hint of
   what it does; Save posts only the changed fields, one call each in the right order (cadence first, then days, then the cap), and the
   plain-words line re-renders from the answer; Cancel closes. Pause asks its reason inline. **Freeze / Approve** show a second button
   ("Yes, freeze" with the reason box / "Yes, approve") for 10 s, then fall back; the answer patches the line. **Your item rules** grouped
   by rule (never re-order · on demand · keep-in-stock · max on shelf · internal use), each row with a ✕ and, for keep / max, an inline
   number + save; the add box autocompletes over the stock master (`<datalist>` filled from the new API, 250 ms debounce); an added or
   removed rule also ticks / unticks the matching candidate row. **Order of the block:** Approve rules with the one-line summary
   ("23 suppliers · N never re-order · M on demand · frozen: no · not yet approved") at the top · the freeze line · the shop-wide line ·
   Suppliers (folded, Kedar first) · the two check-lists · Your item rules · the Kedar review / holidays · last changes (folded; refreshed
   on the next open) · Approve rules again at the bottom. Tables scroll inside `.tblwrap`, never the page. No `prompt(`, no `confirm(` in
   the block (the rest of the page's older dialogs are untouched — not this brief).
2. **`order_rules.py`** (anchored, two additions): `GET /finance/porders/api/rules/items?q=` — at most 20 item names from the newest stock
   snapshot (the stock master), every typed word must appear, owner-only, `{item, qty, packing}`; and `set_item_rule` now answers with
   `counts` (`item_rules`, `by_rule`, the lists' sizes) and `row` (item, rule, value, set_by, set_at), so the page needs no re-fetch after
   a tick. The state API is unchanged (same keys, same rows — asserted against the box as it is).

## Pins (read live 26-Sep-2026 17:23 IST)
| file | FROM | TO |
|---|---|---|
| /root/finance/finance_ui/finance_approvals.html | 7de583154b87bd4d3ba13ce6de1c53a9 | eba564a425c1fc844f1d8d975a1d5eca |
| /root/finance/order_rules.py | df6196fcb750f3dd5401695bd254a7aa | b17226d4cc10d7cf9fef8a75465ac76b |

Restarts `clinic-finance` only. No seed: nothing in finance.db changes (the database is still backed up first, as always).

## Proof
The box has no browser and no node, so the page's JavaScript was parsed in the session with a real parser (esprima 4.0.1, Python) on the
built bytes: the page's one script (151,355 chars) and the rules block alone (29,392 chars) both parse; the installer's pin check proves
the bytes placed are those bytes. `walk_s414.py` — the real finance app over a scratch copy: (1) the rules state answers the owner with the
same keys, rule keys and counts as the box as it is; (2) the items API: `w414 alpha` → exactly the two of our three snapshot items carrying
both words, `gamma beta` (any order) → the one, an empty q → capped at 20, nonsense → none, darpan 403; (3) a tick on our in-stock
never-sold item (a never-reorder candidate) answers 200 with `counts.by_rule.never = before + 1`, `counts.item_rules`, `counts.lists` and
the row (rule never, set_by manoj); the state then lists it under item rules, drops it from the candidates, the spine's list holds it;
untick → counts back, row null, gone from the list; keep-in-stock 50 → row.value 50; a nonsense rule 400; darpan 403; our rows removed and
`order_rules.json` restored byte for byte; (4) the page: the block has no `prompt(` / `confirm(`, its braces / parens / brackets balance
(a string-aware count — the block carries no regex literal), every piece is present (poKeepOpen, poTick / poTickAll / poApply, poEditOpen /
poEditSave / poPauseAsk, poFreezeAsk, poApproveAsk, the items autocomplete, the grouped item rows, `poD_*` ids), Approve rules rendered at
the top AND the bottom, everything S410's walk reads still there, one `loadPORules`, no 10-digit number. Negative control: S410's block
asks with `prompt(` ×4 / `confirm(` ×2, no poKeepOpen, the items API 404, the tick answers without counts. Then S412's, S411's, S410's,
S409's, S408's (26/27 + the S411-declared supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run.

**Declared scratch pre-states for three frozen walks** (data the live box has grown since their day; the walks are not edited): S411's
walk counts the first statement of each account "by words" — its scratch copy starts without the learned tails (as in S412's installer);
S412's walk seeds the real shelf and expects three degenerate pipe periods, the 10-Sep anchor and a `stmt_file` without its own three
columns (its negative control reads them as absent; S412's install changed all three on the live box) — its scratch copy gets those
rows, that anchor and the S411-shape table back before its walk; S404's walk answers two OPEN swap pairs of the real count 1, and Darpan
answered the last open pairs between 14:07 and 14:09 IST on 26-Sep — its scratch is a copy of `finance.db.bak_S412_20260926_140429`,
the backup S412's install took at 14:04:29, the last database that walk was green on. The frozen walks then run 17/17, 13/13 and 65/65.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S414_RULES_PAGE_UX/install_S414_RULES_PAGE_UX.sh
```
Undo: the two `.bak_S414_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. No data to reverse.
