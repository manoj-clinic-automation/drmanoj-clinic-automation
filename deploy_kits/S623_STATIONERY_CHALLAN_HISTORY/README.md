# S623_STATIONERY_CHALLAN_HISTORY — the Variety challans as the stationery received history (D756)

*Kit S623 and D756 claimed at the S323 close's chat (board `_numbers` v588 → v589, 22-Oct-2026 12:1x IST). Built, walked and
rehearsed in the Scan App chat at session 337 (22-Oct-2026), in the chat itself — the owner, 14:07 IST: "do the previous session
pending build inside this chat only. Do not use API for this". Brief: `claude_code_briefs/S623_STATIONERY_CHALLAN_HISTORY.md` v2
(aada3d74) with its R1 (8cfeea39, 3 BLOCKER · 7 CORRECTION · 8 NOTE — all applied).*

## What it does, in the owner's words

His board note 22-Oct 06:31 IST: *"scanapp - populate all entries that are possible from the variety challans and shavez excel
files"*, with his rulings of 12:09 IST. The six Variety Stationers challans are entered as stationery **received**, each paper on
its own challan date — all before his 18-Oct opening count, so the nine counted stocks stay exactly as he counted them.

| paper | challan date | lines written |
|---|---|---|
| B-0003 | 24-08-2026 | A4 paper (75 gsm) 1 ream |
| B-0013 | 15-09-2026 | File folder DC-217 1 (₹240) · Register 192 pages 3 · Copy — Classmate 72 pages 6 (₹40) · Small copy — Anmol 96 pages 4 (₹40) · Register 72 pages 6 · Register 104 pages 12 · the ring file (already matched) re-dated · the token line **corrected 100 → 1 packet** (₹120) · the NK Pathology estimate books left out |
| B-0109 | 01-10-2026 | Register 192 pages 6 · Register 104 pages 2 · Clear bag (premium) 2 (₹44) |
| B-0114 | 03-10-2026 | File folder DC-217 2 (₹240) |
| B-0133 | 07-10-2026 | A4 paper (75 gsm) 20 reams |
| B-0163 | 14-10-2026 | X-ray envelope 8.5 x 10.5 — 500 |

**What his Stationery page shows after it** (https://followup.dr-manoj.in/scanapp/stationery): the nine counted stocks unchanged;
A4 paper 21, File folder DC-217 3, X-ray envelope 500, Token 1 (less anything issued since); October's *Received this month* and
*The papers that fed the stock* = B-0109, B-0114, B-0133, B-0163 (B-0003 is August's, B-0013 September's) — so a counted item can
show "received" in October without its stock rising (it came before the count). On the sorting desk each paper shows its lines
matched, into the stock.

## How (no code changes)

- **No file is changed or placed, and no service is restarted.** `history_s623.py` imports `/root/assetapp/stationery.py`
  (pinned 18268ff0, S585's TO) read only for its own rules, and writes `stationery_line` rows in the exact column shape of its
  `save_lines`. `sorting_desk.py` (110335ea) is pinned because the line numbers follow the desk's reading of each paper.
- **One day and one time per paper** (R1 B1): the challan date, 12:00 IST (computed with +05:30). B-0013's two lines already
  matched on the desk are re-written the way a desk re-save writes them (old rows voided and kept).
- **Line numbers = the paper's own reading** (R1 B2): checked on the box — the reading's line at that number must carry the
  expected word and quantity, else the paper is left alone. A later desk Save of the paper says *Stationery: unchanged.*
- **Gates per paper** (R1 C4): found once by its stamp, not a second scan, not pharmacy, in Stationery & packaging now
  (`paper_counts`); its saved lines exactly the expected ones; its date before the last count of every counted item on it.
  An absent or retired item skips only its row (C6). Each line's unit is its item's own (C5).
- **One transaction** with the done-key `stationery.history_s623`; the stock read before and after — every item must move by
  exactly what the written lines account for (counted items: 0), else it rolls back by itself (C2).
- Every row written: `by_whom` = `history (Variety challans, S623)`; every row voided: `voided_by` the same (B3).

## Install — the owner's one server line (after his publish)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S623_STATIONERY_CHALLAN_HISTORY/install_s623.sh
```

Order: gates → the build lock → ALREADY INSTALLED (the key) → pins → the walk on made-up databases (32 checks, the negative
control and two mutants) → on a scratch copy of the live database: the control red, the step, a second run writing nothing,
verify green, the undo rehearsed back exactly → the database backup `assets.db.bak_S623_<stamp>` → the step live → verify live
(a red check undoes it at once and marks the key undone) → healthz → what his pages show → `S623_STATIONERY_CHALLAN_HISTORY: DONE`. `DRY=1` stops before
the backup.

## Undo

```
python3 -B /root/deploy/repo/deploy_kits/S623_STATIONERY_CHALLAN_HISTORY/history_s623.py --undo /root/assetapp/assets.db
```

It voids S623's lines (kept, never deleted) and brings back B-0013's ring file and token-of-100 lines exactly. A paper that a
person has re-saved on the desk since, or taken off Stationery, is left as it is (its lines are then that person's). The key is
marked *undone*, so a re-install may write again. The database backup `assets.db.bak_S623_<stamp>` stays beside the database.

## Proven before the publish (in the chat, 22-Oct)

- the walk `walk_s623.py` on made-up databases of the live shape (read from the owner's desk, read only, 14:2x IST): **34 green,
  0 red** — the control (verify on the old state) 27 red; the stock guard's mutant refused; the reading check's mutant shows the check matters;
- the rehearsal `rehearse_s623.sh` on a made-up root: **8 green, 0 red** (dry run, install, lock released, backup, ALREADY INSTALLED,
  other bytes refused, another build's lock refused and left, no paper writable → refused with nothing written);
- an independent cold review K1 (in the chat): SAFE TO INSTALL, 0 blockers, 5 corrections — all made in place (the key marked
  *undone* by an undo; the undo leaves a paper a person took off Stationery; the control on the live copy must be 20+ red; the
  undo's own exit read; the pins before ALREADY INSTALLED), and its notes 8, 9, 11 (active item first; a warning when a line is
  left out; one memory copy per verify). Its probe of correction 2 re-run green;
- the earlier kits' walks (S585, S568, S582) are not re-run: no code changed (R1 note 6).
