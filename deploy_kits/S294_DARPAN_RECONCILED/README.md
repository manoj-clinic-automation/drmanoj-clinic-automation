# S294_DARPAN_RECONCILED — Darpan's list only after reconciliation, and only the count-day figures

**Session 264 (Sanjeevni project), after its close · 17-Sep-2026 · step 1 of the stock-check sequence, corrected.**

## The ruling

The owner printed the sheet the desk footer called *"Hand sheet for Darpan"*. It was the wrong sheet:
`render_diffs` — every difference of the count, a paragraph of instructions, NIPRO and VINTAZ on it
although he had merged them (D412, F-337), and the ankle binders on it although their swap comes first.

> *"Kindly check everything in documentation and come up with the proper output. All these detailed
> descriptions are not required here — only after our total reconciliation: the stock they counted on
> that date, the Marg stock export on that date in adjacent columns, and the difference clearly marked.
> That was what was finalized."*

## The change

`stock_app.py` — which lines may go on Darpan's list (`_tranche_pool`), and why none can yet (`_tranche_hold`):

- **no list at all** while any same-salt pair (D385) or orthotic swap family still waits for the owner's
  word on the desk — the swap comes first; *Darpan counts again* counts as a word, so he can send a
  paired line on;
- then only open lines in the real-loss and cannot-be-real lanes, and orthotics on their own list;
- never a consumable (the NIPRO syringes), never a parked or decided line (VINTAZ), never a line whose
  Marg figure is below zero (that is a STOCK RECEIVE voucher, D398), never a bill-check or surplus line;
- the cut button, when it cannot cut, says what it waits for instead of "nothing left".

`pad_receipt.py` — Darpan's list only: columns **Shelf counted | Marg stock | Difference** (the difference
bold), then REASON no. and REMARKS; the paragraph is gone; one line names the count day and what the
two figures are; the reason legend stays.

`stock_desk.html` — the footer link becomes **All differences — your copy (not for Darpan)**, and a new
link **Darpan's list — cut and print it on the loss page** goes where the cut button is.

No table, no route, no data. `clinic-finance` is restarted.

## The proof

`selftest_s294.py`, **0 failed**: the three files at their live pins; anchors once; refusal; idempotence;
backups are the live bytes; compile; the desk script parses; the old and new pool driven over a fixture
shaped like count #1 (the old carried the Marg-negative, the paired and the bill-check lines; the new
cuts nothing while a pair or a family is open, names both in the hold, and once they carry a word gives
only the real losses — no NIPRO, no VINTAZ, no orthotic on the medicine list); the list read back as text.

Rehearsed on the office PC against the 17-Sep nightly database, with the published S288, S292 and S293
patchers applied first (the live chain reproduced byte for byte): today the list is held — *12 same-salt
pairs and 2 orthotic swap families (ANKLE BINDER L, ANKLE BINDER M)*; with those given a word in the
rehearsal copy, list 1 cuts ten real losses and renders as in `EVIDENCE_list1_s294.png`. The installer was
rehearsed in a scratch root: install, second run, refusal on a tampered file, restore on a bad patch.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S294_DARPAN_RECONCILED/install_S294_DARPAN_RECONCILED.sh
```

Rollback: the three `.bak_S294_*` files beside the originals, then `systemctl restart clinic-finance`.

## Then

Desk → give the same-salt pairs and the two ankle-binder families their word → loss page → cut list 1 →
print → Darpan writes the reason → Amir types it → the owner decides on the desk.
