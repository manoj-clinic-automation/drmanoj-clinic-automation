# S927_HUB_NEEDS_YOU_INLINE · Sanjeevni session 502 · 22-Nov-2026

The owner (09:39, 12:08 IST): the Hub's Needs-you redesigned — "better layout, inline expandable lines with the scans and item lines inline, each line's full flow workable from the Hub"; "Counted as arrived, not in Marg — should open inline the scan and purchase lines etc, so that full audit can be done without leaving the page; and do this wherever applicable". Mock-up v1 OK'd: https://claude.ai/artifact/UvcwHAqo1rKtfq9ii7gsP2

* **NEW `/root/finance/hub_panels.py`** (mounted by `sanjeevni_day.init` beside `hub_cash`): `GET /finance/sanjeevni/api/needs-you/panel?kind=&ref=` — one line's panel as HTML; `POST /finance/sanjeevni/api/needs-you/act` — its doors (checker and above):
  * `porders` — the S926 section (`order_flow.team_table_s926`) with its own doors, inline.
  * `arrived` (ref = the order line) — the order (what, when, who tapped / the scan), **the scan** (thumbnail, full size, its read lines with this medicine marked), **Marg's purchase lines from that dealer since the arrival** (the same name marked), the Marg stock; doors **Ask Amir to enter it** (a tap job on his card, once), **It is this Marg line** (pick a line → the order line is marked billed on that bill, as `porders.detect_supplies` writes it; a different Marg name is learnt as the medicine's partner in the one name list), **Never came** (the line reads short; it carries as a shortage).
  * `tapped` — goods tapped as arrived with no bill: the order's lines and who tapped (read only).
  * `voucher` — a count voucher Marg never moved: Amir's job state (made, tapped done when); door **Ask Amir again** (a job, once a day). Accepting Marg's figure belongs to the Stock check page (next build).
  * `expiry` — the current run's batches (read only; the taps are on the expiry page).
  * `seen` — an information line: **Seen** (not shown for 30 days; table `hub_seen`).
  * `decorate()` — every line gets its panel kind + ref and its age where the source knows the moment; Seen lines left out; **the "Orthotic shortages" line retired** while S926's purchase line stands.
* **`sanjeevni_approvals.py`** — the lines pass through `hub_panels.decorate` before S761 groups them (`NEEDS_YOU_WITHOUT_S927=1` for an older kit's frozen walk only).
* **`stock_watch.py`** — `arrival_needs_you` lines carry `panel="arrived"`, `ref` (the order line id) and `since` (the arrival moment).
* **`finance_ui/finance_approvals.html`** — each line: **▾ open here** (the panel fetched and its scripts run; a tap inside never leaves the line), the age chip (amber; red past 14 days), the arrow still opens the page; **three tiers** (Now · Your word · For your information); the arrived group drawn one line per item.

Walk: `walk_s927.py` on a copy of the database — 35 checks (decorate on a made-up answer and on the copy's own open arrivals; every door; the panels render; no 10-digit run); the CONTROL (the live files) goes red. The whole Needs-you chain runs on the copy (21 lines here without the spine).
Install: one server line (the installer's header). Undo: `undo_s927.sh`.
