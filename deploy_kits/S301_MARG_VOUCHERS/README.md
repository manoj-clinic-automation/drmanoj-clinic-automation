# S301_MARG_VOUCHERS — the Marg cleanup list becomes Marg vouchers Amir can key, each recorded as entered

**Session 266 (Sanjeevni project) · 17-Sep-2026 evening**, on the owner's "proceed" on the work list: *vouchers Amir can
key — batches of 6 to 8 lines, one Marg voucher each, in the 09-Sep format — each with a "done in Marg" record, so a round
closes on the server.* This builds S235 T7 and D388.

## The change

**The round.** On Amir's board (Stock Check tile → step 6 → *The vouchers*), everything on the Marg cleanup list waits as
voucher lines: confirmed swaps, write-offs, pursued lines and Marg fixes. **Make the Marg vouchers** freezes them as a
round:

- STOCK ISSUE lines (Marg down) and STOCK RECEIVE lines (Marg up) are kept apart.
- Orthotics come first, then medicines, then consumables; sizes of one product stay together.
- A voucher holds **at most six lines** (setting `stock.voucher_lines`). One batch is one voucher in Marg.

**The Excel.** Each round downloads as one workbook in the 09-Sep format, with two sheets:

- **VOUCHER 1 - SHORT** and **VOUCHER 2 - EXCESS**.
- The set header, the batch summary and "how to use" come first.
- Then each block, headed *MARG VOUCHER n of m — enter these k items as ONE voucher in Marg*, with the columns Family ·
  Item · Qty in Marg · Counted <day> · CORRECTION · Marg after · Rate used · Value · Reason · Corrected in Marg on ·
  Initials.
- Sign-off comes last.

**Entered.** Each voucher has a box for **Marg's own voucher number** and an **Entered in Marg** button.

- The record is append-only, with an undo.
- The number is also written to the S221 voucher record (`stock_voucher`).
- A round reads *closed* when every voucher in it is entered.

**A round is never edited.** When something changes later, only the *difference* goes on the next round:

- **A remainder decided later** runs from Marg-after-swap to the shelf.
- **An answer taken back** becomes a reversal.

Each line starts where the last one for that item ended, so keyed in order Marg ends where the lines say.

**The hub's step 6** shows *Not yet on a voucher* and *Marg vouchers entered n of m*, with a button to the vouchers on
Amir's board.

## The proof

**`selftest_s301.py`: 51 checks, 0 failed.** It covers:

- **The files:** the pins, anchors once, refusal, idempotence, backups, compile, both page scripts parse.
- **The waiting lines:** confirmed swaps wait at once, a part swap included, with family and count-day value; a No or an
  undecided line does not wait.
- **The round:** round 1 has ISSUE and RECEIVE apart; a second press finds nothing.
- **Later changes:** a remainder decided later waits 1 → 0; an answer taken back after its round becomes a reversal and
  says so; round 2 with the setting at 1 line gives 2 + 1 vouchers.
- **Every chain adds up.**
- **Entered:** recorded, taken back, and a round closes.
- **The workbook:** both sheets, the batch header and columns, the entered number; it opens in openpyxl.

**Rehearsed on the office PC** against the 17-Sep nightly database, through the live S288 → S299 chain
(`rehearsal_s301.txt`, and `rehearsal_round1_vouchers.xlsx` in the working papers, not in the kit):

- **Today, before any Yes:** 29 decided lines wait, which makes 6 Marg vouchers.
- **With the orthotic pairs answered Yes** in the copy: 45 lines wait, including the 18 swap lines.
- **Round 1:** 45 lines on 8 Marg vouchers — 4 STOCK ISSUE (6, 6, 6, 5 lines) and 4 STOCK RECEIVE (6, 6, 6, 4 lines).
  No line fails to add up or moves 0, no voucher is over six lines, and nothing is left waiting.
- **One voucher recorded as entered:** step 6 reads 1 of 8.
- **The ankle-binder answer taken back:** a STOCK RECEIVE reversal on BAMBOO L (1 → 3) waits for the next round.

**On the box, before anything is placed,** `walk_s301.py` runs the patched module on a scratch copy of the live database.
In order, it checks that:

1. the hub and Amir's board build;
2. a Yes waits as ISSUE + RECEIVE;
3. a round is made and its lines add up;
4. the workbook is written;
5. a voucher is recorded;
6. the Yes taken back becomes a reversal.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S301_MARG_VOUCHERS/install_S301_MARG_VOUCHERS.sh
```

It restarts clinic-finance only.

**Rollback:**

1. Put back the three `.bak_S301_*` files beside the originals.
2. Run `systemctl restart clinic-finance`.

The two new tables are left in place; nothing else reads them.
