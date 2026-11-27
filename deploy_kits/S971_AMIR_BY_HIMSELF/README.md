# S971_AMIR_BY_HIMSELF — kit B of S534_FINAL_BUILD_PLAN (built at Sanjeevni session 538, 27-Nov-2026)

**What he asked (D1090, D1091; mock-ups v7/v9; his "proceed" 15:10 IST 27-Nov; his word 17:17 IST on the loss register):** Amir's corrections run by
themselves; a voucher nobody asked for is looked into by the system first and asked of Amir only when it cannot explain it; only what stays
unsettled reaches the owner; every loss written off is documented for good.

## The parts
* **The claim card** (`voucher_inquiry.py`, plan 2.2): Amir tapped done, Marg's NEWER Stock Issue / Receive report lacks it → back on his card by itself:
  *Voucher Marg mein nahi mila* — "STOCK ISSUE 2 patte — ITEM. Aapne dd-mm ko 'Kar diya' bataya tha; Marg ki nayi report mein yeh voucher nahi hai." —
  **Ab bana diya** (the next report decides; still missing → the owner's list) · **Pehle bana chuka hoon** (→ the owner's list: the print and scan of that voucher
  come with kit C). His **Back to Amir** (a second round) · **Close** (his OK, a line of his). Only done taps on or after `stock.claim_from` (set to the install
  day): nothing old reaches Amir. A claim closes by itself when Marg's report shows it, or when Marg equals the shelf.
* **The export line**: done taps waiting for a newer report → ONE line on his Hub's Needs-you and in box 2: "Take Marg's Stock Issue + Stock Receive
  (01-10 → today)", however many wait.
* **The inquiry** (plan 2.5), from his rule date (`stock.voucher_rule_from`, his to set on the page the day he tells Amir): (a) the system looks first — an
  ask the line answers (the judge's new *keyed before the ask*, within `stock.voucher_early_days` 7) · an issue and a receive that cancel (the judge, within
  `stock.voucher_cancel_days` 7) · a move between two batches of one item · Marg equal to the shelf after it → explained, closed, counted; (b) else ONE
  question on Amir's card (*Sawaal · Stock voucher* — "L000031 (25-10): STOCK ISSUE — … System ne yeh nahi maanga tha. Kyon banaya?") with five one-tap
  answers; (c) *Galti se bana* → the exact reversal on his card (one card a voucher, one *Marg mein kar diya*), closed by the next report · *Ginti mein farak
  tha* → a recount at the head of Darpan's next list: agrees → explained; not → the reversal to Amir and a red line to the owner · *Batch theek kiya* →
  explained once a newer Batch Stock export is in (the Expiry watch judges batches every night) · *Kharab / expiry* → his one tap OK; (d) his list only when
  unsettled: *Pata nahi*, no answer in `stock.inq_question_days` (2) days, a recount that disagrees → **Reverse** · **Close**; (e) the month's tally, his only.
  A question explained meanwhile leaves Amir's card by itself.
