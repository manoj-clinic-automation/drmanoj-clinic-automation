# S334_SHAVEZ_MORNING — Shavez's morning tile, certified by the spine's readers

**Project: Sanjeevni — Pharmacy & Marg · session S274 · 20-Sep-2026.** D567 items **1** and **2**, from `SHAVEZ_MORNING_TILE_PLAN.md` (S270, the owner's word of 18-Sep) and `START_HERE_SESSION_274.md` §0.

## What it does

The tile **'Aaj ki reports'** (`/finance/reports/aaj`, S243 — already granted by name to `shavez` and `amir`) becomes the morning page the plan describes:

| plan § | on the page |
|---|---|
| 2.1 | opens on **one thing** — *"DD-MM-YYYY ki bikri report aur closing stock nikaliye"* — with the Marg path and the settings (Bill Wise Statement · Report Type Detail · With Item Details Yes · the date; Closing Stock · poore store · Totals). The date is **yesterday, or the last day the counter sold**: the counter is closed on Sundays (measured Jul–Sep 2026, no Sunday sale day), so a Monday asks for Saturday's. |
| 2.2 | a file that lands reads **⌛ aa gayi HH:MM · jaanch ho rahi hai…** (the door's VERIFIED = structural). He may start the second export meanwhile. |
| 2.3 | **✓ aa gayi, jaanch poori · 24 bills / 374 items** only when the report **re-adds under the spine's certified reader** — the reading `/root/finance/spine/readings/<md5>.json` (kit S331), or, for a report the door KEEPS on this box (closing stock, the lists), the same `marg_read.py` run here on the kept file, cached in memory. A witness that fails reads **✗ jaanch me fail — dobara banaiye** with the reason in plain words and the check names in small type. Both in and certified → *Aaj ka kaam poora*. |
| 2.4 | both arrived before midnight → *Kal raat ho gaya*. |
| 3 | **the missed morning:** on a counter day, from **10:00**, if the pair is not in — a red banner *"Kal ki … baaki hai — abhi mat nikaliye, counter par bikri shuru ho chuki hai"*, naming only what is missing; from **21:00** it turns to *"Ab nikaliye"*. The same line, in English, rides the owner's card. The banner never blames a person (attendance is not visible to the finance server yet). `REPORTS_SALE_START` / `REPORTS_SALE_END` move the two clocks; the medical-PC agent's first-sale time replaces them later (plan §4). |
| 1 | **on the 1st** (kept until the 7th or until they arrive): Stock valuation and Stock expiry as on the last day of the month before. The spine has no reader for these two; their tick is the door's format check and says so on the page. |
| 6 | **the owner's own three** (item 2): the salt-wise list older than **8 days**, the category-wise or item list older than **35 days** → *" · OVERDUE: salt list 9 days"* appended to the `line` the hub's Marg card already prints (`/finance/reports/aaj/api/status`). Age = the newest of the spine's certified reading (`sp_export`) or the door's VERIFIED copy. The category list is known only to the spine (the VPS door has no signature for it — S270, the manojz-only signature). |

Amir's purchase rows and the salt-task row are as S243 left them (his own tile confirms his work).

## What it touches

- `/root/finance/reports_tile.py` — **78afc54b (S243) → 2798436712be69eb3c4486a0913e38f4**, full-file replacement, backup `reports_tile.py.bak_S334_78afc54b`. Restart `clinic-finance`.
- **Nothing else.** No `portal.py`, no `tile_grants.json` (the tile and its grants exist since S243 v13), no `finance_app.py`, no crontab, no table, no file written by the page (one in-process cache). Reads, never writes: `/root/finance/spine/readings/`, `/root/finance/spine/spine.db`, `/root/marg_ingest/archive/`.

## Proof

- `reports_tile.py` selftest: **40 checks, 0 failures** (in-memory db + a scratch readings folder): the due-day rule, the banner at 10:00 / 21:00 / Sunday, arrived-not-ticked, a failed reading = dobara, a passed reading = tick with count, night-before, the stock_feed row not hiding the door's certificate, the monthly rows, the owner's three lists at 5 / 18 / 36 days, Amir's rows and the salt row as before, the page rendering every state, two readings that certify nothing.
- `walk_s334.py` on the PC (20-Sep, nightly DB of 01:40, readings made from the real September exports with the S331 reader, the kept closings staged under their VPS names): **13 checks green** — today's page renders with no 10-digit number; 39 verified sale exports of 12 days, 8 certified, 0 failed the reader; three kept closings certified (374 / 374 / 377 items); the last 14 days render as picked dates; negative controls: no readings and no kept files → nothing ticked; a failed reading → BAD; the banner names only what is missing; a Sunday raises no banner.
- The installer runs the same selftest and walk on the box against a scratch copy of the live database and the real readings before placing anything; red → nothing placed; red after placing → byte-identical restore. Health gate per F-525: `/finance/healthz` 200, the page 302/401 (login gate), the kit's own `api/healthz` names the kit.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S334_SHAVEZ_MORNING/install_S334_SHAVEZ_MORNING.sh
```

## Not in this kit, said plainly

- The first-sale time from the medical-PC agent (plan §4) — the 10:00 rule stands until it is measured.
- Attendance on the banner (plan §3, *"Shavez aaj nahi"*) — the finance server cannot see the attendance app yet (the S241 gap); the banner blames nobody.
- The certificate's **lag**: a sale export is read by the spine only once manojz has mirrored it to Drive and `spine_evidence.py` has run (every 10 min, 08–23). Until then the row is honest: *jaanch ho rahi hai*. The walk on the box prints the measured lag door → reading for the last 12 days; if it is hours, the cure is the door running the reader at take time (a later kit, the owner's call).
