# S683_AMIR_SCANS_TRUE_ONLY — Amir's scan list carries only a bill clearly missing from Marg

*Sanjeevni session 369 · 30-Oct-2026 · on the owner's "Build only the fix" of 18:05 IST.*

## For the owner
Amir's step 2 (*Scan ho chuke bill*) showed 6 scans: 4 from September, which you have finalised, and 2 from October. All six were bills
that Marg already has. Five were second scans of a bill whose number the machine misread, and one was a bill whose only scan never got
paired with it. After this kit his list shows a scan only when it is clearly a bill missing from Marg. Today that is **0**.
His screen, its words and its layout do not change.

## The six (read from the papers themselves, 30-Oct)
| scan | the paper | in Marg | why it was listed |
|---|---|---|---|
| B-0041 L.K. Drug House | 078347, 07-09, Rs 841 | 783473 (Amir typed a 3 extra), has scan B-0029 | number read 78347 |
| B-0054 Deepam | A000575, 09-09, Rs 950 | 575, has scan B-0026 | number read A0001575, the item rate taken as the total |
| B-0079 A.A. Pharmaceuticals | 0000415, 18-09, Rs 2,195 | 415, has scan B-0224 | the shop's own name read as the supplier, number "1" |
| B-0100 Bass Pharma | A014538, 29-09, Rs 1,597 (blurred) | 14538, **no scan** | a handwritten "412" read as the number, a 2023 date |
| B-0122 Shivaaz | SF 003499 (top strip only) | 3499, has scan B-0134 | a person had answered "not this bill" (07-Oct) |
| B-0150 Deepam | A000678, 12-10, Rs 12,922 | A000678 (Marg date 15-10), has scan B-0154 | number read A0006678 |

## What changes — one file
`/root/finance/purchase_app.py` **da04d546 → 2e1e9023** (`make_s683.py`, three anchored edits):
1. `_s683_final_months`, `_s683_hold` (new, just above `scans_for_amir`).
2. `scans_for_amir` reads the bills that have a scan and the finalised months once, and after S452's own rules **holds** a scan when:
   - **a.** its month is FINALISED (`purchase_month.status='final'`): the scan day's month — and the paper's bill date's month too when
     it is read within 60 days of the scan, so a misread paper date never hides an open month's bill — *month finalised*;
   - **b.** its supplier has a Marg bill within 60 days with the same number (a digit run equal, or a run of 4+ digits inside the other),
     or within 3 days with the last three digits alike — *in Marg: second scan of bill N* / *in Marg: bill N not yet paired*.
   Anything else stays on his list exactly as before.

Untouched: the matcher and its links, reception's questions, Amir's screen and words, the download guard (a held scan answers
*"reception ki jaanch mein"*, as every held scan does), the owner's Scan links line (*N to enter · M held*), every other page.

## The proof
`walk_s683.py`: 23 checks on the walk's OWN rows (suppliers WALKSIX / WALKTWO, export `walk683e1`, scans 9683001+, month 2099-01;
removed after; a row checksum of every table before and after showed no difference) — **23 of 23 green**; the control on the live
file **9 S683 check(s) red · 14 green**. The old = new proof on the 30-Oct database copy with the ten unpaired scans' real readings:
**old 6 listed / new 0 listed · 6 held by S683 · 0 other differences · genuine bills hidden 0 of 460** — every open-month Marg bill,
offered to the rule as a NEW scan of itself, is held by none (the old file reproduces today's live list exactly). On the box the proof
runs on a copy of the database and the LIVE scans (read only), and the installer stops unless all of it holds.

**An independent cold review** found one blocker: a third rule ("an unscanned Marg bill of the supplier within 7 days") hid 13 of
October's 82 bills as if missing — KEDAR and A.A. bill every 2–3 days at repeating amounts. **Dropped.** It also asked for the
finalised-month rule to rest on the scan day (done), for the proof to measure over-hiding (the genuine-bills count, now a gate) and for
walk checks on a sequential supplier, a misread paper date and `purchase_bill.scan_bill_id` (added). Rule b: 0 false holds on 630 bills.
The installer was rehearsed on a made-up root: dry, install, again (ALREADY INSTALLED), a forced red at [8/8] (put back to da04d546),
a moved pin (STOP), a corrupt kit (refused); the lock released every time.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s683kit && cp -rp /root/deploy/repo/deploy_kits/S683_AMIR_SCANS_TRUE_ONLY /tmp/s683kit && bash /tmp/s683kit/install_S683_AMIR_SCANS_TRUE_ONLY.sh
```
Gates → pin da04d546 → rebuild from the box's bytes → compile on both pythons → walk + control + proof on a copy → backup
`purchase_app.py.bak_S683_da04d546` → place → md5 read-back → restart clinic-finance → healthz 200 → `/finance/amir/step/2` 302 →
journal clean → walk on the placed file → lock released. Red after placing: the file back, finance restarted.

**Undo:** `\cp -p /root/finance/purchase_app.py.bak_S683_da04d546 /root/finance/purchase_app.py && systemctl restart clinic-finance`

## Named, not done
- A paper whose number AND amount are both misread (B-0100: a handwritten "412", a wrong total) of a Marg bill that has no scan can
  still reach Amir's list in an open month — rare; holding on "a Marg bill nearby" hid genuine bills, so it is not done.
- Bass bill 14538 (29-09) still has no paired scan: B-0100 is its paper (blurred). September is finalised.
- Marg's 783473 (L.K., 07-09) is the paper's 078347 with an extra 3 — a Marg typing slip in a finalised month; the amount agrees.
- B-0150's paper names the buyer as another shop and address (Sanjeevni Medical Store, Nagaria Parikshit) — for the owner's eye only.
- When Amir moves to digital entry, his grey line *"N scan reception ke paas hain"* will count these holds too (amir_day.py).
- If `scans_for_amir` ever raised, Amir's list would go empty silently (amir_day's catch) — unchanged by this kit.
