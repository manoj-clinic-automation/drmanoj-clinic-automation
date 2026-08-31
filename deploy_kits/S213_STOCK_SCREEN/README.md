# S213_STOCK_SCREEN — the stock screen (F-245): the counting page joins the ledger

**Built and walk-proven offline at Session 213, 31-Aug-2026. NOT INSTALLED.**

## The gap (S212, measured)

`stock_snapshot` 376 · `stock_rate` 187 — filled by machines. `stock_count` 0 ·
`stock_count_item` 0 · `stock_diff` 0 — empty, because a PERSON must fill them
and there was no page for a person to fill them on. `stock_app.py` served JSON
only; no page in the repository fetched `/finance/stock/…`; the S207 counting
page (proven twice at phone width) published to an artifact, not this ledger.
**The two halves had never been joined. This kit is the join.**

## What ships

| file | role |
|---|---|
| `stock_app.py` **v2** (full file; every S208 route untouched) | adds `GET /finance/stock/page/count` — the counting page served live, its item universe injected from the ledger's OWN newest snapshot (no more per-machine copies of the data); `GET /finance/stock/page/diffs` — the checker's cause screen; and `/api/count` no longer trusts the client's `marg_qty` — **the server's snapshot is the authority**, a differing client claim is overridden and reported back |
| `stock_check_live.html` | the S207 template with the artifact-era self-publishing removed whole: **"Send to ledger"** POSTs the finished count to `/api/count`, the endpoint that raises differences. Every dummy-run fix survives verbatim (clamp-at-zero, batch-sum honesty, Not-OK-never-toggles, two-person gate, bill anchor, phone-width report) — the walk asserts each. localStorage stays as the counter's crash-proof working copy, under a fresh key |
| `stock_diffs.html` | open differences largest-first, one tap names the door (the eight causes, UNEXPLAINED honest by design); a difference still closes ITSELF when Marg's next snapshot agrees |
| `WALK_stock_screen.py` | **27 checks**: real Flask mount, real schema, snapshot by machine token, the pages served and role-gated, a count filling all three tables with exactly the right diff valued through the rate, the lying-client override, the mandatory bill anchor, cause naming, self-reconciling close, and the page's own guarantees |

## Deliberately Phase A (recorded, not forgotten)

Batch FEFO prefill needs batch data the server does not hold — the page's
batch boxes remain, honestly unprefilled ("Marg does not hold a per-batch
shelf figure"). Phase B: batches into the snapshot push, and reviving
`PUSH_STOCK_DAILY.bat` (never completed a run — S212 finding) so the snapshot
is a daily series. Orthotic grouping is by pack size (the rule that actually
decides counting mode); the archive's category flag can ride Phase B.

## Install

Three `\cp` and a restart (INSTALL_ONE_PASTE.txt). The live `stock_app.py`
must first equal the S208 kit bytes `5e5246eaeb1c9875dda4c625bbf4fc42` — the
install checks it before overwriting. Rollback = re-copy the S208 file.

## Gate
From INSIDE this folder: `md5sum -c SUMS.md5` · `python -B WALK_stock_screen.py`.
