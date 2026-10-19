# S598_ARRIVALS_BY_LINE — the bill LINE is the unit of the one arrivals rule (F-942)

**Brief:** `claude_code_briefs/S598_ARRIVALS_BY_LINE.md` (v2, Sanjeevni session 328, 19-Oct-2026), from the design `S328_F942_READING.md` and the
independent read R1 (`03_WORKING_PAPERS/S328/S598_R1_REVIEW.md`: two blockers, eleven corrections, all folded in). The owner's word, 08:47 IST
19-Oct: "I want this orthotic sizes of one item … confusion to end so that this becomes clean." Closes **F-942**. No ruling, no new F.
**Charter:** `SANJEEVNI_BUILD_CHARTER.md` v1.1. Three Sanjeevni files, no new file placed, no new table, no new setting, no staff word. ONE data
step on `finance.db` (reversible). Kit shape: S583's / S593's. One restart.

## What it does

- **`stock_figure.py` (3.1) — the bill LINE is the unit of the rule.** Sizes of one orthotic share a 20-letter spine key, so the by-bill rule
  credited one size's order line with the whole family's bill (KNEE SUPPORT HINGED XL ordered 2, "billed 6" by bill 672 of 28-09, which carried
  M ×4 and L ×2 and no XL). Now:
  - **`_line_forms(ctx, name)`** — every spelling Marg or the count has printed for the item (`printed_forms`: the name, its ticked rename
    partner, the accepted seen_names), clipped as the estate clips (`{pad_norm(f[:27]), pad_norm(f)}`); a clipped order spelling (≥ 27 letters)
    also takes every rename group holding a form that starts with it (R1-C2).
  - **`_siblings(sp, k20, ctx)`** — True when more than one ITEM lives under the key (`sp_item` names, two spellings of one renamed item folded
    into one member). **`_matches(ctx, sp, k20, forms, sib, name27)`** — THE one match: the bill line's printed name in the forms, or the key
    alone when the key has no sibling. The only place a `name27` is compared with forms.
  - **`_purchase_lines_of(sp, k20, since_day, ctx)`** replaces `_purchases_of` — one row per bill LINE (`seq, name27, qty, free, units`), never
    summed by bill; `since_day=""` = every line of the key (rule a). **`_taken_lines(sp, k20, line_id, ctx)`** replaces `_taken_bills` — per OTHER
    order line of the key with a `billed_bill_no`: `(its vendor key, _bill(bill), ITS forms, sib)`; a bill line is TAKEN when `(supkey, bill)`
    equals an entry's and `_matches(entry.forms, entry.sib, name27)` is True (R1-B1: one bill line is never credited to two order lines of one
    item, whatever the two spellings).
  - **`_carried`** on lines: rule (a) reads the lines of the line's own bill that MATCH and sums them (`units=None` when none matches — Marg's
    answer trusted, the figure unknown); then (b) per line, the match, (c) (d) (e) by date and vendor as before; the first matching eligible
    line wins, the other lines of THAT bill that match are summed into it (two batches); the return gains `qty, free, seq, name27`, `units` is the
    LINE's. No matching line → None, and **`_family_bill`** (the family's bill that carried OTHER sizes: the newest bill since `lo` passing the
    loop's vendor-and-date test, `sizes` = its lines of the key as Marg printed them) is kept in the ctx and served by **`arrivals_open()`**
    as `family_bill`. `carried()`'s cache key unchanged; `expired`, `taps`, `scan_lines`, `scan_arrivals`, `shelf`, `marg`, `family`, `key_of`,
    `printed_forms` untouched. `VERSION 1.3`, `KIT = "S598_ARRIVALS_BY_LINE"`.
- **`porders.py` (3.3) — `detect_supplies` writes the matched LINE's packs:** `q = qty + free` from `carried()`'s return; the key-level
  `SUM(qty)+SUM(free)` query is gone. Nothing else in the function moves (fresh Ctx per row, `("c","d")` only, the writes, the audit,
  `_close_complete_orders`).
