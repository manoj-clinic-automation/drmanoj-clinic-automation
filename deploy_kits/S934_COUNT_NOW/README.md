# S934_COUNT_NOW — Count now, placed to the last sale bill (Session 505, the Sanjeevni chat, 23-Nov-2026)

**The owner's word (08:16–08:22 IST):** "I clicked the count button … it is showing at the head of Darpan's next morning list … Why not it gets pushed immediately?" — then: "the count button will have the option to count now or count tomorrow, and accordingly it will show in the points console. And for the count now, he needs to key in the last sale voucher so that matching can be accurate." — "We need to clear whatever counts I have raised … and then you build this."

## What changes
| file | from | what |
|---|---|---|
| `stock_watch.py` | 0dd0a40a → TO | `ask(…, mode)` — `now` (Darpan's screen at once) or `next` (the head of his next morning list, as before; an open ask of the other mode is moved); `withdraw_ask` / `withdraw_all_open`; `now_view` (Darpan's "Abhi ginti" card); `answer_now` (his count + the last sale bill number; checked against Marg's bill chain: not before yesterday's last bill, not more than 300 past it); `_s934_settle` (a bill-placed count is judged once its day's sale report is in); the morning roster never takes a Count now; the day's Needs-you line says a bill-placed count waits for its report. New columns: `stock_watch_ask.mode`, `.closed_how`; `stock_point.last_bill`, `.ask_id` (additive). |
| `stock_figure.py` | 5d15e77d → TO | `points()` / `base()` carry the last bill; `shelf()` carries a bill-placed count forward without the day's sales billed up to that bill (`day_sales_cut`, from the spine's SALE rows, which carry their bill). |
| `stock_check.py` | bf68c55b → TO (v1.3, kit name S930 kept) | `/api/count {item, mode}`; NEW `/api/withdraw {ask_id}`; his open asks with id and mode; a count waiting for its report flagged; the settle runs when the page's record is read. |
| `stock_check.html` | 4d6cbc6f → TO | Count → **Count now / Next list**; "Your open asks" with a two-tap **Withdraw** (no dialog, F-1464); a bill-placed count says "judged when that day's sale report is in". |
| `stockmatch.py` | 57d04d3e → TO (v1.3) | NEW `/finance/stockmatch/api/now`; the mount line `S934 stockmatch mounted v1.3`. |
| `stockmatch.html` | 0ec2e32d → TO | Darpan's **Abhi ginti** card above Aaj ki ginti: strips/tablets (or pieces) + **Aakhri bill no.** + Bhej do; yesterday's last bill shown as a hint. |

## The rule for a Count now
- Darpan keys the shelf quantity and the last sale bill number at that moment.
- The point is saved at once (status `awaits_sales`), with no verdict yet.
- When the sale report for that day is in **in the spine** (an accepted bill-wise sale export reaching the day, taken after it — Marg's bill chain alone is never enough): **expected = the figure at the END of the day** (the shelf figure for a counted item, Marg's for an uncounted one, with the scan-tied arrivals as `expect_for_point`; the point itself left out) **+ that day's sales billed AFTER the number − the deliveries tapped or scanned AFTER the count**. A short beyond the allowance is a loss line by name.
- A purchase bill dated the count day (its hour unknown): the gap is shown and noted, never a loss line.
- A later count of the same item already standing when the report arrives: the bill-placed count is closed unjudged, said in its note.
- The count day's patient returns (credit notes carry no A number) are taken as made before the count — in the judgment and in the carry forward alike.
- Carried forward, the day's sales up to the number are not taken off again.
- No number keyed → judged now by its time, as any spot count, and Darpan is told so. Morning-list counts need no number (they are before the first sale).
- A new financial year (1–7 April) accepts a number below the old series' last.
- An older caller of `ask()` with no mode (the Loss desk's Count this) never moves an open ask.

## The one-off at install
Every ask open at the moment of the install is withdrawn (his word 08:22). A rostered row Darpan has not counted leaves its list, **and any copy carried onto a later list** (a carried row is a new row the ask never pointed to — found by the walk, T8b).

## Proofs
- `synth_s934.py` — made-up spines before and after the count day's report, bills A5001–A5004, Marg's chain to the day before (last 5000): 46 checks (T0–T33, with T18b the morning window, T24c a delivery after the count, T24d a purchase dated the day, T24e a later count, T24f / T25b a patient's return, T27b a call with no mode): the two modes, the move between them, withdraw (and its carried copy), the bill check, the wait, the judgment on a shelf basis / a Marg basis / a loss beyond the allowance, the carry forward (250 → 200 = Marg; the old rule read 150, a false 50 short), the routes on a Flask test app, the pages' markup, the day's line. The control on the live files: 40 red, then stops on the missing column.
- `liveshape_s934.py` — the stock of record built on COPIES of the live databases with the old and the new files: identical row for row; the columns added; Darpan's view and the page's record answer; nothing to judge.
- Not worse on the new files (S837 rule): synth_s933, synth_s928, walk_s927, synth_s894 identical; walk_s930 one SUPERSEDED line (its fixed list of the page's doors — S934 adds `/api/withdraw`), named in the installer.

## The cold review (a separate agent)
NOT SAFE at v3, two MUST: (1) the judgment could run in the morning window when Marg's bill chain already held the day and the spine did not — false loss lines; (2) a delivery after the count was expected on the shelf — false loss lines. Both fixed (v4) with the SHOULDs (a later count; returns; the Marg basis's scan-tied arrivals; the Loss desk's call with no mode) and the LOWs (the evening tag; the roster history; a new financial year; Darpan told when no number; undo closes waiting counts). Left for later: a 'Galat likha? Badlo' for a Count now; S894's asked-count line for a Count now.

## Install (the owner's one line on the VPS, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s934kit && cp -rp /root/deploy/repo/deploy_kits/S934_COUNT_NOW /tmp/s934kit && bash /tmp/s934kit/install_S934_COUNT_NOW.sh
```
Undo: `bash /root/deploy/repo/deploy_kits/S934_COUNT_NOW/undo_s934.sh`

## Kit 2 waits
Kit 2 (every other reader on the stock of record) waits for Darpan's counts and a look at the page together — the owner's word 08:22.