* **Withdraw** (S969's red "not to be keyed" row): his desk write-off Amir has not tapped done → off Amir's card (`done_how 'withdrawn'`; the judge asks nothing of it).
* **The loss register** (his word 17:17): every desk write-off with its count (who counted, counted vs Marg), its group (within the allowance / his call),
  its value at cost (`stock_rate`) and MRP (typed MRP, else the spine's) FROZEN at the tap (`stock_desk_action.cost_p / mrp_p / priced`; the write-offs
  made before this kit priced once at install, said so), Marg's voucher once keyed; withdrawn lines struck and out of the totals; month totals; the
  06-Sep full count's frozen runs beside; the pursued items' ends. `/finance/stockcheck/losses` (printable), `/api/losses` — the owner only.
* **The settings** on the Stock check page (two taps, no dialog): the rule date, the question days, the cancel and keyed-early windows, the batch check, the claim date.
* **F-1725**: the intro line no longer stays "Loading the figures of record…" once the boxes are read.

## Files
`voucher_inquiry.py` NEW · `stock_losses.html` NEW · `stock_check.py` 5a8bde22 → v1.8 · `stock_check.html` ac3de342 · `voucher_judge.py` 768adaa9 → v1.3
(still read only: a reversal's units from its own row, a withdrawn job asks nothing, his cancel window; matching otherwise unchanged) · `amir_day.py` 6212fbf0 (the S971 asks and reversal card, `tapr:`, the sync before his page — at most once in 5 minutes, never inside an
open transaction — and the Hub's lines). Three new tables (made by the installer): `stock_voucher_claim`, `stock_voucher_inquiry`, `stock_inquiry_job`;
three columns on `stock_desk_action`. PLANNED `stock_watch.py` and `stock_amir.html` RELEASED (not touched: the recount is `stock_watch.ask`).
Pushes: ONE to Amir per sync that put cards on his page (`order_rules._push`).

## Proof
* `walk_s971.py` **85/85** on made-up data (S969's fixture), twice on one layout; the control on the live files red at its first line.
  `walk_s969.py` 48/49, `walk_s967.py` 39/41, `walk_s965_regress.py` 31/32 on the new files — only their version lines and S967's rules panel (its rule date,
  cancel and batch rows moved to the editable list).
* **Live shape** (the 27-Nov database copy, device VM only): the desk read only (short 6 · way 14 · moves 3); with the claim date today nothing reaches
  Amir; as if the rule date were 01-11, one question (AD00012, ROSIKA FORTE 1:2) — the rest explained; the full count's three runs read.
* Rehearsal on a made-up root (`rehearse_s971.sh`) **13/13**: dry · red@4 · red@5 · the old mount in the log · install · again · undo · install again ·
  wrong FROM · a read pin moved · a new file already there · the lock · a corrupt kit.

## Reviews
**Cold review** (a separate agent): NOT SAFE — 1 MUST, built in: **M1** the judge's new 'keyed before the ask' step stole lines (a cancel pair broken, a
line already inside Marg's figure taken, the kit's own reversal closed by an older line) → removed from the judge; the inquiry tells such a line only
(after the count the item stands on, within the window), the ask untouched. SHOULD built in: open rows followed whatever the rule date (S1); the
recount's items kept in the same commit, answered by the count's own id never by clocks, no recount in 7 days → his list (S2, S11); the batch check
switch honoured (S3); the undo withdraws open S971 cards (S4); the owner-only, rate-limited sync on his read, nothing written with no date set (S5, S6);
a report must cover the answer's day (S7); box 3 hidden by ask, not item (S8); Withdraw by the write-off's own key (S9); the voucher's day in the
inquiry's key and the reversal keys — Marg's numbers start again each year (S10); Close takes the inquiry's recount off Darpan's list (S11).
**Second look** (a separate agent): NOT SAFE — 1 MUST built in: **M1** one open ask could explain many lines and a row so explained was closed for
good → one ask explains ONE line (oldest voucher first), such a row stays OPEN as 'early' (no card), re-judged every sync and asked of Amir once the ask
is answered by another line; 'keyed twice' is never an explanation. SHOULD built in: the undo sets withdrawn reversal / desk write-off lines aside
(kind 'tap_wd') so the old judge does not read them as "said done"; Reverse from a recount withdraws Darpan's recount; a record row with no figure
waits; Withdraw picks the undone write-off; box 4's voucher lines by day too.
**Re-look** (a separate agent): NOT SAFE — 1 MUST built in: every row drew on the shared ask set (an asked row's 'Galti se bana' made an empty reversal;
an older row starved a newer one) → only a new row or a young 'early' row draws; every other row keeps its real lines; an answer never acts on no lines;
an 'early' row older than the question days is asked of Amir. Walked with a control that goes red on the unfixed rule (I4c). Final re-look SAFE; its two SHOULD built in (a recount that disagrees
on a line no longer 'nobody asked' reverses the row's own lines, else closes; no stale 'watched' words).
**Noted:** the undo withdraws open S971 cards and sets withdrawn lines aside; the tables stay.

## Install
His publish, then one server line (in the installer's head). Undo: `bash /root/deploy/repo/deploy_kits/S971_AMIR_BY_HIMSELF/undo_s971.sh`.
