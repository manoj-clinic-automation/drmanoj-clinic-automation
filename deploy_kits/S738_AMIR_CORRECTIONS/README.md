# S738_AMIR_CORRECTIONS — Amir's correction list; the owner's step view with the scan in place

*Sanjeevni session 396 · 06-Nov-2026 · D839 · D840 · the purchase reconciliation, kit 2 (`S391_PURCHASE_RECONCILE_PLAN.md`), built to the owner's mock https://claude.ai/artifact/8wUuc5o8bNUp19xWRFdtXs (his OK 21:28 IST, after his changes 21:23–21:27: the bill date, the scan number and a folded in-page scan on every line of his page, PC first; a back-to-top button on both pages; the bill date on each of Amir's cards).*

## For the owner
- **Amir's card "Marg sudhar" gains "Purchase bill Marg mein theek karein · n"** — one card per bill whose register line is *Amir: a Marg correction*, with **Bill ki tareekh** and **Kaagaz dekhiye** (the scan opens):
  - the paper reads **less** than Marg → *Marg mein bill ₹X kijiye*;
  - the paper reads **more** → the paper's lines Marg lacks (named only when they add up exactly), and both roads: *a return written on the bill: the full bill and a purchase return; else add the line*;
  - **entered twice** → *Marg mein ek entry hataiye*.
  He taps nothing; a card leaves only when **his own export** shows Marg = the paper. A green line counts what his exports proved in 14 days.
- **Your step view** (`/finance/purchase/page/check`): every scanned line of rows 1–5 shows the bill date and the scan, and a folded **Show scan ▾** that opens the scan right there beside *what the scan read · Marg*; row 3 says *on Amir's list since dd-mm* and lists what his export proved (✓, not counted); a ↑ back-to-top button; columns with a header on the PC, one card per bill on the phone.
- September stays parked; a finalised month is never listed.

## What changes — three files (`make_s738.py`: every FROM pin exact, the one anchor exactly once, else REFUSED)
| file | FROM → TO | what |
|---|---|---|
| `/root/finance/scan_register.py` | `4d8432ea` → `f4706186` | the S738 section appended (`sec_sr738.txt`): `s738_fixes` (read only; a month that cannot be read RAISES, so nothing is synced; one result per web request), `_s738_missing` (lines named only when every Marg line is accounted for on the paper, the paper's lines add up to its total, the unmatched lines add up to the difference within ₹2, and none is a freight / round-off / tax line), `s738_sync` / `s738_tracked` (table `s738_fix`; a line is credited to Amir only when Marg's amount changed from what it was when first shown AND a bill-wise export arrived after; a double only when no other live entry of it is left; anything else that leaves is *gone*, never credited), `s738_scan_ok`, and the step view: `_ck_line`, `check_rows`, `check_body` wrapped (the folded viewer, the header, row 3's since / proved, the CSS, the ↑ button) |
| `/root/finance/amir_day.py` | `10a5f9c4` → `ff195fc0` | the S738 section appended (`sec_amir738.txt`): `state` (the list read once, then the card derived again), `_card_rows` (the block after the scans row; his line — step 6's tick), `settle` (the sync, only when the list was read; rolled back on a fault), `_shell` (a ↑ link, no JavaScript) |
| `/root/finance/purchase_app.py` | `5fde52aa` → `7a0c615e` | one route: `GET /api/s738/scan/<id>` — the scan inline (PDF / JPEG / PNG by its bytes, `nosniff`); the doctor any captured pharmacy scan, Amir (`purchase.scan_file_users`) only a scan on his list, everyone else 403 |

## The proof
- `walk_s738.py` — **42 checks, 42 green** on made-up rows (its own temp folder, made-up scan files): the list (less / more with the one line named / more with none / twice / an agreeing bill absent); Amir's page (the count, the bill date on every card, the words, both roads, *Kaagaz dekhiye* by the S738 door, no "check / export again" sentence, the ↑ link, the tracker kept); the door (Amir on / off his list, another login, the doctor); the step view (date and scan in columns, a folded viewer per scanned line loading only when opened, the read-vs-Marg table, since when, the ↑ button, the PC layout, the GET writes nothing); the proof by his own export (the line leaves, settled with the export's arrival, audited, the green line at once, the owner's ✓ line, the door closes for Amir, a later export reopens it); a line that left because reception re-typed the amount is NOT credited; a month that cannot be read syncs nothing; a negative amount prints right; his day held as Marg work. **Control on the live files: 40 red — every S738 check.**
- **S736's walk: 1 red, S726's walk: 5 red — all layout checks of the step view's lines (now in columns, the owner's ask) and the 390-px regex catching `min-width:900px`. S711's walk 38/0.** The installer requires exactly these.
- `proof_s738.py` — on the box's own databases, both opened `mode=ro`: Amir's list as it stands (supplier, bill, date, scan, kind, Marg, paper, the lines named); last line `PROOF S738: N correction(s) for Amir (less a, more b, twice c)`.
- Rehearsed on a made-up root (stub health / systemctl / journalctl): DRY (nothing written, the database's md5 unchanged) · install · ALREADY INSTALLED · a forced red at [7/8] and at [8/8] (three files back) · a changed live file refused at [2/8].

## Install — DRY first (its proof read by Claude), then the real line
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s738kit && cp -rp /root/deploy/repo/deploy_kits/S738_AMIR_CORRECTIONS /tmp/s738kit && DRY=1 bash /tmp/s738kit/install_S738_AMIR_CORRECTIONS.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s738kit && cp -rp /root/deploy/repo/deploy_kits/S738_AMIR_CORRECTIONS /tmp/s738kit && bash /tmp/s738kit/install_S738_AMIR_CORRECTIONS.sh
```
Gates: SUMS, KIT_ID, the window 04:00–23:30 IST, the build lock, the three live pins, the rebuild (both pythons), the walk green, the control 40 red, S736's / S711's / S726's walks with their named reds, the proof; backups `*.bak_S738_<from8>`, placed and read back, `clinic-finance` restarted, healthz, Amir's page / the step view / the scan door 302/401/403 without a login, the journal (new PIDs only), the walk on the placed files, the proof by the placed files. Any red after placing puts the three files back.

## Undo
The installer prints the one line. The table `s738_fix` stays (nothing reads it after an undo).

## Reviews
- Visual (Chromium, 390 / 1366 px): taken in — the rows' own CSS (`.row`) no longer lays rows sideways; the column header; the Show scan button at the line's end, *Hide scan ▴* when open; the table's labels in normal case, no word break; *Scanned dd-mm hh:mm*; a 560-px scan area and a plain message when a scan cannot be shown; Amir's figures in dark 15-px text, the date bold, a compact *Kaagaz dekhiye*, the twice-entered numbers in the sentence, the mock's export note.
- Cold review R1 NOT SAFE (packaging: SUMS stale, the kit not the build walked) + 5 should-fix — all built: a failed month syncs nothing; credit only on a changed Marg amount after a later export, a double only when its twin is gone; the stricter missing-line rule; speed (one result per request, finalised months skipped, the door's fast read); the negative amount.

## Named, not done
- Returns themselves (kit 3): a *more* line with a return written on the bill is Amir's (full bill + purchase return) — kit 3 tracks the purchase return's credit.
- A PDF in a frame may not draw on a phone's browser; *Open the scan in a new tab* is beside it.
- Cold review R2 SAFE TO INSTALL; its should-fix built (the list kept per web request only).
