# S534 — PLAN REVIEW of the S533 design, by Fable 5.1 (27-Nov-2026, before any build)

*His instruction at the S534 open (09:43 IST): run the whole S533 plan through Fable first, answer whether revisions are needed, build only after his approval. This paper is that review. Nothing was built or changed. Evidence: the 27-Nov code bundle and database copy, read in the device VM by a sub-agent (item names and counts only; no patient or party name). Design under review: `S533_SHORT_COUNT_AND_CORRECTIONS_DESIGN.md` (D1090, D1091), mock-up v9.*

## 1 · Verdict in one line

The design is sound and buildable — every rule it relies on has a data source in the live code today — with **one workflow revision he must decide** (§2.1), **four technical corrections I make myself** (§3), and **two wording fixes** (§4). The order of kits changes: kit A splits in two.

## 2 · For his decision (what he can see)

**2.1 Batch-only corrections — the design forgot a desk that already runs.** Design §3.3(4) and §3.5(c) say: when only a batch is wrong and the total is right, do nothing now; the Batch Stock export decides. But the Expiry watch (S693) already judges Marg's batch report every night and already puts wrong-batch pairs on Amir's card — 11 such asks are open on his card today (ETOZOX 90, LINVIZ 600, TRAMAVIN P, JAKMAC 5, BIO D3 MAX ×2, DYNAPAR QPS PLUS, DOLONEX, OSTOVAXL DM, PEMZOLE D, G DRESS 10; 29 done, 7 superseded, 3 receive-only). The voucher judge shows all 11 as "waiting". Two ways, his to choose:
- **(a) Keep the night-time batch asks as they are** (nothing live changes); the NEW desk simply stays quiet on batch-only gaps and shows those asks in box 2 "On its way to Marg". *Recommended.*
- **(b) Switch the night-time batch asks off**; batch-only differences wait for the weekly Batch Stock export and reach Amir only from the new inquiry path.

**2.2 Pursue — the end of the road (stated, not asked).** The design says Pursue puts a recount on Darpan's next list and "the row comes back with both counts", and stops there. The rule I will build unless he says otherwise: recount agrees with Marg → the row closes by itself ("count error"); recount still short → the row returns to box 1 with both counts, for his Write off (or a second Pursue).

**2.3 A count made after 17:00 shows the next morning.** S952's evening rule (live): a count taken after 17:00 waits for the day's sale report before it is judged. So Write off / Pursue appear on such a row only after it is judged — usually the next morning. Visible behaviour; no choice, only to know.

## 3 · Technical corrections I make (decided, stated once)

