# S857_CHECK_OPEN_PATHS — the purchase check names what is open, and how each resolves (17-Nov-2026, Sanjeevni session 476)

**Why.** The owner, 17-Nov 20:54 IST: "NEFT on hold · 1 open" does not say what is open; what is open should be named, its full flow inline on
the page, expanding on a click, with the resolving path there too. Row 7's "1 your confirm" reads as either "you must confirm" or "you have
confirmed" — better framing. Anything still pending highlighted with its full resolution path on his page.

**Now** (no new page):
- **The strip** of the purchase check (`/finance/purchase/page/check?month=`) reads "NEFT on hold · N open — <what is open>" and expands on a
  tap: each open item with its row, whose it is, its numbered path to resolution and "Open row N ▸", which opens that row in place.
  One source: `month_asks.open_items` (rows 2–6 from the register, row 7 from the dealer summaries, row 8 from S855's asks).
- **Every row holding something open** carries an amber left border.
- **Row 7's words:** "settled by your confirmation" when row 3 has nothing waiting, "waiting for your confirmation (row 3)" when it has;
  the same on the dealer's line and the snapshot.
- **The month card** (S855) counts what is open; a bill a fresh export will clear is listed inside that export ("It clears by itself: …").

**Files:** `scan_register.py` 95c5ad0e (one tail block, `make_s857.py`) · `month_asks.py` d0592c40 (replaced whole: `open_items`, the card).
**Proof:** `synth_s857.py` on a made-up counted month in a copy of finance.db (T0–T7, the real page in Flask); the control (the live files)
red. On the box: R1 on copies of the live databases (every open month's check draws, its strip naming what holds it), S855's own proof green on
the new files, and walk_s781, walk_s761, walk_s750/753/755, synth_s849, synth_s850, walk_s814, walk_s845 the same on the live and the new files.
**Install:** publish, then the one server line in the installer's head. **Undo:** `bash /root/deploy/repo/deploy_kits/S857_CHECK_OPEN_PATHS/undo_s857.sh`.
