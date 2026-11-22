# S930_STOCK_CHECK_PAGE · Sanjeevni session 503 · 22-Nov-2026 · AFTER S928

The owner's Stock check page to his mock-up v5 (https://claude.ai/artifact/XzqcBUHoroPyTt7xG8bNea, "ok" 22-Nov 07:49, D1037): one page in
place of Stock drift and Stock now (the stock plan's "13 pages to 5", `S501_STOCK_PAGES_CONSOLIDATION.md` §7), every figure from the one
stock function.

* **NEW `/root/finance/stock_check.py` + `stock_check.html`** (mounted by `sanjeevni_day.init` beside hub_panels; roles as the drift page's):
  `/finance/stockcheck/` — Marg's figure (the newest usable closing), the shelf (the last count carried forward alone), the delivery
  waiting for Marg (by the scanned bill, S928), the gap; each item ONCE under Marg's current name (a count under an old spelling read
  through the rename memory, F-1563); **Darpan's counts** (every spot/darpan point, 30 days, what it was judged against, the evening
  tag, "you asked"); **Count this** on every row and in one box with name suggestions (stock_watch.ask → the head of his next list; the
  open asks and the next list shown); **Need a look** (medicines a strip or more apart, the under-one-strip fold, orthotics apart); **the
  deliveries waiting for Marg** with each line's tap against the bill ("10:0 short, back on the dealer's next order"); the items Marg
  holds with no shelf figure yet; **the count names Marg no longer prints** (the identity question's cases); the items that agree; the
  reports behind the page. Doors: `/api/rows`, `/api/count`, `/api/find`, `/api/healthz`. The retired addresses `/finance/stock/page/drift`
  and `/page/now` send here (an `app.before_request`, exact paths only); their code stays, unlinked. English, PC first, no dialogs.
* `/root/finance/sanjeevni_day.py` c01bf05b → the mount (one try block).
* `/root/finance/stock_watch.py` (S928's TO) → a count line on his Needs-you opens the page (`href`).
* `/root/finance/finance_ui/finance_approvals.html` bc5d52c9 → the Hub's Go to: **Stock check** first under Stock & expiry; the 06-Sep
  count's hub named as closed; 'Stock now' gone.

Walk: `walk_s930.py <files> <COPY of finance.db> <the S928 kit folder>` — the S928 synth's fixtures, the module on a bare Flask app with a
stub login: 31 checks (the page, the redirect, the data-item Count buttons, the 2-minute cache and ?fresh=1, the viewer, the note word, the trailing slash, every door, the figures of the made-up items, Count this once and twice, the Needs-you href,
the Go to line, no dialog, no long number); the control goes red on 3. `liveshape_s930.py` — the page built on COPIES of the live
databases on the box (≥ 200 items, under 2 minutes). walk_s927 and synth_s928 run on the new files (never worse).
Install: one server line (the installer's header), after S928. Undo: `undo_s930.sh`.
Cold review (first look): NOT SAFE (1 MUST: a name inside a JS string in onclick) → v1.1 fixes it and the 5 SHOULD + 1 LOW (the since-moment as S928 A5b, no core on a clamped shelf, a 2-minute cache with 'read again', the viewer admitted as before, Darpan's free text not shown, the trailing slash).