1. **Kit A splits.** A1 = the read-only page: the five boxes, every row's inline folds (path · voucher lines · ledger with count rows), the whole-item re-judge shown, F-1706 and F-1707 fixed, F-1708 assessed. Proven end to end on the 27-Nov database copy. A2 = the desk's writes: Write off → Amir's card, Pursue → Darpan's next list, the allowance group button. A2 is the first thing that writes to Amir's card from this page, so it gets its own walk and review. Then B, then C as designed.
2. **Proof claim corrected.** The design said "proof on the 27-Nov database copy (VM only)". The spine (sales) is not in the bundle (F-1661), and `stock_check.record()`, `allowance_units` and the item ledger all read the spine. So: the judge, the record, the counts and the 13 cards' outcomes are proven in the VM; the allowance figures and the ledger fold are proven at the server walk on a made-up spine (as S509/S530 learned).
3. **F-1706 cause confirmed, fix fixed.** `voucher_judge.asks()` merges the S957 re-ask into the earlier count ask and keeps `done_day = max(old, new)` → KT ROS DT's 26-11 ask carries the 19-11 done mark → "not in Marg". Fix: a merged re-ask newer than the done mark clears the done mark → "waiting". Per-ask timestamps exist (`stock_voucher_entered.at`, `amir_job.done_at`, `stock_batch_fix.judged_at`).
4. **F-1707 cause confirmed.** `item_ledger.py` reads sales, vouchers, purchases and batch stock — never `stock_point`, where Darpan's 23-11 counts sit (12 rows). One new source, no schema change.
5. **F-1708 is two things.** The lost batch prefix ("-260753A", "T-260753") is in storage, straight from Marg's purchase export — Marg printed it so; not a ledger fault, a display note ("batch as Marg printed it"). The "bill 4043 for 4100" note: both bills are real (4043 on 02-11, 4100 on 05-11) — the ledger's owed/bill pairing choice, read in A1 before calling it a fault.
6. **Write off's batch is a suggestion.** The system names the batch from Marg's last batch report (today's is 23-11, about a week old), nearest expiry first; the card says so, and Amir keys what Marg shows if Marg disagrees. The judge matches on item + units (batch exact only for batch fixes), so a different batch still closes the ask.
7. **Kit B keeps the card's Hindi shape.** The judge parses the asked quantity from the card's words (`_units_from_words`: "7 patte + 11 goli"); every new card kind keeps that exact shape (or the kit adds structured columns and the judge reads them first).
8. **Kit C gates the register route.** D1088's one-item register route (`ask_registers`) stays second: it fires only when no scan ask is open for that cut name, else both would fire.
9. **Allowance scale.** `setting` holds `stock.allowance_scale` 2, which the design does not mention; A1 reads how S952's judgment uses it and the page shows the allowance figure actually applied to each row.
10. **Pushes.** Reception's and Amir's notifications reuse the parent's `ring_common.push_user` (S958 already imports it); a PLANNED line only if `portal_sw.js` changes.

## 4 · Wording fixes to the design

- "Monthly Batch Stock export" → "the Batch Stock export (about weekly today: 8 kept, 22-10 … 23-11)".
- GEN D3 NANO stands among the 13 old cards but the judge already holds it settled (in Marg / fixed by another entry) — it folds into "Settled in Marg"; no action.

## 5 · What checked out (no change)

- The allowance: `stock_watch.allowance_units` = `stock.allowance_pct` 1.0 % of the item's own sales since its last count, floor `stock.allowance_min_strips` 1 — as §3.1 says.
- Batch-level Marg stock exists (`stock_batch_now`, 334 rows, with expiry) — Write off's batch has a source.
- Asks are stored three ways and merged by the judge (count rounds, Amir's STOCK ISSUE taps, batch fixes); matching = kind + name (cut to 15/20/24, renames) + units, line day ≥ ask day − 1.
- Fresh vs carried count is distinguishable (`stock_point.at/source/status`; `stock_of_record.base_kind` + `old_base` flag).
- Darpan's next list: `stock_watch.ask(mode='next')` with `recount_of` — Pursue is one call.
- Amir's Stock Issue card kind exists (`amir_job` kind tap, key `S957:ktros:7-11`) — Kit B reuses it; the one-tap answer vocabulary (`said_at/said_what/reopened_at`) exists since S533.
- Two taps, no confirm dialog: already the page's pattern; no `confirm(` anywhere on Darpan's or Amir's screens.
- §5's eight live rows agree exactly with `stock_of_record` on the 27-Nov copy (Marg cap 25-11). The judge on the copy: 302 asks — in Marg 227, waiting 24, not in Marg 4, part 4, wrong batch 6, fixed by another entry 26, superseded 11.

## 6 · Noted for the close, not for this build

- `purchase_line` holds each Marg purchase line 6–7 times (once per export) — the purchase import is Sanjeevni's own; an F at the close, repair in its own kit.
- The rule date for "no voucher unless asked" (design §7) is his to set on the page once he has told Amir; nothing waits on it before Kit B.

## 7 · Build order after his approval

A1 (read-only page + F-1706/F-1707, F-1708 assessed) → A2 (Write off · Pursue · allowance group) → B (Amir by himself: write-off card, claimed-not-in-report card, export line, inquiry + settings + tally) → C (voucher scans on the pharmacy lane; Scan App files need a PLANNED line first, D646). Each its own kit number, each proven as the kit pattern says.