- **`stock_watch.py` (3.4) — the owner's words only:** `arrival_needs_you`'s two lines gain ` (its bill N of dd-mm carried SIZE, SIZE, not this
  size)` when `family_bill` is set — the clause built once (`more`) inside the function, used by both words lines (charter 8). English, owner only.
  `_arrivals`, `expected_units` untouched (4b-2's).
- **The data step (3.5) — `rejudge_s598.py`, run ONCE by the installer after placing:** every `purchase_order_line` with
  `detected_at >= 2026-10-19T08:03:00` (S593's seven: ids 2, 3, 28, 30, 36, 47, 50) is printed, saved whole to
  `/root/finance/purchase_order_line.bak_S598_<stamp>.json`, then re-judged with a fresh Ctx: AGREE = a (c)/(d) hit on the same folded bill number
  with the same packs → untouched; DISAGREE → `billed_qty, billed_bill_no, billed_date, detected_at` NULL and, only when `arrived_by='marg'`
  with S593's `line_detected` audit row (the system's own write), `supplied, short, arrived_by, arrived_at` NULL too; audit `line_rejudged_s598`
  with before / after. `_close_complete_orders` not called; `purchase_order.status` of 1, 10, 13, 20 asserted equal. **`undo_s598.py`** restores
  every column from the JSON, refusing a row whose `detected_at` / `arrived_at` moved since (R1-C6); written, never run by the installer.

## What the re-judge does on this box (the walk on the 19-Oct copy, the installer on live)

**Two rows cleared, not one.** The brief expected line 3 alone (KNEE SUPPORT HINGED XL: bill 672 carries M and L, no XL). The data says line 50
(L S BELT CONT GRAY UNISON XXX, order 20 of 07-10) is the same fault: Yuvika's bill YS…2627 of 07-10 was re-exported after the 11-Oct renames and
its belt line prints `L S BELT XXL CONT GRAY UNI` — the XXL size by name (the rename partner of `L S BELT CONT GRAY UNISON XXL`), not XXX (whose
partner is `L S BELT XXXL CONT GRAY UNISO`). The brief's §2 read that family as "one lump in 27 letters"; that holds only for the OLD spellings
(`L S BELT CONT GRAY UNISON X`), and the 18-10 export printed the new one. Under the brief's own rule a bill line answers only the size it names,
so the re-judge clears line 50 too — the decision is the brief's §7 "behaviour changes" applied, named here and in the report. The other five
(ANKLE BINDER BAMBOO M by 2627's `ANKLE BINDER M BAMBOO` through the ticked rename; CROCAL and PREGHYPE NT TAB by 3463; BRUTAFLAM GEL; CAST SHOE M
TYNOR) agree by name and packs and stay.

**The install-day state it restores (charter 7; R1-B2) — no word changes:** reception's *Orders* card: order 1's line 3 and order 20's line 50 read
`open` again and the `all` button returns on both (the page lists the 20 newest received orders; `_orders` holds them all); `_on_order` counts
Yuvika KNEE SUPPORT HINGED XL ×2 and L S BELT CONT GRAY UNISON XXX ×1 again; the orthotic shortage card loses both (4 → 2 items). The owner's
Needs-you gains the XL and XXX lines (their orders are scan-tied) and the clause on five lines: KNEE SUPPORT HINGED XXL UNISO and XL (bill 672:
M, L), ANKLE BINDER BAMBOO L (2627: ANKLE BINDER M BAMBOO), L S BELT CONT GRAY UNISON XXX (738 of 18-10, the newest family bill: M, XL), and
KNEE IMMOBILIZER UNISON XL (672: KNEE IMMOBILIZER UNISON L — the rule working on a third family).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_figure.py` | 92367a196b360f0cded4cda6a5ded700 | cb577821d9e1eb40110312b4331df9ef |
| `/root/finance/stock_watch.py` | c5f3ce21a785c45df58f21932cf920e7 | 299c3ef76b73a10e4af1cd15974c7a3f |
| `/root/finance/porders.py` | 78ea72be7d87a7c56c65de7d4c96a952 | e5a5c4d4dfa15c3ecd0b0cdf4786abcd |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `shelf_figure.py` 23b2394a, `order_rules.py` 8d078dbe,
`porders_s454.py` 40f1755a, `order_sheet.py` 1f1e85c1, `stock_app.py` 4f73d0b0, `amir_day.py` 3af992d9, `spine/spine_build.py` e3d3ed85,
`spine/spine_read.py` 827b0040, `item_alias.py` 111a8e48, `qty_words.py` 706db7cc, `marg_purchase_rows.py` 41d68148 (pinned to the bytes read on
19-Oct); and proved unmoved: `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (84 lines, `# S577_WITNESS` once), `spine.db`'s
schema. The four ticked renames the kit stands on are read from `item_alias.done_rows` at the open (STOP if one is missing). Service
`clinic-finance`, restarted once. Window 08:00–23:49 IST, the spine green and under 30 minutes old; `DOCTOR_AUTO_OFF` around the restart.
No duty added, moved or removed: `DUTY_MAP` untouched.

## The install (`install_S598_ARRIVALS_BY_LINE.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS) → the FROM pins and the read-only md5s, the crontab → the four renames → the spine green → build from the
live bytes (13 anchored edits, each anchor exactly once) → compile on both pythons → scratch (the finance folder twice, finance.db / assets.db /
spine.db by the backup API) → the walk on the OLD files (every control red) then on the NEW files → DRY stops → the install-day state BEFORE and as
the NEW files read the same copy → backups (`finance.db.bak_S598_<stamp>`, `<file>.bak_S598_<from8>` ×3) → `DOCTOR_AUTO_OFF` → the three files
staged and renamed in ONE command → one restart → healthz 200, the pages 302 → journal clean → **`rejudge_s598.py` once on live** (the rows' JSON
first; its result line must equal the walk's on the copy) → `porders.detect_supplies` once (writes quoted; expected none new) → the state AFTER
(lines 3 and 50 open, XL off the card asserted) → nothing else moved → md5 read-back → the off-switch removed. Red after placing: the three files
back in one command, one restart, healthz; if the re-judge had run, `undo_s598.py` from the JSON with the row diff printed.

## The walk (`walk_s598.py`)

On scratch copies only (the real app in one process, the walk's own header session for reception, Darpan, Amir, Shavez and the owner; its own
rows by key `W598 …`; the spine copy never written by the code under test — the synthetic bills go to a second copy, `spine_syn.db`, through a
plain rw connection with `sp_meta.built` bumped). Controls as the brief's §4: (0) the four renames and the seven rows; (1) bill 672 — line 3 →
None with `family_bill` 672 [M, L], line 4 likewise, line 1 by rule (a) = the L line's units with seq and name27, line 3 as marked by (a) → units
None; (2) bill 2627 — line 2 → the `ANKLE BINDER M BAMBOO` line through the rename, packs 1 = S593's write, line 48 → None with `family_bill` 2627
[M], the four spellings on one key told apart; (7) S593's 24 lines replayed OLD vs NEW (how / bill / packs; the disagreements exactly 3 and 50;
the count of open lines ≥ 27 letters); (8) `rejudge_s598.py` on the copy — 3 and 50 cleared, five untouched, one audit row each, statuses equal,
idempotent; `undo_s598.py` on a third copy restores all seven byte-equal, then refuses a row whose `detected_at` was bumped; (9) the owner's lines
with the clause; (10) the staff screens and the owner's pages dumped and diffed against the OLD files' dumps — the only differences the three
states on reception's and the owner's `api/state` and the owner's arrival lines, no word on any staff page; (11) `figures()` for every master and
orthotic item equal OLD vs NEW; (3) two sizes on one bill → each line its own, A's mark written → B still carried; (4) one renamed item twice /
a single-member key with a clipped bill spelling → the second line None (green on OLD too, by bill — stated); (5) the key fallback; (6) two
batches → one hit, qty summed; (12) the greps; (13) the spine untouched, selftest green, healthz. `--expect-red` is the negative control;
`--state` prints the install-day state.

## Charter

- **Retired:** `_purchases_of` (the by-bill lump) → `_purchase_lines_of`; `_taken_bills` (per bill) → `_taken_lines` (per bill line, keyed on the
  match); rule (a)'s by-bill query → the same lines read; `detect_supplies`' key-level `SUM(qty)+SUM(free)` → the matched line's packs. One rule,
  one place, one match function.
- **Left (named):** sizes that agree in their first 27 letters stay one lump on an OLD-spelling bill (Marg's report cannot tell them apart; R1-C3);
  a sibling line with no bill line of its own name (an unticked rename, a Marg typo, a size that never came) → None → counted as arrived until
  expiry → the owner's line, sitting `open` on a `received` order where every staff door says `not_sent` — only a Marg bill naming the size can
  close it (the D712 gap, unchanged; today: XL, XXL, L, XXX); the family split of a shared key's movements in `shelf()` / `marg()` (approximate
  by design; the `sp_alias` fold means a post-rename bill line still carries the old key); the order line's own 27-letter match in `_arrivals` /
  `scan_lines` (charter 12, SEEN since S577); the stock proof's family handling; 4b-2's files; S537's older marks (line 1 agrees, read-only).
- **Charter 5:** the re-judge sets columns NULL only on rows the SYSTEM wrote (`arrived_by='marg'` with S593's audit row), never a person's entry;
  the JSON and the `line_rejudged_s598` audit row are the old row kept and marked.
- **Decided (the brief left it open or the data differed):** `_family_bill` does NOT exclude a bill line already credited to the sibling order line
  (R1-C9 said "not in taken"): the clause says what the bill carried, and the brief's own controls 2 and 9 expect the clause for ANKLE BINDER BAMBOO
  L whose M line is line 2's; line 50 cleared beside line 3 (above); `detect_supplies` on live is run directly, as S593 did (there is no
  `order_sheet._every_read`; `cron_pass` would also send notices); the clause is built once inside `arrival_needs_you` and used by both words lines
  (three anchored edits there plus the docstring, not one per words line).
- **Behaviour changes (rule 4, 1b, 7):** a sibling size with no bill line of its own name is "not in Marg's purchases" with the family's bill named;
  `billed_qty` is the matched line's packs, never a family sum; one bill line is credited to at most one order line of an item; two of S593's seven
  marks are corrected on install and the three screen STATES return to their pre-08:03 shape (no words).
- **Dependency state at install:** S593 live (porders 78ea72be), S594's crontab line in, the four renames ticked, the spine green,
  `order.source = marg_sheet`, `arrival.back_days` unset (default 2), `arrival.bill_grace_days` 3.
