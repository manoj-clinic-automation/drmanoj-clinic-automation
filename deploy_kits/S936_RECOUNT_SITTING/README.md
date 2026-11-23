# S936_RECOUNT_SITTING — the recount rule (D1046) and one bill per sitting (D1047)

Kit S936 · Sanjeevni session 506 · 23-Nov-2026 · built on S934's live bytes (the TO of S934_COUNT_NOW).

## What it does

**D1046 — the recount rule** (the owner, 23-Nov 11:18, after TRAMATEE P): a count short of the expected figure by about a delivery received in the
days before it is more likely a missed carton than a loss. Such a count is **held** (`stock_point.status = 'recount'`):

- never the shelf base — `stock_figure.points()` leaves it out, so the order engine (`order_rules._s454_shelf_snap → shelf_figure.figures →
  stock_figure.shelf`), the stock of record, the Stock check and every later judgment never see it;
- no loss line, no trace, not in the month's leakage or the watch list;
- one Count-now ask opened by itself (`by 'system'`, `recount_of` = the held point) with Darpan's question on his Abhi ginti card:
  *"Dobara giniye: pichhli ginti mein bill 502 (MANNAT PHARMA, 20-11) ka maal shayad gina nahi gaya. Uska carton bhi dekhkar poori ginti likhiye."*
- the next count of the item (any door) answers it: the held point becomes `'recounted'`, the new count is judged as any count and is never
  held itself (short again → a loss line by name). A morning-list correction ("Galat likha? Badlo") withdraws the recount instead.
- "About a delivery": the shortfall within `count.recount_tol_pct` (default 25 %) of a delivery's units — a tap (its tapped and its billed
  quantity) or a Marg purchase line — dated or arrived within `count.recount_days` (default 5) before the count; never under one strip / pc.
  Darpan's own flag ("Kuchh gadbad hai") is never held.

**First repair** (`repair_s936.py`, run by the installer after the files are live): TRAMATEE P TAB 15T — point 388 (21-11 10:43, 9:4) →
recounted; loss line 7 voided; trace 35 closed; the 23-11 count (44:0) re-judged against the base before it. Guarded row by row; idempotent;
the before-values go to `/root/finance/.s936_repair_before.json` for the undo.

**D1047 — one bill per sitting** (the owner, 23-Nov 11:41): Darpan's Abhi ginti card has ONE "Aakhri sale bill no." box at the top; each item
line shows the bill it will carry; "Sale hui? Naya bill likhiye" clears it for a new one. The server takes the sitting's bill (his newest Count
now with a bill today, within `count.sitting_minutes`, default 60) when an item comes without one and the page did not say `no_bill`.

## Files

| live file | FROM | change |
|---|---|---|
| `/root/finance/stock_watch.py` | 048b51df | the hold, the recount ask, the sitting's bill, three settings |
| `/root/finance/stock_figure.py` | d7fac10c | `points()` leaves out `recount` / `recounted` |
| `/root/finance/stockmatch.py` | e459af2a | the person to Darpan's view; `/api/now` takes `no_bill`; mount line `S936 stockmatch mounted v1.4` |
| `/root/finance/stockmatch.html` | 2a985d94 | the Abhi ginti card (Hindi) |

TO pins in `TO_PINS.md5`. Additive columns: `stock_watch_ask.recount_of / why / why_hi`.

## Proofs

- `synth_s936.py` — 38 checks on made-up data; the control (the live files) goes red.
- `liveshape_s936.py` — on copies of the live databases: the stock of record identical old vs new; the repair on the copy; the record after it.
- The earlier proofs not worse: S934 (five lines superseded by D1047 — `synth_s934_under_s936.py` puts those two inputs to the new rule and
  passes whole), S933, S928, S930, S927, S894.

## Install (one server line)

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s936kit && cp -rp /root/deploy/repo/deploy_kits/S936_RECOUNT_SITTING /tmp/s936kit && bash /tmp/s936kit/install_S936_RECOUNT_SITTING.sh
```

Undo: `bash /root/deploy/repo/deploy_kits/S936_RECOUNT_SITTING/undo_s936.sh`
