# REPORT_S414 — the buying-rules block: no redraw on a tap, real editors, ticks that stay (S414_RULES_PAGE_UX, F-635)

Installed on srv1746119 on 26-Sep-2026, 17:45–17:49 IST (installer's own clock). Kit `deploy_kits\S414_RULES_PAGE_UX\`.

## For the owner
- **When you tick an item now:** the row stays exactly where it is. A small green "✓ saved" appears on it, the row greys out with the rule
  name beside it, and the list stays open. Untick it and it is back in the running, no question asked. At the top of each list you see
  "N of M ticked", buttons **Tick all shown / Untick all shown**, a box to type part of a name, a sort (by stock or by name) and
  "show ticked only". Your earlier ticks are shown in the same list, greyed, so nothing vanishes.
- **How you edit a supplier:** open **Suppliers**, tap **edit** on the line. The line opens into a small form under it: cadence, the
  order days (Mon–Sat), Thursday ok, Sunday blocked, lead days, safety days, cover cap, single-source extra, a review date with its
  target, pause with its reason, a note. Every field carries one line saying what it does. **Save** or **Cancel**. The plain-words line
  above re-writes itself at once. **pause** asks its reason in the line itself.
- **Where Approve rules is:** at the top of the block, first thing, with a one-line summary ("23 suppliers · N never re-order · M on
  demand · frozen: no · not yet approved"), and again at the bottom. Tapping it shows "Yes, approve" beside it for 10 seconds. Freeze works
  the same way, with its reason box in the line. No pop-up boxes anywhere in this block any more.

https://followup.dr-manoj.in/finance/approvals

## For the chat

### Pins — FROM → TO, md5 read back on the box after placing (17:49 IST)
| file | FROM (read live 17:23 IST) | TO (read back) |
|---|---|---|
| /root/finance/finance_ui/finance_approvals.html (clinic file, declared) | 7de583154b87bd4d3ba13ce6de1c53a9 | eba564a425c1fc844f1d8d975a1d5eca |
| /root/finance/order_rules.py | df6196fcb750f3dd5401695bd254a7aa | b17226d4cc10d7cf9fef8a75465ac76b |

Both built on the box from the live bytes by `make_s414.py` (three anchored edits on the page: the S410 JS block replaced between its two
markers, one CSS insert, the card's words; three on `order_rules.py`) and equal to the kit's pins. Nothing else touched; no seed; nothing in
finance.db changed (it was still backed up first).

### What the page does now (finance_approvals.html, the rules block)
`loadPORules` draws the block once through `poKeepOpen` (remembers every open `<details>` by id + the scroll, restores them; the first draw
opens the two check-lists and the item rules, folds Suppliers and "last changes"). Every later action patches the DOM in place from the API's
answer: `poTick` / `poTickAll` (one POST per row, a running "saving k of n…"), `poApply` (filter on every typed word, sort by value or name,
ticked-only — all client-side, rows re-ordered in place), `poEditOpen` / `poEditSave` (the inline form; Save posts only the changed fields,
one `rules/set` call each in the right order — cadence first, then order days, then the cap — and re-renders the line from the answer's
`words`; a server refusal keeps the form open with the message), `poPauseAsk` (reason inline), `poFreezeAsk` / `poFreezeGo` (reason box +
"Yes, freeze" for 10 s), `poApproveAsk` / `poApproveGo` (both places update), the item-rule rows grouped by rule (`poItemOff` ✕ removes the
row and un-ticks the matching candidate row; `poItemVal` saves the inline number; `poItemAdd` with a `<datalist>` filled by
`poItemSuggest` from the new items API, 250 ms debounce). Candidates already ticked (from `item_rules`) are merged INTO their list as ticked
rows. The summary line (`.po-sum`) and the counts (`counts` from the tick answer) update without a re-fetch. "last changes" is refreshed on the
next open of the block (said on the page). Tables scroll inside `.tblwrap`, never the page.

### The two API additions (order_rules.py)
`GET /finance/porders/api/rules/items?q=` — owner-only; names from the newest stock snapshot (the stock master, 377 items today); every
typed word must appear; ≤ 20, name order; `{item, qty, packing}`. `set_item_rule` (behind `POST …/rules/item`) now also answers `counts`
(`item_rules`, `by_rule` per rule, the lists' sizes) and `row` (item, rule, value, set_by, set_at). The state API is unchanged.

### The walk (install log, 17:45 IST) — `WALK_S414 GREEN -- 8/8`
No browser and no node on the box: the page's JavaScript was parsed in this session with esprima 4.0.1 (a real parser, Python) on the built
bytes — the page's one script (151,355 chars) and the rules block alone (29,392 chars) both parse; the installer's step 3 proves the bytes
placed are those bytes (pin equality). On the box, the real app over a scratch copy of the live database:
- the rules state answers the owner with the SAME keys, rule keys and counts as the box as it is (23 suppliers, 45 never / 15 on-demand
  candidates, 1 item rule); darpan 403.
- items API: `w414 alpha` → exactly the two of our three planted snapshot items carrying both words (`item, packing, qty`); `gamma beta` (any
  order) → the one; an empty q → capped at 20; nonsense → none; darpan 403.
- a tick on our in-stock never-sold item (a never-reorder candidate) answers 200 with `counts.by_rule.never` = before + 1 (1 → 2),
  `counts.item_rules`, `counts.lists` and the row (rule never, set_by manoj); the state then lists it under item rules, drops it from the
  candidates, the spine's list holds it; untick → counts back, row null, gone from the list; keep-in-stock 50 → `row.value` 50,
  `by_rule.keep` 1; a nonsense rule 400; darpan 403; our rows removed, the counts as before, `order_rules.json` restored byte for byte.
- the page: the block (29,392 chars) carries NO `prompt(` and NO `confirm(`; its braces / parens / brackets balance (string-aware count; the
  block has no regex literal); the old prompt-driven editor is gone; every piece present (poKeepOpen, poTick / poTickAll / poApply,
  poEditOpen / poEditSave / poPauseAsk, poFreezeAsk, poApproveAsk, the items autocomplete, the grouped item rows, the `poD_*` ids); Approve
  rules rendered at the top AND the bottom (2 places); everything S410's walk reads still there (oosBar, loadPOOos, New items this month,
  Approve rules); the S414 CSS; one `loadPORules`; no 10-digit number.
- **Negative control** (S410's page and API on the same scratch): the block asks with `prompt(` ×4 / `confirm(` ×2, has no poKeepOpen and no
  check-list; the items API is 404; the tick answers 200 without counts or row.
- Live after placing (17:50 IST): the rules block on the live page has 0 `prompt(` / `confirm(` (the page's other, older blocks keep their 7 —
  not this brief).

Earlier kits' walks on the patched files: **S412 17/17, S411 13/13, S410 32/32**, S409 24/24, S408 26/27 (the one red is the
S411-declared supersession, accepted by name), S407 27/27, S406 27/27, S405 29/29, **S404 65/65**, S403 52/52, S400 63/63, S402 16/16.

**Declared scratch pre-states (data the live box has grown since those kits' day; no walk was edited, no check skipped):**
- S411's walk counts the first statement of each account "by words": its scratch starts without the learned tails (as S412's installer did).
- S412's walk seeds the real shelf and expects the three degenerate pipe periods, the 10-Sep anchor and a `stmt_file` without the three S412
  columns (its negative control reads them as absent) — S412's own install changed all three on the live box; its scratch gets them back.
  (Run 1 showed exactly that one red, the negative control reading `0` instead of null; run 2 with the table pre-state: 17/17.)
- S404's walk answers two OPEN swap pairs of the real count 1. Darpan answered the last open pairs between 14:07 and 14:09 IST today
  (`stock_match` rows 9–11, read on the box) — after S412's install had run that walk green at 14:05. Its scratch is therefore a copy of
  `finance.db.bak_S412_20260926_140429` (the backup S412's install took at 14:04:29, the last database that walk was green on). Run 2 died
  in its probe with an IndexError on `open_pairs[1]`; run 3 with that source: 65/65. Later kits will need the same until S404's walk is
  revised to plant its own pairs — outside this brief, noted for the chat.

### Placing, restart, health
- Backups: `/root/finance/finance.db.bak_S414_20260926_174505` (backup API, 25,522,176 bytes); `finance_approvals.html.bak_S414_7de58315`
  and `order_rules.py.bak_S414_df6196fc` beside the files — read back at their FROM md5s.
- `systemctl restart clinic-finance` — active; healthz 200 (local and public, 17:50 IST); `/finance/approvals` and the items API answer 302
  to a plain curl (login gate, expected); journal: only the two gunicorn "worker was sent SIGTERM" lines of the restart.

### Not done / outside the brief
- The page's JavaScript was parsed, not driven: no browser or node on the box (brief §4 allowed the text/API assertion). The parser check and
  the structural checks say the block is sound; the owner's first tap on the live page is the behavioural proof — if anything misbehaves,
  the undo is the two `.bak_S414_*` files and one restart.
- The rest of the approvals page still uses its older `prompt()` / `confirm()` dialogs (Marg load, counts, bills, NOT-FILED) — not this brief.
- "last changes" (the audit list) does not update live after a tick; it refreshes when the block is next opened (said on the page).
- S404's frozen walk now depends on the 14:04 backup file staying on the box (named above) — a small walk revision for a later kit.
- No permission asked; nothing installed; no file the brief did not name touched.

### After publish
The kit folder reached origin in commit `7a910e4` (26-Sep-2026 17:47 IST) — a `PUBLISH_ALL` run by the other chat that swept the pending
tree while my installer was running (it also carried their `S415_NIGHTLY_SELFHEAL` and `S416_BUNDLE_ALLOWLIST` folders, not mine, not
installed by me); the kit's files had not changed since 17:44, and `git diff HEAD` on the folder is empty. This report went in `e78f543`
(17:51 IST; gate clean). On the box at 17:51 IST: `git pull` → HEAD e78f543; `md5sum -c` of the repository kit all OK; `diff -r` repository
kit vs the kit that ran: **IDENTICAL**; the repository installer answers ALREADY INSTALLED; the build lock (owner S414_RULES_PAGE_UX, held
17:45–17:51) removed; `/tmp/s414kit` cleaned; clinic-finance / clinic-portal / assetapp active; public healthz 200.
