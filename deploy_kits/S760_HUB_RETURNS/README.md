# S760_HUB_RETURNS — the hub's Returns card as approved (Sanjeevni session 414, 09-Nov-2026)

**The owner's approval: D873** (23:22 IST 8-Nov and 05:32 IST 9-Nov — the Returns mock `Main.dc.html` and the batch check `Batch.dc.html` on the design canvas). Fault repaired: **F-1200**; the returns half of **F-1199** (one waiting count on the page). **Four files of this project; no table, no setting, no money figure changes; the hub's reads write nothing.** `finance_app.py` is not touched.

## What it does
1. **Every month on one card.** The month picker goes. One read, `GET /finance/darpan/api/cn-hub` (role *checker*, as cn-detail), built by `returns_kinds.hub()` on the same engine (`finance_returns_audit`) and the same enrich (the S406 rule) as cn-detail.
2. **Needs your OK — every month together, newest first.** Each line names only the medicine(s) in question and the money in question; **Approve / Reject on the line** (the owner only — `cn-approve`, untouched). Approve is a second tap ("Tap again to approve ₹x"); Reject asks why (prefilled) and records *recover ₹x (items) — why*. **Reject never recovers more than was refunded.**
3. **Repeats** — one batch of one medicine in two or more waiting returns — named once at the top.
4. **The batch check** for a medicine the patient never bought: the spine's SALES of that medicine with that batch in the last 180 days, **a count only** — amber "sold by us N times, never under this patient's ID", red "we never sold batch X". No other patient's name, ID, phone or bill leaves the door (walk H5).
5. **Can't be checked yet** beneath (no patient on the bill / the name differs from the ID / the walk-in ID / lines not read yet).
6. **The months folded, newest first** (this month open); each opens to a short table (one status per return), the owner's non-cash returns at its foot. **Months before `returns.act_from` are History**, counted only.
7. **F-1200:** a refund shortfall under the rounding line (₹20 or 2 %, `returns.noise_p` / `noise_pct`) is never shown — on the new card, and the S406 month view's *withheld on the refund* badge obeys the same line (`short_noise`, added by `enrich`).
8. The matched medicines fold into one ✓ line; the system lines sit behind *how this was checked* (with the kind flip). The S406 month view and the first view stay one link away; if the new door fails, the page shows the month view and says why.
9. The spot-count list also folds at the foot of the card (it still fills the Checks fold as before).
10. **One waiting number on the page (the coordinator's decision, 09-Nov):** the Needs-you returns line reads the card's own count — `returns_kinds.hub(..., light=True)`, the same function and rule without the batch look-ups — every month, worded as the card: *Returns waiting for your OK — N · ₹X · oldest DD-Mon* (₹ in whole rupees, rounded once on the server for both). If that read fails, the S446 line as it was. `NEEDS_YOU_WITHOUT_S406=1` (older kits' frozen walks) keeps the old path.
11. History is named by its months: *History — April to August* (the data starts in April).
12. **The cold review's findings (09-Nov), fixed:** (1) the box proof reads the LIVE spine read-only (`SPINE_DB`), prints counts only and the time, and stops the install if the hub read takes over 3 s, if the Needs-you line and the card disagree, or if the read saves a row; (2) **cn-approve can decide a return only the spine holds** (an orphan credit note) — its date read from the spine, read only; every other bill as before, an unknown bill still 404; (3) **no new GET writes** — `hub()` reads kinds through `enrich(..., save=False)` / `kind_of(..., save=False)`; cn-detail, the flip, the Month table and `pending_count` keep the old behaviour (save=True); (4) the card escapes `'` with its own escaper (`rhEsc`) and passes every value to onclick through `data-` attributes — the page-wide `esc()` is untouched; (6) an amount the engine could not read is never *recover ₹0*: the line says *amount could not be read* and the button is a plain *Reject*; (7) the batch is compared with the same normalisation on both sides (upper case, trimmed, runs of spaces as one — in Python and in the spine's SQL).
13. **Left as is, by decision (finding 5):** `/finance/darpan/api/cn-hub` is guarded at role *checker*, like its neighbours cn-detail and cn-approve; the decision buttons are drawn for the owner only and cn-approve itself refuses anyone else.

## Install (the VPS; DRY first)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s760kit && cp -rp /root/deploy/repo/deploy_kits/S760_HUB_RETURNS /tmp/s760kit && DRY=1 bash /tmp/s760kit/install_S760_HUB_RETURNS.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s760kit && cp -rp /root/deploy/repo/deploy_kits/S760_HUB_RETURNS /tmp/s760kit && bash /tmp/s760kit/install_S760_HUB_RETURNS.sh
```
Gates: SUMS · KIT_ID · the window (04:00–23:30 IST) · the build lock · the four live pins · the rebuild to the TO pins (both pythons compile) · `walk_s760` green on the rebuilt files · its CONTROL on the live files (19 red, all S760) · the earlier walks S677, S406, S368 — no red beyond the live files' own · the proof by both on a COPY of finance.db and the live spine (read only; it prints the real counts — the waiting returns, the repeats, the batch checks, the time the read takes). After placing: restart, health, the hub / cn-hub / cn-detail / needs-you refuse a stranger, the journal (new PIDs only), the walk and the proof again on the placed files. Any red after placing puts the three files back by itself.

**Undo (one line):** printed at the end of the install — the four `.bak_S760_<from8>` files copied back and `clinic-finance` restarted.

## Proved offline (manojz, 09-Nov)
`walk_s760` on the rebuilt files: **0 failed**; the CONTROL on the live files: **19 failed, all S760** (with the review's: the batch normalised both sides, the reads on a READ-ONLY connection, cn_kind unchanged by the GETs, Approve and Reject on a spine-only return, the unreadable amount, the escaping) (six of them the Needs-you checks: the line counts exactly what the card counts on the fixture, its words, its fail-soft, the wiring, the frozen-walk switch, light = full). `walk_s677` 32/32 green on both. `walk_s406` and `walk_s368`: identical output on old and new (their reds are the live files' own — S406's walk predates S677's spine). The proof ran on the 09-Nov nightly database copy without a spine (every return reads *not examinable* there) — the real counts come from the box's proof.

## Pins
| path | from | to |
|---|---|---|
| /root/finance/returns_kinds.py | 9dd7175de142cbf3c8f6e6b415580822 | see TO_PINS.md5 |
| /root/finance/darpan_app.py | a55ecbed4bbe1230b24565b4185b8755 | see TO_PINS.md5 |
| /root/finance/finance_ui/finance_approvals.html | 037af6261a636273a71db99625da4abf | see TO_PINS.md5 |
| /root/finance/sanjeevni_approvals.py | d063e939bbe14d21a3741b8629fceef7 | see TO_PINS.md5 |

Noted, not this kit's: cn-detail's own day discovery reads `sale_line_item` + `sale_item`, not the spine, so a credit note the spine alone holds (an orphan) is on the hub and not in cn-detail (walk E4).

By design, not a fault: S446's old walk asserts the line's former words (*Counter returns waiting for your OK: N,*); re-run on a box with waiting returns, that one check reads red because the wording now matches the card.

**Built at S414 with the device shell down at the end (F-1197):** every walk below was run on manojz on these exact files (the built TO md5s 6338c361 · 2785ff9e · 11eab919 · 1408fb42 were reproduced byte-for-byte in the cloud from the same patches); the walk and the rehearsal of THIS version were then run again in the cloud on a SCHEMA-ONLY database made from the bundle's own schema files (no patient row): walk_s760 0 failed, its control 19 failed (all S760) -- the same as on manojz; the rehearsal dry / real / again / red all ok (earlier walk: S677). The proof's live-spine path was tried on the walk's made-up spine ('spine yes', cn_kind rows unchanged); the box's DRY run is the first read of the real spine.
